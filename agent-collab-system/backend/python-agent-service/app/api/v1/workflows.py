from fastapi import APIRouter, Depends

from app.core.deps import get_request_context
from app.core.security import RequestContext
from app.schemas.workflow import WorkflowCreateRequest, WorkflowResponse

router = APIRouter()


@router.post("", response_model=WorkflowResponse)
async def create_workflow(
    payload: WorkflowCreateRequest,
    context: RequestContext = Depends(get_request_context),
) -> WorkflowResponse:
    return WorkflowResponse(
        workflow_id="wf_placeholder",
        name=payload.name,
        mode="draft",
        owner_dept_id=context.dept_id,
    )


@router.get("/health")
async def workflow_health() -> dict[str, str]:
    return {"status": "ok", "module": "workflows"}
