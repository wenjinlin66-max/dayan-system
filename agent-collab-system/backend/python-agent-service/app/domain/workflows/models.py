from dataclasses import dataclass


@dataclass(slots=True)
class WorkflowSummary:
    workflow_id: str
    code: str
    name: str
    mode: str
