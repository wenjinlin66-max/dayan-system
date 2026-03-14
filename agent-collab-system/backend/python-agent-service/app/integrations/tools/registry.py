from __future__ import annotations

from app.core.config import settings
from app.integrations.go_client.records import GoRecordsClient
from app.integrations.tools.executors.department_table import DepartmentTableExecutor, MockRecordsGateway
from app.runtime.handlers.execution import DepartmentTableWriter


class ToolRegistry:
    department_table_writer: DepartmentTableWriter

    def __init__(self, department_table_writer: DepartmentTableWriter) -> None:
        self.department_table_writer = department_table_writer

    @classmethod
    def build_default(cls) -> ToolRegistry:
        client = GoRecordsClient(settings.go_records_base_url, settings.go_records_timeout_ms) if settings.go_records_base_url else None
        writer = DepartmentTableExecutor(
            route_map=settings.department_table_route_map,
            tenant_id=settings.runtime_default_tenant_id,
            client=client,
            mock_gateway=MockRecordsGateway(),
            enable_mock_fallback=settings.enable_mock_records_gateway,
        )
        return cls(writer)

    def get_department_table_writer(self) -> DepartmentTableWriter:
        return self.department_table_writer
