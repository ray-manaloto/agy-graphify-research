import json
import hashlib
from pathlib import Path
from agy_graphify.telemetry import CausalTelemetryEvent

def verify_causal_events_file(file_path: Path):
    if not file_path.is_file():
        print(f"File not found: {file_path}")
        return

    lines = [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Total events in file: {len(lines)}")

    # Test 1: Single continuous chain assuming prev_hash carries over across all lines
    prev_hash_continuous = ""
    continuous_mismatches = []
    
    # Test 2: Resettable chain assuming prev_hash resets when step_index == 0 or prev_hash = ""
    prev_hash_per_session = ""
    session_mismatches = []

    for idx, line in enumerate(lines):
        raw = json.loads(line)
        event = CausalTelemetryEvent.model_validate(raw)
        
        # Continuous calculation
        expected_continuous = event.compute_causal_hash(prev_hash_continuous)
        if event.causal_hash != expected_continuous:
            continuous_mismatches.append((idx, event.event_id, event.step_index, expected_continuous, event.causal_hash))
        prev_hash_continuous = event.causal_hash

        # Check if step_index == 0 (start of a workflow session)
        if event.step_index == 0:
            expected_session = event.compute_causal_hash("")
        else:
            expected_session = event.compute_causal_hash(prev_hash_per_session)

        if event.causal_hash != expected_session:
            session_mismatches.append((idx, event.event_id, event.step_index, expected_session, event.causal_hash))
        prev_hash_per_session = event.causal_hash

    print(f"\n--- Continuous Hash Chain Verification ---")
    print(f"Mismatches: {len(continuous_mismatches)}")
    for m in continuous_mismatches[:5]:
        print(f"Line {m[0]} (step_index={m[2]}, event_id={m[1]}): expected {m[3][:16]}..., got {m[4][:16]}...")

    print(f"\n--- Per-Session Hash Chain Verification (reset on step_index=0) ---")
    print(f"Mismatches: {len(session_mismatches)}")
    for m in session_mismatches[:5]:
        print(f"Line {m[0]} (step_index={m[2]}, event_id={m[1]}): expected {m[3][:16]}..., got {m[4][:16]}...")

if __name__ == "__main__":
    verify_causal_events_file(Path(".gemini/telemetry/causal_events.jsonl"))
