---
title: Branch Protection & Enforcement Architecture
doc_id: okf-branch-protection
version: 1.0.0
type: architecture
status: approved
author: agy-graphify
tags:
  - security
  - git
  - hooks
  - github
---

# Branch Protection & Enforcement Architecture

## Overview
This document specifies the strict branch protection and direct-commit prevention mechanisms on the `agy-graphify-research` codebase. All new features and fixes must go through the standard PR workflow (`uv run agy-task create-pr`) and squash-merge to `main`.

## Enforcements

### Local `pre-commit` Hook
- A native git `pre-commit` hook automatically installed by `EnvironmentVerifier`.
- It executes `uv run agy-verify` on every commit.

### Code-Level State Verification
- `EnvironmentVerifier._check_branch_enforcement()` compares `HEAD` SHA against `main` SHA.
- Rejects direct commits to `main`.
- Can be overridden explicitly via the environment variable `ALLOW_MAIN_COMMIT=1`.

### Multi-Agent Hooks Interception
- Configured in `.gemini/hooks.json`.
- A `BeforeTool` hook prevents autonomous subagents from running `git commit` commands while on the `main` branch.

### GitHub Remote Ruleset Protection
- Automated through `uv run agy-task update-github-ruleset`.
- Configures GitHub branch protection for `main` to `enforce_admins=true`, completely eliminating direct push vectors.

## Exceptions
- Commits are permitted on feature branches (where `HEAD` does not equal `main`).
- Emergency bypass allowed manually by administrators setting `ALLOW_MAIN_COMMIT=1`.
