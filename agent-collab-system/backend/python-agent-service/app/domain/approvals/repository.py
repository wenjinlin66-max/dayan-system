from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.approval import ApprovalTask
from app.db.models.execution import ExecutionRun


class ApprovalRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_task(self, task: ApprovalTask) -> ApprovalTask:
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_task_by_go_id(self, go_approval_id: str) -> ApprovalTask | None:
        result = await self.session.execute(select(ApprovalTask).where(ApprovalTask.go_approval_id == go_approval_id))
        return result.scalar_one_or_none()

    async def list_pending_tasks(self, dept_id: str | None = None) -> list[ApprovalTask]:
        stmt = select(ApprovalTask).where(ApprovalTask.status == "pending")
        if dept_id:
            stmt = stmt.join(ExecutionRun, ExecutionRun.id == ApprovalTask.execution_id).where(ExecutionRun.dept_id == dept_id)
        result = await self.session.execute(stmt.order_by(ApprovalTask.execution_id.desc()))
        return list(result.scalars().all())

    async def update_task(self, task_id: str, **values: object) -> ApprovalTask | None:
        task = await self.get_task(task_id)
        if task is None:
            return None
        for key, value in values.items():
            setattr(task, key, value)
        await self.session.flush()
        return task

    async def get_task(self, task_id: str) -> ApprovalTask | None:
        result = await self.session.execute(select(ApprovalTask).where(ApprovalTask.id == task_id))
        return result.scalar_one_or_none()
