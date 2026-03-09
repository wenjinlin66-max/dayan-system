class NodeDispatcher:
    """Routes node types to runtime handlers."""

    def __init__(self, handlers: dict[str, object] | None = None) -> None:
        self.handlers = handlers or {}

    def get_handler(self, node_type: str) -> object | None:
        return self.handlers.get(node_type)
