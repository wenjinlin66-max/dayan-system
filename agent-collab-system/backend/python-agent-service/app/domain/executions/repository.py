from __future__ import annotations

from sqlalchemy import delete, select
from app.db.models.approval import ApprovalTask
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.execution import ExecutionCheckpoint, ExecutionRun


class ExecutionRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_run(self, run: ExecutionRun) -> ExecutionRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def create_checkpoint(self, checkpoint: ExecutionCheckpoint) -> ExecutionCheckpoint:
        self.session.add(checkpoint)
        await self.session.flush()
        return checkpoint

    async def get_run(self, execution_id: str) -> ExecutionRun | None:
        result = await self.session.execute(select(ExecutionRun).where(ExecutionRun.id == execution_id))
        return result.scalar_one_or_none()

    async def list_runs_by_workflow(self, workflow_id: str, *, dept_id: str | None = None, limit: int = 100) -> list[ExecutionRun]:
        stmt = select(ExecutionRun).where(ExecutionRun.workflow_id == workflow_id)
        if dept_id:
            stmt = stmt.where(ExecutionRun.dept_id == dept_id)
        stmt = stmt.order_by(ExecutionRun.started_at.desc().nullslast(), ExecutionRun.id.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_run(self, execution_id: str, **values: object) -> None:
        run = await self.get_run(execution_id)
        if run is None:
            return
        for key, value in values.items():
            setattr(run, key, value)
        await self.session.flush()

    async def delete_run(self, execution_id: str) -> bool:
        run = await self.get_run(execution_id)
        if run is None:
            return False
        _ = await self.session.execute(delete(ApprovalTask).where(ApprovalTask.execution_id == execution_id))
        _ = await self.session.execute(delete(ExecutionCheckpoint).where(ExecutionCheckpoint.execution_id == execution_id))
        await self.session.delete(run)
        await self.session.flush()
        return True
