from fastapi import APIRouter, Depends

from app.core.deps import get_request_context
from app.core.security import RequestContext
from app.schemas.execution import ExecutionStartRequest, ExecutionStatusResponse

router = APIRouter()


@router.post("/start", response_model=ExecutionStatusResponse)
async def start_execution(
    payload: ExecutionStartRequest,
    context: RequestContext = Depends(get_request_context),
) -> ExecutionStatusResponse:
    return ExecutionStatusResponse(
        execution_id="exec_placeholder",
        workflow_id=payload.workflow_id,
        workflow_version=payload.version,
        mode=payload.mode,
        status="pending",
        current_node=None,
        thread_id="exec_placeholder",
        dept_id=context.dept_id,
    )


@router.get("/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution(execution_id: str) -> ExecutionStatusResponse:
    return ExecutionStatusResponse(
        execution_id=execution_id,
        workflow_id="wf_placeholder",
        workflow_version=1,
        mode="released",
        status="pending",
        current_node=None,
        thread_id=execution_id,
        dept_id="default",
    )
