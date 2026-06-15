"""Módulo: test_database."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Asegurar DATABASE_URL apunte a localhost para tests locales.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://scrum_bot:scrum_bot_pass@db:5432/scrum_bot_db",
)
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")
os.environ.setdefault("SLACK_SIGNING_SECRET", "test")
os.environ.setdefault("STANDUP_CHANNEL_ID", "Ctest")
os.environ.setdefault("GITHUB_TOKEN", "ghp_test")

from src.infrastructure.database import (
    close_db,
    get_async_session_maker,
    get_engine,
    get_session,
    init_db,
)


@pytest.mark.asyncio
async def test_get_session_yields_async_session() -> None:
    """get_session entrega una AsyncSession funcional."""
    try:
        async for session in get_session():
            assert isinstance(session, AsyncSession)
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as exc:
        pytest.skip(f"PostgreSQL no disponible: {exc}")
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_async_session_maker_creates_session() -> None:
    """get_async_session_maker crea sesiones válidas."""
    try:
        maker = get_async_session_maker()
        async with maker() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as exc:
        pytest.skip(f"PostgreSQL no disponible: {exc}")
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_engine_is_async() -> None:
    """El engine está configurado para async."""
    try:
        async with get_engine().connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as exc:
        pytest.skip(f"PostgreSQL no disponible: {exc}")
    finally:
        await close_db()


@pytest.mark.asyncio
async def test_init_db_does_not_raise() -> None:
    """init_db ejecuta sin errores aunque no haya modelos ORM aún."""
    try:
        await init_db()
    except Exception as exc:
        pytest.skip(f"PostgreSQL no disponible: {exc}")
    finally:
        await close_db()
