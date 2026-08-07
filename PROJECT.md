# Project: Skill Consolidation & Extraction Pipeline Verification

## Architecture
- Canonical master skill: `.agents/skills/graphify_pipeline/SKILL.md`
- Skills directory: `.agents/skills/`
- Test suite: `tests/test_skill_deduplication.py`

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Master Pipeline Ingestion & Graph Extraction | GitHub/Crates parsing, sources.json deduplication, update-all-sources, colibri-graphify | M1 | R1 |
| 2 | Symlink Cleanup & Directory Integrity | Clean duplicate/broken hyphen symlinks, retain canonical underscore dirs | M2 | R2 |
| 3 | Skill Deduplication Test Suite | Unit tests in test_skill_deduplication.py checking symlinks, frontmatter, keywords | M3 | R3 |
| 4 | Gate & System Verification | 124/124 pytest pass & agy-verify decision: allow | M4 | AC |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Master Skill Consolidation | `.agents/skills/graphify_pipeline/SKILL.md` R1 | none | COMPLETED |
| 2 | Symlink Directory Cleanup | `.agents/skills/` R2 | M1 | COMPLETED |
| 3 | Deduplication Test Suite | `tests/test_skill_deduplication.py` R3 | M2 | COMPLETED |
| 4 | Final Verification Gate | Full pytest (124/124) & agy-verify | M3 | COMPLETED |

## Interface Contracts
- `graphify_pipeline/SKILL.md` frontmatter & tasks: `update-all-sources`, `colibri-graphify`, `Deduplicate`, `graphify-out/graph.json`, `GRAPH_REPORT.md`
- `tests/test_skill_deduplication.py`: unit tests verifying skill integrity.

## Code Layout
- Skills: `.agents/skills/`
- Tests: `tests/`
