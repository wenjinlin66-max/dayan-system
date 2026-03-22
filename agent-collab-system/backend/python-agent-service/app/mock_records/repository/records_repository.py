from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

TableModel = (
    ProductMasterRecord
    | ProductBomRecord
    | CustomerOrderRecord
    | PartsDemandRecord
    | PurchaseRequestRecord
    | ManufacturingRequestRecord
    | CustomerSupplyRequestRecord
)


class MockRecordsRepository:
    TABLE_MODEL_MAP: ClassVar[dict[str, type[TableModel]]] = {
        "product_master": ProductMasterRecord,
        "product_bom": ProductBomRecord,
        "customer_order": CustomerOrderRecord,
        "parts_demand": PartsDemandRecord,
        "purchase_request": PurchaseRequestRecord,
        "manufacturing_request": ManufacturingRequestRecord,
        "customer_supply_request": CustomerSupplyRequestRecord,
    }
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def get_model(self, table_name: str):
        model = self.TABLE_MODEL_MAP.get(table_name)
        if model is None:
            raise ValueError("RECORDS_TABLE_NOT_FOUND")
        return model

    async def list_rows(self, table_name: str) -> list[TableModel]:
        model = self.get_model(table_name)
        result = await self.session.execute(select(model).order_by(model.updated_at.desc()))
        return list(result.scalars().all())

    async def get_row(self, table_name: str, record_id: str) -> TableModel | None:
        model = self.get_model(table_name)
        result = await self.session.execute(select(model).where(model.id == record_id))
        return result.scalar_one_or_none()

    async def create_row(self, table_name: str, values: dict[str, object]) -> TableModel:
        model = self.get_model(table_name)
        payload = {**values}
        _ = payload.setdefault("id", f"rec_{uuid4().hex[:12]}")
        payload["updated_at"] = datetime.now(UTC)
        instance = model(**payload)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update_row(self, table_name: str, record_id: str, values: dict[str, object]) -> TableModel:
        instance = await self.get_row(table_name, record_id)
        if instance is None:
            raise ValueError("RECORD_NOT_FOUND")
        for key, value in values.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        instance.updated_at = datetime.now(UTC)
        await self.session.flush()
        return instance

    async def delete_row(self, table_name: str, record_id: str) -> TableModel:
        instance = await self.get_row(table_name, record_id)
        if instance is None:
            raise ValueError("RECORD_NOT_FOUND")
        await self.session.delete(instance)
        await self.session.flush()
        return instance

    async def append_change_log(self, log: SensorChangeLogRecord) -> SensorChangeLogRecord:
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_recent_events(self, limit: int = 20) -> list[SensorChangeLogRecord]:
        result = await self.session.execute(select(SensorChangeLogRecord).order_by(SensorChangeLogRecord.created_at.desc()).limit(limit))
        return list(result.scalars().all())

    async def list_rows_by_field(self, table_name: str, field_name: str, field_value: object) -> list[TableModel]:
        model = self.get_model(table_name)
        column = getattr(model, field_name, None)
        if column is None:
            raise ValueError("RECORDS_TABLE_FIELD_NOT_FOUND")
        result = await self.session.execute(select(model).where(column == field_value).order_by(model.updated_at.desc()))
        return list(result.scalars().all())

    async def delete_rows_by_field(self, table_name: str, field_name: str, field_value: object) -> list[TableModel]:
        rows = await self.list_rows_by_field(table_name, field_name, field_value)
        for row in rows:
            await self.session.delete(row)
        await self.session.flush()
        return rows

    async def remove_execution_references(self, execution_id: str) -> None:
        result = await self.session.execute(select(SensorChangeLogRecord).where(SensorChangeLogRecord.triggered_execution_ids.is_not(None)))
        logs = list(result.scalars().all())
        for log in logs:
            current_ids = list(log.triggered_execution_ids or [])
            next_ids = [item for item in current_ids if item != execution_id]
            if next_ids != current_ids:
                log.triggered_execution_ids = next_ids
        await self.session.flush()
