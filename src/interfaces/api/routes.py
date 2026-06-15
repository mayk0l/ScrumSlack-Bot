"""Módulo: routes."""

from fastapi import APIRouter

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
