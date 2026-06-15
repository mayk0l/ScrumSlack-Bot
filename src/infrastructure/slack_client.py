"""Módulo: slack_client.

Configuración de Slack Bolt AsyncApp y helpers de notificación.
"""

from __future__ import annotations

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler
from slack_sdk.web.async_client import AsyncWebClient


def create_slack_app(token: str, signing_secret: str) -> AsyncApp:
    """Crea una instancia de AsyncApp de Slack Bolt."""
    return AsyncApp(token=token, signing_secret=signing_secret)


def create_slack_handler(app: AsyncApp) -> AsyncSlackRequestHandler:
    """Crea el handler FastAPI para Slack Bolt."""
    return AsyncSlackRequestHandler(app)


class SlackNotifier:
    """Helper para enviar mensajes y modales a Slack."""

    def __init__(self, client: AsyncWebClient):
        self._client = client

    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: list[dict] | None = None,
    ) -> dict:
        """Envía un mensaje a un canal."""
        kwargs: dict = {"channel": channel, "text": text}
        if blocks is not None:
            kwargs["blocks"] = blocks
        return await self._client.chat_postMessage(**kwargs)

    async def send_thread_reply(
        self, channel: str, thread_ts: str, text: str
    ) -> dict:
        """Responde en un hilo."""
        return await self._client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=text,
        )

    async def open_modal(self, trigger_id: str, view: dict) -> dict:
        """Abre un modal."""
        return await self._client.views_open(
            trigger_id=trigger_id,
            view=view,
        )

    async def update_message(
        self,
        channel: str,
        ts: str,
        text: str,
        blocks: list[dict] | None = None,
    ) -> dict:
        """Actualiza un mensaje existente."""
        kwargs: dict = {"channel": channel, "ts": ts, "text": text}
        if blocks is not None:
            kwargs["blocks"] = blocks
        return await self._client.chat_update(**kwargs)
