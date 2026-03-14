from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session, get_request_context
from app.core.security import RequestContext
from app.domain.approvals.repository import ApprovalRepository
from app.domain.approvals.service import ApprovalService
from app.domain.executions.repository import ExecutionRepository
from app.domain.executions.service import ExecutionService
from app.domain.workflows.repository import WorkflowRepository
from app.schemas.approval import ApprovalResumeRequest, ApprovalResumeResponse, ApprovalTaskListResponse

router = APIRouter()


def build_service(session: AsyncSession) -> ApprovalService:
    execution_service = ExecutionService(ExecutionRepository(session), WorkflowRepository(session), approval_repository=ApprovalRepository(session))
    return ApprovalService(ApprovalRepository(session), execution_service)


@router.get("", response_model=ApprovalTaskListResponse)
async def list_approval_tasks(
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalTaskListResponse:
    service = build_service(session)
    return await service.list_pending(context.dept_id)


@router.post("/resume", response_model=ApprovalResumeResponse)
async def resume_approval(
    payload: ApprovalResumeRequest,
    context: RequestContext = Depends(get_request_context),
    session: AsyncSession = Depends(get_db_session),
) -> ApprovalResumeResponse:
    service = build_service(session)
    try:
        run = await service.execution_service.execution_repository.get_run(payload.execution_id)
        if run is None or run.dept_id != context.dept_id:
            raise ValueError("APPROVAL_TASK_NOT_FOUND")
        return await service.resume(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
