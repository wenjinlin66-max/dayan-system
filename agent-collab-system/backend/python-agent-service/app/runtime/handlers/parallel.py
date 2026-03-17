from __future__ import annotations

from typing import cast

from app.runtime.models import JsonValue, NodeExecutionResult, RuntimeNode, RuntimeState


class ParallelNodeHandler:
    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        if not next_nodes:
            return NodeExecutionResult(next_node_id=None, route_decided=True)
        raw_pending = state.context.get("parallel_pending_nodes")
        pending = cast(list[JsonValue], raw_pending) if isinstance(raw_pending, list) else []
        state.context["parallel_pending_nodes"] = cast(list[JsonValue], [*next_nodes[1:], *pending])
        state.context["parallel_origin_node"] = node.id
        return NodeExecutionResult(next_node_id=next_nodes[0], route_decided=True)
