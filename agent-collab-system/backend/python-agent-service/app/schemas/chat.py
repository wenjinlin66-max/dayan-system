from pydantic import BaseModel, Field


class ChatSessionCreateRequest(BaseModel):
    title: str | None = None


class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    dept_id: str
    last_message_at: str | None = None


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1)
    message_type: str = "text"


class ChatMessageResponse(BaseModel):
    message_id: str
    session_id: str
    dept_id: str | None = None
    created_at: str | None = None
    role: str
    content: str | None = None
    route_type: str | None = None
    related_execution_id: str | None = None
    payload: dict[str, object] | None = None


class ChatMessageListResponse(BaseModel):
    session_id: str
    items: list[ChatMessageResponse]


class WorkflowCatalogItem(BaseModel):
    workflow_id: str
    title: str
    category: str
    summary: str
    dept_id: str
    confidence: float | None = None
    required_inputs: list[str] = Field(default_factory=list)
    input_schema: dict[str, object] | None = None


class WorkflowCatalogResponse(BaseModel):
    items: list[WorkflowCatalogItem]


class ChatRouteRequest(BaseModel):
    session_id: str | None = None
    content: str = Field(min_length=1)


class ChatRouteResponse(BaseModel):
    route_type: str
    needs_confirmation: bool = False
    candidate_workflows: list[WorkflowCatalogItem] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    execution_id: str | None = None
    reply: str | None = None


class ChatWorkflowStartRequest(BaseModel):
    source: str = "catalog"
    note: str | None = None
    source_message_id: str | None = None
    input_values: dict[str, object] | None = None
