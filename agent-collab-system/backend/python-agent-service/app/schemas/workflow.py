from typing import Literal

from pydantic import BaseModel, Field


WorkflowTriggerType = Literal["dialog_trigger", "event_trigger", "schedule_trigger"]


class WorkflowDialogTriggerConfig(BaseModel):
    summary: str = ""
    synonyms: list[str] = Field(default_factory=list)
    example_utterances: list[str] = Field(default_factory=list)
    allowed_roles: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    input_schema: dict[str, object] | None = None


class WorkflowCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    code: str = Field(min_length=1)
    visibility: str = "private"
    owner_dept_id: str | None = None
    ui_schema: dict[str, object] = Field(default_factory=dict)


class WorkflowDraftUpdateRequest(BaseModel):
    name: str | None = None
    ui_schema: dict[str, object] = Field(default_factory=dict)
    schema_version: str = "2026-03"


class WorkflowCompileRequest(BaseModel):
    schema_version: str = "2026-03"


class WorkflowPublishRequest(BaseModel):
    release_note: str | None = None
    category: WorkflowTriggerType = "dialog_trigger"
    summary: str = ""
    dialog_trigger_config: WorkflowDialogTriggerConfig | None = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    code: str
    name: str
    mode: str
    owner_dept_id: str
    workflow_category: WorkflowTriggerType = "dialog_trigger"
    workflow_trigger_type: WorkflowTriggerType = "dialog_trigger"
    latest_draft_version: int | None = None
    current_release_version: int | None = None


class WorkflowVersionResponse(BaseModel):
    workflow_id: str
    version: int
    mode: str
    compile_status: str
    ui_schema: dict[str, object]
    execution_dag: dict[str, object] | None = None
    compile_errors: list[object] | None = None
    release_note: str | None = None
    is_current_release: bool = False


class WorkflowVersionListResponse(BaseModel):
    workflow_id: str
    versions: list[WorkflowVersionResponse]
