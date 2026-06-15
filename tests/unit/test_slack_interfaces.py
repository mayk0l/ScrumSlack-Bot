"""Módulo: test_slack_interfaces."""

from slack_bolt.async_app import AsyncApp

from src.interfaces.slack.bolt_app import register_handlers
from src.interfaces.slack.modals import build_standup_modal


def test_build_standup_modal_structure() -> None:
    """El modal tiene la estructura esperada."""
    modal = build_standup_modal()
    assert modal["type"] == "modal"
    assert modal["callback_id"] == "standup_submission"
    assert len(modal["blocks"]) == 3


def test_register_handlers_does_not_raise() -> None:
    """El registro de handlers no lanza excepciones."""
    app = AsyncApp(token="xoxb-test", signing_secret="test")
    services = {
        "standup_service": None,
        "report_service": None,
        "risk_service": None,
        "default_team_id": "00000000-0000-0000-0000-000000000000",
        "default_channel_id": "C000",
    }
    register_handlers(app, services)
    assert app is not None
