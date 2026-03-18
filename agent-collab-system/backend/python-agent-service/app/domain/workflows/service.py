from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import cast
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from app.db.models.workflow import Workflow, WorkflowRegistry, WorkflowVersion
from app.domain.workflows.compiler import WorkflowCompiler
from app.domain.workflows.repository import WorkflowRepository
from app.schemas.workflow import (
    WorkflowCompileRequest,
    WorkflowCreateRequest,
    WorkflowDraftUpdateRequest,
    WorkflowDialogTriggerConfig,
    WorkflowPublishRequest,
    WorkflowResponse,
    WorkflowTriggerType,
    WorkflowVersionListResponse,
    WorkflowVersionResponse,
)


class WorkflowService:
    repository: WorkflowRepository
    compiler: WorkflowCompiler

    def __init__(self, repository: WorkflowRepository, compiler: WorkflowCompiler | None = None) -> None:
        self.repository = repository
        self.compiler = compiler or WorkflowCompiler()

    async def create_workflow(self, payload: WorkflowCreateRequest, *, dept_id: str, user_id: str) -> WorkflowResponse:
        owner_dept_id = payload.owner_dept_id or dept_id
        workflow_id = f"wf_{uuid4().hex[:12]}"
        workflow = Workflow(
            id=workflow_id,
            code=payload.code,
            name=payload.name,
            owner_dept_id=owner_dept_id,
            visibility=payload.visibility,
            latest_draft_version=1,
            current_release_version=None,
            status="active",
            created_by=user_id,
            updated_by=user_id,
        )

        try:
            _ = await self.repository.create_workflow(workflow)

            draft = WorkflowVersion(
                id=f"wfv_{uuid4().hex[:12]}",
                workflow_id=workflow_id,
                version=1,
                mode="draft",
                ui_schema=payload.ui_schema,
                execution_dag=None,
                compile_status="pending",
                compile_errors=None,
                schema_version="2026-03",
                content_hash=None,
                release_note=None,
                is_current_release=False,
                created_by=user_id,
            )
            _ = await self.repository.create_version(draft)
            await self.repository.session.commit()
        except IntegrityError as exc:
            await self.repository.session.rollback()
            raise ValueError("WORKFLOW_CODE_ALREADY_EXISTS") from exc

        return self._to_workflow_response(workflow)

    async def update_draft(
        self,
        workflow_id: str,
        payload: WorkflowDraftUpdateRequest,
        *,
        dept_id: str,
        user_id: str,
    ) -> WorkflowVersionResponse:
        workflow = await self.repository.get_workflow(workflow_id)
        workflow = self._require_workflow_access(workflow, dept_id)

        draft = await self.repository.get_latest_draft(workflow_id)
        if draft is None:
            next_version = (workflow.latest_draft_version or workflow.current_release_version or 0) + 1
            draft = WorkflowVersion(
                id=f"wfv_{uuid4().hex[:12]}",
                workflow_id=workflow_id,
                version=next_version,
                mode="draft",
                ui_schema=payload.ui_schema,
                execution_dag=None,
                compile_status="pending",
                compile_errors=None,
                schema_version=payload.schema_version,
                content_hash=None,
                release_note=None,
                is_current_release=False,
                created_by=user_id,
            )
            _ = await self.repository.create_version(draft)
            await self.repository.update_workflow(
                workflow_id,
                latest_draft_version=next_version,
                updated_by=user_id,
                updated_at=datetime.now(timezone.utc),
                name=payload.name or workflow.name,
            )
        else:
            await self.repository.update_version(
                draft.id,
                ui_schema=payload.ui_schema,
                schema_version=payload.schema_version,
                compile_status="pending",
                compile_errors=None,
                execution_dag=None,
                content_hash=None,
            )
            if payload.name:
                await self.repository.update_workflow(
                    workflow_id,
                    name=payload.name,
                    updated_by=user_id,
                    updated_at=datetime.now(timezone.utc),
                )

        await self.repository.session.commit()
        latest = await self.repository.get_latest_draft(workflow_id)
        if latest is None:
            raise ValueError("DRAFT_NOT_FOUND")
        return self._to_version_response(latest)

    async def compile_workflow(self, workflow_id: str, payload: WorkflowCompileRequest, *, dept_id: str) -> WorkflowVersionResponse:
        workflow = await self.repository.get_workflow(workflow_id)
        _ = self._require_workflow_access(workflow, dept_id)
        draft = await self.repository.get_latest_draft(workflow_id)
        if draft is None:
            raise ValueError("DRAFT_NOT_FOUND")

        execution_dag, errors = self.compiler.compile(draft.ui_schema)
        compile_status = "failed" if errors else "success"
        content_hash = None if errors else hashlib.sha256(
            json.dumps(execution_dag, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        await self.repository.update_version(
            draft.id,
            execution_dag=execution_dag,
            compile_status=compile_status,
            compile_errors=errors or None,
            schema_version=payload.schema_version,
            content_hash=content_hash,
        )
        await self.repository.session.commit()
        compiled = await self.repository.get_version(workflow_id, draft.version)
        if compiled is None:
            raise ValueError("WORKFLOW_VERSION_NOT_FOUND")
        return self._to_version_response(compiled)

    async def publish_workflow(
        self,
        workflow_id: str,
        payload: WorkflowPublishRequest,
        *,
        dept_id: str,
    ) -> WorkflowVersionResponse:
        draft = await self.repository.get_latest_draft(workflow_id)
        workflow = await self.repository.get_workflow(workflow_id)
        workflow = self._require_workflow_access(workflow, dept_id)
        if draft is None:
            raise ValueError("DRAFT_NOT_FOUND")
        if draft.compile_status != "success" or draft.execution_dag is None:
            raise ValueError("WORKFLOW_NOT_COMPILED")

        dialog_trigger_config = self._resolve_dialog_trigger_config(draft.ui_schema, payload)

        await self.repository.deactivate_registry_entries(workflow_id)
        await self.repository.clear_current_release_flags(workflow_id)
        await self.repository.update_version(
            draft.id,
            mode="released",
            is_current_release=True,
            released_at=datetime.now(timezone.utc),
            release_note=payload.release_note,
        )
        await self.repository.update_workflow(
            workflow_id,
            current_release_version=draft.version,
            updated_at=datetime.now(timezone.utc),
        )

        registry_entry = WorkflowRegistry(
            id=f"wfr_{uuid4().hex[:12]}",
            workflow_id=workflow_id,
            workflow_version=draft.version,
            dept_id=dept_id,
            category=payload.category,
            title=workflow.name,
            summary=dialog_trigger_config.summary or payload.summary or f"{workflow.name} workflow",
            synonyms=dialog_trigger_config.synonyms or None,
            example_utterances=dialog_trigger_config.example_utterances or None,
            allowed_roles=dialog_trigger_config.allowed_roles or None,
            required_inputs=dialog_trigger_config.required_inputs or None,
            input_schema=dialog_trigger_config.input_schema,
            approval_policy="risk_based",
            risk_level="medium",
            output_contract=None,
            status="active",
        )
        _ = await self.repository.upsert_registry_entry(registry_entry)
        await self.repository.session.commit()

        release = await self.repository.get_current_release(workflow_id)
        if release is None:
            raise ValueError("RELEASE_NOT_FOUND")
        return self._to_version_response(release)

    async def get_current_release(self, workflow_id: str, *, dept_id: str) -> WorkflowVersionResponse:
        workflow = await self.repository.get_workflow(workflow_id)
        _ = self._require_workflow_access(workflow, dept_id)
        release = await self.repository.get_current_release(workflow_id)
        if release is None:
            raise ValueError("RELEASE_NOT_FOUND")
        return self._to_version_response(release)

    async def get_latest_draft(self, workflow_id: str, *, dept_id: str) -> WorkflowVersionResponse:
        workflow = await self.repository.get_workflow(workflow_id)
        _ = self._require_workflow_access(workflow, dept_id)
        draft = await self.repository.get_latest_draft(workflow_id)
        if draft is None:
            raise ValueError("DRAFT_NOT_FOUND")
        return self._to_version_response(draft)

    async def list_versions(self, workflow_id: str, *, dept_id: str) -> WorkflowVersionListResponse:
        workflow = await self.repository.get_workflow(workflow_id)
        _ = self._require_workflow_access(workflow, dept_id)
        versions = await self.repository.list_versions(workflow_id)
        return WorkflowVersionListResponse(
            workflow_id=workflow_id,
            versions=[self._to_version_response(version) for version in versions],
        )

    async def list_workflows(self, *, dept_id: str | None, include_all: bool = False) -> list[WorkflowResponse]:
        if include_all:
            workflows = await self.repository.list_workflows()
        else:
            workflows = await self.repository.list_workflows_by_dept(dept_id or "")
        responses: list[WorkflowResponse] = []
        for workflow in workflows:
            registry = await self.repository.get_current_registry_entry(workflow.id)
            responses.append(self._to_workflow_response(workflow, registry))
        return responses

    async def delete_workflow(self, workflow_id: str, *, dept_id: str) -> None:
        workflow = await self.repository.get_workflow(workflow_id)
        _ = self._require_workflow_access(workflow, dept_id)
        await self.repository.delete_registry_entries(workflow_id)
        await self.repository.delete_versions(workflow_id)
        await self.repository.delete_workflow_row(workflow_id)
        await self.repository.session.commit()

    @staticmethod
    def _require_workflow_access(workflow: Workflow | None, dept_id: str) -> Workflow:
        if workflow is None or workflow.owner_dept_id != dept_id or workflow.status != "active":
            raise ValueError("WORKFLOW_NOT_FOUND")
        return workflow

    @staticmethod
    def _to_workflow_response(workflow: Workflow, registry: WorkflowRegistry | None = None) -> WorkflowResponse:
        trigger_type = WorkflowService._normalize_trigger_type(registry.category if registry else None)
        return WorkflowResponse(
            workflow_id=workflow.id,
            code=workflow.code,
            name=workflow.name,
            mode="released" if workflow.current_release_version else "draft",
            owner_dept_id=workflow.owner_dept_id,
            workflow_category=trigger_type,
            workflow_trigger_type=trigger_type,
            latest_draft_version=workflow.latest_draft_version,
            current_release_version=workflow.current_release_version,
        )

    @staticmethod
    def _normalize_trigger_type(value: str | None) -> WorkflowTriggerType:
        if value in {"dialog_trigger", "event_trigger", "schedule_trigger"}:
            return cast(WorkflowTriggerType, value)
        return "dialog_trigger"

    @staticmethod
    def _resolve_dialog_trigger_config(ui_schema: dict[str, object], payload: WorkflowPublishRequest) -> WorkflowDialogTriggerConfig:
        if payload.dialog_trigger_config is not None:
            return payload.dialog_trigger_config

        raw_nodes = ui_schema.get("nodes")
        if isinstance(raw_nodes, list):
            for raw_node in raw_nodes:
                if not isinstance(raw_node, dict):
                    continue
                if raw_node.get("type") != "dialog_agent":
                    continue
                raw_config = raw_node.get("config")
                if not isinstance(raw_config, dict):
                    continue
                return WorkflowDialogTriggerConfig(
                    summary=str(raw_config.get("triggerSummary") or payload.summary or ""),
                    synonyms=WorkflowService._to_string_list(raw_config.get("triggerSynonyms")),
                    example_utterances=WorkflowService._to_string_list(raw_config.get("triggerExampleUtterances")),
                    allowed_roles=WorkflowService._to_string_list(raw_config.get("triggerAllowedRoles")),
                    required_inputs=WorkflowService._to_string_list(raw_config.get("triggerRequiredInputs")),
                    input_schema=cast(dict[str, object] | None, raw_config.get("triggerInputSchema") if isinstance(raw_config.get("triggerInputSchema"), dict) else None),
                )

        return WorkflowDialogTriggerConfig(summary=payload.summary)

    @staticmethod
    def _to_string_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]

    @staticmethod
    def _to_version_response(version: WorkflowVersion) -> WorkflowVersionResponse:
        return WorkflowVersionResponse(
            workflow_id=version.workflow_id,
            version=version.version,
            mode=version.mode,
            compile_status=version.compile_status,
            ui_schema=version.ui_schema,
            execution_dag=version.execution_dag,
            compile_errors=version.compile_errors,
            release_note=version.release_note,
            is_current_release=version.is_current_release,
        )
