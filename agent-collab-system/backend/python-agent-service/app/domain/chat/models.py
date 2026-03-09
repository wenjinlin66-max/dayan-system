from dataclasses import dataclass


@dataclass(slots=True)
class ChatSessionSummary:
    session_id: str
    title: str
