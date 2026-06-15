"""Módulo: database.

Configuración de SQLAlchemy async: engine, session factory y utilidades.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.config import settings

Base = declarative_base()

engine = create_async_engine(settings.database_url, echo=settings.app_debug)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """Async generator que provee una sesión de base de datos."""
    async with async_session_maker() as session:
        yield session


async def init_db() -> None:
    """Crea todas las tablas en desarrollo.

    No usar en producción; usar Alembic en su lugar.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Cierra el pool de conexiones del engine."""
    await engine.dispose()
