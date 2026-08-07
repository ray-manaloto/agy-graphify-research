---
name: repo-ingest
description: Modular repository cloning and deduplication skill backed by python task entrypoints.
---

# Repository Ingestion & Deduplication Skill

1. **Parse Input Sources**:
   - Accept GitHub URLs, organisation pages, or Crates.io packages.
   - Deduplicate target URLs against existing repositories in `repos/`.

2. **Execute Multi-Threaded Clone**:
   - Run `uv run python scratch/ingest_extended_sources.py`
