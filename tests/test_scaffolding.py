"""Módulo: test_scaffolding."""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_DIRS = [
    "migrations",
    "migrations/versions",
    "src",
    "src/domain",
    "src/application",
    "src/infrastructure",
    "src/infrastructure/repositories",
    "src/interfaces",
    "src/interfaces/slack",
    "src/interfaces/api",
    "tests",
    "tests/unit",
    "tests/integration",
]

EXPECTED_PY_FILES = [
    "src/__init__.py",
    "src/config.py",
    "src/main.py",
    "src/domain/__init__.py",
    "src/domain/models.py",
    "src/domain/repositories.py",
    "src/domain/exceptions.py",
    "src/application/__init__.py",
    "src/application/standup_service.py",
    "src/application/github_service.py",
    "src/application/risk_service.py",
    "src/application/report_service.py",
    "src/application/ai_service.py",
    "src/application/sprint_service.py",
    "src/application/excel_sync_service.py",
    "src/application/notification_service.py",
    "src/infrastructure/__init__.py",
    "src/infrastructure/database.py",
    "src/infrastructure/orm_models.py",
    "src/infrastructure/repositories/__init__.py",
    "src/infrastructure/repositories/team_repo.py",
    "src/infrastructure/repositories/member_repo.py",
    "src/infrastructure/repositories/standup_repo.py",
    "src/infrastructure/repositories/pr_repo.py",
    "src/infrastructure/repositories/sprint_repo.py",
    "src/infrastructure/repositories/risk_repo.py",
    "src/infrastructure/repositories/metric_repo.py",
    "src/infrastructure/slack_client.py",
    "src/infrastructure/github_client.py",
    "src/infrastructure/ai_client.py",
    "src/infrastructure/scheduler.py",
    "src/interfaces/__init__.py",
    "src/interfaces/slack/__init__.py",
    "src/interfaces/slack/bolt_app.py",
    "src/interfaces/slack/commands.py",
    "src/interfaces/slack/modals.py",
    "src/interfaces/slack/events.py",
    "src/interfaces/api/__init__.py",
    "src/interfaces/api/routes.py",
    "src/interfaces/api/dependencies.py",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/unit/__init__.py",
    "tests/unit/test_standup_service.py",
    "tests/unit/test_risk_service.py",
    "tests/unit/test_github_service.py",
    "tests/integration/__init__.py",
    "tests/integration/test_slack_commands.py",
]

# Archivos que ya fueron implementados y no deben tener solo placeholder.
IMPLEMENTED_PY_FILES = {
    "src/config.py": ["class Settings", "pydantic_settings"],
    "src/main.py": ["FastAPI", "include_router"],
    "src/interfaces/api/routes.py": ["APIRouter", "@router.get"],
    "src/domain/models.py": ["@dataclass", "UUID", "uuid4"],
    "src/domain/exceptions.py": ["class DomainException", "class EntityNotFoundError"],
    "src/domain/repositories.py": ["class TeamRepository", "abstractmethod", "async def"],
    "src/infrastructure/database.py": ["create_async_engine", "async_sessionmaker", "Base"],
    "src/infrastructure/orm_models.py": ["class TeamORM", "to_domain", "from_domain"],
    "src/infrastructure/repositories/team_repo.py": ["class TeamRepositoryImpl", "TeamRepository"],
    "src/infrastructure/repositories/member_repo.py": ["class MemberRepositoryImpl", "MemberRepository"],
    "src/infrastructure/repositories/standup_repo.py": ["class StandupSessionRepositoryImpl", "class StandupResponseRepositoryImpl"],
    "src/infrastructure/repositories/pr_repo.py": ["class PullRequestRepositoryImpl", "PullRequestRepository", "on_conflict_do_update"],
    "src/infrastructure/repositories/sprint_repo.py": ["class SprintRepositoryImpl", "SprintRepository"],
    "src/infrastructure/repositories/risk_repo.py": ["class RiskRepositoryImpl", "RiskRepository"],
    "src/infrastructure/repositories/metric_repo.py": ["class MetricRepositoryImpl", "MetricRepository"],
}

EXPECTED_CONFIG_FILES = [
    "docker-compose.yml",
    "Dockerfile",
    "requirements.txt",
    ".env.example",
    ".gitignore",
    "alembic.ini",
    "migrations/env.py",
    "migrations/script.py.mako",
    "project_tracking.xlsx",
]


@pytest.mark.parametrize("relative_path", EXPECTED_DIRS)
def test_directory_exists(relative_path: str) -> None:
    """Verifica que todos los directorios del scaffolding existan."""
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"Directorio no encontrado: {relative_path}"
    assert path.is_dir(), f"No es un directorio: {relative_path}"


@pytest.mark.parametrize("relative_path", EXPECTED_PY_FILES)
def test_python_file_exists_and_has_placeholder(relative_path: str) -> None:
    """Verifica que los archivos .py existan y tengan el placeholder correcto."""
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"Archivo no encontrado: {relative_path}"
    assert path.is_file(), f"No es un archivo: {relative_path}"

    content = path.read_text(encoding="utf-8")
    name = path.stem

    if relative_path in IMPLEMENTED_PY_FILES:
        for marker in IMPLEMENTED_PY_FILES[relative_path]:
            assert marker in content, f"Falta marcador '{marker}' en {relative_path}"
        return

    if name == "__init__":
        assert content == "", f"__init__.py debe estar vacío: {relative_path}"
    else:
        expected = f'"""Módulo: {name}."""\n'
        assert content == expected, (
            f"Placeholder incorrecto en {relative_path}. "
            f"Esperado: {expected!r}, Obtenido: {content!r}"
        )


@pytest.mark.parametrize("relative_path", EXPECTED_CONFIG_FILES)
def test_config_file_exists(relative_path: str) -> None:
    """Verifica que los archivos de configuración del scaffolding existan."""
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"Archivo no encontrado: {relative_path}"
    assert path.is_file(), f"No es un archivo: {relative_path}"
