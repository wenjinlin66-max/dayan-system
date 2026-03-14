from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.mock_records.db.base import MockRecordsBase


def utc_now() -> datetime:
    return datetime.now(UTC)


class InventoryStockRecord(MockRecordsBase):
    __tablename__: str = "inventory_stock"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    stock_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    safety_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warehouse_id: Mapped[str] = mapped_column(String(32), nullable=False, default="W-01")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="healthy")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class ProductionOrderRecord(MockRecordsBase):
    __tablename__: str = "production_order"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    order_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    workshop_id: Mapped[str] = mapped_column(String(32), nullable=False, default="WS-01")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DeviceStatusRecord(MockRecordsBase):
    __tablename__: str = "device_status"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    vibration: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    device_state: Mapped[str] = mapped_column(String(32), nullable=False, default="online")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class SensorChangeLogRecord(MockRecordsBase):
    __tablename__: str = "sensor_change_log"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    table_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    record_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(32), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), nullable=False, default="dayan_mock_records")
    changed_fields: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    before_data: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    after_data: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    triggered_execution_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
