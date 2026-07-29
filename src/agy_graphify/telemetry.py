"""Async Telemetry & Conversation Event Parser for Self-Reflection & Self-Learning."""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import msgspec
from pydantic import BaseModel

from .logger import logger


class TelemetryEvent(BaseModel):
    """Structured event extracted from agent transcripts for self-reflection."""

    conversation_id: str
    step_index: int
    event_type: str
    source: str
    status: str
    content_summary: str
    tool_calls: list[dict[str, Any]] = []


class TelemetryCollector:
    """Parses agent transcript JSONL logs and writes structured telemetry to project scope."""

    def __init__(self, project_dir: Path | None = None, app_data_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path.cwd()
        self.app_data_dir = app_data_dir or (Path.home() / ".gemini" / "antigravity")
        self.output_dir = self.project_dir / ".gemini" / "telemetry"

    def _parse_transcript_file(self, conv_path: Path) -> list[TelemetryEvent]:
        events: list[TelemetryEvent] = []
        transcript_file = conv_path / ".system_generated" / "logs" / "transcript.jsonl"
        if not transcript_file.is_file():
            return events

        try:
            content = transcript_file.read_text(encoding="utf-8")
        except (PermissionError, OSError):
            return events

        for line in content.splitlines():
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                event = TelemetryEvent(
                    conversation_id=conv_path.name,
                    step_index=raw.get("step_index", 0),
                    event_type=raw.get("type", "UNKNOWN"),
                    source=raw.get("source", "UNKNOWN"),
                    status=raw.get("status", "DONE"),
                    content_summary=str(raw.get("content", ""))[:200],
                    tool_calls=raw.get("tool_calls", []),
                )
                events.append(event)
            except json.JSONDecodeError:
                continue

        return events

    async def collect_events(self, conversation_id: str | None = None) -> list[TelemetryEvent]:
        """Parse conversation transcript.jsonl and extract telemetry events gracefully."""
        events: list[TelemetryEvent] = []
        brain_dir = self.app_data_dir / "brain"

        try:
            if not brain_dir.is_dir():
                logger.info(f"No brain directory found at {brain_dir}")
                return events

            target_convs = (
                [brain_dir / conversation_id] if conversation_id else list(brain_dir.iterdir())
            )
        except (PermissionError, FileNotFoundError) as exc:
            logger.warning(f"Could not access brain directory at {brain_dir}: {exc}")
            return events

        for conv_path in target_convs:
            if conv_path.is_dir():
                events.extend(self._parse_transcript_file(conv_path))

        self.output_dir.mkdir(parents=True, exist_ok=True)

        jsonl_output = self.output_dir / "events.jsonl"
        with jsonl_output.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(ev.model_dump_json() + "\n")

        msgpack_output = self.output_dir / "events.msgpack"
        msgpack_bytes = msgspec.msgpack.encode([ev.model_dump() for ev in events])
        msgpack_output.write_bytes(msgpack_bytes)

        logger.info(f"Collected {len(events)} telemetry events into {self.output_dir}")
        return events


async def async_main(*params: str) -> None:
    """Async main for telemetry collector CLI."""
    parser = argparse.ArgumentParser(description="Telemetry & Conversation Event Collector")
    parser.add_argument("--conversation-id", help="Target conversation ID to parse")

    args = parser.parse_args(list(params) if params else None)

    collector = TelemetryCollector()
    events = await collector.collect_events(conversation_id=args.conversation_id)
    print(f"Telemetry collector processed {len(events)} events.")


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
