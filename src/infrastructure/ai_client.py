"""Módulo: ai_client.

Cliente async para OpenRouter API (formato compatible con OpenAI).
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from src.domain.exceptions import ExternalServiceError


class AIClient:
    """Cliente async para generación de texto con LLMs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: float = 60.0,
        max_retries: int = 3,
    ):
        self._model = model
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Envía una petición a /chat/completions con retry."""
        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json=payload,
                )
                if response.status_code == 429:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                last_exception = exc
                if exc.response.status_code >= 500:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue
                raise ExternalServiceError(
                    "OpenRouter",
                    f"HTTP {exc.response.status_code}: {exc.response.text}",
                ) from exc
            except httpx.RequestError as exc:
                last_exception = exc
                wait = 2 ** attempt
                await asyncio.sleep(wait)

        raise ExternalServiceError(
            "OpenRouter",
            f"Fallo tras {self._max_retries} intentos: {last_exception}",
        ) from last_exception

    async def generate_summary(
        self, prompt: str, context: str, max_tokens: int = 1000
    ) -> str:
        """Genera un resumen a partir de prompt + contexto."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": context},
            ],
            "max_tokens": max_tokens,
        }
        data = await self._request(payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ExternalServiceError(
                "OpenRouter", "Respuesta inesperada del modelo"
            ) from exc

    async def analyze_risks(
        self, standup_data: str, pr_data: str
    ) -> str:
        """Analiza datos de standup y PRs para detectar riesgos."""
        prompt = (
            "Eres un Scrum Master experto. Analiza el siguiente standup y "
            "pull requests abiertos. Identifica riesgos, bloqueos y "
            "recomendaciones accionables en español y de forma concisa."
        )
        context = f"## Standup\n{standup_data}\n\n## Pull Requests\n{pr_data}"
        return await self.generate_summary(prompt, context)

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self._client.aclose()
