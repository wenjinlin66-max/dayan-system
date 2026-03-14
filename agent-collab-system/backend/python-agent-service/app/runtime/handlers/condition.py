from __future__ import annotations

from app.runtime.models import NodeExecutionResult, RuntimeNode, RuntimeState


class ConditionNodeHandler:
    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        _ = state
        preferred_next = node.config.get("preferred_next")
        if isinstance(preferred_next, str) and preferred_next in next_nodes:
            return NodeExecutionResult(next_node_id=preferred_next, route_decided=True)
        return NodeExecutionResult(next_node_id=next_nodes[0] if next_nodes else None, route_decided=True)
