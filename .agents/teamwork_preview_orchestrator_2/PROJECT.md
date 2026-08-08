# Project: Graphify Multi-Modal Source Architecture Implementation

## Architecture
- Workspace multi-modal sources standardized under `raw/` subdirectories:
  - `raw/papers/` for `.pdf` academic papers & books
  - `raw/media/` for `.mp4`, `.mp3`, `.m4a`, `.wav` video/audio
  - `raw/web/` for scraped web pages, HTML, and markdown articles
  - `raw/images/` for `.png`, `.jpg`, `.svg` images & diagrams
- `config/sources.json`: Central mapping configuration file (v1.1.0) registering all source paths.
- `src/agy_graphify/source_registry.py`: `SourceRegistryManager` updated to load `config/sources.json`, auto-create subdirectories with `.gitkeep` files, and scan multi-modal raw sources.
- `src/agy_graphify/tasks.py`: `update-all-sources` CLI action invoking auto-creation and raw source scanning; `create-pr` action fixed to properly handle subprocess returncodes and error out if git/gh fails.
- `tests/test_source_registry.py` & `tests/test_workspace_layout_standards.py`: Comprehensive test suites validating source registry behavior and layout standards.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | `raw/` Directory Layout | Canonical `raw/papers`, `raw/media`, `raw/web`, `raw/images` with `.gitkeep` files | M1 | ORIGINAL_REQUEST §1 |
| 2 | `config/sources.json` v1.1.0 | Updated JSON config with `"sources"` dict mapping all multi-modal paths | M2 | ORIGINAL_REQUEST §2 |
| 3 | `SourceRegistryManager` Config Parsing | Parse `config/sources.json` in `SourceRegistryManager.__init__` / `_load_sources_config` | M3 | ORIGINAL_REQUEST §3 |
| 4 | `ensure_source_directories` | Auto-create missing source subdirectories and place `.gitkeep` files | M3 | ORIGINAL_REQUEST §3 |
| 5 | `scan_raw_sources` | Discover and catalog `.pdf`, `.mp4`, `.mp3`, `.html`, `.png` etc. files in `raw/` subdirs | M3 | ORIGINAL_REQUEST §3 |
| 6 | `update_all_sources` Task Action | Wire `ensure_source_directories` & `scan_raw_sources` into `update-all-sources` action in `tasks.py` | M3 | ORIGINAL_REQUEST §3 |
| 7 | Unit Test Suite (`test_source_registry.py`) | Tests for config parsing, directory auto-creation, scanning, and end-to-end `update_all_sources` | M4 | ORIGINAL_REQUEST §4 |
| 8 | Layout Standards Test (`test_workspace_layout_standards.py`) | Assert `raw/` subdirectories exist and contain `.gitkeep` files | M4 | ORIGINAL_REQUEST §4 |
| 9 | Pytest & Verification | Run full pytest suite (135 passing) and `ALLOW_MAIN_COMMIT=1 uv run agy-verify` | M4 | ORIGINAL_REQUEST §5 |
| 10 | PR Creation & Merge | Create pull request using standard tool/skill and squash-merge to main | M4 | ORIGINAL_REQUEST §5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Directory Layout Creation | `raw/papers/.gitkeep`, `raw/media/.gitkeep`, `raw/web/.gitkeep`, `raw/images/.gitkeep` | None | DONE |
| M2 | Config Mapping Update | `config/sources.json` v1.1.0 update with `"sources"` mapping | M1 | DONE |
| M3 | Source Registry & Task Enhancement | `src/agy_graphify/source_registry.py` & `src/agy_graphify/tasks.py` | M2 | DONE |
| M4 | Testing, Verification & Real PR Merge | Fix exception swallowing in `tasks.py`, track `raw/` in git, clean telemetry log, verify `agy-verify`, execute REAL commit & squash-merge to main | M3 | IN_PROGRESS (Iteration 2 Remediation) |

## Interface Contracts
### `SourceRegistryManager` API
- `__init__(config_path: Path | None = None)`: Loads `config/sources.json`.
- `ensure_source_directories(base_dir: Path | None = None) -> list[Path]`: Guarantees `repos/`, `raw/papers/`, `raw/media/`, `raw/web/`, `raw/images/` exist with `.gitkeep`.
- `scan_raw_sources(base_dir: Path | None = None) -> dict[str, list[Path]]`: Returns dictionary mapping source type to list of file paths.
- `update_all_sources()`: Runs `ensure_source_directories()`, `scan_raw_sources()`, `sync_and_get_deltas()`, and `audit_graph_coverage()`.

## Code Layout
- `config/sources.json`
- `raw/papers/.gitkeep`
- `raw/media/.gitkeep`
- `raw/web/.gitkeep`
- `raw/images/.gitkeep`
- `src/agy_graphify/source_registry.py`
- `src/agy_graphify/tasks.py`
- `tests/test_source_registry.py`
- `tests/test_workspace_layout_standards.py`
