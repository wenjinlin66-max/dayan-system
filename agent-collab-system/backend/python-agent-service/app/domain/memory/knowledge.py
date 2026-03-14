from __future__ import annotations

from typing import cast

from app.runtime.models import JsonValue, RuntimeState


class KnowledgeMemoryAccessor:
    """Knowledge memory accessor backed by runtime input/context."""

    state: RuntimeState

    def __init__(self, state: RuntimeState) -> None:
        self.state = state

    def search_knowledge(self, query: str, scopes: list[str] | None = None) -> list[dict[str, JsonValue]]:
        normalized_query = query.lower().strip()
        matched: list[dict[str, JsonValue]] = []
        for item in self._documents():
            scope = str(item.get("scope") or "")
            if scopes and scope and scope not in scopes:
                continue
            haystack = " ".join(
                [
                    str(item.get("title") or ""),
                    str(item.get("content") or ""),
                    " ".join(cast(list[str], item.get("tags")) if isinstance(item.get("tags"), list) else []),
                ]
            ).lower()
            if not normalized_query or normalized_query in haystack:
                matched.append(item)
        return matched

    def fetch_document(self, doc_id: str) -> dict[str, JsonValue] | None:
        return next((item for item in self._documents() if item.get("doc_id") == doc_id), None)

    def _documents(self) -> list[dict[str, JsonValue]]:
        raw_from_input = self.state.input_payload.get("knowledge_docs")
        if isinstance(raw_from_input, list):
            return cast(list[dict[str, JsonValue]], raw_from_input)
        raw_from_context = self.state.context.get("knowledge_docs")
        if isinstance(raw_from_context, list):
            return cast(list[dict[str, JsonValue]], raw_from_context)
        return []
