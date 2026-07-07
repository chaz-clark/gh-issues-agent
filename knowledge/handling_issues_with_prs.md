# Handling Issues with Associated Pull Requests

## When to Apply This Pattern

When working through issues from the sprint plan, some issues may reference existing pull requests (PRs) in their description or comments. These PRs often contain partial solutions, design approaches, or implementation attempts that should inform your work.

## Recognition Pattern

Issues that mention PRs typically include:
- Explicit PR references: `PR #120 fixes...`, `see pull request #120`
- GitHub auto-links: Pull request URLs in the issue body or comments
- Status indicators: `In flight`, `Ask (toolkit-wide)`, or similar language suggesting work in progress

## Required Steps Before Implementation

### 1. Check for PR References

Before starting work on any issue, scan the issue body and comments for PR references:

```bash
# Example: Check issue #123 for PR references
grep -i "pr #\|pull request\|github.com.*pull" .github_issues/open/issue-0123-*.md
```

### 2. Review the PR if Found

Use `gh pr view` to read the PR:

```bash
# View PR details including files changed
gh pr view 120 --json body,files,state,headRefName
```

Key information to extract:
- **Current state**: OPEN, CLOSED, MERGED
- **Files changed**: What the PR modified
- **Approach taken**: Read the PR description and code changes
- **Why it's incomplete**: If still OPEN, understand what's blocking it

### 3. Learn from the PR

**If PR is OPEN:**
- The approach may be partially correct but incomplete
- Check if the issue asks for extension beyond what the PR does
- Consider whether to build on the PR or implement differently

**If PR is CLOSED (not merged):**
- Read the close reason (usually in comments)
- Learn what was wrong with the approach
- Implement a better solution that addresses the feedback

**If PR is MERGED:**
- The issue should be closed; if not, it's asking for follow-up work
- Build on top of the merged changes

## Case Study: Issue #123 and PR #120

**Context:** Issue #123 asked for toolkit-wide Windows UTF-8 console fix.

**Discovery:** Issue body mentioned `PR #120 fixes the highest-impact crash site — cb_init.py`

**Investigation:**
```bash
gh pr view 120 --json files,state,body
# Found: PR #120 was OPEN, bundled two fixes (PDF rendering + console encoding)
# Files: _md_to_pdf.py, cb_init.py
```

**Decision Made:**
- PR bundled two unrelated fixes (PDF + console encoding)
- Console encoding fix was inline in cb_init.py only
- Issue #123 asked for toolkit-wide fix (68 tools, not just cb_init.py)
- **Action:** Closed PR #120 with explanation, implemented toolkit-wide fix separately

**Outcome:**
- Learned from PR #120's inline approach for cb_init.py
- Implemented superior shared-function approach (`_env_loader.force_utf8_console()`)
- Retrofitted all 68 tools vs. PR's single-tool fix
- Closed issue #123 with reference to the new commit

## Integration with Sprint Workflow

Update the standard sprint workflow (from `gh_issues_agent.md`):

1. **Check the sprint**: Read `knowledge/agile_sprint.md` — find the next `[ ]` issue
2. **Sync issues**: Run `gh_sync.py`
3. **Pick work**: Open the `.md` file for the issue
4. **Check for PRs**: ⭐ NEW STEP ⭐ Scan issue for PR references; if found, `gh pr view <number>`
5. **Learn from PR**: ⭐ NEW STEP ⭐ Read PR files, approach, and state; decide whether to build on it, learn from it, or supersede it
6. **Fix it**: Make the code change with PR context in mind
7. **Commit**: Reference both the issue and the PR if relevant (`Fixes #123`, `Supersedes PR #120`)
8. **Close issue**: Run `gh_close.py --issue <number>` with commit reference
9. **Update sprint**: Mark `[x]` in `agile_sprint.md`

## Comment Patterns

### When Closing a PR to Implement Differently

```markdown
Thanks for this PR! After review, we're handling this differently:

**<aspect 1> (your changes in <file>):**
<explanation of why we're not using this approach>

**<aspect 2> (your changes in <file>):**
<explanation - could be positive if asking them to split it out>

Closing this PR in favor of <reference to new approach or issue>.
<Acknowledgment if any of their work is being used>.
```

### When Closing an Issue After Learning from a PR

```markdown
Fixed in commit <sha>.

<Brief description of what was implemented>.

Note: This supersedes PR #<number> (closed). <One sentence explaining why the new approach is different/better>.
```

## Why This Matters

**Respect for contributor work:**
- PRs represent real effort; acknowledging them shows respect
- Learning from their approach (even if not merging) honors their contribution

**Better solutions:**
- PRs often surface edge cases or requirements you might miss
- Seeing what didn't work helps avoid repeating mistakes

**Clear audit trail:**
- Future maintainers can trace design decisions through PR/issue cross-references
- Commit messages linking to both create full context

## Pitfalls to Avoid

❌ **DON'T** start implementing without checking for PRs
❌ **DON'T** close a PR without explanation or acknowledgment
❌ **DON'T** ignore the PR's approach — at minimum, understand why it exists
❌ **DON'T** duplicate work if a merged PR already addressed part of the issue

✅ **DO** read the PR before coding
✅ **DO** explain your reasoning when closing a PR
✅ **DO** reference both issue and PR in your commit/close comments
✅ **DO** acknowledge good ideas from the PR even if not using the exact code
