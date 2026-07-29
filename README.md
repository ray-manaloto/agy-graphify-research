# agy-graphify-research

This repository contains the Python library, project plugin, state/toolchain verification tools, and multi-agent orchestration engine for Antigravity & Graphify.

## Toolchain Pinning (`.mise.toml`)

All tools and runtime environments are explicitly pinned in `.mise.toml` without using `latest`:

- **Python**: `3.14.6`
- **uv**: `0.12.0`
- **ruff**: `0.15.12`
- **ty**: `0.0.32`
- **hk**: `1.53.0`
- **fnox**: `1.31.1`
- **pkl**: `0.32.1`
- **datamodel-code-generator**: `0.71.0`

## Architecture & Project Plugin

All project automation is packaged as a project plugin (`.gemini/plugins/agy-graphify-research/`). All skills delegate execution directly to `mise` tasks:

```
.gemini/plugins/agy-graphify-research/
├── plugin.json
└── skills/
    ├── graphify/SKILL.md          # Calls: mise run graphify -- "$@"
    ├── orchestrate/SKILL.md       # Calls: mise run orchestrate -- "$@"
    ├── verify-state/SKILL.md      # Calls: mise run verify -- "$@"
    ├── verify-toolchain/SKILL.md  # Calls: mise run verify -- "$@"
    └── python-task/SKILL.md       # Calls: mise run task -- "$@"
```

## Python Library Package (`src/agy_graphify/`)

- **`agy_graphify.verify`**: `EnvironmentVerifier` enforcing isolated project state and explicit toolchain version pinning (`python = "3.14.6"`, `uv`, `ruff`, `ty`, `hk`, `fnox`, `pkl`).
- **`agy_graphify.serializer`**: `SerializerEngine` using `msgspec` (C-speed MsgPack binary encoding/decoding) and `orjson` (fast JSON serialization).
- **`agy_graphify.graph`**: `GraphifyEngine` for persistent knowledge graph building and querying.
- **`agy_graphify.orchestration`**: `OrchestrationEngine` for multi-agent workflow decomposition and dispatch.

## Verification & Execution Commands

```bash
# Run model generation, Ruff (ALL rules), Ty static analysis, Pytest suite, & Verification
mise run check

# Run skills via Mise wrappers
mise run verify
mise run graphify -- --mode deep
mise run orchestrate -- "Multi-agent research pipeline"

# Git hook verification (pre-commit & post-commit)
hk check
```
