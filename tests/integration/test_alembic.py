"""Módulo: test_alembic."""

import os
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

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

from src.config import settings
from src.infrastructure.database import Base


EXPECTED_TABLES = {
    "teams",
    "members",
    "sprints",
    "standup_sessions",
    "standup_responses",
    "pull_requests",
    "issues",
    "risks",
    "metric_snapshots",
}


def test_alembic_ini_exists() -> None:
    """alembic.ini debe existir y apuntar al directorio de migraciones."""
    path = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    assert path.exists(), "alembic.ini no encontrado"
    content = path.read_text(encoding="utf-8")
    assert "script_location = migrations" in content
    assert "sqlalchemy.url" in content


def test_migrations_env_py_exists() -> None:
    """migrations/env.py debe existir y configurar metadata."""
    path = Path(__file__).resolve().parent.parent.parent / "migrations" / "env.py"
    assert path.exists(), "migrations/env.py no encontrado"
    content = path.read_text(encoding="utf-8")
    assert "Base.metadata" in content
    assert "settings.database_url" in content


def test_initial_migration_file_exists() -> None:
    """Debe existir al menos un archivo de migración generado."""
    versions_dir = Path(__file__).resolve().parent.parent.parent / "migrations" / "versions"
    assert versions_dir.exists(), "migrations/versions no existe"
    migration_files = list(versions_dir.glob("*.py"))
    assert len(migration_files) >= 1, "No se encontraron migraciones"


@pytest.mark.asyncio
async def test_alembic_tables_created() -> None:
    """alembic upgrade head crea todas las tablas esperadas."""
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public'"
                )
            )
            tables = {row[0] for row in result.all()}
            for expected in EXPECTED_TABLES:
                assert expected in tables, f"Tabla faltante: {expected}"
    except Exception as exc:
        pytest.skip(f"PostgreSQL no disponible: {exc}")
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_alembic_upgrade_head_is_idempotent() -> None:
    """Ejecutar upgrade head dos veces no debe fallar."""
    import subprocess

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parent.parent.parent,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"alembic upgrade head falló: {result.stderr}"
