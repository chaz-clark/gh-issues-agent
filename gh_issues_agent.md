---
name: GitHubIssuesAgent
version: "1.0"
last_updated: 2026-07-07
description: Local file-based GitHub issues and PRs workflow — sync, triage, close, and merge without leaving the editor
complexity: standard
agent_type: workflow
platforms: [GitHub]
entry_point: uv run tools/gh_sync.py
dependencies:
  - requests>=2.33.1
  - python-dotenv>=1.2.2 (optional, falls back to gh CLI)
environment:
  GH_TOKEN: GitHub personal access token (or use gh auth token)
  GITHUB_REPO: owner/repo (optional, auto-detected from git remote)
tools:
  - tools/gh_sync.py
  - tools/gh_create.py
  - tools/gh_close.py
knowledge_files:
  - knowledge/agile_sprint.md
  - knowledge/gh_issues_agent_mission.md
  - knowledge/github_issues_reference.md
  - knowledge/handling_issues_with_prs.md
---

# GitHub Issues Agent Guide

## Mission

Manage GitHub issues and pull requests for any repo as a local, file-based workflow. Pull issues/PRs down as readable markdown, triage by label, work through fixes and features in priority order, and close (or merge) them with an audit-trail comment when done.

**What it does**: Syncs open GitHub issues + PRs + comments into `.github_issues/open/` as markdown files, helps triage and prioritize work by label, and closes/merges them via the GitHub API when resolved.

**Why it exists**: Keeps issue tracking local and integrated with the development workflow — no browser context-switching, full comment history available while coding, and a clear audit trail of what was fixed and when.

**Who uses it**: Solo developers (or LLMs working on their behalf) who want to triage and close issues/PRs from the terminal as part of a normal commit workflow.

**Cross-repo capability**: Any repo can file bugs against any other repo with `GITHUB_REPO=owner/repo uv run tools/gh_create.py ...` — zero per-repo setup required beyond `gh auth login`.

---

## Agent Instructions

1. Read this file for mission, workflow, label taxonomy, and pitfalls.
2. Read `knowledge/agile_sprint.md` to understand the current sprint, what is in progress, and what is next. Always check sprint status before proposing work.
3. Read `knowledge/gh_issues_agent_mission.md` for the full milestone rationale and issue triage philosophy.
4. Read `knowledge/handling_issues_with_prs.md` for the pattern to follow when an issue references an existing pull request (from a contributor or prior attempt).
5. See `knowledge/github_issues_reference.md` for GitHub API field reference.

---

## Agent Quickstart

1. **Check the sprint**: Read `knowledge/agile_sprint.md` — find the active sprint, identify the next `[ ]` issue in order
2. **Sync issues**: Run `uv run tools/gh_sync.py` to pull all open issues + PRs + comments into `.github_issues/open/`
3. **Pick work**: Open the `.md` file for the next issue/PR in the sprint plan, read the full description + comments
4. **Check for PR references**: If working on an issue that mentions an existing PR, use `gh pr view <number>` to review it first (see `knowledge/handling_issues_with_prs.md`)
5. **Fix it**: Make the code change — do not commit yet
6. **Commit**: After verifying the fix locally — commit with a descriptive message referencing the issue (`Fixes #42` or `Closes #42`) and PR if relevant (`Supersedes PR #120`)
7. **Close/Merge**: Run `uv run tools/gh_close.py --number 42 --comment "Fixed in commit abc123."` (add `--merge` for PRs you want to squash-merge)
8. **Update the sprint**: Mark the issue `[x]` in `knowledge/agile_sprint.md` with the commit hash
9. **Re-sync**: Run `uv run tools/gh_sync.py` to confirm all sprint issues are in `closed/`

---

## Workflow Steps

### 1. Check Sprint
Read `knowledge/agile_sprint.md` — find the active sprint and the next `[ ]` issue in order. Do not pick work outside sprint order without a reason.

**Input**: `knowledge/agile_sprint.md`
**Output**: Next issue number to work

### 2. Sync
Pull all open issues + PRs + comments from GitHub into `.github_issues/open/` as markdown files.

**Command**: `uv run tools/gh_sync.py`
**Input**: `GH_TOKEN` (or `gh auth token`), repo (auto-detected or `GITHUB_REPO` env var)
**Output**: `.github_issues/open/issue-NNNN-*.md` and `pr-NNNN-*.md` files

### 3. Read Issue/PR
Open the issue/PR file for the sprint's next item. Read description and all comments before writing any code.

**Input**: `.github_issues/open/issue-NNNN-*.md` or `pr-NNNN-*.md`
**Output**: Full context for the fix

### 4. Fix
Edit code. Do not commit yet — verify locally first.

**Input**: Issue/PR file context + codebase
**Output**: Edited files, uncommitted

### 5. Commit
Commit with message referencing the issue (`Fixes #N` or `Closes #N`).

**Input**: Verified fix
**Output**: Committed fix with issue reference

### 6. Close or Merge
Run `gh_close.py --number N --comment "Fixed in commit <hash>."` to post comment, close on GitHub, move local file to `closed/`.

For PRs: Add `--merge` flag to squash-merge instead of just closing.

**Command**: `uv run tools/gh_close.py --number 42 --comment "Fixed in abc123."`
**Command (merge PR)**: `uv run tools/gh_close.py --number 42 --comment "LGTM" --merge`
**Input**: Issue/PR number, commit hash
**Output**: Closed issue/PR on GitHub + file in `.github_issues/closed/`

### 7. Update Sprint
Mark the issue `[x]` in `knowledge/agile_sprint.md` with commit hash. If all sprint issues are `[x]`, run full QC sign-off, then tag and move sprint to Completed Sprints.

**Input**: `knowledge/agile_sprint.md`, commit hash
**Output**: Updated sprint tracking + optional version tag

### 8. Re-sync
Run `gh_sync.py` to confirm all sprint issues are in `closed/`.

**Command**: `uv run tools/gh_sync.py`
**Input**: GitHub API
**Output**: Refreshed `.github_issues/open/`

---

## Label Taxonomy

Priority order and handling rules for GitHub issue labels.

| Label | Priority | Handling | Close Template |
|-------|----------|----------|----------------|
| **bug** | 1 | Fix before any enhancement work. Every open bug blocks a potential user. | `Fixed in commit {hash}. {one-line description of what was broken and what changed}.` |
| **enhancement** | 2 | Batch by tool affected. Work one tool's enhancements together. | `Implemented in commit {hash}. {brief description of what was added and how it works}.` |
| **documentation** | 3 | Quick wins — update README, AGENTS.md, or knowledge files. Usually resolvable in a single pass. | `Updated in commit {hash}. {what was clarified or added}.` |
| **question** | 4 | Answer in a comment, then close. If the answer reveals a missing doc, open a documentation issue. | `Answered above. Feel free to reopen if you need more detail.` |
| **duplicate** | 5 | Close immediately with a reference to the canonical issue. | `Duplicate of #{canonical_issue}. Tracking there.` |
| **wontfix** | 6 | Close with a clear explanation of why the request is out of scope. | `Closing as out of scope: {reason}. {alternative if any}.` |
| **good first issue** | 7 | Leave open for contributors. Add a comment with pointers to relevant files if one is not already there. | `Fixed by @{contributor} in commit {hash}. Thanks!` |

---

## Issue File Format

Files written by `gh_sync.py` to `.github_issues/open/`:

### Issues
**Filename pattern**: `issue-{number:04d}-{slug}.md`

**Frontmatter fields**:
- `issue`: Issue number
- `title`: Issue title
- `state`: `open` or `closed`
- `labels`: Array of label names
- `created`: ISO 8601 timestamp
- `updated`: ISO 8601 timestamp
- `author`: GitHub username
- `url`: Browser URL for the issue

**Sections**:
1. `# #{number} — {title}`
2. `## Description` — issue body
3. `---` (separator)
4. `## Comments` — if any exist

**Comment format**: `### @{username} — {YYYY-MM-DD HH:MM UTC}\n\n{body}`

### Pull Requests
**Filename pattern**: `pr-{number:04d}-{slug}.md`

**Additional frontmatter fields** (beyond issue fields):
- `head`: Source branch (`user:branch`)
- `base`: Target branch (usually `main`)
- `draft`: `true` or `false`
- `mergeable`: `true`, `false`, or `unknown`
- `mergeable_state`: GitHub's merge status (`clean`, `dirty`, `blocked`, etc.)

---

## Slug Rules

Issue/PR filenames use slugified titles:
- Lowercase
- Spaces → hyphens
- Non-alphanumeric removed
- Max 60 chars

Example: "Canvas sync fails on empty modules" → `canvas-sync-fails-on-empty`

---

## Key Principles

### 1. Always Include a Commit Reference When Closing
Every `gh_close.py` call should include `--comment` with the commit hash or PR number.

**Why**: Without a link, there's no way to trace what change resolved the issue. GitHub cross-references work automatically when the comment includes `Fixes #N` or a direct commit URL. This is the audit trail.

### 2. Work Bugs Before Features
The `bug` label is priority 1 — resolve all open bugs before picking up enhancements.

**Why**: A toolkit with broken behavior erodes trust faster than a toolkit with fewer features. Users who hit a bug and file it deserve a fast response.

### 3. Batch Enhancements by Topic
Group `enhancement` issues by the file or module they affect before starting work — keep related changes in one pass instead of context-switching across modules.

**Why**: Context switching between tools mid-session costs more than the overhead of grouping. Related enhancements often share a code path and can be addressed in one pass.

### 4. Never Edit Files in `.github_issues/` by Hand
The `open/` and `closed/` files are generated output — treat them as read-only. Edits will be overwritten on the next `gh_sync.py` run.

**Why**: The sync script overwrites files on each run. Local edits create a false record that disappears without warning.

### 5. Re-run gh_sync.py at Session Start
The local mirror lies as soon as someone touches GitHub directly (browser, mobile app, another tool). Always sync at the start of each session.

**Why**: You need the current state. Stale local files lead to closing the wrong issue or missing new reports.

---

## API Endpoints Reference

All endpoints use base URL `https://api.github.com`.

### Required Headers
```
Authorization: Bearer {GH_TOKEN}
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
```

### List Open Issues and PRs
```
GET /repos/{owner}/{repo}/issues?state=open&per_page=100&page=N
```
Returns both issues AND pull requests. Filter PRs by checking for `pull_request` key.

### Get PR Details
```
GET /repos/{owner}/{repo}/pulls/{number}
```
Fetches additional PR metadata (head/base branches, mergeable state, draft status).

### List Comments
```
GET /repos/{owner}/{repo}/issues/{issue_number}/comments?per_page=100&page=N
```
Paginated. Fetch all pages if `issue.comments > 100`.

### Post Comment
```
POST /repos/{owner}/{repo}/issues/{issue_number}/comments
Body: {"body": "markdown string"}
```
Returns 201 on success.

### Close Issue/PR
```
PATCH /repos/{owner}/{repo}/issues/{issue_number}
Body: {"state": "closed"}
```
Returns 200 with updated object.

### Merge PR (Squash)
```
PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge
Body: {"merge_method": "squash"}
```
Returns 200 on successful merge.

### Check Rate Limit
```
GET /rate_limit
```
Returns remaining requests and reset timestamp. Use before large syncs.

**Rate limits**: 5,000 requests/hour for authenticated users.

---

## Existing Tooling

| Tool | Purpose | When to use |
|---|---|---|
| `tools/gh_sync.py` | Pulls open issues AND PRs + comments into `.github_issues/open/` (issues as `issue-NNNN-*.md`, PRs as `pr-NNNN-*.md`); archives closed ones into `closed/`. | Start of every session, and after closing an issue or merging a PR. |
| `tools/gh_create.py --title "..." [--body / --body-file ...] [--label ...]` | Creates a new issue on GitHub and drops its markdown mirror into `.github_issues/open/`. Validates labels against the repo taxonomy. | When filing a bug or enhancement — including against another repo via `GITHUB_REPO=owner/repo`, the canonical cross-repo case where an agent discovers a defect in a producer repo while working in a consumer. |
| `tools/gh_close.py --number N --comment "..." [--merge]` | Posts comment, closes issue/PR on GitHub, moves local file to `closed/`. For PRs: `--merge` flag squash-merges instead of just closing. | Always — never close issues/PRs via GitHub UI when working from this repo (audit trail lives in the comment). Use `--merge` for PRs you've reviewed and want to land. |

**Auth**: All three tools first check the `GH_TOKEN` env var, then fall back to `gh auth token` (SSH-based). Run `gh auth login` once and the toolkit works with no `.env` or manual export. An explicit `GH_TOKEN=...` still wins if set, but SSH auth via `gh` CLI is the canonical pattern.

**Note**: The `--issue` flag in `gh_close.py` is deprecated (use `--number` instead, which works for both issues and PRs).

---

## Validation

### Pre-run Checklist
- [ ] `GH_TOKEN` set (or `gh auth token` works)
- [ ] Token has `repo` or `public_repo` scope on the target repo
- [ ] `uv sync` completed (requests installed; python-dotenv optional)
- [ ] `.github_issues/` folder exists (or will be created by `gh_sync.py`)

### Post-sync Checklist
- [ ] `.github_issues/open/` contains `.md` files matching open issues/PRs on GitHub
- [ ] Each file has frontmatter (issue/pr number, title, labels, url)
- [ ] Comments section present on issues/PRs that have comments
- [ ] PR files include head/base branch, draft status, mergeable state

### Post-close Checklist
- [ ] Issue/PR shows as closed on GitHub (or merged if `--merge` used)
- [ ] File moved from `open/` to `closed/`
- [ ] Comment with commit reference visible on the GitHub issue/PR

### Success Criteria
- `gh_sync.py` exits 0 and prints count of issues/PRs synced
- `gh_create.py` exits 0 and confirms issue created + file dropped
- `gh_close.py` exits 0 and confirms comment posted + issue/PR closed (or merged)
- No issue/PR files remain in `open/` after all bugs are resolved

---

## Common Pitfalls and Solutions

### 1. gh_sync.py Pulls Pull Requests Too

**Problem**: The sync output includes PR entries mixed with issues.

**Why it happens**: GitHub's `/issues` endpoint returns both issues and pull requests. The script now INCLUDES PRs by design (v2.0+).

**Solution**: PRs are written as `pr-NNNN-*.md` files with additional metadata (head/base branch, mergeable state, draft flag). Issues are `issue-NNNN-*.md`. Both are valid work items.

### 2. Issue/PR File Disappears from open/ Without Being Closed

**Problem**: A file that was in `open/` is gone after re-running `gh_sync.py`, but it's not in `closed/` either.

**Why it happens**: The issue/PR was closed directly on GitHub (in the browser or by another tool) between syncs. `gh_sync.py` only writes currently-open items; it moves closed ones to `closed/`.

**Solution**: Check `closed/` first. If it's there, the issue was resolved. If it's missing entirely, it may have been deleted on GitHub — check the repo's closed issues list.

### 3. Rate Limiting on Large Repos

**Problem**: `gh_sync.py` fails mid-run with a 403 or 429 error on repos with many issues.

**Why it happens**: GitHub's REST API rate limit is 5,000 requests/hour for authenticated users. Each issue + its comments is multiple requests; repos with 50+ issues and heavy comment threads can hit this.

**Solution**: The script uses pagination (100 per page) to minimize requests. If you hit rate limits, wait an hour or use a fine-grained token with higher limits. Check remaining rate limit: `GET /rate_limit`.

### 4. Closing the Wrong Issue Number

**Problem**: `gh_close.py --number 42` closes a different issue than intended.

**Why it happens**: Issue numbers are reused across repos — if `GITHUB_REPO` is not set correctly and the script detects the wrong remote, it closes an issue on the wrong repo.

**Solution**: Always verify `GITHUB_REPO` resolves correctly before a close. Add `echo $GITHUB_REPO` or check the script output — it prints the repo name before acting.

---

## External System Lessons

### GitHub API — Issues Endpoint Returns Pull Requests

**Behavior**: `GET /repos/{owner}/{repo}/issues` returns both issues and pull requests. PRs have a `pull_request` key in the response object; plain issues do not.

**Why it matters**: As of v2.0 (2026-06-30), this toolkit handles BOTH issues and PRs. The `pull_request` key is used to distinguish them, not filter them out.

**How to handle**: `gh_sync.py` now pulls both. Items with `pull_request` key are rendered as `pr-NNNN-*.md` files with additional PR metadata. For full PR details, the tool fetches `/repos/{owner}/{repo}/pulls/{number}` separately.

### GitHub API — Auto-Close via Commit Message

**Behavior**: GitHub auto-closes issues when commits/PRs containing `Closes #N`, `Fixes #N`, or `Resolves #N` land on the default branch.

**Why it matters**: A locally-closed issue (via `gh_close.py`) plus a `Closes #N` commit produces a single clean close, not a double-close.

**How to handle**: Use `gh_close.py` for explicit, audited closes with a comment. Use the `Closes #N` syntax in commits for the auto-close path.

### GitHub API — Rate Limit Headers

**Behavior**: Every API response includes `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers. At 0 remaining, requests return 403 until the reset timestamp.

**Why it matters**: A sync run on a large issue backlog can exhaust the hourly budget.

**How to handle it**: The scripts don't currently inspect rate limit headers — if you hit limits, add a check on `resp.headers.get("X-RateLimit-Remaining")` and sleep until reset if needed.

### GitHub API — Token Scopes

**Behavior**: Personal Access Tokens (classic) need `public_repo` scope minimum to comment + close issues on a public repo. Private repos need `repo` scope.

**Why it matters**: 401/403 errors from `gh_sync.py` or `gh_close.py` almost always trace to token scope or expiry, not the code.

**How to handle**: When auth errors appear, regenerate the token with `public_repo` (or `repo` for private repos) before debugging anything else.

---

## Error Handling

### Known Failures

| Failure | Cause | Mitigation |
|---------|-------|------------|
| **rate_limit_exceeded** | More than 5,000 API requests in an hour | Check `X-RateLimit-Remaining` header. Wait until `X-RateLimit-Reset` timestamp before retrying. |
| **token_insufficient_scope** | `GH_TOKEN` does not have write access to issues | Regenerate token with `repo` or `public_repo` scope. `gh_close.py` will return 403. |
| **repo_not_detected** | `git remote origin` is not set or is not a GitHub URL | Set `GITHUB_REPO=owner/repo` explicitly. |

### Retry Strategy
- Max retries: 3
- Backoff: exponential
- Timeout per attempt: 30s

---

## When to Use This Agent

- **At the start of each dev session** — check `knowledge/agile_sprint.md` first, then sync issues
- **After pushing a fix** — close the issue and update `knowledge/agile_sprint.md`
- **When a sprint completes** — mark it done, review lessons learned, confirm next sprint order
- **When new issues are filed** — triage against `knowledge/gh_issues_agent_mission.md` value streams and add to the appropriate sprint
- **Cross-repo bug filing** — when working in a consumer repo and discovering a defect in a producer repo, use `GITHUB_REPO=owner/repo uv run tools/gh_create.py ...` to file against the producer

### When NOT to Use

- **Do not run `gh_close.py` without a committed fix** — close only after the change is pushed
- **Do not edit files in `.github_issues/` by hand** — they are generated output and will be overwritten

---

## Cross-References

**Related tooling**:
- `knowledge/agile_sprint.md` — current sprint plan and milestone status
- `knowledge/gh_issues_agent_mission.md` — mission, triage philosophy, milestone framework
- `knowledge/github_issues_reference.md` — GitHub API field reference

**Producer repos** (when using cross-repo bug filing):
- Any GitHub repo — use `GITHUB_REPO=owner/repo` to file bugs against it
