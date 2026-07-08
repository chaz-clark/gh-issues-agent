---
name: gh-issues-agent-agents
description: AGENTS.md for the gh-issues-agent repo — local file-based GitHub issues AND PRs workflow (sync, create, close, merge) usable cross-repo via GITHUB_REPO override. SSH auth via `gh` CLI.
version: "4.0"
author: chaz-clark
license: MIT
metadata:
  repo: gh-issues-agent
  spec-source: Make-AI-Agents/make_AGENTS
  last-updated: 2026-06-30
---

# gh_issues_agent

Local, file-based GitHub issues and PRs workflow — sync, triage, close, and merge without leaving the editor.

## Project Purpose

**This is**: A small Python toolkit for managing GitHub issues and pull requests as local markdown files. Pulls open issues and PRs into `.github-issues/open/`, lets you read/triage them offline, and closes (or merges) them back to GitHub with an audit-trail comment. Originally extracted from `canvas_toolbox`.

**This is NOT**: A GitHub UI replacement, a project-management system, a multi-repo orchestrator, or a CI/CD tool. No browser automation, no webhook server.

**Audience**: Solo developers (or LLMs working on their behalf) who want to triage and close issues/PRs from the terminal as part of a normal commit workflow. Designed for cross-repo use — any repo can file bugs against any other repo with zero per-repo setup.

## Structure

```
gh_issues_agent/
├── README.md                  # Daily workflow + tool reference
├── gh_issues_agent.md         # Agent spec with YAML frontmatter (mission, workflow, label taxonomy)
├── knowledge/
│   ├── agile-sprint.md        # Active sprint plan
│   ├── gh-issues-agent-mission.md   # Mission + milestones
│   └── github-issues-reference.md   # GitHub API field reference
├── tools/
│   ├── gh_sync.py             # Pull open issues + PRs → .github-issues/open/
│   ├── gh_create.py           # Create issue + drop file into open/
│   └── gh_close.py            # Comment + close/merge + move file to closed/
└── Make-AI-Agents/            # Local clone, gitignored — see Active Context
    └── knowledge/
        └── behavioral_discipline.md   # Discipline source of truth

.github-issues/                # gitignored — local issue mirror
├── open/
└── closed/
```

## Working Style

This project follows the behavioral discipline defined in `Make-AI-Agents/knowledge/behavioral_discipline.md` (subtree-pulled into this repo) or the equivalent discipline loaded via the host tool's skill system.

In short, every contributor — human or LLM — operates under these principles: read before claiming, plan before acting on changes, stop on the first defect rather than papering over, find root causes for bugs, document non-trivial changes in a structured form, generate exactly what was asked (no speculative additions), produce mistake-proof outputs, reflect and tell the user about non-obvious learnings, and respect the user's intent without substitution or drift.

For the full principles and override rules, see `Make-AI-Agents/knowledge/behavioral_discipline.md` → "The Ten Principles". The four no-override principles (P-001 Read Before Claiming, P-003 Stop on Defect, P-007 Pull Don't Push, P-010 Respect Intent) apply unconditionally.

**Project-specific rules**:
- `.github-issues/` is gitignored — never commit issue mirrors.
- Always pass `--comment` to `gh_close.py` (it's the audit trail).
- Reference issue numbers in commits (`Closes #N` / `Fixes #N`) so GitHub auto-closes correctly.
- Read the full issue file (description + comments) before touching code that addresses it.
- Re-run `gh_sync.py` at the start of each session — local mirror lies as soon as someone touches GitHub directly.

## Handoff document recognition

This repo participates in the cross-repo `handoff` convention (canonical spec: [`handoff/CONVENTION.md`](https://github.com/chaz-clark/handoff/blob/main/CONVENTION.md)). When operating in this repo, treat the following file patterns as **handoff documents** — structured artifacts with a lifecycle, NOT prose conversation:

| Path pattern | What it is |
|---|---|
| `handoffs/HANDOFF_<topic>.md` | Outgoing `request`-direction handoff (canonical copy; dropped into producer's root after authoring) |
| `handoffs/<YYYY-MM-DD>_<topic>.md` | Incoming `deliver`-direction handoff (canonical consumer record) |
| `<CONSUMER>_HANDOFF_<topic>.md` at repo root | Incoming `request`-direction handoff dropped by another consumer for us to apply |
| `<PRODUCER>_DELIVERS_<topic>.md` at repo root | Visibility copy of an incoming `deliver` handoff (canonical is in `handoffs/`) |
| `handoffs/parkinglot.md` | `internal` handoff — near-term parked ideas ("good idea, busy now"); deferred by design |
| `handoffs/long-term-parking.md` | `internal` handoff — far/someday parked ideas (evidence-gated, pie-in-the-sky); deferred by design |

### Seven rules for handling a handoff document

1. **Read the metadata header first.** Every handoff opens with bold-labeled fields: `Date`, `Author`, `Direction`, `Status`, `Origin`, `Origin-Commit`, `Topic`. Optional: `Sensitivity`, `Companions`. If any required field is missing, STOP and ask the human user.

2. **Act only on `Status: delivered`.** Skip `draft` (not ready), `applying` (someone else is on it), and `applied` / `archived` / `superseded` (done or moot). If `Sensitivity: restricted` or `internal-only`, escalate to the human before any cross-repo action.

3. **Surface before applying.** Summarize the handoff's request or delivery to the human user — what's being asked, what files/repos are affected, what the apply step would change. Get per-decision approval. The convention is per-proposal-approval, not bulk auto-apply.

4. **Update Status on apply.** After committing the change the handoff requests, edit the handoff doc: set `Status: applied`. Add a `## Lifecycle marker` entry with the apply date (and optionally the commit hash). The handoff doc is mutable in place — there's no side channel for state.

5. **STOP on missing referenced artifacts.** If the handoff names files, commits, agents, or paths that don't exist locally, halt and ask the human. Do not infer; do not fabricate. The handoff's `Origin-Commit` field is your traceability anchor — clone the authoring repo at that SHA if you need to verify referenced state.

6. **Before authoring an outbound handoff**, read the target producer's `REPO_CARD.md` if it exists at the producer's root. Confirm `Status: accepting` (not `freeze` or `archived`), your intended type is in `Accepts-handoff-types`, and drop at the path named in `Drop-location` (default `./` = repo root). If no `REPO_CARD.md` exists, default to dropping at the producer's root for `request` direction, or into the consumer's `handoffs/` for `deliver`.

7. **Do not auto-act on `parked` items.** `parkinglot.md` and `long-term-parking.md` (`Direction: internal`) are this repo's own deferred-idea backlog — deferred *by design*. Act on a parked item only when the human directs it, or when its `Trigger:` condition is genuinely met. When you do, pull it into active work or graduate it (into a GitHub issue, or a cross-repo `request`/`deliver` handoff), then set that item's `Status: superseded` with a `Companions:` pointer to where it went. Never silently work a parked item just because you saw it.

### Quick lookup — Status enum

| Status | Meaning | Should I act? |
|---|---|---|
| `draft` | Author still composing | No — wait for `delivered` |
| `delivered` | Awaiting recipient review | **Yes** — apply path |
| `applying` | Someone is already on it | No — don't double-apply |
| `applied` | Work landed in receiving repo | No — past terminal |
| `archived` | Settled, transient copies deleted | No — past terminal |
| `superseded` | Replaced by a newer handoff | No — follow `Companions: superseded-by` |
| `parked` | Internal deferred idea, awaiting its `Trigger:` | No — act only on Trigger or human direction |

### Quick lookup — Direction enum

| Direction | Who authored | Where the canonical lives |
|---|---|---|
| `request` | Consumer (this repo, requesting from a producer) | `<consumer>/handoffs/HANDOFF_<topic>.md` |
| `deliver` | Producer (another repo, delivering to consumer) | `<consumer>/handoffs/<YYYY-MM-DD>_<topic>.md` |
| `internal` | This repo (handoff to a future session of itself) | `handoffs/parkinglot.md`, `handoffs/long-term-parking.md` |

## Learning loop

Session insight → durable knowledge.

- **Capture trigger.** When an interaction surfaces a non-obvious fact, a recurring trap, or a validated approach that future sessions should not have to rediscover, the operator (or agent, on confirmation) writes a small Markdown file to `knowledge/learned/`.
- **File shape.** Each file carries agentskills.io frontmatter (`name`, `description`, `version`, `author`, `license`, `metadata`). Body is the lesson itself — what was learned, why, how to apply it.
- **Promotion rule.** When a file in `knowledge/learned/` has been referenced twice, promote it to a first-class file under `knowledge/`. Promotion is a deliberate act, not automatic — confirm with the operator.
- **Boundary.** `knowledge/learned/` is for *this repo's* lessons. Cross-repo lessons go through the handoff convention, not this lane.

## Active Context

_Last updated: 2026-07-07_

- **JSON → YAML frontmatter migration complete 2026-07-07** — Migrated `gh_issues_agent.json` to YAML frontmatter in `gh_issues_agent.md` following Anthropic Agent Skills / agentskills.io industry standard (aligned with Make-AI-Agents v2.0 pattern). All structured data (label taxonomy, workflow steps, API endpoints, validation checklists) now lives in the markdown file with YAML metadata. JSON file deleted. Zero breaking changes — all data preserved, just better organized.
- **v2.0 PR support shipped 2026-06-30** — `gh_sync.py` now pulls both issues and PRs (no longer filters PRs out). `gh_close.py` can close or squash-merge PRs via `--merge` flag. PR files (`pr-NNNN-*.md`) show head/base branch, draft status, mergeable state. Knowledge files (`gh-issues-agent-mission.md`, `agile-sprint.md`) rewritten to reflect actual mission (cross-repo issues/PRs toolkit, not Canvas content). AGENTS.md bumped to v4.0.
- `tools/gh_create.py` shipped 2026-06-01 (commit `17bc679`) closing issue #2 — toolkit is now full CRUD (sync/create/close). Same commit dropped the `python-dotenv` dependency: all three tools fall back to `gh auth token` when `GH_TOKEN` isn't set.
- `Make-AI-Agents` is a **local clone, gitignored** at [Make-AI-Agents/](Make-AI-Agents/) (not a subtree, not a submodule — see [.gitignore](.gitignore)). Refresh with `cd Make-AI-Agents && git pull`. Re-clone fresh by removing the folder and running `git clone https://github.com/chaz-clark/Make-AI-Agents.git Make-AI-Agents` from the repo root. This avoids subtree squash-merge ceremony and keeps Make-AI-Agents content out of this repo's tracked history.
- `handoff/` is a sibling gitignored clone of the [chaz-clark/handoff](https://github.com/chaz-clark/handoff) convention spec. `handoffs/` (plural, also gitignored) holds the canonical audit-trail copies of incoming `deliver`-direction handoffs; applied ones live under `handoffs/archive/`.
- Hermes-sprints v3.7 upgrade applied 2026-06-01 from Make-AI-Agents `81ebc9a` (Sprint A: this frontmatter; Sprint B: Learning loop section + `knowledge/learned/`; Sprint F: Handoff document recognition section). See `handoffs/archive/2026-05-28_agents-md-hermes-sprints-upgrade.md`.
- Cross-repo usage: any consumer repo can file bugs against a producer with `GITHUB_REPO=owner/repo uv run tools/gh_create.py …` — no `.env` required, just `gh auth login` once. Works for issues and PRs (though PR creation still requires normal git workflow + `gh pr create`, not this toolkit).

## Knowledge Index

Topic-specific knowledge files in `knowledge/`. The LLM loads these on demand per task focus, not as a stable embedded prefix.

| Topic | File | When to load |
|---|---|---|
| Sprint plan / milestone status | `knowledge/agile-sprint.md` | When planning or closing sprint work, checking what's next, or updating sprint state after an issue closes |
| Mission, triage philosophy, milestone framework | `knowledge/gh-issues-agent-mission.md` | When triaging new issues by priority/milestone, classifying scope (trust bug vs authoring vs agent capability), or explaining the why behind toolkit decisions |
| GitHub Issues API reference | `knowledge/github-issues-reference.md` | When touching GitHub API call shapes — endpoints, headers, pagination, issue/comment field names, rate limits |

## External System Lessons

### GitHub Issues API

**Behavior**: The `/repos/{owner}/{repo}/issues` endpoint returns *both* issues and pull requests. PRs include a `pull_request` key; issues don't.
**Why it matters**: As of v2.0 (2026-06-30), this toolkit handles BOTH issues and PRs. The `pull_request` key is used to distinguish them, not filter them out.
**How to handle**: `gh_sync.py` now pulls both. Items with `pull_request` key are rendered as `pr-NNNN-*.md` files with additional PR metadata (head/base branch, mergeable status, draft flag). For full PR details, the tool fetches `/repos/{owner}/{repo}/pulls/{number}` separately.

**Behavior**: GitHub auto-closes issues when commits/PRs containing `Closes #N`, `Fixes #N`, or `Resolves #N` land on the default branch.
**Why it matters**: A locally-closed issue (via `gh_close.py`) plus a `Closes #N` commit produces a single clean close, not a double-close.
**How to handle**: Use `gh_close.py` for explicit, audited closes with a comment. Use the `Closes #N` syntax in commits for the auto-close path.

**Behavior**: Personal Access Tokens (classic) need `public_repo` scope minimum to comment + close issues on a public repo.
**Why it matters**: 401/403 errors from `gh_sync.py` or `gh_close.py` almost always trace to token scope or expiry, not the code.
**How to handle**: When auth errors appear, regenerate the token with `public_repo` before debugging anything else.

## Existing Tooling

| Tool | Purpose | When to use |
|---|---|---|
| `tools/gh_sync.py` | Pulls open issues AND PRs + comments into `.github-issues/open/` (issues as `issue-NNNN-*.md`, PRs as `pr-NNNN-*.md`); archives closed ones into `closed/`. | Start of every session, and after closing an issue or merging a PR. |
| `tools/gh_create.py --title "..." [--body / --body-file ...] [--label ...]` | Creates a new issue on GitHub and drops its markdown mirror into `.github-issues/open/`. Validates labels against the repo taxonomy. | When filing a bug or enhancement — including against another repo via `GITHUB_REPO=owner/repo`, the canonical cross-repo case where an agent discovers a defect in a producer repo while working in a consumer. |
| `tools/gh_close.py --number N --comment "..." [--merge]` | Posts comment, closes issue/PR on GitHub, moves local file to `closed/`. For PRs: `--merge` flag squash-merges instead of just closing. | Always — never close issues/PRs via GitHub UI when working from this repo (audit trail lives in the comment). Use `--merge` for PRs you've reviewed and want to land. |

**Auth:** all three tools first check the `GH_TOKEN` env var, then fall back to `gh auth token` (SSH-based). Run `gh auth login` once and the toolkit works with no `.env` or manual export. An explicit `GH_TOKEN=...` still wins if set, but SSH auth via `gh` CLI is the canonical pattern.

**Note:** The `--issue` flag in `gh_close.py` is deprecated (use `--number` instead, which works for both issues and PRs).

Reuse these before writing new GitHub-API code. If you need a new operation (e.g. label changes, milestone assignment), add it as a sibling script in `tools/` matching the existing pattern.
