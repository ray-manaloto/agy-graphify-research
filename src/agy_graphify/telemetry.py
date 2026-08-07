"""Async Telemetry & Conversation Event Parser for Self-Reflection & Self-Learning."""

import argparse
import asyncio
import hashlib
import json
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import msgspec
from pydantic import BaseModel, ValidationError

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


class CausalTelemetryEvent(BaseModel):
    """Extended telemetry event with causal DAG references and subagent metadata."""

    event_id: str
    conversation_id: str
    causal_parent_id: str | None = None
    step_index: int = 0
    event_type: str = "UNKNOWN"
    subagent_role: str | None = None
    status: str = "DONE"
    content_summary: str = ""
    tool_calls: list[dict[str, Any]] = []
    causal_hash: str = ""

    def compute_causal_hash(self, prev_hash: str = "") -> str:
        payload = f"{self.event_id}:{self.conversation_id}:{self.causal_parent_id}:{self.step_index}:{self.status}:{prev_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class MemoryStoreAdapter:
    """Adapter incorporating cxdb causal DAG tracing and pensyve long-term memory for TelemetryCollector."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.causal_events_file = output_dir / "causal_events.jsonl"
        self.semantic_memory_file = output_dir / "semantic_memory.json"
        self.remediation_file = output_dir / "remediation_rules.json"
        self._causal_dag: dict[str, list[CausalTelemetryEvent]] = {}
        self._last_hash: str = ""

        if self.causal_events_file.is_file() and self.causal_events_file.stat().st_size > 0:
            try:
                content = self.causal_events_file.read_text(encoding="utf-8").strip()
                if content:
                    last_line = content.splitlines()[-1].strip()
                    if last_line:
                        data = json.loads(last_line)
                        if isinstance(data, dict) and "causal_hash" in data:
                            self._last_hash = str(data["causal_hash"])
            except Exception as exc:
                logger.debug(f"Failed to seed last_hash from {self.causal_events_file}: {exc}")

    def append_causal_event(self, event: CausalTelemetryEvent) -> None:
        """Append event to causal DAG store with incremental hash verification."""
        event.causal_hash = event.compute_causal_hash(self._last_hash)
        self._last_hash = event.causal_hash

        if event.conversation_id not in self._causal_dag:
            self._causal_dag[event.conversation_id] = []
        self._causal_dag[event.conversation_id].append(event)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        with self.causal_events_file.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def get_causal_lineage(self, conversation_id: str) -> list[CausalTelemetryEvent]:
        """Query execution lineage for a specific conversation ID."""
        return self._causal_dag.get(conversation_id, [])

    def handle_symphony_event(self, event: Any) -> None:
        """Handle incoming SymphonyEvent from EventDispatcher and record causal telemetry event."""
        event_type_str = (
            event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        )
        causal_ev = CausalTelemetryEvent(
            event_id=event.event_id,
            conversation_id=event.graph_id,
            causal_parent_id=event.node_id,
            step_index=len(self.get_causal_lineage(event.graph_id)),
            event_type=event_type_str,
            subagent_role=event.payload.get("role")
            if hasattr(event, "payload") and isinstance(event.payload, dict)
            else None,
            status="DONE"
            if "COMPLETED" in event_type_str or "STARTED" in event_type_str
            else event_type_str,
            content_summary=f"Symphony event {event_type_str} for graph {event.graph_id}"
            + (f" node {event.node_id}" if getattr(event, "node_id", None) else ""),
            tool_calls=[],
        )
        self.append_causal_event(causal_ev)

    def subscribe_to_dispatcher(self, dispatcher: Any) -> None:
        """Subscribe this MemoryStoreAdapter instance to all EventType channels on EventDispatcher."""
        from .models.graph_engine_schema import EventType

        for et in EventType:
            dispatcher.subscribe(et, self.handle_symphony_event)

    def record_remediation_rules(self, failed_tools: list[dict[str, Any]]) -> None:
        """Consolidate failed tool instances into persistent pensyve-style self-healing rules."""
        if not failed_tools:
            return

        existing_rules: list[dict[str, Any]] = []
        if self.remediation_file.is_file():
            try:
                existing_rules = json.loads(self.remediation_file.read_text(encoding="utf-8"))
            except Exception:
                existing_rules = []

        seen = {
            f"{r.get('tool')}:{json.dumps(r.get('args'), sort_keys=True)}"
            for r in existing_rules
            if isinstance(r, dict)
        }
        for item in failed_tools:
            if isinstance(item, dict):
                key = f"{item.get('tool')}:{json.dumps(item.get('args'), sort_keys=True)}"
                if key not in seen:
                    existing_rules.append(item)
                    seen.add(key)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.remediation_file.write_text(json.dumps(existing_rules, indent=2), encoding="utf-8")

    def query_remediation_rules(self, tool_name: str | None = None) -> list[dict[str, Any]]:
        """Retrieve stored remediation rules for dynamic prompt augmentation."""
        if not self.remediation_file.is_file():
            return []
        try:
            rules = json.loads(self.remediation_file.read_text(encoding="utf-8"))
            if not isinstance(rules, list):
                return []
            if tool_name:
                return [r for r in rules if isinstance(r, dict) and r.get("tool") == tool_name]
            return rules
        except Exception:
            return []


class TelemetryCollector:
    """Parses agent transcript JSONL logs and writes structured telemetry to project scope."""

    _phoenix_initialized: bool = False

    def __init__(self, project_dir: Path | None = None, app_data_dir: Path | None = None) -> None:
        self.project_dir = (project_dir or Path.cwd()).resolve()
        self.app_data_dir = (app_data_dir or (Path.home() / ".gemini" / "antigravity")).resolve()
        self.output_dir = self.project_dir / ".gemini" / "telemetry"
        self.memory_adapter = MemoryStoreAdapter(output_dir=self.output_dir)
        self._init_phoenix()

    def _init_phoenix(self) -> None:
        """Initialize local Arize Phoenix OpenTelemetry tracing if available."""
        if TelemetryCollector._phoenix_initialized:
            return
        try:
            import os

            phoenix_dir = self.project_dir / ".gemini" / "phoenix"
            phoenix_dir.mkdir(parents=True, exist_ok=True)
            os.environ["PHOENIX_WORKING_DIR"] = str(phoenix_dir)

            import phoenix as px

            px.launch_app()  # Launches local Arize Phoenix dashboard server
            TelemetryCollector._phoenix_initialized = True
            logger.info("Arize Phoenix local OTEL telemetry server initialized.")
        except Exception:
            logger.debug(
                "Arize Phoenix OTEL server not active; falling back to local file telemetry."
            )

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
                if not isinstance(raw, dict):
                    continue

                tool_calls_raw = raw.get("tool_calls")
                tool_calls = tool_calls_raw if isinstance(tool_calls_raw, list) else []

                event = TelemetryEvent(
                    conversation_id=conv_path.name,
                    step_index=int(raw.get("step_index", 0) or 0),
                    event_type=str(raw.get("type", "UNKNOWN")),
                    source=str(raw.get("source", "UNKNOWN")),
                    status=str(raw.get("status", "DONE")),
                    content_summary=str(raw.get("content", ""))[:200],
                    tool_calls=tool_calls,
                )
                events.append(event)
            except (
                json.JSONDecodeError,
                AttributeError,
                TypeError,
                ValidationError,
                ValueError,
            ) as exc:
                logger.debug(f"Skipping malformed transcript line: {exc}")
                continue

        return events

    def analyze_failed_tools(self, events: list[TelemetryEvent]) -> list[dict[str, Any]]:
        """Self-healing analyzer: Extracts failed tool executions for dynamic prompt remediation."""
        failed_tools: list[dict[str, Any]] = []
        for ev in events:
            if str(ev.status).upper() in ("ERROR", "FAILED"):
                if isinstance(ev.tool_calls, list):
                    for tc in ev.tool_calls:
                        if isinstance(tc, dict):
                            failed_tools.append(
                                {
                                    "conversation_id": ev.conversation_id,
                                    "step_index": ev.step_index,
                                    "tool": tc.get("name", "unknown"),
                                    "args": tc.get("args", {}),
                                }
                            )
        return failed_tools

    @contextmanager
    def trace_subagent_span(
        self, span_name: str, attributes: dict[str, Any] | None = None
    ) -> Generator[Any, None, None]:
        """Context manager for emitting OpenTelemetry spans."""
        try:
            from opentelemetry import trace

            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(span_name, attributes=attributes or {}) as span:
                yield span
        except ImportError:
            logger.debug(f"OpenTelemetry not installed, tracing skipped for {span_name}")
            yield None

    async def collect_events(self, conversation_id: str | None = None) -> list[TelemetryEvent]:
        """Parse conversation transcript.jsonl and extract telemetry events gracefully."""
        events: list[TelemetryEvent] = []
        brain_dir = self.app_data_dir / "brain"

        try:
            if not brain_dir.is_dir():
                logger.info(f"No brain directory found at {brain_dir}")
                return events

            if conversation_id:
                target_path = brain_dir / conversation_id
                if not target_path.is_dir():
                    logger.warning(
                        f"Requested conversation ID '{conversation_id}' does not exist in {brain_dir}"
                    )
                    return events
                target_convs = [target_path]
            else:
                target_convs = list(brain_dir.iterdir())
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

        for idx, ev in enumerate(events):
            causal_ev = CausalTelemetryEvent(
                event_id=f"{ev.conversation_id}-{ev.step_index}-{idx}",
                conversation_id=ev.conversation_id,
                causal_parent_id=conversation_id,
                step_index=ev.step_index,
                event_type=ev.event_type,
                status=ev.status,
                content_summary=ev.content_summary,
                tool_calls=ev.tool_calls,
            )
            self.memory_adapter.append_causal_event(causal_ev)

        failed_tools = self.analyze_failed_tools(events)
        if failed_tools:
            self.memory_adapter.record_remediation_rules(failed_tools)
            logger.warning(
                f"Self-healing: Logged {len(failed_tools)} failed tool executions for remediation."
            )

        logger.info(f"Collected {len(events)} telemetry events into {self.output_dir}")
        return events


async def async_main(*params: str) -> None:
    """Async main for telemetry collector CLI."""
    parser = argparse.ArgumentParser(description="Telemetry & Conversation Event Collector")
    parser.add_argument("--conversation-id", help="Target conversation ID to parse")

    args = parser.parse_args(list(params) if params else [])

    collector = TelemetryCollector()
    events = await collector.collect_events(conversation_id=args.conversation_id)
    print(f"Telemetry collector processed {len(events)} events.")


def main(*params: str) -> None:
    asyncio.run(async_main(*params))


if __name__ == "__main__":
    main()
