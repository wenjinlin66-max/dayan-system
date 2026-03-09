from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentMemory(Base):
    __tablename__ = "agent_memories"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    memory_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    agent_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    dept_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text(), nullable=False)


class RagDocIndex(Base):
    __tablename__ = "rag_docs_index"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dept_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
