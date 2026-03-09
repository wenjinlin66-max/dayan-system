from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    thread_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False, index=True)
    dept_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    error_summary: Mapped[str | None] = mapped_column(Text(), nullable=True)


class ExecutionCheckpoint(Base):
    __tablename__ = "execution_checkpoints"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    checkpoint_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
