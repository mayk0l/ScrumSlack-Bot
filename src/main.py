"""Módulo: main."""

from fastapi import FastAPI

from src.interfaces.api.routes import router as api_router

app = FastAPI(title="Scrum Master Bot")

app.include_router(api_router)
