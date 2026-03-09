class ExecutionService:
    """Placeholder execution service."""

    async def start(self, workflow_id: str) -> dict[str, str]:
        return {"execution_id": "exec_placeholder", "workflow_id": workflow_id, "status": "pending"}
