from __future__ import annotations

from collections.abc import Awaitable
from typing import Protocol

from app.runtime.models import NodeExecutionResult, RuntimeNode, RuntimeState


class RuntimeHandler(Protocol):
    def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> Awaitable[NodeExecutionResult]: ...


class NodeDispatcher:
    """Routes node types to runtime handlers."""

    handlers: dict[str, RuntimeHandler]

    def __init__(self, handlers: dict[str, RuntimeHandler] | None = None) -> None:
        self.handlers = handlers or {}

    def get_handler(self, node_type: str) -> RuntimeHandler | None:
        return self.handlers.get(node_type)
