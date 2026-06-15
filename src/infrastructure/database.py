"""Módulo: database.

Configuración de SQLAlchemy async: engine, session factory y utilidades.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.config import settings

Base = declarative_base()

_engine = None
_async_session_maker = None


def get_engine():
    """Retorna el engine async, creándolo lazy si es necesario."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(settings.database_url, echo=settings.app_debug)
    return _engine


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Retorna la factory de sesiones, creándola lazy si es necesario."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


async def get_session() -> AsyncSession:
    """Async generator que provee una sesión de base de datos."""
    maker = get_async_session_maker()
    async with maker() as session:
        yield session


async def init_db() -> None:
    """Crea todas las tablas en desarrollo.

    No usar en producción; usar Alembic en su lugar.
    """
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Cierra el pool de conexiones del engine."""
    global _engine, _async_session_maker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
    _async_session_maker = None
