"""Módulo: test_slack_client."""

import pytest
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient

from src.infrastructure.slack_client import (
    SlackNotifier,
    create_slack_app,
    create_slack_handler,
)


def test_create_slack_app_returns_async_app() -> None:
    """create_slack_app retorna una instancia de AsyncApp."""
    app = create_slack_app("xoxb-test", "secret")
    assert isinstance(app, AsyncApp)


def test_create_slack_handler_returns_handler() -> None:
    """create_slack_handler retorna un AsyncSlackRequestHandler."""
    app = create_slack_app("xoxb-test", "secret")
    handler = create_slack_handler(app)
    assert isinstance(handler, AsyncSlackRequestHandler)


@pytest.mark.asyncio
async def test_slack_notifier_send_message() -> None:
    """send_message delega en el cliente de Slack."""
    calls = []

    class FakeClient:
        async def chat_postMessage(self, **kwargs):
            calls.append(kwargs)
            return {"ok": True}

    notifier = SlackNotifier(FakeClient())  # type: ignore[arg-type]
    await notifier.send_message("C1", "hola")
    assert len(calls) == 1
    assert calls[0]["channel"] == "C1"
    assert calls[0]["text"] == "hola"


@pytest.mark.asyncio
async def test_slack_notifier_open_modal() -> None:
    """open_modal delega en el cliente de Slack."""
    calls = []

    class FakeClient:
        async def views_open(self, **kwargs):
            calls.append(kwargs)
            return {"ok": True}

    notifier = SlackNotifier(FakeClient())  # type: ignore[arg-type]
    view = {"type": "modal"}
    await notifier.open_modal("trigger", view)
    assert len(calls) == 1
    assert calls[0]["trigger_id"] == "trigger"
    assert calls[0]["view"] == view
