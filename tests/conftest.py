import os
from pathlib import Path

# Ensure PHOENIX_WORKING_DIR points to workspace directory to avoid sandbox permissions issue
workspace_dir = Path(__file__).resolve().parent.parent
phoenix_dir = workspace_dir / ".gemini" / "phoenix"
phoenix_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PHOENIX_WORKING_DIR", str(phoenix_dir))
