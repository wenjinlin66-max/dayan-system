class WorkflowCompiler:
    """Placeholder compiler from ui_schema to execution_dag."""

    def compile(self, ui_schema: dict[str, object]) -> dict[str, object]:
        return {"entrypoint": ui_schema.get("entrypoint", "start"), "nodes": [], "edges": []}
