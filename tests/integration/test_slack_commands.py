"""Módulo: test_slack_commands.

Pruebas de integración para comandos de Slack.
"""

from unittest.mock import MagicMock
from slack_bolt.async_app import AsyncApp
from src.interfaces.slack.commands import register_commands


def test_register_commands():
    """Prueba que los comandos se registran correctamente en la app."""
    app = AsyncApp(token="xoxb-mock", signing_secret="mock-secret")
    
    from src.container import init_container
    from src.config import settings
    init_container(settings, MagicMock())

    # Mock services (kept for signature backwards compatibility)
    services = {
        "session_maker": MagicMock(),
        "github_client": MagicMock(),
        "default_team_id": "123",
        "default_channel_id": "C123"
    }
    
    # Register should not raise exceptions
    register_commands(app, services)
    
    # Verify commands were registered
    assert len(app._listeners) > 0
