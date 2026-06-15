"""Módulo: test_infrastructure."""

import shutil
import subprocess
import time
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DEPENDENCIES = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic-settings",
    "slack-bolt",
    "slack-sdk",
    "sqlalchemy",
    "asyncpg",
    "alembic",
    "httpx",
    "apscheduler",
    "openpyxl",
    "openai",
    "structlog",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "python-dotenv",
]

REQUIRED_ENV_VARS = [
    "APP_ENV",
    "APP_DEBUG",
    "APP_PORT",
    "DATABASE_URL",
    "SLACK_BOT_TOKEN",
    "SLACK_SIGNING_SECRET",
    "SLACK_APP_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_DEFAULT_ORG",
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "STANDUP_CHANNEL_ID",
    "STANDUP_TIME",
    "SUMMARY_TIME",
    "TIMEZONE",
    "EXCEL_FILE_PATH",
]

REQUIRED_GITIGNORE_PATTERNS = [
    "__pycache__/",
    "*.pyc",
    ".env",
    ".venv/",
    "venv/",
    "project_tracking.xlsx",
]


@pytest.mark.parametrize("dependency", REQUIRED_DEPENDENCIES)
def test_requirements_txt_includes_dependency(dependency: str) -> None:
    """Verifica que requirements.txt incluya las dependencias principales."""
    content = (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert dependency in content, f"Falta dependencia: {dependency}"


@pytest.mark.parametrize("var", REQUIRED_ENV_VARS)
def test_env_example_includes_variable(var: str) -> None:
    """Verifica que .env.example defina todas las variables requeridas."""
    content = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    assert var in content, f"Falta variable de entorno en .env.example: {var}"


def test_docker_compose_yml_is_valid_yaml() -> None:
    """Verifica que docker-compose.yml sea YAML válido."""
    content = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    parsed = yaml.safe_load(content)
    assert "services" in parsed
    assert "app" in parsed["services"]
    assert "db" in parsed["services"]
    assert "volumes" in parsed


def test_dockerfile_has_required_instructions() -> None:
    """Verifica que Dockerfile tenga las instrucciones mínimas."""
    content = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert content.startswith("FROM python:3.12-slim")
    assert "COPY requirements.txt" in content
    assert "RUN pip install" in content
    assert 'CMD ["uvicorn", "src.main:app"' in content
    assert "EXPOSE 3000" in content


def test_docker_compose_app_depends_on_db() -> None:
    """Verifica que el servicio app dependa de db con healthcheck."""
    content = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    parsed = yaml.safe_load(content)
    app = parsed["services"]["app"]
    assert app["depends_on"]["db"]["condition"] == "service_healthy"
    db = parsed["services"]["db"]
    assert "healthcheck" in db


@pytest.mark.parametrize("pattern", REQUIRED_GITIGNORE_PATTERNS)
def test_gitignore_ignores_required_patterns(pattern: str) -> None:
    """Verifica que .gitignore ignore archivos sensibles y generados."""
    content = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert pattern in content, f"Falta patrón en .gitignore: {pattern}"


def test_docker_build_succeeds() -> None:
    """Verifica que la imagen Docker se construya exitosamente."""
    if shutil.which("docker") is None:
        pytest.skip("Docker no está disponible")

    result = subprocess.run(
        ["docker", "build", "-t", "scrum-master-bot:test", "."],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Docker build falló:\n{result.stderr}"


def test_docker_compose_up_health_check() -> None:
    """Levanta docker-compose y verifica que /api/health responda."""
    if shutil.which("docker") is None:
        pytest.skip("Docker no está disponible")

    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        shutil.copy(PROJECT_ROOT / ".env.example", env_file)

    down = subprocess.run(
        ["docker", "compose", "down", "-v"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    up = subprocess.run(
        ["docker", "compose", "up", "-d", "--build"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert up.returncode == 0, f"docker compose up falló:\n{up.stderr}"

    try:
        deadline = time.time() + 60
        last_error = ""
        while time.time() < deadline:
            result = subprocess.run(
                ["curl", "-fsS", "http://localhost:3000/api/health"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and '"status":"ok"' in result.stdout:
                break
            last_error = result.stderr or result.stdout
            time.sleep(1)
        else:
            pytest.fail(f"Health check no respondió a tiempo: {last_error}")
    finally:
        subprocess.run(
            ["docker", "compose", "down", "-v"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
