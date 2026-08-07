---
name: pr
description: Full-lifecycle PR workflow skill to create feature branches, commit files, merge PR to remote main, rebase local main, and clean up local feature branches.
---

# Full-Lifecycle PR Workflow Skill (`pr`)

1. **Rebase & Checkout Main**:
   - Clean up stale rebase state if left in a broken state (`git rebase --abort` if `.git/rebase-merge` or `.git/rebase-apply` exists).
   - Ensure local `main` is checked out and rebased against `origin/main` before branching:
     `git checkout main && git pull --rebase origin main` (or `uv run agy-task sync-main`; requires `BypassSandbox: true` for remote Git operations).
   - Pass `ALLOW_MAIN_COMMIT=1` in environment during administrative system staging and PR creation.

2. **Create Feature Branch**:
   - Create a fresh feature branch off rebased `main`:
     `git checkout -b feat/<feature-name>`

3. **Stage, Commit & Create PR**:
   - Stage changes cleanly: `git add -A`
   - Check `git status --porcelain` before committing: `git commit -m "feat(<scope>): <description>"`
   - Create PR using gh CLI wrapper (`uv run agy-task create-pr feat/<feature-name>`) or `gh pr create --fill --head feat/<feature-name>` (requires `BypassSandbox: true`).

4. **Merge PR & Delete Remote Feature Branch**:
   - Merge the PR into remote `main` using squash-merge:
     `gh pr merge feat/<feature-name> --squash --delete-branch` (requires `BypassSandbox: true`).

5. **Rebase Local Main & Delete Local Feature Branch**:
   - Switch to `main`, pull rebased `origin/main` (with `BypassSandbox: true`), and delete the local feature branch:
     `git checkout main && git pull --rebase origin main && git branch -D feat/<feature-name>`

6. **Verify Zero Pending Branches & Clean State**:
   - Confirm only `main` remains cleanly active (`git branch -a`).
   - Run `uv run agy-verify` to ensure zero `.sh` shell script violations and clean environment state.
