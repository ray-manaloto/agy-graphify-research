# Investigation Report: Multi-Modal Source Architecture & SourceRegistryManager Integration

## 1. Observation

Direct code inspection of the codebase yielded the following observations:

1. **`config/sources.json` (`config/sources.json:1-6`)**:
   ```json
   {
     "version": "1.0.0",
     "updated_at": "2026-08-06T17:38:00Z",
     "manifest_source": "graphify-out/extended_repo_manifest.json"
   }
   ```
   - *Observation*: Contains version 1.0.0 metadata but lacks any `"sources"` mapping for repositories or `raw/` multi-modal subdirectories (`raw/papers/`, `raw/media/`, `raw/web/`, `raw/images/`).

2. **`src/agy_graphify/source_registry.py` (`src/agy_graphify/source_registry.py:13-125`)**:
   - Lines 13–18:
     ```python
     CONFIG_DIR = Path("config")
     CONFIG_DIR.mkdir(parents=True, exist_ok=True)
     REGISTRY_FILE = CONFIG_DIR / "sources.json"
     STATE_FILE = Path(".gemini") / "commit_state.json"
     STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
     REPOS_BASE = Path("repos")
     ```
   - Lines 23–24: `SourceRegistryManager.__init__()` initializes `self.state` via `_load_state()`.
   - *Observation*: `REGISTRY_FILE` (`config/sources.json`) is defined on Line 15 as a module constant but is **never loaded, parsed, or referenced** anywhere inside `SourceRegistryManager` or `source_registry.py`.
   - Lines 47–80: `sync_and_get_deltas()` reads `graphify-out/extended_repo_manifest.json` and updates git SHA state for `git` repos.
   - Lines 82–114: `audit_graph_coverage()` audits repo coverage in `graphify-out/graph.json`.
   - Lines 117–121:
     ```python
     def update_all_sources() -> None:
         """CLI Entrypoint to sync repositories, update commit SHA differential state, and audit graph coverage."""
         mgr = SourceRegistryManager()
         mgr.sync_and_get_deltas()
         mgr.audit_graph_coverage()
     ```
   - *Observation*: `update_all_sources()` currently only executes git SHA delta syncing and graph coverage auditing. It does not verify or auto-create `raw/` subdirectories, nor does it scan multi-modal files (`.pdf`, `.mp4`, `.mp3`, `.html`, `.png`, etc.).

3. **`src/agy_graphify/tasks.py` (`src/agy_graphify/tasks.py:807-841`)**:
   - Lines 807–808:
     ```python
     async def update_sources_action(*_params: str) -> None:
         update_all_sources()
     ```
   - Lines 840–841:
     ```python
     dispatcher.register("update-all-sources", update_sources_action)
     dispatcher.register("update_all_sources", update_sources_action)
     ```
   - *Observation*: `tasks.py` registers `update-all-sources` to call `update_sources_action()`, which delegates directly to `update_all_sources()` in `source_registry.py`.

4. **Architecture Spec Requirements (`docs/graphify_sources_proposal_architecture.md:21-48`)**:
   - Outlines 6 multi-modal source categories:
     1. Code Repositories (`repos/`)
     2. Markdown & Docs (`docs/`, `repos/`, `raw/`)
     3. PDF Papers & Books (`.pdf` in `raw/papers/`)
     4. Video & Audio (`.mp4`, `.mp3`, `.m4a`, `.wav` in `raw/media/`)
     5. Scraped Web URLs (`raw/web/`)
     6. Images & Diagrams (`.png`, `.jpg`, `.svg` in `raw/images/`)
   - Requires `config/sources.json` to register these source mappings explicitly.

---

## 2. Logic Chain

1. **Step 1 (Source Configuration Gap)**:
   - *Observation*: `config/sources.json` currently lacks a `"sources"` dictionary, and `SourceRegistryManager` does not parse `REGISTRY_FILE`.
   - *Deduction*: Adding the `"sources"` field to `config/sources.json` (version 1.1.0) and enhancing `SourceRegistryManager` to load and parse this configuration enables centralized, data-driven path resolution for all multi-modal source categories.

2. **Step 2 (Auto-Creation Requirement)**:
   - *Observation*: When `uv run agy-task update-all-sources` runs, it calls `update_all_sources()` in `source_registry.py`. Currently, `update_all_sources()` assumes target directories exist.
   - *Deduction*: Adding an `ensure_source_directories()` method to `SourceRegistryManager` — and invoking it inside `update_all_sources()` — guarantees that `repos/`, `raw/papers/`, `raw/media/`, `raw/web/`, and `raw/images/` are verified and auto-created with `.gitkeep` files before any indexing or syncing operations run.

3. **Step 3 (Multi-Modal File Discovery)**:
   - *Observation*: Multi-modal raw sources (`.pdf`, `.mp4`, `.mp3`, `.html`, `.png`) reside inside `raw/` subdirectories. `ColibriExtractor` (`src/agy_graphify/colibri_extractor.py`) supports these extensions, but `SourceRegistryManager` does not index or scan them.
   - *Deduction*: Adding a `scan_raw_sources()` method to `SourceRegistryManager` allows the registry to discover and track multi-modal files in `raw/papers/`, `raw/media/`, `raw/web/`, and `raw/images/`, reporting file counts during `update-all-sources`.

4. **Step 4 (Task Dispatcher Integration)**:
   - *Observation*: `tasks.py` wraps `update_all_sources()`.
   - *Deduction*: Since `tasks.py` calls `update_all_sources()`, enhancing `update_all_sources()` inside `source_registry.py` automatically equips `uv run agy-task update-all-sources` with multi-modal directory creation and scanning capabilities without breaking existing CLI options.

---

## 3. Caveats

- **External Tooling Dependencies**: Ingestion of binary media (`.mp4`, `.mp3`) or PDF files (`.pdf`) relies on sidecar processors (e.g. `Whisper` or `pdfplumber` / `pypdf`) during `colibri-graphify` extraction. `SourceRegistryManager` itself performs filesystem registration, directory auto-creation, and file scanning, leaving heavy media parsing to `ColibriExtractor`.
- **Read-Only Scope**: This report provides technical analysis and blueprints. Code implementations and tests will be executed by the implementation agents.

---

## 4. Conclusion

To support multi-modal sources (`raw/papers/`, `raw/media/`, `raw/web/`, `raw/images/`), the following updates must be made:

### A. Update `config/sources.json`
```json
{
  "version": "1.1.0",
  "updated_at": "2026-08-07T22:18:00Z",
  "manifest_source": "graphify-out/extended_repo_manifest.json",
  "sources": {
    "git_repositories": "repos/",
    "raw_papers": "raw/papers/",
    "raw_media": "raw/media/",
    "raw_web": "raw/web/",
    "raw_images": "raw/images/"
  }
}
```

### B. Update `src/agy_graphify/source_registry.py`
1. **Initialize & Parse `config/sources.json`**:
   - `SourceRegistryManager.__init__(self, config_path: Path | None = None)`: Load `sources` configuration from `config/sources.json`.
   - Add helper `_load_sources_config(self) -> dict[str, str]`.
2. **Auto-Create Directory Method**:
   - Add `ensure_source_directories(self, base_dir: Path | None = None) -> list[Path]`:
     - Resolves paths for `git_repositories` (`repos/`), `raw_papers` (`raw/papers/`), `raw_media` (`raw/media/`), `raw_web` (`raw/web/`), `raw_images` (`raw/images/`).
     - Ensures directories exist (`dir_path.mkdir(parents=True, exist_ok=True)`).
     - Creates `.gitkeep` file in each directory if missing.
3. **Multi-Modal Scanning Method**:
   - Add `scan_raw_sources(self, base_dir: Path | None = None) -> dict[str, list[Path]]`:
     - Scans `raw/papers/` for `.pdf`.
     - Scans `raw/media/` for `.mp4`, `.mp3`, `.m4a`, `.wav`, `.mkv`, `.mov`, `.webm`.
     - Scans `raw/web/` for `.html`, `.htm`, `.md`, `.json`, `.txt`.
     - Scans `raw/images/` for `.png`, `.jpg`, `.jpeg`, `.svg`, `.webp`.
     - Returns dictionary of discovered files categorized by source type.
4. **Update `update_all_sources()` Function**:
   - Update `update_all_sources()` to call `mgr.ensure_source_directories()`, `mgr.scan_raw_sources()`, `mgr.sync_and_get_deltas()`, and `mgr.audit_graph_coverage()`.

### C. Update `src/agy_graphify/tasks.py`
- Update `update_sources_action` to handle optional parameters or base path if passed, delegating to `update_all_sources()`.

### D. New and Updated Unit Tests
1. **`tests/test_source_registry.py`**:
   - Test initialization and parsing of `config/sources.json`.
   - Test directory creation and `.gitkeep` placement.
   - Test multi-modal file scanning across `raw/` subdirectories.
   - Test end-to-end `update_all_sources()` function.
2. **`tests/test_workspace_layout_standards.py`**:
   - Test verification that `raw/papers`, `raw/media`, `raw/web`, `raw/images` exist and contain `.gitkeep`.

---

## 5. Verification Method

1. **Unit Test Verification**:
   - Execute: `uv run pytest tests/test_source_registry.py tests/test_workspace_layout_standards.py -v`
   - Expected Result: 100% pass across all source registry and layout standard unit tests.

2. **CLI Task Execution Verification**:
   - Execute: `uv run agy-task update-all-sources`
   - Expected Result: Terminal log confirms auto-creation/verification of `repos/`, `raw/papers/`, `raw/media/`, `raw/web/`, `raw/images/`, logs scanned raw source counts, and completes git SHA differential sync.

3. **Full Test Suite & Environment Verification**:
   - Execute: `uv run pytest` (130+ tests passing)
   - Execute: `ALLOW_MAIN_COMMIT=1 uv run agy-verify` (Returns `decision: allow`)
