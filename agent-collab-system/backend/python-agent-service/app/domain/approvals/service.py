from __future__ import annotations

from app.domain.approvals.repository import ApprovalRepository
from app.domain.chat.repository import ChatRepository
from app.domain.executions.service import ExecutionService
from app.schemas.approval import ApprovalResumeRequest, ApprovalResumeResponse, ApprovalTaskListResponse, ApprovalTaskResponse


class ApprovalService:
    repository: ApprovalRepository
    execution_service: ExecutionService

    def __init__(self, repository: ApprovalRepository, execution_service: ExecutionService) -> None:
        self.repository = repository
        self.execution_service = execution_service

    async def list_pending(self, dept_id: str | None = None) -> ApprovalTaskListResponse:
        tasks = await self.repository.list_pending_tasks(dept_id)
        items: list[ApprovalTaskResponse] = []
        for task in tasks:
            run = await self.execution_service.execution_repository.get_run(task.execution_id)
            context_snapshot = run.context_snapshot if run and isinstance(run.context_snapshot, dict) else {}
            items.append(
                ApprovalTaskResponse(
                    approval_task_id=task.id,
                    go_approval_id=task.go_approval_id,
                    execution_id=task.execution_id,
                    workflow_id=run.workflow_id if run else "",
                    dept_id=(run.dept_id if run else (dept_id or "")),
                    current_node=str(context_snapshot.get("approval_current_node")) if context_snapshot.get("approval_current_node") is not None else None,
                    title=str(context_snapshot.get("approval_title") or "审批任务"),
                    summary=str(context_snapshot.get("approval_summary") or "等待审批后继续执行。"),
                    status=task.status,
                    decision=task.status if task.status != "pending" else None,
                    comment=None,
                )
            )
        return ApprovalTaskListResponse(items=items)

    async def resume(self, payload: ApprovalResumeRequest) -> ApprovalResumeResponse:
        task = await self.repository.get_task_by_go_id(payload.go_approval_id)
        if task is None or task.execution_id != payload.execution_id:
            raise ValueError("APPROVAL_TASK_NOT_FOUND")
        run = await self.execution_service.execution_repository.get_run(task.execution_id)
        context_snapshot = run.context_snapshot if run and isinstance(run.context_snapshot, dict) else {}
        raw_next_node = context_snapshot.get("approval_next_node")
        next_node: str | None = raw_next_node if isinstance(raw_next_node, str) else None
        decision = "approved" if payload.decision in {"approved", "approve", "同意"} else "rejected"
        _ = await self.repository.update_task(task.id, status=decision)
        execution_status = await self.execution_service.resume_from_approval(
            payload.execution_id,
            next_node=next_node,
            decision=decision,
            comment=payload.comment,
        )
        session_id = self.execution_service._extract_session_id(run) if run else None
        if session_id and run:
            chat_repository = ChatRepository(self.repository.session)
            await chat_repository.append_assistant_message(
                session_id=session_id,
                dept_id=run.dept_id,
                content=f"审批结果已回写到当前部门对话框：{('已同意' if decision == 'approved' else '已驳回')}《{context_snapshot.get('approval_title') or '审批任务'}》。",
                payload={
                    "message_kind": "approval_result",
                    "execution_id": payload.execution_id,
                    "go_approval_id": payload.go_approval_id,
                    "decision": decision,
                    "comment": payload.comment,
                    "next_node": next_node,
                },
                related_execution_id=payload.execution_id,
            )
        await self.repository.session.commit()
        return ApprovalResumeResponse(
            execution_id=payload.execution_id,
            status=execution_status.status,
            next_node=next_node,
        )
