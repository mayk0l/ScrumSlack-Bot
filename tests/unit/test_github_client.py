"""Módulo: test_github_client."""

import pytest

from src.domain.exceptions import ExternalServiceError
from src.infrastructure.github_client import GitHubClient


@pytest.fixture
def client() -> GitHubClient:
    return GitHubClient(token="ghp_test")


@pytest.mark.asyncio
async def test_get_open_pull_requests_returns_json(client: GitHubClient) -> None:
    """El cliente retorna el payload JSON mockeado."""
    expected = [{"number": 1, "title": "Feature"}]

    async def fake_request(method: str, path: str, **kwargs):
        class Response:
            def json(self):
                return expected

        return Response()

    client._request = fake_request
    result = await client.get_open_pull_requests("org", "repo")
    assert result == expected


@pytest.mark.asyncio
async def test_client_raises_external_service_error(client: GitHubClient) -> None:
    """Errores HTTP no 500 se propagan como ExternalServiceError."""
    import httpx

    async def fake_http_request(*args, **kwargs):
        response = httpx.Response(404, text="not found")
        raise httpx.HTTPStatusError(
            "Not found", request=None, response=response
        )

    client._client.request = fake_http_request
    with pytest.raises(ExternalServiceError):
        await client.get_open_pull_requests("org", "repo")


@pytest.mark.asyncio
async def test_close_does_not_raise(client: GitHubClient) -> None:
    """Cerrar el cliente no lanza excepciones."""
    await client.close()
