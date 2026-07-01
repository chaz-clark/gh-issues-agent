#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.31",
# ]
# ///
"""
gh_close.py

Post a comment and close a GitHub issue or PR. Moves the local file from
.github_issues/open/ to .github_issues/closed/.

Usage:
    uv run tools/gh_close.py --number 42 --comment "Fixed in commit abc123."
    uv run tools/gh_close.py --number 42 --merge  # For PRs: merge instead of just close
    ./tools/gh_close.py --number 42 --comment "..."   # if marked executable

Auth:
    GH_TOKEN env var (if set), else falls back to `gh auth token` (gh CLI).

Env vars optional:
    GITHUB_REPO    owner/repo — auto-detected from git remote if not set
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import requests


def _resolve_token():
    token = os.environ.get("GH_TOKEN", "").strip()
    if token:
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return ""


GH_TOKEN = _resolve_token()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")

OPEN_DIR = Path(".github_issues/open")
CLOSED_DIR = Path(".github_issues/closed")

API_BASE = "https://api.github.com"


def _headers():
    return {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _detect_repo():
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        m = re.search(r"github\.com[:/](.+?/[^.]+?)(?:\.git)?$", url)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def close_issue_or_pr(repo, number, comment=None, merge=False):
    # Determine if it's a PR or issue by checking local files
    is_pr = False
    for f in OPEN_DIR.glob(f"pr-{number:04d}-*.md"):
        is_pr = True
        break

    # Post comment if provided (works for both issues and PRs)
    if comment:
        resp = requests.post(
            f"{API_BASE}/repos/{repo}/issues/{number}/comments",
            headers=_headers(),
            json={"body": comment},
            timeout=30,
        )
        resp.raise_for_status()
        print(f"  Comment posted to #{number}")

    # Handle PR merge or close
    if is_pr:
        if merge:
            # Attempt to merge the PR
            resp = requests.put(
                f"{API_BASE}/repos/{repo}/pulls/{number}/merge",
                headers=_headers(),
                json={"merge_method": "squash"},  # Can be: merge, squash, rebase
                timeout=30,
            )
            if resp.status_code == 200:
                print(f"  PR #{number} merged on GitHub")
            else:
                print(f"  Warning: Could not merge PR #{number} (status {resp.status_code})")
                print(f"  Falling back to close without merge")
                resp = requests.patch(
                    f"{API_BASE}/repos/{repo}/pulls/{number}",
                    headers=_headers(),
                    json={"state": "closed"},
                    timeout=30,
                )
                resp.raise_for_status()
                print(f"  PR #{number} closed on GitHub")
        else:
            # Just close the PR without merging
            resp = requests.patch(
                f"{API_BASE}/repos/{repo}/pulls/{number}",
                headers=_headers(),
                json={"state": "closed"},
                timeout=30,
            )
            resp.raise_for_status()
            print(f"  PR #{number} closed on GitHub")
    else:
        # Close the issue
        resp = requests.patch(
            f"{API_BASE}/repos/{repo}/issues/{number}",
            headers=_headers(),
            json={"state": "closed"},
            timeout=30,
        )
        resp.raise_for_status()
        print(f"  Issue #{number} closed on GitHub")

    # Move local file to closed/
    CLOSED_DIR.mkdir(parents=True, exist_ok=True)
    moved = False
    for pattern in [f"issue-{number:04d}-*.md", f"pr-{number:04d}-*.md"]:
        for f in sorted(OPEN_DIR.glob(pattern)):
            dest = CLOSED_DIR / f.name
            shutil.move(str(f), str(dest))
            print(f"  Moved {f.name} -> closed/")
            moved = True

    if not moved:
        print(f"  Note: no local file found for #{number} in open/ — run gh_sync.py to refresh")


def main():
    parser = argparse.ArgumentParser(
        description="Close a GitHub issue or PR and move its local file to closed/"
    )
    parser.add_argument(
        "--number", type=int, required=True,
        help="Issue or PR number to close"
    )
    parser.add_argument(
        "--issue", type=int, dest="number",
        help="(Deprecated: use --number) Issue number to close"
    )
    parser.add_argument(
        "--comment", type=str, default=None,
        help="Comment to post before closing (include commit hash or PR reference)"
    )
    parser.add_argument(
        "--merge", action="store_true",
        help="For PRs: merge instead of just closing (uses squash merge)"
    )
    args = parser.parse_args()

    if not GH_TOKEN:
        print("ERROR: no GitHub token. Set GH_TOKEN or run `gh auth login`.")
        sys.exit(1)

    repo = GITHUB_REPO or _detect_repo()
    if not repo:
        print("ERROR: Could not detect repo. Set GITHUB_REPO=owner/repo.")
        sys.exit(1)

    print(f"Closing #{args.number} on {repo}...")
    close_issue_or_pr(repo, args.number, args.comment, args.merge)
    print("Done.")


if __name__ == "__main__":
    main()
