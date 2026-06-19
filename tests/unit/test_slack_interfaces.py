"""Módulo: test_slack_interfaces."""

from slack_bolt.async_app import AsyncApp

from src.interfaces.slack.bolt_app import register_handlers
from src.interfaces.slack.modals import build_standup_modal


def test_build_standup_modal_structure() -> None:
    """El modal tiene la estructura esperada."""
    modal = build_standup_modal()
    assert modal["type"] == "modal"
    assert modal["callback_id"] == "standup_submission"
    # Verificamos los inputs esenciales en lugar de un conteo fijo de bloques,
    # ya que el modal puede incluir bloques de contexto/divisores opcionales.
    input_block_ids = [
        b.get("block_id") for b in modal["blocks"] if b.get("type") == "input"
    ]
    assert "yesterday_block" in input_block_ids
    assert "today_block" in input_block_ids
    assert "blockers_block" in input_block_ids


def test_register_handlers_does_not_raise() -> None:
    """El registro de handlers no lanza excepciones."""
    app = AsyncApp(token="xoxb-test", signing_secret="test")
    class FakeSession:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def commit(self): pass

    services = {
        "session_maker": lambda: FakeSession(),
        "github_client": None,
        "default_team_id": "00000000-0000-0000-0000-000000000000",
        "default_channel_id": "C000",
    }
    register_handlers(app, services)
    assert app is not None
