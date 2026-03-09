from fastapi import APIRouter

from app.schemas.approval import ApprovalResumeRequest, ApprovalResumeResponse

router = APIRouter()


@router.post("/resume", response_model=ApprovalResumeResponse)
async def resume_approval(payload: ApprovalResumeRequest) -> ApprovalResumeResponse:
    return ApprovalResumeResponse(
        execution_id=payload.execution_id,
        status="running",
        next_node="next_placeholder",
    )
