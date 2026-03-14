from __future__ import annotations

from app.domain.memory.service import MemoryService
from app.runtime.models import NodeExecutionResult, RuntimeNode, RuntimeState


class DialogNodeHandler:
    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        memory = MemoryService.bind_runtime(state)
        latest_message = state.input_payload.get("message")
        _ = state.context.setdefault("dialog_message", latest_message)
        memory.context.set_context("latest_dialog_node", node.id)
        memory.history.write_history(
            {
                "memory_type": "execution_history",
                "agent_type": "dialog_agent",
                "workflow_id": state.workflow_id,
                "execution_id": state.execution_id,
                "summary": f"{node.name} 处理了一次对话输入",
                "payload": {"message": latest_message},
            }
        )
        return NodeExecutionResult(next_node_id=next_nodes[0] if next_nodes else None)
