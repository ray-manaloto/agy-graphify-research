#!/usr/bin/env python3
"""Project environment verification hook script for Antigravity / Gemini CLI."""

import sys
from pathlib import Path

# Add project src/ to sys.path so agy_graphify can be imported directly
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from agy_graphify.verify import main  # noqa: E402

if __name__ == "__main__":
    main()
