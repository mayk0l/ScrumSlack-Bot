"""Módulo: test_api_routes."""

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_health_check() -> None:
    """El health check responde 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
