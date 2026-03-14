import asyncio
import json
from time import monotonic
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_request_context
from app.core.security import RequestContext
from app.db.session import get_session_factory
from app.domain.approvals.repository import ApprovalRepository
from app.domain.executions.repository import ExecutionRepository
from app.domain.executions.service import ExecutionService
from app.domain.workflows.repository import WorkflowRepository
from app.schemas.execution import ExecutionStartRequest, ExecutionStatusResponse, MockEventInjectRequest, ExecutionTrigger, ExecutionOperator

router = APIRouter()


def build_service(session: AsyncSession) -> ExecutionService:
    return ExecutionService(ExecutionRepository(session), WorkflowRepository(session), approval_repository=ApprovalRepository(session))


@router.post("/start", response_model=ExecutionStatusResponse)
async def start_execution(
    payload: ExecutionStartRequest,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ExecutionStatusResponse:
    service = build_service(session)
    try:
        return await service.start(payload, dept_id=context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_404_NOT_FOUND if detail in {"WORKFLOW_VERSION_NOT_FOUND", "RELEASE_NOT_FOUND"} else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=detail) from exc


@router.post("/inject/mock-event", response_model=ExecutionStatusResponse)
async def mock_event_inject(
    payload: MockEventInjectRequest,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ExecutionStatusResponse:
    service = build_service(session)
    raw_event_id = payload.event.get("event_id")
    event_id: str = raw_event_id if isinstance(raw_event_id, str) and raw_event_id else f"evt_mock_{uuid4().hex[:10]}"
    start_payload = ExecutionStartRequest(
        workflow_id=payload.workflow_id,
        version=payload.version,
        mode=payload.mode,
        dept_id=payload.dept_id or context.dept_id,
        operator=ExecutionOperator(user_id=context.user_id, roles=context.roles),
        trigger=ExecutionTrigger(type="event", event_id=event_id),
        input={
            "message": f"Mock event injected: {payload.event_type}",
            "event": {
                "event_id": event_id,
                "event_type": payload.event_type,
                "source": payload.source,
                "dept_id": payload.dept_id or context.dept_id,
                "payload": payload.event,
            },
            "input_values": payload.input_values,
            "knowledge_docs": payload.knowledge_docs,
        },
    )
    try:
        return await service.start(start_payload, dept_id=context.dept_id, user_id=context.user_id)
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_404_NOT_FOUND if detail in {"WORKFLOW_VERSION_NOT_FOUND", "RELEASE_NOT_FOUND"} else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=detail) from exc


@router.get("/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution(
    execution_id: str,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ExecutionStatusResponse:
    service = build_service(session)
    try:
        return await service.get_status_for_dept(execution_id, dept_id=context.dept_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{execution_id}/stream")
async def stream_execution(
    execution_id: str,
    context: RequestContext = Depends(get_request_context),
) -> StreamingResponse:
    session_factory = get_session_factory()

    async def event_generator():
        deadline = monotonic() + 30
        while monotonic() < deadline:
            async with session_factory() as stream_session:
                service = build_service(stream_session)
                status_payload = await service.get_status_for_dept(execution_id, dept_id=context.dept_id)
            yield f"event: status\ndata: {json.dumps(status_payload.model_dump(), ensure_ascii=False)}\n\n"
            if status_payload.status in {"finished", "failed", "cancelled"}:
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
