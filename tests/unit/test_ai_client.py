"""Módulo: test_ai_client."""

import pytest

from src.domain.exceptions import ExternalServiceError
from src.infrastructure.ai_client import AIClient


@pytest.fixture
def client() -> AIClient:
    return AIClient(api_key="sk-test", model="test-model")


@pytest.mark.asyncio
async def test_generate_summary_returns_content(client: AIClient) -> None:
    """El cliente retorna el contenido generado."""
    expected_content = "Resumen de prueba"

    async def fake_request(payload: dict):
        return {
            "choices": [
                {"message": {"content": expected_content}}
            ]
        }

    client._request = fake_request
    result = await client.generate_summary("prompt", "context")
    assert result == expected_content


@pytest.mark.asyncio
async def test_generate_summary_raises_on_invalid_response(client: AIClient) -> None:
    """Respuesta inesperada del modelo lanza ExternalServiceError."""
    async def fake_request(payload: dict):
        return {"invalid": "response"}

    client._request = fake_request
    with pytest.raises(ExternalServiceError):
        await client.generate_summary("prompt", "context")


@pytest.mark.asyncio
async def test_close_does_not_raise(client: AIClient) -> None:
    """Cerrar el cliente no lanza excepciones."""
    await client.close()
