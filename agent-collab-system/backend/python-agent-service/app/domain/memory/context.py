from __future__ import annotations

from app.runtime.models import JsonValue, RuntimeState


class ContextMemoryAccessor:
    """Execution-scoped context memory accessor."""

    state: RuntimeState

    def __init__(self, state: RuntimeState) -> None:
        self.state = state

    def get_context(self, key: str, default: JsonValue | None = None) -> JsonValue:
        return self.state.context.get(key, default)

    def set_context(self, key: str, value: JsonValue) -> None:
        self.state.context[key] = value

    def append_context_event(self, event: dict[str, JsonValue]) -> None:
        raw_events = self.state.context.get("context_events")
        events = raw_events if isinstance(raw_events, list) else []
        events.append(event)
        self.state.context["context_events"] = events
