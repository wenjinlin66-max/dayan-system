from __future__ import annotations

import asyncpg
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_mock_engine: AsyncEngine | None = None
_mock_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(settings.database_url, future=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        get_engine()
    if _session_factory is None:
        raise RuntimeError("session factory initialization failed")
    return _session_factory


def get_mock_engine() -> AsyncEngine:
    global _mock_engine, _mock_session_factory
    if _mock_engine is None:
        _mock_engine = create_async_engine(settings.mock_database_url, future=True)
        _mock_session_factory = async_sessionmaker(_mock_engine, expire_on_commit=False, class_=AsyncSession)
    return _mock_engine


def get_mock_session_factory() -> async_sessionmaker[AsyncSession]:
    global _mock_session_factory
    if _mock_session_factory is None:
        get_mock_engine()
    if _mock_session_factory is None:
        raise RuntimeError("mock session factory initialization failed")
    return _mock_session_factory


async def ensure_mock_database_exists() -> None:
    admin_connection = await asyncpg.connect(
        host=settings.mock_pghost,
        port=settings.mock_pgport,
        user=settings.mock_pguser,
        password=settings.mock_pgpassword,
        database="postgres",
    )
    try:
        exists = await admin_connection.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", settings.mock_pgdatabase)
        if exists:
            return
        await admin_connection.execute(f'CREATE DATABASE "{settings.mock_pgdatabase}"')
    finally:
        await admin_connection.close()
