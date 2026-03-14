from __future__ import annotations

from dataclasses import dataclass

from app.domain.memory.context import ContextMemoryAccessor
from app.domain.memory.history import HistoryMemoryAccessor
from app.domain.memory.knowledge import KnowledgeMemoryAccessor
from app.runtime.models import RuntimeState


@dataclass(slots=True)
class RuntimeMemoryBundle:
    context: ContextMemoryAccessor
    history: HistoryMemoryAccessor
    knowledge: KnowledgeMemoryAccessor


class MemoryService:
    """Memory service facade for runtime handlers."""

    @staticmethod
    def bind_runtime(state: RuntimeState) -> RuntimeMemoryBundle:
        return RuntimeMemoryBundle(
            context=ContextMemoryAccessor(state),
            history=HistoryMemoryAccessor(state),
            knowledge=KnowledgeMemoryAccessor(state),
        )
