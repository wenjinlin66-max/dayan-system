from pydantic import BaseModel, Field


class ExecutionTrigger(BaseModel):
    type: str = "manual"
    event_id: str | None = None
    session_id: str | None = None
    message_id: str | None = None


class ExecutionOperator(BaseModel):
    user_id: str
    roles: list[str] = Field(default_factory=list)


class ExecutionStartRequest(BaseModel):
    workflow_id: str
    version: int | None = None
    mode: str = "released"
    trigger: ExecutionTrigger = Field(default_factory=ExecutionTrigger)
    dept_id: str | None = None
    operator: ExecutionOperator | None = None
    input: dict[str, object] = Field(default_factory=dict)


class ExecutionStatusResponse(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_version: int
    mode: str
    status: str
    current_node: str | None
    thread_id: str
    dept_id: str
    started_at: str | None = None
    updated_at: str | None = None
    final_output: dict[str, object] | None = None


class WorkflowExecutionHistoryItem(BaseModel):
    execution_id: str
    workflow_id: str
    workflow_name: str
    dept_id: str
    status: str
    execution_type: str
    task_summary: str
    target_summary: str
    result_status: str | None = None
    result_summary: str | None = None
    result_details: list[str] = Field(default_factory=list)
    started_at: str | None = None
    updated_at: str | None = None


class WorkflowExecutionHistoryResponse(BaseModel):
    workflow_id: str
    workflow_name: str
    items: list[WorkflowExecutionHistoryItem]


class MockEventInjectRequest(BaseModel):
    workflow_id: str
    version: int | None = None
    mode: str = "released"
    dept_id: str | None = None
    event_type: str = "mock.event"
    source: str = "mock_event_injector"
    event: dict[str, object] = Field(default_factory=dict)
    input_values: dict[str, object] = Field(default_factory=dict)
    knowledge_docs: list[dict[str, object]] = Field(default_factory=list)
