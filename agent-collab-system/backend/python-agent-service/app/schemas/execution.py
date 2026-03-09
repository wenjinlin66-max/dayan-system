from pydantic import BaseModel


class ExecutionStartRequest(BaseModel):
    workflow_id: str
    version: int = 1
    mode: str = "released"
    input: dict[str, object] = {}


class ExecutionStatusResponse(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_version: int
    mode: str
    status: str
    current_node: str | None
    thread_id: str
    dept_id: str
