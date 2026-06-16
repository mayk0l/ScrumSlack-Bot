"""Módulo: config."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 3000

    # Database
    database_url: str

    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str = ""

    # GitHub
    github_token: str
    github_default_org: str = ""

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4"

    # Standup
    standup_channel_id: str
    standup_time: str = "09:00"
    summary_time: str = "17:00"
    timezone: str = "America/Santiago"

    # Excel
    excel_file_path: str = "project_tracking.xlsx"

import sys
from pydantic import ValidationError

try:
    settings = Settings()
except ValidationError as e:
    print("❌ ERROR DE CONFIGURACIÓN: Faltan variables de entorno requeridas:")
    for error in e.errors():
        print(f"  - {error['loc'][0]}: {error['msg']}")
    sys.exit(1)
