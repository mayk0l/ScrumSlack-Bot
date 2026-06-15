"""Módulo: github_client.

Cliente async para la API REST de GitHub v3 con retry y manejo de errores.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from src.domain.exceptions import ExternalServiceError


class GitHubClient:
    """Cliente async de GitHub con retry simple."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://api.github.com",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=timeout,
        )

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> httpx.Response:
        """Ejecuta una petición con retry y backoff exponencial."""
        last_exception: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._client.request(method, path, **kwargs)
                if response.status_code == 429:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                last_exception = exc
                if exc.response.status_code >= 500:
                    wait = 2 ** attempt
                    await asyncio.sleep(wait)
                    continue
                raise ExternalServiceError(
                    "GitHub",
                    f"HTTP {exc.response.status_code}: {exc.response.text}",
                ) from exc
            except httpx.RequestError as exc:
                last_exception = exc
                wait = 2 ** attempt
                await asyncio.sleep(wait)

        raise ExternalServiceError(
            "GitHub",
            f"Fallo tras {self._max_retries} intentos: {last_exception}",
        ) from last_exception

    async def get_open_pull_requests(self, org: str, repo: str) -> list[dict]:
        """Lista PRs abiertos de un repositorio."""
        response = await self._request(
            "GET", f"/repos/{org}/{repo}/pulls", params={"state": "open"}
        )
        return response.json()

    async def get_pr_reviews(
        self, org: str, repo: str, pr_number: int
    ) -> list[dict]:
        """Lista reviews de un PR."""
        response = await self._request(
            "GET", f"/repos/{org}/{repo}/pulls/{pr_number}/reviews"
        )
        return response.json()

    async def get_open_issues(self, org: str, repo: str) -> list[dict]:
        """Lista issues abiertos de un repositorio."""
        response = await self._request(
            "GET", f"/repos/{org}/{repo}/issues", params={"state": "open"}
        )
        return response.json()

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        await self._client.aclose()
