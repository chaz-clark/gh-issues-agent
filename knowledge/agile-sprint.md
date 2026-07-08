---
name: gh-issues-agent-sprints
description: Sprint plan and milestone tracker for gh-issues-agent toolkit development
version: "2.0"
author: chaz-clark
license: MIT
metadata:
  repo: gh-issues-agent
  last-updated: 2026-06-30
---

# gh-issues-agent — Sprint Plan

Tracks active and completed work for the `gh-issues-agent` toolkit. Each sprint represents a cohesive feature set or bug-fix wave. Updated when issues are closed and committed to GitHub.

---

## Sprint Status Legend

- `[ ]` — not started
- `[~]` — in progress
- `[x]` — complete (closed on GitHub + committed)

---

## Sprint 1 — Core Toolkit (Extraction) ✅

**Goal:** Extract issue sync and close tools from `canvas_toolbox`, establish cross-repo pattern.

**Status:** Complete (2026-04-29)

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| — | Extract `gh_sync.py` from canvas_toolbox | M | `[x]` | Initial extraction |
| — | Extract `gh_close.py` from canvas_toolbox | M | `[x]` | Initial extraction |
| — | Establish `.github-issues/` local mirror pattern | S | `[x]` | Initial extraction |
| — | Add AGENTS.md v1.0 | S | `[x]` | — |

**Definition of done:**
- Tools work standalone (no canvas_toolbox dependencies)
- `GITHUB_REPO=owner/repo` override works for cross-repo usage
- Local mirror syncs to `.github-issues/open/` and `closed/`

---

## Sprint 2 — Issue Creation ✅

**Goal:** Add ability to create issues from the command line (completing CRUD).

**Status:** Complete (2026-06-01)

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| #2 | Add `gh_create.py` tool for creating issues | M | `[x]` | 17bc679 |
| — | Drop `python-dotenv` dependency (use `gh auth token` fallback) | XS | `[x]` | 17bc679 |

**Definition of done:**
- `gh_create.py --title "..." --body "..." --label bug` works
- Cross-repo creation via `GITHUB_REPO=owner/repo` works
- Label validation against repo taxonomy
- All three tools use `gh auth token` fallback (SSH auth canonical)

---

## Sprint 3 — PR Support (v2.0) ✅

**Goal:** Handle pull requests alongside issues (public repos now receive external contributions via PRs).

**Status:** Complete (2026-06-30)

| # | Issue | Size | Status | Commit |
|---|---|---|---|---|
| — | Update `gh_sync.py` to pull PRs (remove filter, add PR metadata rendering) | M | `[x]` | This session |
| — | Update `gh_close.py` to close/merge PRs (`--merge` flag for squash-merge) | M | `[x]` | This session |
| — | Distinguish PR files (`pr-NNNN-*.md`) from issue files (`issue-NNNN-*.md`) | XS | `[x]` | This session |
| — | Render PR-specific metadata (head/base branch, draft, mergeable, merged status) | S | `[x]` | This session |
| — | Update knowledge files to reflect v2.0 mission (drop stale Canvas content) | M | `[x]` | This session |

**Definition of done:**
- `gh_sync.py` pulls both issues and PRs
- `gh_close.py --number N --merge` merges PRs
- PR files show branch, draft status, mergeable state in frontmatter
- AGENTS.md updated to document PR support
- Mission file reflects cross-repo issues/PRs toolkit purpose

---

## Future Work (Backlog)

Ideas for future sprints, not yet scheduled:

### Potential Sprint 4 — Enhanced PR Workflow
- Add `--merge-method` flag to `gh_close.py` (support merge, squash, rebase)
- Fetch PR review comments and approval status in sync
- Add `--draft` flag to create draft PRs (if we add PR creation tool)

### Potential Sprint 5 — Label & Milestone Management
- `gh_label.py` — create/update/delete labels
- `gh_milestone.py` — assign issues/PRs to milestones
- `gh_assign.py` — assign issues/PRs to users

### Potential Sprint 6 — Batch Operations
- `gh_batch_close.py` — close multiple issues/PRs by number or label query
- `gh_batch_label.py` — apply labels to multiple issues matching a pattern
- Dry-run mode for all batch operations

---

## How to Update This File

When closing an issue or completing work:
1. Mark its row `[x]` and fill in the commit hash
2. When all items in a sprint are `[x]`, mark the sprint Status as **Complete** and move it to the completed section above Future Work
3. Run `gh_sync.py` to confirm all sprint issues are in `.github-issues/closed/` (if tracked on GitHub)
4. Note any scope changes or lessons learned in the sprint's notes

---

## Completed Sprints Summary

| Sprint | Completion Date | Shipped |
|---|---|---|
| Sprint 1 — Core Toolkit | 2026-04-29 | `gh_sync.py`, `gh_close.py`, AGENTS.md v1.0 |
| Sprint 2 — Issue Creation | 2026-06-01 | `gh_create.py`, SSH auth fallback, issue #2 closed |
| Sprint 3 — PR Support (v2.0) | 2026-06-30 | PR sync, PR close/merge, updated knowledge files |

---

## Notes

- This repo's issues track bugs and enhancements to the toolkit itself
- Cross-repo bug reports (filed via `GITHUB_REPO=...`) land in the target repo's tracker, not here
- Sprint sizing: XS (<1hr), S (2-4hr), M (half day), L (1-2 days), XL (2-3 days)
