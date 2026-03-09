from dataclasses import dataclass


@dataclass(slots=True)
class ApprovalTaskSummary:
    approval_id: str
    execution_id: str
    status: str
