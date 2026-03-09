from pydantic import BaseModel


class ApprovalResumeRequest(BaseModel):
    execution_id: str
    go_approval_id: str
    decision: str
    comment: str | None = None


class ApprovalResumeResponse(BaseModel):
    execution_id: str
    status: str
    next_node: str | None = None
