from __future__ import annotations

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.workflow import Workflow, WorkflowRegistry, WorkflowVersion


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_workflow(self, workflow: Workflow) -> Workflow:
        self.session.add(workflow)
        await self.session.flush()
        return workflow

    async def create_version(self, version: WorkflowVersion) -> WorkflowVersion:
        self.session.add(version)
        await self.session.flush()
        return version

    async def get_workflow(self, workflow_id: str) -> Workflow | None:
        result = await self.session.execute(select(Workflow).where(Workflow.id == workflow_id))
        return result.scalar_one_or_none()

    async def list_workflows(self) -> list[Workflow]:
        result = await self.session.execute(select(Workflow).order_by(Workflow.updated_at.desc()))
        return list(result.scalars().all())

    async def list_workflows_by_dept(self, dept_id: str) -> list[Workflow]:
        result = await self.session.execute(
            select(Workflow)
            .where(Workflow.owner_dept_id == dept_id, Workflow.status == "active")
            .order_by(Workflow.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_version(self, workflow_id: str, version: int) -> WorkflowVersion | None:
        result = await self.session.execute(
            select(WorkflowVersion).where(
                WorkflowVersion.workflow_id == workflow_id,
                WorkflowVersion.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_draft(self, workflow_id: str) -> WorkflowVersion | None:
        result = await self.session.execute(
            select(WorkflowVersion)
            .where(WorkflowVersion.workflow_id == workflow_id, WorkflowVersion.mode == "draft")
            .order_by(WorkflowVersion.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_current_release(self, workflow_id: str) -> WorkflowVersion | None:
        result = await self.session.execute(
            select(WorkflowVersion).where(
                WorkflowVersion.workflow_id == workflow_id,
                WorkflowVersion.is_current_release.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_versions(self, workflow_id: str) -> list[WorkflowVersion]:
        result = await self.session.execute(
            select(WorkflowVersion)
            .where(WorkflowVersion.workflow_id == workflow_id)
            .order_by(WorkflowVersion.version.desc())
        )
        return list(result.scalars().all())

    async def update_workflow(self, workflow_id: str, **values: object) -> None:
        await self.session.execute(update(Workflow).where(Workflow.id == workflow_id).values(**values))

    async def update_version(self, version_id: str, **values: object) -> None:
        await self.session.execute(update(WorkflowVersion).where(WorkflowVersion.id == version_id).values(**values))

    async def clear_current_release_flags(self, workflow_id: str) -> None:
        await self.session.execute(
            update(WorkflowVersion)
            .where(WorkflowVersion.workflow_id == workflow_id)
            .values(is_current_release=False)
        )

    async def upsert_registry_entry(self, entry: WorkflowRegistry) -> WorkflowRegistry:
        existing = await self.get_registry_entry(entry.workflow_id, entry.workflow_version)
        if existing is None:
            self.session.add(entry)
            await self.session.flush()
            return entry

        existing.dept_id = entry.dept_id
        existing.category = entry.category
        existing.title = entry.title
        existing.summary = entry.summary
        existing.synonyms = entry.synonyms
        existing.example_utterances = entry.example_utterances
        existing.allowed_roles = entry.allowed_roles
        existing.required_inputs = entry.required_inputs
        existing.input_schema = entry.input_schema
        existing.approval_policy = entry.approval_policy
        existing.risk_level = entry.risk_level
        existing.output_contract = entry.output_contract
        existing.status = entry.status
        await self.session.flush()
        return existing

    async def get_registry_entry(self, workflow_id: str, workflow_version: int) -> WorkflowRegistry | None:
        result = await self.session.execute(
            select(WorkflowRegistry).where(
                WorkflowRegistry.workflow_id == workflow_id,
                WorkflowRegistry.workflow_version == workflow_version,
            )
        )
        return result.scalar_one_or_none()

    async def get_current_registry_entry(self, workflow_id: str) -> WorkflowRegistry | None:
        result = await self.session.execute(
            select(WorkflowRegistry)
            .where(WorkflowRegistry.workflow_id == workflow_id, WorkflowRegistry.status == "active")
            .order_by(WorkflowRegistry.workflow_version.desc(), WorkflowRegistry.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_registry_entries(self, workflow_id: str) -> None:
        await self.session.execute(delete(WorkflowRegistry).where(WorkflowRegistry.workflow_id == workflow_id))

    async def delete_versions(self, workflow_id: str) -> None:
        await self.session.execute(delete(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow_id))

    async def delete_workflow_row(self, workflow_id: str) -> None:
        await self.session.execute(delete(Workflow).where(Workflow.id == workflow_id))
