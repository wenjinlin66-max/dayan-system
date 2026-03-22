from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import logging
from typing import cast
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.approvals.repository import ApprovalRepository
from app.domain.executions.repository import ExecutionRepository
from app.domain.executions.service import ExecutionService
from app.domain.workflows.repository import WorkflowRepository
from app.mock_records.db.models import (
    CustomerOrderRecord,
    CustomerSupplyRequestRecord,
    ManufacturingRequestRecord,
    PartsDemandRecord,
    ProductBomRecord,
    ProductMasterRecord,
    PurchaseRequestRecord,
    SensorChangeLogRecord,
)
from app.mock_records.repository.records_repository import MockRecordsRepository
from app.mock_records.schemas.records import (
    MockRecordMutationResponse,
    MockRecordsRecentEventItem,
    MockRecordsRecentEventsResponse,
    MockRecordsRowListResponse,
    MockRecordsSourceItem,
    MockRecordsSourcesResponse,
    MockRecordsTableItem,
    MockRecordsTablesResponse,
    MockRecordsTableSchemaField,
    MockRecordsTableSchemaResponse,
)
from app.schemas.execution import ExecutionOperator, ExecutionStartRequest, ExecutionTrigger

logger = logging.getLogger(__name__)

RecordModel = (
    ProductMasterRecord
    | ProductBomRecord
    | CustomerOrderRecord
    | PartsDemandRecord
    | PurchaseRequestRecord
    | ManufacturingRequestRecord
    | CustomerSupplyRequestRecord
)

DERIVED_TABLE_NAMES = (
    "parts_demand",
    "purchase_request",
    "manufacturing_request",
    "customer_supply_request",
)

DOWNSTREAM_REQUEST_TABLE_NAMES = (
    "purchase_request",
    "manufacturing_request",
    "customer_supply_request",
)

PRODUCT_BOM_SOURCE_REF_OPTIONS: dict[str, tuple[str, ...]] = {
    "purchase": ("供应商采购", "现货采购", "委外采购"),
    "manufacture": ("车间生产", "自制加工", "委托生产"),
    "customer": ("客户提供", "客户寄送", "客户指定供料"),
}

PRODUCT_BOM_SOURCE_REF_ALIASES: dict[str, str] = {
    "采购": "供应商采购",
    "生产": "车间生产",
    "制造": "车间生产",
    "客户提供": "客户提供",
    "客供": "客户提供",
}


@dataclass(slots=True)
class TableConfig:
    table_name: str
    label: str
    description: str
    source_system: str
    model: type[RecordModel]
    fields: list[MockRecordsTableSchemaField]
    visible_in_workbench: bool = True


TABLE_CONFIGS = {
    "product_master": TableConfig(
        table_name="product_master",
        label="产品主表",
        description="产品基础资料：编码、名称、版本与标准售价。",
        source_system="dayan_mock_records",
        model=ProductMasterRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="product_code", label="产品编码", field_type="string"),
            MockRecordsTableSchemaField(name="product_name", label="产品名称", field_type="string"),
            MockRecordsTableSchemaField(name="product_version", label="版本", field_type="string"),
            MockRecordsTableSchemaField(name="category", label="产品类别", field_type="string"),
            MockRecordsTableSchemaField(name="unit_price", label="标准售价", field_type="number"),
            MockRecordsTableSchemaField(name="customer_notes", label="客户说明", field_type="string"),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
    "product_bom": TableConfig(
        table_name="product_bom",
        label="产品 BOM",
        description="定义每个产品由哪些零件组成、每件产品消耗多少、零件来源是什么。",
        source_system="dayan_mock_records",
        model=ProductBomRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="product_code", label="产品编码", field_type="string"),
            MockRecordsTableSchemaField(name="part_code", label="零件编码", field_type="string"),
            MockRecordsTableSchemaField(name="part_name", label="零件名称", field_type="string"),
            MockRecordsTableSchemaField(name="qty_per_unit", label="单件用量", field_type="number"),
            MockRecordsTableSchemaField(name="source_type", label="来源类型", field_type="string"),
            MockRecordsTableSchemaField(name="unit_cost", label="单件成本", field_type="number"),
            MockRecordsTableSchemaField(name="source_ref", label="来源说明", field_type="string"),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
    "customer_order": TableConfig(
        table_name="customer_order",
        label="客户订单",
        description="输入客户订单后，系统据此计算零件需求并下发分表。",
        source_system="dayan_mock_records",
        model=CustomerOrderRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="order_no", label="订单编号", field_type="string"),
            MockRecordsTableSchemaField(name="customer_name", label="客户名称", field_type="string"),
            MockRecordsTableSchemaField(name="product_code", label="产品编码", field_type="string"),
            MockRecordsTableSchemaField(name="product_name", label="产品名称", field_type="string"),
            MockRecordsTableSchemaField(name="ordered_qty", label="订单数量", field_type="number"),
            MockRecordsTableSchemaField(name="unit_price", label="成交单价", field_type="number"),
            MockRecordsTableSchemaField(name="total_amount", label="订单金额", field_type="number"),
            MockRecordsTableSchemaField(name="order_status", label="订单状态", field_type="string"),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
    "parts_demand": TableConfig(
        table_name="parts_demand",
        label="零件需求表",
        description="按订单展开后的零件总需求，可作为感知型工作流输入。",
        source_system="dayan_mock_records",
        model=PartsDemandRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="order_no", label="订单编号", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="customer_name", label="客户名称", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="product_code", label="产品编码", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="product_name", label="产品名称", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="part_code", label="零件编码", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="part_name", label="零件名称", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="source_type", label="来源类型", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="required_qty", label="总需求数", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="purchase_qty", label="采购需求数", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="manufacture_qty", label="生产需求数", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="customer_qty", label="客户提供数", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="unit_cost", label="单件成本", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="total_cost", label="总成本", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
    "purchase_request": TableConfig(
        table_name="purchase_request",
        label="销售/采购部表单",
        description="来源为 purchase 的零件会写入这里，作为后续采购下发输入。",
        source_system="dayan_mock_records",
        model=PurchaseRequestRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="order_no", label="订单编号", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="product_code", label="产品编码", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="part_code", label="零件编码", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="part_name", label="零件名称", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="request_qty", label="申请数量", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="supplier_hint", label="采购说明", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="estimated_cost", label="预计成本", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="request_status", label="表单状态", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
    "manufacturing_request": TableConfig(
        table_name="manufacturing_request",
        label="生产部表单",
        description="来源为 manufacture 的零件会写入这里，作为生产下发表单。",
        source_system="dayan_mock_records",
        model=ManufacturingRequestRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="order_no", label="订单编号", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="product_code", label="产品编码", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="part_code", label="零件编码", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="part_name", label="零件名称", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="request_qty", label="生产数量", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="workshop_id", label="生产单元", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="estimated_cost", label="预计成本", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="request_status", label="表单状态", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
    "customer_supply_request": TableConfig(
        table_name="customer_supply_request",
        label="客户配合表单",
        description="来源为 customer 的零件会写入这里，作为客户提供物料的协同清单。",
        source_system="dayan_mock_records",
        model=CustomerSupplyRequestRecord,
        fields=[
            MockRecordsTableSchemaField(name="id", label="记录ID", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="order_no", label="订单编号", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="customer_name", label="客户名称", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="product_code", label="产品编码", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="part_code", label="零件编码", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="part_name", label="零件名称", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="request_qty", label="客户提供数", field_type="number", editable=False),
            MockRecordsTableSchemaField(name="handoff_note", label="协同说明", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="request_status", label="表单状态", field_type="string", editable=False),
            MockRecordsTableSchemaField(name="updated_at", label="更新时间", field_type="datetime", editable=False),
        ],
    ),
}


class MockRecordsService:
    repository: MockRecordsRepository
    main_session: AsyncSession
    workflow_repository: WorkflowRepository
    execution_service: ExecutionService

    def __init__(self, mock_session: AsyncSession, main_session: AsyncSession) -> None:
        self.repository = MockRecordsRepository(mock_session)
        self.main_session = main_session
        self.workflow_repository = WorkflowRepository(main_session)
        self.execution_service = ExecutionService(
            execution_repository=ExecutionRepository(main_session),
            workflow_repository=self.workflow_repository,
            approval_repository=ApprovalRepository(main_session),
        )

    def list_sources(self) -> MockRecordsSourcesResponse:
        return MockRecordsSourcesResponse(sources=[MockRecordsSourceItem(source_system="dayan_mock_records", label="Mock Records 独立测试库")])

    def list_tables(self) -> MockRecordsTablesResponse:
        visible_configs = [config for config in TABLE_CONFIGS.values() if config.visible_in_workbench]
        return MockRecordsTablesResponse(
            tables=[
                MockRecordsTableItem(
                    table_name=config.table_name,
                    label=config.label,
                    source_system=config.source_system,
                    description=config.description,
                )
                for config in visible_configs
            ]
        )

    def get_table_schema(self, table_name: str) -> MockRecordsTableSchemaResponse:
        config = self._get_table_config(table_name)
        return MockRecordsTableSchemaResponse(
            table_name=config.table_name,
            label=config.label,
            source_system=config.source_system,
            fields=config.fields,
        )

    async def list_rows(self, table_name: str) -> MockRecordsRowListResponse:
        rows = await self.repository.list_rows(table_name)
        return MockRecordsRowListResponse(table_name=table_name, rows=[self._serialize_row(row) for row in rows])

    async def create_row(
        self,
        table_name: str,
        values: dict[str, object],
        *,
        dept_id: str,
        user_id: str,
        record_id: str | None = None,
        internal_write: bool = False,
        commit_changes: bool = True,
    ) -> MockRecordMutationResponse:
        _ = dept_id
        before = None
        payload = dict(values)
        if record_id:
            payload["id"] = record_id
        sanitized_values = self._sanitize_values(table_name, payload, allow_record_id=bool(record_id), internal_write=internal_write)
        row = await self.repository.create_row(table_name, sanitized_values)
        after = self._serialize_row(row)
        response = await self._build_mutation_response(table_name, row.id, "created", before, after, user_id=user_id)
        await self._run_post_mutation_sync(table_name, before=before, after=after, user_id=user_id)
        if commit_changes:
            await self._commit_changes()
        return response

    async def update_row(
        self,
        table_name: str,
        record_id: str,
        values: dict[str, object],
        *,
        dept_id: str,
        user_id: str,
        internal_write: bool = False,
        commit_changes: bool = True,
    ) -> MockRecordMutationResponse:
        _ = dept_id
        existing = await self.repository.get_row(table_name, record_id)
        if existing is None:
            raise ValueError("RECORD_NOT_FOUND")
        before = self._serialize_row(existing)
        sanitized_values = self._sanitize_values(
            table_name,
            values,
            allow_record_id=False,
            existing_values=before,
            internal_write=internal_write,
        )
        row = await self.repository.update_row(table_name, record_id, sanitized_values)
        after = self._serialize_row(row)
        response = await self._build_mutation_response(table_name, row.id, "updated", before, after, user_id=user_id)
        await self._run_post_mutation_sync(table_name, before=before, after=after, user_id=user_id)
        if commit_changes:
            await self._commit_changes()
        return response

    async def delete_row(self, table_name: str, record_id: str, *, dept_id: str, user_id: str) -> MockRecordMutationResponse:
        _ = dept_id
        existing = await self.repository.get_row(table_name, record_id)
        if existing is None:
            raise ValueError("RECORD_NOT_FOUND")
        before = self._serialize_row(existing)
        row = await self.repository.delete_row(table_name, record_id)
        response = await self._build_mutation_response(table_name, row.id, "deleted", before, before or {}, user_id=user_id)
        await self._run_post_mutation_sync(table_name, before=before, after=None, user_id=user_id)
        await self._commit_changes()
        return response

    async def list_recent_events(self) -> MockRecordsRecentEventsResponse:
        events = await self.repository.list_recent_events()
        return MockRecordsRecentEventsResponse(
            events=[
                MockRecordsRecentEventItem(
                    change_event_id=item.id,
                    table_name=item.table_name,
                    record_id=item.record_id,
                    operation=item.operation,
                    event_type=item.event_type,
                    changed_fields=list(item.changed_fields or []),
                    triggered_execution_ids=list(item.triggered_execution_ids or []),
                    created_at=item.created_at.replace(tzinfo=timezone.utc).isoformat() if item.created_at else None,
                )
                for item in events
            ]
        )

    async def write_rows(
        self,
        table_name: str,
        rows: list[dict[str, object]],
        *,
        dept_id: str,
        user_id: str,
        operation: str,
        replace_by_field: str | None = None,
        replace_by_value: object | None = None,
        internal_write: bool = False,
    ) -> list[MockRecordMutationResponse]:
        mutations: list[MockRecordMutationResponse] = []

        if operation == "replace_rows" and (not replace_by_field or replace_by_value is None):
            raise ValueError("RECORDS_REPLACE_ROWS_MISSING_MATCH")

        if operation == "replace_rows" and replace_by_field and replace_by_value is not None:
            existing_rows = await self.repository.delete_rows_by_field(table_name, replace_by_field, replace_by_value)
            for row in existing_rows:
                before = self._serialize_row(cast(RecordModel, row))
                await self._log_change_event(
                    table_name=table_name,
                    record_id=cast(str, before.get("id") or ""),
                    operation="deleted",
                    before=before,
                    after=before,
                    user_id=user_id,
                    note=f"Workflow replace_rows cleared existing {table_name} rows",
                )
            if table_name == "parts_demand" and replace_by_field == "order_no":
                for downstream_table in DOWNSTREAM_REQUEST_TABLE_NAMES:
                    downstream_rows = await self.repository.delete_rows_by_field(downstream_table, replace_by_field, replace_by_value)
                    for row in downstream_rows:
                        before = self._serialize_row(cast(RecordModel, row))
                        await self._log_change_event(
                            table_name=downstream_table,
                            record_id=cast(str, before.get("id") or ""),
                            operation="deleted",
                            before=before,
                            after=before,
                            user_id=user_id,
                            note=f"Workflow replace_rows cleared downstream {downstream_table} rows",
                        )

        for row in rows:
            record_id = None
            if operation in {"upsert_rows", "replace_rows"}:
                raw_record_id = row.get("id") or row.get("record_id")
                record_id = str(raw_record_id) if isinstance(raw_record_id, (str, int)) else None
            mutations.append(
                await self.create_row(
                    table_name,
                    row,
                    dept_id=dept_id,
                    user_id=user_id,
                    record_id=record_id,
                    internal_write=internal_write,
                    commit_changes=False,
                )
            )
        await self._commit_changes()
        return mutations

    async def _build_mutation_response(
        self,
        table_name: str,
        record_id: str,
        operation: str,
        before: dict[str, object] | None,
        after: dict[str, object],
        *,
        user_id: str,
    ) -> MockRecordMutationResponse:
        event_id, triggered_execution_ids = await self._log_change_event(
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            before=before,
            after=after,
            user_id=user_id,
            note="Triggered from temporary mock records workbench",
        )
        return MockRecordMutationResponse(
            table_name=table_name,
            record_id=record_id,
            row=after,
            change_event_id=event_id,
            triggered_execution_ids=triggered_execution_ids,
        )

    async def _log_change_event(
        self,
        *,
        table_name: str,
        record_id: str,
        operation: str,
        before: dict[str, object] | None,
        after: dict[str, object],
        user_id: str,
        note: str,
    ) -> tuple[str, list[str]]:
        event_type = f"record.{operation}"
        event_id = f"evt_mock_{uuid4().hex[:10]}"
        changed_fields = self._calculate_changed_fields(before, after, operation=operation)
        triggered_execution_ids = await self._trigger_matching_workflows(
            table_name=table_name,
            event_id=event_id,
            event_type=event_type,
            operation=operation,
            before=before,
            after=after,
            user_id=user_id,
        )
        _ = await self.repository.append_change_log(
            SensorChangeLogRecord(
                id=event_id,
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                event_type=event_type,
                source_system="dayan_mock_records",
                changed_fields=changed_fields,
                before_data=before,
                after_data=after,
                triggered_execution_ids=triggered_execution_ids,
                note=note,
            )
        )
        return event_id, triggered_execution_ids

    async def _commit_changes(self) -> None:
        await self.repository.session.commit()
        await self.main_session.commit()

    async def _run_post_mutation_sync(
        self,
        table_name: str,
        *,
        before: dict[str, object] | None,
        after: dict[str, object] | None,
        user_id: str,
    ) -> None:
        if table_name == "product_bom":
            product_code = cast(str | None, (after or before or {}).get("product_code"))
            if product_code:
                await self._sync_orders_for_product(product_code, user_id=user_id)

    async def _sync_orders_for_product(self, product_code: str, *, user_id: str) -> None:
        orders = await self.repository.list_rows_by_field("customer_order", "product_code", product_code)
        for order in orders:
            await self._sync_order_projection(cast(CustomerOrderRecord, order).order_no, user_id=user_id)

    async def _sync_order_projection(self, order_no: str, *, user_id: str) -> None:
        existing_order = await self.repository.list_rows_by_field("customer_order", "order_no", order_no)
        if not existing_order:
            await self._purge_projection_rows(order_no, user_id=user_id)
            return

        order = cast(CustomerOrderRecord, existing_order[0])
        await self._purge_projection_rows(order_no, user_id=user_id)

        bom_rows = [cast(ProductBomRecord, item) for item in await self.repository.list_rows_by_field("product_bom", "product_code", order.product_code)]
        if not bom_rows:
            return

        demand_rows = self._build_parts_demand_rows(order, bom_rows)

        await self._create_projection_rows("parts_demand", demand_rows, user_id=user_id)

    async def _purge_projection_rows(self, order_no: str, *, user_id: str) -> None:
        for table_name in DERIVED_TABLE_NAMES:
            rows = await self.repository.delete_rows_by_field(table_name, "order_no", order_no)
            for row in rows:
                serialized = self._serialize_row(cast(RecordModel, row))
                await self._log_change_event(
                    table_name=table_name,
                    record_id=cast(str, serialized.get("id") or ""),
                    operation="deleted",
                    before=serialized,
                    after=serialized,
                    user_id=user_id,
                    note=f"Derived rows rebuilt from customer order {order_no}",
                )

    async def _create_projection_rows(self, table_name: str, rows: list[dict[str, object]], *, user_id: str) -> None:
        for row_payload in rows:
            row = await self.repository.create_row(table_name, row_payload)
            after = self._serialize_row(row)
            await self._log_change_event(
                table_name=table_name,
                record_id=row.id,
                operation="created",
                before=None,
                after=after,
                user_id=user_id,
                note=f"Derived rows rebuilt from customer order {cast(str, after.get('order_no') or '')}",
            )

    def _build_parts_demand_rows(
        self,
        order: CustomerOrderRecord,
        bom_rows: list[ProductBomRecord],
    ) -> list[dict[str, object]]:
        aggregated: dict[tuple[str, str], dict[str, object]] = {}
        for bom in bom_rows:
            required_qty = max(0, order.ordered_qty * bom.qty_per_unit)
            source_type = self._normalize_product_bom_source_type(bom.source_type)
            key = (bom.part_code, source_type)
            current = aggregated.get(key)
            purchase_qty = required_qty if source_type == "purchase" else 0
            manufacture_qty = required_qty if source_type == "manufacture" else 0
            customer_qty = required_qty if source_type == "customer" else 0
            if current is None:
                aggregated[key] = {
                    "id": f"dem_{order.order_no}_{bom.part_code}_{source_type}",
                    "order_no": order.order_no,
                    "customer_name": order.customer_name,
                    "product_code": order.product_code,
                    "product_name": order.product_name,
                    "part_code": bom.part_code,
                    "part_name": bom.part_name,
                    "source_type": source_type,
                    "required_qty": required_qty,
                    "purchase_qty": purchase_qty,
                    "manufacture_qty": manufacture_qty,
                    "customer_qty": customer_qty,
                    "unit_cost": bom.unit_cost,
                    "total_cost": round(required_qty * bom.unit_cost, 2),
                }
                continue

            current["required_qty"] = cast(int, current["required_qty"]) + required_qty
            current["purchase_qty"] = cast(int, current["purchase_qty"]) + purchase_qty
            current["manufacture_qty"] = cast(int, current["manufacture_qty"]) + manufacture_qty
            current["customer_qty"] = cast(int, current["customer_qty"]) + customer_qty
            current["total_cost"] = round(cast(float, current["total_cost"]) + required_qty * bom.unit_cost, 2)

        return list(aggregated.values())

    async def _trigger_matching_workflows(
        self,
        *,
        table_name: str,
        event_id: str,
        event_type: str,
        operation: str,
        before: dict[str, object] | None,
        after: dict[str, object],
        user_id: str,
    ) -> list[str]:
        workflows = await self.workflow_repository.list_workflows()
        execution_ids: list[str] = []
        for workflow in workflows:
            workflow_dept_id = workflow.owner_dept_id
            release = await self.workflow_repository.get_current_release(workflow.id)
            if release is None or release.compile_status != "success" or not release.execution_dag:
                logger.info(
                    "skip workflow auto-trigger: workflow_id=%s workflow_dept_id=%s reason=no_released_compiled_dag",
                    workflow.id,
                    workflow_dept_id,
                )
                continue
            if not self._has_canvas_nodes(release.ui_schema):
                logger.warning(
                    "skip workflow auto-trigger: workflow_id=%s workflow_dept_id=%s reason=empty_canvas_nodes",
                    workflow.id,
                    workflow_dept_id,
                )
                continue
            if not self._release_matches_event(release.execution_dag, table_name=table_name, event_type=event_type, operation=operation, after_payload=after):
                logger.info(
                    "skip workflow auto-trigger: workflow_id=%s workflow_dept_id=%s reason=event_not_matched table=%s event_type=%s operation=%s",
                    workflow.id,
                    workflow_dept_id,
                    table_name,
                    event_type,
                    operation,
                )
                continue
            response = await self.execution_service.start(
                ExecutionStartRequest(
                    workflow_id=workflow.id,
                    version=release.version,
                    mode="released",
                    dept_id=workflow_dept_id,
                    trigger=ExecutionTrigger(type="event", event_id=event_id),
                    operator=ExecutionOperator(user_id=user_id, roles=[]),
                    input={
                        "event": {
                            "event_id": event_id,
                            "event_type": event_type,
                            "source": "records_workbench",
                            "dept_id": workflow_dept_id,
                            "payload": {
                                "source_system": "dayan_mock_records",
                                "table": table_name,
                                "operation": operation,
                                "before": before,
                                "after": after,
                                "changed_fields": self._calculate_changed_fields(before, after, operation=operation),
                            },
                        }
                    },
                ),
                dept_id=workflow_dept_id,
                user_id=user_id,
            )
            execution_ids.append(response.execution_id)
        return execution_ids

    def _release_matches_event(
        self,
        execution_dag: dict[str, object],
        *,
        table_name: str,
        event_type: str,
        operation: str,
        after_payload: dict[str, object],
    ) -> bool:
        raw_nodes = execution_dag.get("nodes")
        if not isinstance(raw_nodes, list):
            return False
        for raw_item in cast(list[object], raw_nodes):
            if not isinstance(raw_item, dict):
                continue
            item = cast(dict[str, object], raw_item)
            if item.get("type") != "sensor_agent":
                continue
            raw_config = item.get("config")
            if not isinstance(raw_config, dict):
                continue
            config = cast(dict[str, object], raw_config)
            source_system = str(config.get("source_system") or "")
            source_table = str(config.get("source_table") or "")
            source_event_key = str(config.get("source_event_key") or "")
            if source_system and not self._source_system_matches(source_system, "dayan_mock_records"):
                continue
            if source_table and source_table != table_name:
                continue
            if source_event_key and source_event_key not in {event_type, operation}:
                continue
            if not self._sensor_conditions_match(config, after_payload):
                continue
            return True
        return False

    def _sensor_conditions_match(self, config: dict[str, object], source_payload: dict[str, object]) -> bool:
        raw_conditions = config.get("conditions")
        if not isinstance(raw_conditions, list) or not raw_conditions:
            return True

        results: list[bool] = []
        for raw_item in cast(list[object], raw_conditions):
            if not isinstance(raw_item, dict):
                continue
            condition = cast(dict[str, object], raw_item)
            field = condition.get("field")
            operator = condition.get("operator")
            if not isinstance(field, str) or not isinstance(operator, str):
                continue
            left = self._resolve_condition_field(source_payload, field)
            value_from_field = condition.get("value_from_field")
            if isinstance(value_from_field, str):
                right = self._resolve_condition_field(source_payload, value_from_field)
            else:
                right = condition.get("value")
            results.append(self._compare_condition_values(left, operator, right))

        if not results:
            return True
        return any(results) if str(config.get("condition_logic") or "and") == "or" else all(results)

    @staticmethod
    def _resolve_condition_field(source_payload: dict[str, object], path: str) -> object:
        current: object = source_payload
        for key in filter(None, path.split(".")):
            if not isinstance(current, dict):
                return None
            current = current.get(key)
        return current

    @staticmethod
    def _compare_condition_values(left: object, operator: str, right: object) -> bool:
        if operator == "eq":
            return left == right
        if operator == "ne":
            return left != right
        if operator in {">", ">=", "<", "<="} and isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if operator == ">":
                return left > right
            if operator == ">=":
                return left >= right
            if operator == "<":
                return left < right
            return left <= right
        return False

    @staticmethod
    def _source_system_matches(configured_system: str, actual_system: str) -> bool:
        configured = configured_system.strip()
        actual = actual_system.strip()
        if configured == actual:
            return True
        aliases = {
            "erp_prod": {"erp_prod", "dayan_mock_records"},
            "dayan_mock_records": {"dayan_mock_records", "erp_prod"},
        }
        return actual in aliases.get(configured, set())

    @staticmethod
    def _has_canvas_nodes(ui_schema: dict[str, object] | None) -> bool:
        if not isinstance(ui_schema, dict):
            return False
        raw_nodes = ui_schema.get("nodes")
        if not isinstance(raw_nodes, list):
            return False
        return len(cast(list[object], raw_nodes)) > 0

    def _get_table_config(self, table_name: str) -> TableConfig:
        config = TABLE_CONFIGS.get(table_name)
        if config is None:
            raise ValueError("RECORDS_TABLE_NOT_FOUND")
        return config

    def _sanitize_values(
        self,
        table_name: str,
        values: dict[str, object],
        *,
        allow_record_id: bool,
        existing_values: dict[str, object] | None = None,
        internal_write: bool = False,
    ) -> dict[str, object]:
        config = self._get_table_config(table_name)
        allowed_fields = {field.name for field in config.fields if field.editable or internal_write}
        sanitized = {key: value for key, value in values.items() if key in allowed_fields}
        if not sanitized and values:
            raise ValueError("RECORDS_MUTATION_FIELDS_INVALID")
        if allow_record_id:
            raw_record_id = values.get("record_id") or values.get("id")
            if isinstance(raw_record_id, str) and raw_record_id:
                sanitized["id"] = raw_record_id
        if table_name == "customer_order":
            raw_ordered_qty = sanitized.get("ordered_qty")
            raw_unit_price = sanitized.get("unit_price")
            if raw_ordered_qty is None and existing_values is not None:
                raw_ordered_qty = existing_values.get("ordered_qty")
            if raw_unit_price is None and existing_values is not None:
                raw_unit_price = existing_values.get("unit_price")
            ordered_qty = self._coerce_int(raw_ordered_qty)
            unit_price = self._coerce_float(raw_unit_price)
            sanitized["total_amount"] = round(ordered_qty * unit_price, 2)
        if table_name == "product_bom":
            raw_source_type = sanitized.get("source_type")
            if raw_source_type is None and existing_values is not None:
                raw_source_type = existing_values.get("source_type")
            normalized_source_type = self._normalize_product_bom_source_type(raw_source_type)
            sanitized["source_type"] = normalized_source_type

            raw_source_ref = sanitized.get("source_ref")
            if raw_source_ref is None and existing_values is not None:
                raw_source_ref = existing_values.get("source_ref")
            sanitized["source_ref"] = self._normalize_product_bom_source_ref(normalized_source_type, raw_source_ref)
        return sanitized

    @staticmethod
    def _coerce_int(value: object | None) -> int:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(float(value.strip() or "0"))
            except ValueError:
                return 0
        return 0

    @staticmethod
    def _coerce_float(value: object | None) -> float:
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip() or "0")
            except ValueError:
                return 0.0
        return 0.0

    @staticmethod
    def _normalize_product_bom_source_type(value: object | None) -> str:
        normalized = str(value or "").strip().lower()
        if normalized in {"purchase", "采购", "buy", "purchasing", "采购件"}:
            return "purchase"
        if normalized in {"manufacture", "生产", "制造", "自制", "manufacturing"}:
            return "manufacture"
        if normalized in {"customer", "客户提供", "客户供料", "客供", "customer_supply"}:
            return "customer"
        return "purchase"

    @staticmethod
    def _normalize_product_bom_source_ref(source_type: str, value: object | None) -> str:
        allowed_options = PRODUCT_BOM_SOURCE_REF_OPTIONS.get(source_type, PRODUCT_BOM_SOURCE_REF_OPTIONS["purchase"])
        normalized = str(value or "").strip()
        if normalized in allowed_options:
            return normalized
        alias = PRODUCT_BOM_SOURCE_REF_ALIASES.get(normalized)
        if alias and alias in allowed_options:
            return alias
        return allowed_options[0]

    def _serialize_row(self, row: RecordModel) -> dict[str, object]:
        result: dict[str, object] = {}
        for field_name in row.__mapper__.columns.keys():
            value = cast(object, getattr(row, field_name))
            if isinstance(value, datetime):
                result[field_name] = value.isoformat()
            elif isinstance(value, date):
                result[field_name] = value.isoformat()
            else:
                result[field_name] = value
        return result

    def _calculate_changed_fields(self, before: dict[str, object] | None, after: dict[str, object], *, operation: str) -> list[str]:
        if before is None:
            return [key for key in after.keys() if key != "updated_at"]
        if operation == "deleted":
            return [key for key in before.keys() if key != "updated_at"]
        if not after:
            return [key for key in before.keys() if key != "updated_at"]
        changed: list[str] = []
        for key, value in after.items():
            if before.get(key) != value:
                changed.append(key)
        return changed
