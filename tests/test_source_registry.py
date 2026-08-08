"""Unit tests for SourceRegistryManager multi-modal source handling and auto-creation."""

import json
from pathlib import Path
import pytest

from agy_graphify.source_registry import SourceRegistryManager, update_all_sources


def test_load_sources_config(tmp_path: Path) -> None:
    config_file = tmp_path / "config" / "sources.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_data = {
        "version": "1.1.0",
        "sources": {
            "git_repositories": "repos/",
            "raw_papers": "raw/papers/",
            "raw_media": "raw/media/",
            "raw_web": "raw/web/",
            "raw_images": "raw/images/",
        },
    }
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    mgr = SourceRegistryManager(config_path=config_file)
    assert mgr.sources_config["raw_papers"] == "raw/papers/"
    assert mgr.sources_config["raw_media"] == "raw/media/"


def test_ensure_source_directories(tmp_path: Path) -> None:
    mgr = SourceRegistryManager(config_path=tmp_path / "nonexistent.json")
    verified_dirs = mgr.ensure_source_directories(base_dir=tmp_path)

    expected_subpaths = ["repos", "raw/papers", "raw/media", "raw/web", "raw/images"]
    for sub in expected_subpaths:
        dir_path = tmp_path / sub
        assert dir_path.is_dir()
        assert (dir_path / ".gitkeep").exists()

    assert len(verified_dirs) >= 5


def test_scan_raw_sources(tmp_path: Path) -> None:
    mgr = SourceRegistryManager(config_path=tmp_path / "nonexistent.json")
    mgr.ensure_source_directories(base_dir=tmp_path)

    # Create dummy files
    paper = tmp_path / "raw" / "papers" / "arxiv_paper.pdf"
    paper.write_text("dummy pdf", encoding="utf-8")

    media = tmp_path / "raw" / "media" / "video.mp4"
    media.write_text("dummy video", encoding="utf-8")

    web = tmp_path / "raw" / "web" / "article.html"
    web.write_text("<html></html>", encoding="utf-8")

    img = tmp_path / "raw" / "images" / "diagram.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")

    catalog = mgr.scan_raw_sources(base_dir=tmp_path)

    assert "raw_papers" in catalog
    assert paper in catalog["raw_papers"]
    assert media in catalog["raw_media"]
    assert web in catalog["raw_web"]
    assert img in catalog["raw_images"]


def test_update_all_sources_e2e(tmp_path: Path) -> None:
    res = update_all_sources(base_dir=tmp_path)
    assert "directories" in res
    assert "raw_catalog" in res
    assert len(res["directories"]) >= 5
