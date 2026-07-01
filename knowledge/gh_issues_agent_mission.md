---
name: gh-issues-agent-mission
description: Mission, philosophy, and cross-repo usage pattern for gh-issues-agent — the canonical GitHub issues/PRs workflow toolkit
version: "2.0"
author: chaz-clark
license: MIT
metadata:
  repo: gh-issues-agent
  last-updated: 2026-06-30
---

# gh-issues-agent — Mission & Strategy

This file captures the mission, usage philosophy, and cross-repo integration pattern for the `gh-issues-agent` toolkit.

---

## Mission

**Make GitHub issues and PRs manageable as local markdown files across any repo.**

This toolkit exists so that LLM agents (and humans) can:
- Work with issues and PRs offline in their native environment (the editor)
- Triage, comment, and close issues/PRs without leaving the terminal
- Use the same workflow across multiple repos with zero per-repo setup

**This is NOT**: a GitHub UI replacement, a project management system, or a PR review tool. It's a local sync layer for issues and PRs.

**Audience**: Solo developers and LLM agents working across multiple repos who want local control over GitHub workflows.

---

## Core Principles

### 1. SSH Auth Only (via `gh` CLI)

All three tools (`gh_sync.py`, `gh_create.py`, `gh_close.py`) authenticate via SSH using the GitHub CLI:

```bash
gh auth login  # Run once per machine
```

After that, all tools fall back to `gh auth token` automatically. No `.env` files, no manual PAT management, no expiring tokens to remember.

An explicit `GH_TOKEN=...` env var still works if set, but SSH auth is the canonical pattern.

### 2. Cross-Repo by Design

Every tool supports `GITHUB_REPO=owner/repo` override:

```bash
# File a bug in another repo you work with
GITHUB_REPO=chaz-clark/canvas-toolbox uv run tools/gh_create.py \
  --title "Bug: missing field in API response" \
  --body-file bug-report.md \
  --label bug

# Sync issues from a dependency you maintain
GITHUB_REPO=chaz-clark/Make-AI-Agents uv run tools/gh_sync.py
```

This means an LLM agent working in one repo can discover a bug in a producer repo and file it directly — no context switching, no copy-paste to browser.

### 3. Issues AND Pull Requests

As of v2.0 (2026-06-30), the toolkit handles **both issues and PRs**:

- `gh_sync.py` pulls issues and PRs into `.github_issues/open/` (files prefixed `issue-NNNN-` or `pr-NNNN-`)
- `gh_close.py` can close or merge PRs (use `--merge` to squash-merge a PR)
- PRs show branch info, draft status, mergeable state, and review comments in the local mirror

**Why?** Public repos (like `canvas-toolbox`) now receive external contributions via PRs. Issues are bugs/enhancements from users; PRs are code contributions. Same workflow, same local mirror, different GitHub primitive.

### 4. Audit-Trail Comments

Never close an issue or PR silently. Always use `--comment`:

```bash
uv run tools/gh_close.py --number 42 --comment "Fixed in commit abc123."
```

The comment becomes the audit trail. Future maintainers (or future sessions) can trace why something was closed without reading the full commit diff.

---

## Workflow Pattern

### Session Start: Sync

```bash
uv run tools/gh_sync.py
```

Pulls all open issues/PRs into `.github_issues/open/`. Moves closed ones to `closed/`. Run this at the start of every session — the local mirror lies as soon as someone touches GitHub directly.

### Working: Read + Triage

Open an issue file from `.github_issues/open/`, read the description + comments, decide whether to fix it.

If it's a bug you can fix: read the full issue (including comments), fix it, commit with `Closes #N` in the message, then close explicitly:

```bash
uv run tools/gh_close.py --number N --comment "Fixed in commit $(git rev-parse HEAD)."
```

If it's a feature request for later: leave it in `open/`, add a comment via GitHub UI or a follow-up script, sync again.

### Filing Bugs Cross-Repo

When you discover a defect in another repo while working locally:

```bash
GITHUB_REPO=owner/repo uv run tools/gh_create.py \
  --title "Bug: description" \
  --body "Repro steps..." \
  --label bug
```

The issue is created on GitHub, and the local mirror drops into that repo's `.github_issues/open/` (if you sync that repo).

### Closing PRs

For external contributions (PRs from others):

```bash
# Merge a PR after review
uv run tools/gh_close.py --number 15 --merge --comment "LGTM, merging."

# Close without merging (e.g., stale or duplicate)
uv run tools/gh_close.py --number 16 --comment "Closing as duplicate of #14."
```

---

## When to Use This vs. GitHub UI

| Task | Use this toolkit | Use GitHub UI |
|---|---|---|
| Read issues/PRs to decide what to work on | ✅ Toolkit (local `.md` files) | Either |
| Comment + close after fixing | ✅ Toolkit (`gh_close.py --comment`) | Either |
| File a bug in another repo | ✅ Toolkit (`GITHUB_REPO=...`) | GitHub UI |
| Review PR code diffs | GitHub UI | GitHub UI |
| Manage labels, milestones, assignees | GitHub UI | GitHub UI |
| Merge a PR with review approval | ✅ Toolkit (`--merge`) | Either |

**Rule of thumb:** if it's part of the daily issue triage + close loop, use the toolkit. If it's repo metadata management or complex PR review, use GitHub UI.

---

## Cross-Repo Integration (Canonical Use Case)

**Problem:** You maintain multiple repos. Bugs discovered in repo A while working in repo B get lost in Slack threads or Notion drafts.

**Solution:** Every repo has access to this toolkit. When an agent working in `canvas-toolbox` discovers a defect in the underlying `gh-issues-agent` toolkit, it files the bug immediately:

```bash
GITHUB_REPO=chaz-clark/gh-issues-agent uv run tools/gh_create.py \
  --title "gh_sync.py fails on repos with no issues" \
  --body "Repro: ..." \
  --label bug
```

The bug lands in `gh-issues-agent`'s issue tracker, not in a comment or a TODO file.

**How repos consume this toolkit:**

1. Clone or vendor `gh-issues-agent` into the consumer repo (gitignored, or as a subtree)
2. Add `gh-issues-agent/tools/` to PATH or call via `uv run`
3. Set `GITHUB_REPO` when filing cross-repo bugs
4. Sync the consumer's own issues with bare `uv run tools/gh_sync.py` (auto-detects from git remote)

No per-repo setup beyond the initial clone. Same three scripts, same workflow, every repo.

---

## What This Toolkit Is NOT For

- **PR code review** — use GitHub UI for diffs, inline comments, review approval
- **Issue triage at scale** (50+ issues/day) — this is for solo maintainers, not enterprise triage teams
- **Replacing `gh` CLI for everything** — this is a focused subset (issues, PRs, comments, close/merge), not a full GitHub wrapper

---

## Living Document Notes

Update this file when:
- A new tool is added to the toolkit (e.g., `gh_label.py`, `gh_assign.py`)
- The auth pattern changes (unlikely, but possible if GitHub deprecates PATs)
- Cross-repo usage expands to support GitHub Enterprise or non-GitHub forges
- The mission changes (e.g., multi-maintainer workflows, issue template automation)

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-29 | Initial extraction from `canvas_toolbox` — issues only, `gh_sync.py` + `gh_close.py` |
| 2.0 | 2026-06-30 | Added PR support (`gh_sync.py` pulls PRs, `gh_close.py --merge`), shipped `gh_create.py`, dropped `.env` in favor of `gh auth token` fallback |
