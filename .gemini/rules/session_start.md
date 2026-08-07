# Session Startup Goal Resume Rule

When a new session starts:
1. Read the Level 1 progressive handoff context from `uv run agy-verify`.
2. Inspect `.gemini/graph_state.json` or `.gemini/orchestration_plan.json` (< 100 tokens).
3. If pending steps exist, immediately ask the user at the very first turn:
   "Would you like to resume and execute the next logical step for [Goal Name]?"
4. Do NOT read large documentation files or conversation transcripts into context until the user confirms.
