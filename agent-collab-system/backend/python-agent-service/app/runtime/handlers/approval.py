from __future__ import annotations

from uuid import uuid4

from app.db.models.approval import ApprovalTask
from app.domain.approvals.repository import ApprovalRepository
from app.domain.chat.repository import ChatRepository
from app.runtime.models import NodeExecutionResult, RuntimeNode, RuntimeState


class ApprovalNodeHandler:
    repository: ApprovalRepository

    def __init__(self, repository: ApprovalRepository) -> None:
        self.repository = repository

    async def execute(self, node: RuntimeNode, state: RuntimeState, next_nodes: list[str]) -> NodeExecutionResult:
        next_node = next_nodes[0] if next_nodes else None
        go_approval_id = f"go_appr_{uuid4().hex[:12]}"
        task = ApprovalTask(
            id=f"appr_{uuid4().hex[:12]}",
            go_approval_id=go_approval_id,
            execution_id=state.execution_id,
            status="pending",
        )
        _ = await self.repository.create_task(task)
        state.context["active_approval_go_id"] = go_approval_id
        state.context["active_approval_task_id"] = task.id
        state.context["approval_title"] = str(node.config.get("approvalTitle") or "审批任务")
        state.context["approval_summary"] = str(node.config.get("description") or f"等待审批后继续执行节点 {node.name}")
        state.context["approval_current_node"] = node.id
        state.context["approval_next_node"] = next_node
        session_id = state.context.get("chat_session_id")
        if isinstance(session_id, str) and session_id:
            chat_repository = ChatRepository(self.repository.session)
            await chat_repository.append_assistant_message(
                session_id=session_id,
                dept_id=state.dept_id,
                content=f"审批信息已送达当前部门对话框：《{state.context['approval_title']}》等待处理。",
                payload={
                    "message_kind": "approval_pending",
                    "approval_task_id": task.id,
                    "go_approval_id": go_approval_id,
                    "execution_id": state.execution_id,
                    "title": state.context["approval_title"],
                    "summary": state.context["approval_summary"],
                },
                related_execution_id=state.execution_id,
            )
        return NodeExecutionResult(next_node_id=next_node, pause_execution=True, pause_reason="approval_pending")
