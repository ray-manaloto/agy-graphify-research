---
name: verify-toolchain
description: "Verify that all tools (python 3.14.6, uv, ruff, ty, hk, fnox, pkl) are explicitly pinned in .mise.toml without using 'latest'."
trigger: /verify-toolchain
---

# /verify-toolchain

Verifies toolchain pinning and ensures zero unpinned tools or global leaks exist.

## Execution

This skill delegates execution to the project's Python library via `mise`:

```bash
mise run verify -- "$@"
```
