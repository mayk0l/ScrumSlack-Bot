"""Módulo: logging_config.

Configuración central de logging estructurado con structlog. Se llama una
vez al arrancar la app; los módulos obtienen su logger con
`structlog.get_logger(__name__)`.
"""

from __future__ import annotations

import logging

import structlog


def setup_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Configura structlog para toda la aplicación."""
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
    )

    renderer = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
