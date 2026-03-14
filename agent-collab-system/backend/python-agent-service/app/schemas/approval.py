from pydantic import BaseModel


class ApprovalTaskResponse(BaseModel):
    approval_task_id: str
    go_approval_id: str
    execution_id: str
    workflow_id: str
    dept_id: str
    current_node: str | None = None
    title: str
    summary: str
    status: str
    decision: str | None = None
    comment: str | None = None


class ApprovalTaskListResponse(BaseModel):
    items: list[ApprovalTaskResponse]


class ApprovalResumeRequest(BaseModel):
    execution_id: str
    go_approval_id: str
    decision: str
    comment: str | None = None


class ApprovalResumeResponse(BaseModel):
    execution_id: str
    status: str
    next_node: str | None = None
