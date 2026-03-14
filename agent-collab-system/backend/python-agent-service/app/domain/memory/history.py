from __future__ import annotations

from typing import cast

from app.runtime.models import JsonValue, RuntimeState


class HistoryMemoryAccessor:
    """Execution-history memory accessor backed by runtime state."""

    state: RuntimeState

    def __init__(self, state: RuntimeState) -> None:
        self.state = state

    def search_history(self, query: str, agent_type: str | None = None) -> list[dict[str, JsonValue]]:
        normalized_query = query.lower().strip()
        return [
            item
            for item in self._memory_records()
            if (not normalized_query or normalized_query in str(item.get("summary", "")).lower())
            and (agent_type is None or item.get("agent_type") == agent_type)
        ]

    def write_history(self, memory_record: dict[str, JsonValue]) -> None:
        records = self._memory_records()
        records.append(memory_record)
        serialized_records: list[JsonValue] = [cast(JsonValue, item) for item in records]
        self.state.context["history_memories"] = serialized_records

    def _memory_records(self) -> list[dict[str, JsonValue]]:
        raw = self.state.context.get("history_memories")
        if isinstance(raw, list):
            return cast(list[dict[str, JsonValue]], raw)
        records: list[dict[str, JsonValue]] = []
        self.state.context["history_memories"] = []
        return records
