"""Unit tests verifying skill deduplication and valid frontmatter in .agents/skills/."""

import pytest
from pathlib import Path


def test_no_duplicate_skill_symlinks() -> None:
    skills_dir = Path(".agents/skills")
    assert skills_dir.exists(), ".agents/skills directory missing"

    # Symlinks to remove: visual-edit, visual-plan, visual-recap
    disallowed_symlinks = ["visual-edit", "visual-plan", "visual-recap", "repo_ingest"]
    for symlink_name in disallowed_symlinks:
        target = skills_dir / symlink_name
        assert not target.exists(), f"Duplicate skill file/symlink '{symlink_name}' still exists in .agents/skills!"


def test_canonical_skills_contain_valid_frontmatter() -> None:
    skills_dir = Path(".agents/skills")
    assert skills_dir.exists()

    skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]
    assert len(skill_dirs) > 0, "No skill directories found"

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"Skill directory '{skill_dir.name}' missing SKILL.md!"
        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{skill_file} missing YAML frontmatter header ('---')"
