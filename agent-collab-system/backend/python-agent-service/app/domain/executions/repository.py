from __future__ import annotations

from sqlalchemy import select
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

    async def update_run(self, execution_id: str, **values: object) -> None:
        run = await self.get_run(execution_id)
        if run is None:
            return
        for key, value in values.items():
            setattr(run, key, value)
        await self.session.flush()
