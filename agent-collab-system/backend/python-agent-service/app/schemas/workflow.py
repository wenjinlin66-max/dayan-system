from pydantic import BaseModel, Field


class WorkflowCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)


class WorkflowResponse(BaseModel):
    workflow_id: str
    name: str
    mode: str
    owner_dept_id: str
