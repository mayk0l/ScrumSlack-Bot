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
    user_mapping: str = '{"U0123456": "Emiliano J."}'

    @property
    def user_mapping_dict(self) -> dict:
        import json
        try:
            return json.loads(self.user_mapping)
        except Exception:
            return {}

settings = Settings()
