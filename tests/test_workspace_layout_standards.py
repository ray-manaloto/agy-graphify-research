"""Unit tests for workspace layout standards, canonical graphify-out output, and ColibriExtractor multi-modal support."""

from pathlib import Path

import pytest

from agy_graphify.colibri_extractor import ColibriExtractor
from agy_graphify.graph import GraphifyEngine
from agy_graphify.models.graph_schema import GraphData
from agy_graphify.tasks import clean_logs_action


def test_canonical_output_directory_structure(tmp_path: Path) -> None:
    """Verify graphify-out/ is the single canonical output directory at workspace root."""
    engine = GraphifyEngine(target_dir=tmp_path)
    assert engine.output_dir == tmp_path / "graphify-out"
    assert engine.output_dir.name == "graphify-out"


def test_zero_non_standard_graphify_folders() -> None:
    """Verify zero non-standard graphify-out* folders exist at workspace root or nested inside graphify-out/."""
    root = Path.cwd()
    non_standard = [
        d for d in root.glob("graphify-out*")
        if d.is_dir() and d.name != "graphify-out"
    ]
    assert not non_standard, f"Found non-standard graphify output directories: {non_standard}"

    nested_legacy = root / "graphify-out" / "graphify-out"
    assert not nested_legacy.exists(), "Found nested legacy graphify-out directory!"


@pytest.mark.asyncio
async def test_clean_logs_action_prunes_legacy_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify clean_logs_action automatically prunes legacy workspace root and nested directories."""
    monkeypatch.chdir(tmp_path)

    canonical_dir = tmp_path / "graphify-out"
    legacy_dir = tmp_path / "graphify-out-antigravity"
    nested_dir = canonical_dir / "graphify-out"

    canonical_dir.mkdir(parents=True, exist_ok=True)
    legacy_dir.mkdir(parents=True, exist_ok=True)
    nested_dir.mkdir(parents=True, exist_ok=True)

    # Put dummy files in legacy dirs to ensure it prunes non-empty dirs
    (legacy_dir / "old.log").write_text("legacy data\n", encoding="utf-8")
    (nested_dir / "nested.json").write_text("{}\n", encoding="utf-8")

    await clean_logs_action()

    assert canonical_dir.exists(), "Canonical graphify-out/ was incorrectly removed"
    assert not legacy_dir.exists(), "Legacy graphify-out-antigravity/ was not pruned"
    assert not nested_dir.exists(), "Nested graphify-out/graphify-out/ was not pruned"


def test_colibri_extractor_multimodal_extensions() -> None:
    """Verify ColibriExtractor recognizes multi-modal extensions (.py, .md, .pdf, .mp4, .mp3, .png)."""
    supported = ColibriExtractor.SUPPORTED_EXTENSIONS
    expected_extensions = (".py", ".md", ".pdf", ".mp4", ".mp3", ".png")
    for ext in expected_extensions:
        assert ext in supported, f"ColibriExtractor missing multi-modal extension {ext}"


@pytest.mark.asyncio
async def test_colibri_extractor_extract_directory_multimodal(tmp_path: Path) -> None:
    """Verify ColibriExtractor.extract_directory scans and indexes multi-modal files in a directory."""
    (tmp_path / "code.py").write_text("def run(): pass\n", encoding="utf-8")
    (tmp_path / "doc.md").write_text("# Doc\nSummary\n", encoding="utf-8")
    (tmp_path / "paper.pdf").write_bytes(b"%PDF-1.4 dummy paper content")
    (tmp_path / "video.mp4").write_bytes(b"dummy mp4 data")
    (tmp_path / "audio.mp3").write_bytes(b"dummy mp3 data")
    (tmp_path / "diagram.png").write_bytes(b"dummy png data")

    extractor = ColibriExtractor()
    graph_data = await extractor.extract_directory(tmp_path)

    assert isinstance(graph_data, GraphData)
    assert graph_data.metadata["total_files"] == 6
    assert len(graph_data.nodes) >= 1


def test_raw_gitkeep_files_exist_at_workspace_root() -> None:
    """Verify raw/papers/.gitkeep, raw/media/.gitkeep, raw/web/.gitkeep, and raw/images/.gitkeep exist at workspace root."""
    root = Path.cwd()
    expected_gitkeeps = [
        root / "raw" / "papers" / ".gitkeep",
        root / "raw" / "media" / ".gitkeep",
        root / "raw" / "web" / ".gitkeep",
        root / "raw" / "images" / ".gitkeep",
    ]
    for gitkeep in expected_gitkeeps:
        assert gitkeep.exists(), f"Expected gitkeep file missing: {gitkeep}"
        assert gitkeep.is_file(), f"Expected gitkeep path is not a file: {gitkeep}"


def test_config_sources_json_multimodal_mappings() -> None:
    """Verify config/sources.json is version 1.1.0 and contains explicit multimodal sources mappings."""
    import json

    sources_path = Path.cwd() / "config" / "sources.json"
    assert sources_path.exists(), "config/sources.json does not exist"

    data = json.loads(sources_path.read_text(encoding="utf-8"))
    assert data.get("version") == "1.1.0", f"Expected version '1.1.0', got '{data.get('version')}'"

    sources = data.get("sources", {})
    expected_mappings = {
        "git_repositories": "repos/",
        "raw_papers": "raw/papers/",
        "raw_media": "raw/media/",
        "raw_web": "raw/web/",
        "raw_images": "raw/images/",
    }
    for key, expected_val in expected_mappings.items():
        assert key in sources, f"Missing key '{key}' in config/sources.json sources"
        assert sources[key] == expected_val, f"Expected sources['{key}'] to be '{expected_val}', got '{sources[key]}'"

