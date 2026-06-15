"""Módulo: bolt_app.

Registro centralizado de handlers de Slack Bolt.
"""

from __future__ import annotations

from slack_bolt.async_app import AsyncApp

from src.interfaces.slack.commands import register_commands
from src.interfaces.slack.events import register_events
from src.interfaces.slack.modals import register_modals


def register_handlers(app: AsyncApp, services: dict) -> None:
    """Registra todos los comandos, eventos y acciones de Slack."""
    register_commands(app, services)
    register_events(app, services)
    register_modals(app, services)
