#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.31",
# ]
# ///
"""
gh_create.py

Create a GitHub issue and drop its markdown mirror into .github-issues/open/.

Usage:
    uv run tools/gh_create.py --title "..." --body "..." --label bug
    uv run tools/gh_create.py --title "..." --body-file draft.md --label bug --label triage
    GITHUB_REPO=owner/repo uv run tools/gh_create.py --title "..."   # cross-repo

Auth:
    GH_TOKEN env var (if set), else falls back to `gh auth token` (gh CLI).

Env vars optional:
    GITHUB_REPO    owner/repo — auto-detected from git remote if not set
"""

import argparse
import difflib
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

OPEN_DIR = Path(".github-issues/open")
API_BASE = "https://api.github.com"


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


def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
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


def _slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:60]


def _issue_filename(number, title):
    return f"issue-{number:04d}-{_slugify(title)}.md"


def _fetch_label_names(repo, token):
    names = []
    page = 1
    while True:
        resp = requests.get(
            f"{API_BASE}/repos/{repo}/labels",
            headers=_headers(token),
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        names.extend(lb["name"] for lb in batch)
        if len(batch) < 100:
            break
        page += 1
    return names


def _validate_labels(requested, available):
    available_set = set(available)
    unknown = [lb for lb in requested if lb not in available_set]
    if not unknown:
        return
    lines = ["ERROR: unknown label(s) for this repo:"]
    for lb in unknown:
        suggestions = difflib.get_close_matches(lb, available, n=3, cutoff=0.5)
        hint = f"  did you mean: {', '.join(suggestions)}" if suggestions else "  (no close match)"
        lines.append(f"  - {lb!r}")
        lines.append(hint)
    lines.append("")
    lines.append(f"Valid labels: {', '.join(sorted(available))}")
    print("\n".join(lines))
    sys.exit(2)


def _render_new_issue(issue):
    number = issue["number"]
    title = issue["title"]
    state = issue["state"]
    labels = [lb["name"] for lb in issue.get("labels", [])]
    created = issue.get("created_at", "")
    updated = issue.get("updated_at", "")
    author = issue.get("user", {}).get("login", "unknown")
    url = issue.get("html_url", "")
    body = (issue.get("body") or "").strip()

    return (
        "---\n"
        f"issue: {number}\n"
        f'title: "{title}"\n'
        f"state: {state}\n"
        f"labels: [{', '.join(labels)}]\n"
        f"created: {created}\n"
        f"updated: {updated}\n"
        f"author: {author}\n"
        f"url: {url}\n"
        "---\n\n"
        f"# #{number} — {title}\n\n"
        "## Description\n\n"
        f"{body if body else '_No description provided._'}\n"
    )


def create_issue(repo, token, title, body, labels):
    if labels:
        available = _fetch_label_names(repo, token)
        _validate_labels(labels, available)

    payload = {"title": title}
    if body:
        payload["body"] = body
    if labels:
        payload["labels"] = labels

    resp = requests.post(
        f"{API_BASE}/repos/{repo}/issues",
        headers=_headers(token),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    issue = resp.json()

    OPEN_DIR.mkdir(parents=True, exist_ok=True)
    filename = _issue_filename(issue["number"], issue["title"])
    (OPEN_DIR / filename).write_text(_render_new_issue(issue), encoding="utf-8")

    print(f"  Created #{issue['number']} on {repo}")
    print(f"  URL:   {issue['html_url']}")
    print(f"  Local: {OPEN_DIR / filename}")
    return issue


def main():
    parser = argparse.ArgumentParser(
        description="Create a GitHub issue and mirror it locally."
    )
    parser.add_argument("--title", required=True, help="Issue title")
    parser.add_argument("--body", default=None, help="Issue body (markdown)")
    parser.add_argument("--body-file", default=None, help="Read issue body from a file (precedence over --body)")
    parser.add_argument(
        "--label", action="append", default=[],
        help="Label to apply (repeatable). Validated against the repo's label taxonomy."
    )
    args = parser.parse_args()

    body = args.body or ""
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")

    token = _resolve_token()
    if not token:
        print("ERROR: no GitHub token. Set GH_TOKEN or run `gh auth login`.")
        sys.exit(1)

    repo = os.environ.get("GITHUB_REPO", "") or _detect_repo()
    if not repo:
        print("ERROR: Could not detect repo. Set GITHUB_REPO=owner/repo.")
        sys.exit(1)

    print(f"Creating issue on {repo}...")
    create_issue(repo, token, args.title, body, args.label)
    print("Done.")


if __name__ == "__main__":
    main()
