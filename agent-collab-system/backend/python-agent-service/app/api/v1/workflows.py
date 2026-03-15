from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_request_context
from app.core.security import RequestContext
from app.domain.workflows.compiler import WorkflowCompiler
from app.domain.workflows.sensor_metadata import SensorMetadataService
from app.domain.workflows.repository import WorkflowRepository
from app.domain.workflows.service import WorkflowService
from app.schemas.sensor_metadata import SensorMetadataResponse
from app.schemas.workflow import (
    WorkflowCompileRequest,
    WorkflowCreateRequest,
    WorkflowDraftUpdateRequest,
    WorkflowPublishRequest,
    WorkflowResponse,
    WorkflowVersionListResponse,
    WorkflowVersionResponse,
)

router = APIRouter()


def build_service(session: AsyncSession) -> WorkflowService:
    return WorkflowService(WorkflowRepository(session), WorkflowCompiler())


@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreateRequest,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowResponse:
    service = build_service(session)
    try:
        return await service.create_workflow(payload, dept_id=context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        code = status.HTTP_409_CONFLICT if str(exc) == "WORKFLOW_CODE_ALREADY_EXISTS" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    dept_id: str | None = None,
    include_all: bool = False,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> list[WorkflowResponse]:
    service = build_service(session)
    return await service.list_workflows(dept_id=dept_id or context.dept_id, include_all=include_all)


@router.get("/sensor-metadata", response_model=SensorMetadataResponse)
async def get_sensor_metadata(session: AsyncSession = Depends(get_db_session)) -> SensorMetadataResponse:
    return await SensorMetadataService().get_metadata(session)


@router.put("/{workflow_id}/draft", response_model=WorkflowVersionResponse)
async def update_workflow_draft(
    workflow_id: str,
    payload: WorkflowDraftUpdateRequest,
    dept_id: str | None = None,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowVersionResponse:
    service = build_service(session)
    try:
        return await service.update_draft(workflow_id, payload, dept_id=dept_id or context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{workflow_id}/compile", response_model=WorkflowVersionResponse)
async def compile_workflow(
    workflow_id: str,
    payload: WorkflowCompileRequest,
    dept_id: str | None = None,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowVersionResponse:
    service = build_service(session)
    try:
        return await service.compile_workflow(workflow_id, payload, dept_id=dept_id or context.dept_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{workflow_id}/publish", response_model=WorkflowVersionResponse)
async def publish_workflow(
    workflow_id: str,
    payload: WorkflowPublishRequest,
    dept_id: str | None = None,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowVersionResponse:
    service = build_service(session)
    try:
        return await service.publish_workflow(workflow_id, payload, dept_id=dept_id or context.dept_id)
    except ValueError as exc:
        code = status.HTTP_400_BAD_REQUEST if str(exc) == "WORKFLOW_NOT_COMPILED" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.get("/{workflow_id}/releases/current", response_model=WorkflowVersionResponse)
async def get_current_release(
    workflow_id: str,
    dept_id: str | None = None,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowVersionResponse:
    service = build_service(session)
    try:
        return await service.get_current_release(workflow_id, dept_id=dept_id or context.dept_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{workflow_id}/draft", response_model=WorkflowVersionResponse)
async def get_latest_draft(
    workflow_id: str,
    dept_id: str | None = None,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowVersionResponse:
    service = build_service(session)
    try:
        return await service.get_latest_draft(workflow_id, dept_id=dept_id or context.dept_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{workflow_id}/versions", response_model=WorkflowVersionListResponse)
async def list_workflow_versions(
    workflow_id: str,
    dept_id: str | None = None,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> WorkflowVersionListResponse:
    service = build_service(session)
    return await service.list_versions(workflow_id, dept_id=dept_id or context.dept_id)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    dept_id: str | None = None,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = build_service(session)
    try:
        await service.delete_workflow(workflow_id, dept_id=dept_id or context.dept_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/health")
async def workflow_health() -> dict[str, str]:
    return {"status": "ok", "module": "workflows"}
