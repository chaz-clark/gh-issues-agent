#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.31",
# ]
# ///
"""
gh_sync.py

Pull all open GitHub issues + comments into .github-issues/open/ as markdown files.
Moves files for issues no longer open to .github-issues/closed/.

Usage:
    uv run tools/gh_sync.py
    ./tools/gh_sync.py        # if marked executable

Auth:
    GH_TOKEN env var (if set), else falls back to `gh auth token` (gh CLI).

Env vars optional:
    GITHUB_REPO    owner/repo — auto-detected from git remote if not set
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
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

OPEN_DIR = Path(".github-issues/open")
CLOSED_DIR = Path(".github-issues/closed")

API_BASE = "https://api.github.com"


def _headers():
    return {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_all_pages(url, params=None):
    params = dict(params or {})
    params["per_page"] = 100
    results = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results


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


def _format_date(iso):
    try:
        iso_clean = iso.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_clean)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso


def _render_issue(issue, comments, pr_data=None):
    number = issue["number"]
    title = issue["title"]
    state = issue["state"]
    labels = [lb["name"] for lb in issue.get("labels", [])]
    created = issue.get("created_at", "")
    updated = issue.get("updated_at", "")
    author = issue.get("user", {}).get("login", "unknown")
    url = issue.get("html_url", "")
    body = (issue.get("body") or "").strip()
    is_pr = "pull_request" in issue

    lines = [
        "---",
        f"number: {number}",
        f"type: {'pull_request' if is_pr else 'issue'}",
        f'title: "{title}"',
        f"state: {state}",
        f"labels: [{', '.join(labels)}]",
        f"created: {created}",
        f"updated: {updated}",
        f"author: {author}",
        f"url: {url}",
    ]

    if is_pr and pr_data:
        lines.append(f"head: {pr_data.get('head', {}).get('ref', 'unknown')}")
        lines.append(f"base: {pr_data.get('base', {}).get('ref', 'unknown')}")
        lines.append(f"draft: {pr_data.get('draft', False)}")
        lines.append(f"mergeable: {pr_data.get('mergeable', 'unknown')}")
        lines.append(f"merged: {pr_data.get('merged', False)}")

    lines.extend([
        "---",
        "",
        f"# #{number} — {title}",
        "",
        "## Description",
        "",
        body if body else "_No description provided._",
    ])

    if comments:
        lines += ["", "---", "", "## Comments", ""]
        for c in comments:
            commenter = c.get("user", {}).get("login", "unknown")
            date = _format_date(c.get("created_at", ""))
            comment_body = (c.get("body") or "").strip()
            lines += [
                f"### @{commenter} — {date}",
                "",
                comment_body if comment_body else "_Empty comment._",
                "",
            ]

    return "\n".join(lines) + "\n"


def _issue_filename(number, title, is_pr=False):
    prefix = "pr" if is_pr else "issue"
    return f"{prefix}-{number:04d}-{_slugify(title)}.md"


def sync(repo):
    OPEN_DIR.mkdir(parents=True, exist_ok=True)
    CLOSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Syncing issues and PRs from {repo}...")

    items = _get_all_pages(f"{API_BASE}/repos/{repo}/issues", {"state": "open"})

    issue_count = sum(1 for i in items if "pull_request" not in i)
    pr_count = sum(1 for i in items if "pull_request" in i)
    print(f"  {issue_count} open issue(s), {pr_count} open PR(s) found\n")

    current_numbers = set()

    for item in items:
        number = item["number"]
        title = item["title"]
        is_pr = "pull_request" in item
        current_numbers.add(number)

        # Fetch full PR data if this is a PR
        pr_data = None
        if is_pr:
            resp = requests.get(
                f"{API_BASE}/repos/{repo}/pulls/{number}",
                headers=_headers(),
                timeout=30
            )
            if resp.status_code == 200:
                pr_data = resp.json()

        comments = []
        if item.get("comments", 0) > 0:
            comments = _get_all_pages(
                f"{API_BASE}/repos/{repo}/issues/{number}/comments"
            )

        filename = _issue_filename(number, title, is_pr)
        content = _render_issue(item, comments, pr_data)
        (OPEN_DIR / filename).write_text(content, encoding="utf-8")

        label_str = ", ".join(lb["name"] for lb in item.get("labels", []))
        label_str = f" [{label_str}]" if label_str else ""
        item_type = "PR" if is_pr else "issue"
        print(f"  #{number} ({item_type}){label_str} {title}")

    # Move files for issues/PRs no longer open → closed/
    moved = 0
    for pattern in ["issue-*.md", "pr-*.md"]:
        for f in sorted(OPEN_DIR.glob(pattern)):
            m = re.match(r"(?:issue|pr)-(\d+)-", f.name)
            if m and int(m.group(1)) not in current_numbers:
                shutil.move(str(f), str(CLOSED_DIR / f.name))
                moved += 1
                print(f"  -> moved {f.name} to closed/")

    print(f"\nDone: {issue_count} issue(s), {pr_count} PR(s) open; {moved} moved to closed/")


def main():
    if not GH_TOKEN:
        print("ERROR: no GitHub token. Set GH_TOKEN or run `gh auth login`.")
        sys.exit(1)

    repo = GITHUB_REPO or _detect_repo()
    if not repo:
        print("ERROR: Could not detect repo. Set GITHUB_REPO=owner/repo.")
        sys.exit(1)

    sync(repo)


if __name__ == "__main__":
    main()
