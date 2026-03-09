from dataclasses import dataclass


@dataclass(slots=True)
class ExecutionSummary:
    execution_id: str
    workflow_id: str
    status: str
