# Handoff Report — Workspace Layout Standards & ColibriExtractor Multi-Modal Verification

**Agent**: `explorer_survey_2`  
**Date**: 2026-08-07  
**Working Directory**: `/Users/rmanaloto/agy-graphify-research/.agents/explorer_survey_2`  

---

## 1. Observation

### Exact File & Code Inspections
1. **Request & Architecture Spec Requirements**:
   - `ORIGINAL_REQUEST.md` (lines 44–52): Requires updating `clean_logs_action()` in `src/agy_graphify/tasks.py` to prune legacy workspace root directories (`graphify-out-antigravity/` and nested `graphify-out/graphify-out/`), and creating `tests/test_workspace_layout_standards.py`.
   - `docs/graphify_sources_proposal_architecture.md` (lines 42–56): Requires layout standard tests asserting:
     - `graphify-out/` is the single canonical output directory at workspace root.
     - Zero non-standard `graphify-out*` folders exist.
     - `ColibriExtractor` recognizes multi-modal extensions (`.py`, `.md`, `.pdf`, `.mp4`, `.mp3`, `.png`).

2. **Existing Extractor Implementation**:
   - `src/agy_graphify/colibri_extractor.py` (lines 221–225):
     ```python
     async def extract_directory(
         self,
         dir_path: Path,
         extensions: tuple[str, ...] = (".py", ".md", ".c", ".metal", ".h", ".js", ".ts", ".rs"),
     ) -> GraphData:
     ```
     *Observation*: The default `extensions` tuple in `ColibriExtractor.extract_directory` currently lists `.py`, `.md`, `.c`, `.metal`, `.h`, `.js`, `.ts`, `.rs`, but **lacks** multi-modal extensions `.pdf`, `.mp4`, `.mp3`, `.png`.

3. **Workspace Filesystem Audit**:
   - Running `find_by_name` on workspace root `/Users/rmanaloto/agy-graphify-research`:
     - Found `graphify-out` (canonical)
     - Found `graphify-out-antigravity` (legacy non-standard root directory)
   - Running `list_dir` on `/Users/rmanaloto/agy-graphify-research/graphify-out`:
     - Found nested directory `graphify-out/graphify-out` (legacy non-standard nested directory).

4. **Tasks Implementation (`clean_logs_action`)**:
   - `src/agy_graphify/tasks.py` (lines 585–600): `clean_logs_action()` currently only prunes process log files older than 7 days inside `.gemini/telemetry/`. It does not perform directory cleanup for legacy `graphify-out-antigravity/` or `graphify-out/graphify-out/`.

5. **Existing Test Suite**:
   - `tests/` directory contains 22 unit test modules (e.g. `test_colibri_extractor.py`, `test_tasks.py`, `test_process_logging.py`, `test_graph.py`, `test_okf.py`).
   - `tests/test_workspace_layout_standards.py` does not yet exist.

---

## 2. Logic Chain

1. **Pruning Implementation (`tasks.py`)**:
   - `clean_logs_action()` needs to be enhanced to automatically find and remove legacy root directories matching `graphify-out-*` (e.g. `graphify-out-antigravity`) as well as nested legacy directories (`graphify-out/graphify-out`).
   - Once updated, running `uv run agy-task clean-logs` will clean both telemetry logs and legacy output directories.

2. **ColibriExtractor Multi-Modal Support (`colibri_extractor.py`)**:
   - `ColibriExtractor` should explicitly define `SUPPORTED_EXTENSIONS`:
     ```python
     SUPPORTED_EXTENSIONS = (
         ".py", ".md", ".txt", ".pdf", ".mp4", ".mp3", ".png", ".jpg", ".svg",
         ".c", ".metal", ".h", ".js", ".ts", ".rs"
     )
     ```
   - `extract_directory` should default to `ColibriExtractor.SUPPORTED_EXTENSIONS`.
   - `_fallback_heuristic_extraction` should assign appropriate `file_type` metadata for non-code files (`.pdf` -> `"paper"`, `.mp4`/`.mp3` -> `"media"`, `.png` -> `"image"`, `.md` -> `"doc"`).

3. **Proposed Structure for `tests/test_workspace_layout_standards.py`**:
   The test module should contain 5 clean, focused test functions:

   - **Test A: `test_canonical_output_directory_structure`**
     - Verifies `GraphifyEngine(root_path).output_dir` defaults strictly to `root_path / "graphify-out"`.
     - Asserts that canonical output files (`graph.json`, `GRAPH_REPORT.md`, `graph.html`) are created inside `graphify-out/`.

   - **Test B: `test_zero_non_standard_graphify_folders`**
     - Audits workspace root (`Path.cwd()`) for any subdirectories starting with `graphify-out`.
     - Asserts that no directories with `name != "graphify-out"` exist (such as `graphify-out-antigravity`).
     - Asserts that `graphify-out/` does not contain a nested `graphify-out/` subdirectory.

   - **Test C: `test_clean_logs_action_prunes_legacy_directories`** (isolating with `tmp_path` and `monkeypatch.chdir`)
     - Creates mock legacy directories `tmp_path / "graphify-out-antigravity"` and `tmp_path / "graphify-out" / "graphify-out"`.
     - Invokes `await clean_logs_action()`.
     - Verifies legacy folders are deleted, while the canonical `tmp_path / "graphify-out"` directory remains intact.

   - **Test D: `test_colibri_extractor_multimodal_extensions`**
     - Verifies `ColibriExtractor.SUPPORTED_EXTENSIONS` contains `.py`, `.md`, `.pdf`, `.mp4`, `.mp3`, `.png`.
     - Creates mock files in `tmp_path`: `sample.py`, `doc.md`, `paper.pdf`, `video.mp4`, `audio.mp3`, `diagram.png`.
     - Calls `await extractor.extract_directory(tmp_path)`.
     - Asserts `graph_data.metadata["total_files"] == 6`, proving all 6 multi-modal extension types were recognized and processed.

   - **Test E: `test_colibri_extractor_file_type_classification`**
     - Asserts `extract_file` returns valid `GraphData` nodes for `.pdf`, `.mp4`, `.mp3`, and `.png` files without crashing.

---

## 3. Caveats

1. **Execution Environment**:
   - Media file extraction (`.mp4`, `.mp3`) and PDF parsing in `ColibriExtractor` use heuristic fallbacks when external sidecars (ffmpeg, whisper, pdfplumber) are offline. Test assertions should verify file extension discovery and node generation rather than actual binary audio decoding.
2. **Test Isolation**:
   - Tests altering directory layout or running `clean_logs_action()` MUST use `tmp_path` and `monkeypatch.chdir(tmp_path)` to avoid mutating the workspace during test runs.

---

## 4. Conclusion

The proposed layout and multi-modal test suite `tests/test_workspace_layout_standards.py` should be implemented with the following structure:

```python
"""Unit tests for workspace layout standards, canonical graphify-out output, and multi-modal extension support."""

from pathlib import Path
import pytest

from agy_graphify.colibri_extractor import ColibriExtractor
from agy_graphify.graph import GraphifyEngine
from agy_graphify.tasks import clean_logs_action


def test_canonical_output_directory_structure(tmp_path: Path):
    """Verify graphify-out/ is the canonical output directory at workspace root."""
    engine = GraphifyEngine(target_dir=tmp_path)
    assert engine.output_dir == tmp_path / "graphify-out"


def test_zero_non_standard_graphify_folders():
    """Verify zero non-standard graphify-out* folders exist in workspace root."""
    root = Path.cwd()
    non_standard = [
        d for d in root.glob("graphify-out*")
        if d.is_dir() and d.name != "graphify-out"
    ]
    assert not non_standard, f"Found non-standard graphify output directories: {non_standard}"
    assert not (root / "graphify-out" / "graphify-out").exists(), "Found nested graphify-out directory!"


@pytest.mark.asyncio
async def test_clean_logs_action_prunes_legacy_directories(tmp_path: Path, monkeypatch):
    """Verify clean_logs_action prunes legacy workspace root and nested directories."""
    monkeypatch.chdir(tmp_path)
    
    canonical_dir = tmp_path / "graphify-out"
    legacy_dir = tmp_path / "graphify-out-antigravity"
    nested_dir = canonical_dir / "graphify-out"
    
    canonical_dir.mkdir(parents=True, exist_ok=True)
    legacy_dir.mkdir(parents=True, exist_ok=True)
    nested_dir.mkdir(parents=True, exist_ok=True)

    await clean_logs_action()

    assert canonical_dir.exists(), "Canonical graphify-out/ was incorrectly removed"
    assert not legacy_dir.exists(), "Legacy graphify-out-antigravity/ was not pruned"
    assert not nested_dir.exists(), "Nested graphify-out/graphify-out/ was not pruned"


def test_colibri_extractor_supported_extensions():
    """Verify ColibriExtractor recognizes multi-modal extensions."""
    supported = ColibriExtractor.SUPPORTED_EXTENSIONS
    for ext in (".py", ".md", ".pdf", ".mp4", ".mp3", ".png"):
        assert ext in supported, f"ColibriExtractor missing multi-modal extension {ext}"


@pytest.mark.asyncio
async def test_colibri_extractor_multimodal_directory(tmp_path: Path):
    """Verify ColibriExtractor scans and processes all multi-modal file extensions."""
    (tmp_path / "code.py").write_text("def run(): pass\n", encoding="utf-8")
    (tmp_path / "doc.md").write_text("# Doc\nSummary\n", encoding="utf-8")
    (tmp_path / "paper.pdf").write_bytes(b"%PDF-1.4 dummy paper content")
    (tmp_path / "video.mp4").write_bytes(b"dummy mp4 data")
    (tmp_path / "audio.mp3").write_bytes(b"dummy mp3 data")
    (tmp_path / "diagram.png").write_bytes(b"dummy png data")

    extractor = ColibriExtractor()
    graph_data = await extractor.extract_directory(tmp_path)

    assert graph_data.metadata["total_files"] == 6
```

---

## 5. Verification Method

To verify these layout standards and test suite once implemented:

1. **Run New Workspace Layout Unit Tests**:
   ```bash
   uv run pytest tests/test_workspace_layout_standards.py -v
   ```
2. **Run Legacy Directory Pruning Action**:
   ```bash
   uv run agy-task clean-logs
   ```
   Confirm `graphify-out-antigravity/` and `graphify-out/graphify-out/` are removed from the workspace root.
3. **Run Full Test Suite & Environment Check**:
   ```bash
   uv run pytest
   ALLOW_MAIN_COMMIT=1 uv run agy-verify
   ```
   Assert all tests pass (125+ tests) and `agy-verify` returns `decision: allow`.
