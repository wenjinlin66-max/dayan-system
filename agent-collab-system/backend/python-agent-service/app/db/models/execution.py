from datetime import datetime

from sqlalchemy import DateTime, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    workflow_version: Mapped[int] = mapped_column(nullable=False)
    mode: Mapped[str] = mapped_column(String(32), default="released", nullable=False)
    thread_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    entry_node: Mapped[str] = mapped_column(String(128), nullable=False)
    current_node: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    trigger_type: Mapped[str] = mapped_column(String(64), nullable=False)
    dept_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    started_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trigger_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    context_snapshot: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    final_output: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExecutionCheckpoint(Base):
    __tablename__ = "execution_checkpoints"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    checkpoint_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    thread_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    checkpoint_data: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    current_node: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
