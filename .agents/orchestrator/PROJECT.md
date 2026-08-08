# Project: Graphify Standard Architecture Enhancements & Layout Standards

## Architecture
Standard multi-modal graph extraction architecture for `agy-graphify-research`. Canonical output directory at workspace root is strictly `graphify-out/`. Automated log cleanup task (`clean_logs_action`) prunes legacy non-standard output directories (`graphify-out-antigravity/` and nested `graphify-out/graphify-out/`). `ColibriExtractor` supports multi-modal input file extensions (.py, .md, .pdf, .mp4, .mp3, .png).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Automated Pruning of Legacy Directories | Update `clean_logs_action()` in `src/agy_graphify/tasks.py` to prune legacy root and nested output dirs | M1 | ORIGINAL_REQUEST §44 |
| 2 | ColibriExtractor Multi-Modal Extensions | Define `SUPPORTED_EXTENSIONS` containing `.pdf`, `.mp4`, `.mp3`, `.png` in `src/agy_graphify/colibri_extractor.py` | M1 | ORIGINAL_REQUEST §51 |
| 3 | Layout Standards Unit Test Suite | Create `tests/test_workspace_layout_standards.py` asserting canonical output, 0 non-standard dirs, pruning, and extractor extensions | M2 | ORIGINAL_REQUEST §47 |
| 4 | Architecture Proposal Approval | Update `status: approved` in `docs/graphify_sources_proposal_architecture.md` | M3 | ORIGINAL_REQUEST §54 |
| 5 | Legacy Architecture Doc Removal | Remove obsolete file `docs/graphify_sources_current_architecture.md` | M3 | ORIGINAL_REQUEST §55 |
| 6 | E2E Suite & Verification | Run `uv run pytest`, verify `ALLOW_MAIN_COMMIT=1 uv run agy-verify`, and squash-merge PR via `uv run agy-task create-pr` | M4 | ORIGINAL_REQUEST §57 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Implementation Updates | Refactor `clean_logs_action()` in `tasks.py` & add multi-modal extensions to `colibri_extractor.py` | none | DONE |
| M2 | Workspace Layout Test Suite | Add `tests/test_workspace_layout_standards.py` verifying canonical output, pruning, and extractor multi-modal scanning | M1 | DONE |
| M3 | Architecture Transition & Decommissioning | Approve proposal doc & remove obsolete current architecture doc | M1 | DONE |
| M4 | E2E Verification & PR Creation | Run full pytest suite, execute `agy-verify`, and execute `create-pr` task | M2, M3 | IN_PROGRESS |

## Interface Contracts
### `tasks.py` ↔ `clean_logs_action()`
- Signature: `async def clean_logs_action(*_params: str) -> None`
- Functionality: Cleans old process logs in `.gemini/telemetry/` AND prunes non-canonical workspace root directories (`graphify-out*` where `name != "graphify-out"`) and nested legacy directory (`graphify-out/graphify-out`).

### `colibri_extractor.py` ↔ `ColibriExtractor`
- Class constant: `SUPPORTED_EXTENSIONS: tuple[str, ...]` includes `(".py", ".md", ".pdf", ".mp4", ".mp3", ".png", ...)`
- Method signature: `async def extract_directory(self, dir_path: Path, extensions: tuple[str, ...] = SUPPORTED_EXTENSIONS) -> GraphData`

## Code Layout
- `src/agy_graphify/tasks.py`: Clean logs action & task definitions
- `src/agy_graphify/colibri_extractor.py`: Multi-modal graph extractor engine
- `tests/test_workspace_layout_standards.py`: Layout standards & multi-modal unit tests
- `docs/graphify_sources_proposal_architecture.md`: Approved standard architecture specification
