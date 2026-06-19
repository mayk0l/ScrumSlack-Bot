"""Módulo: scheduler.

Servicio de scheduling con APScheduler async.
"""

from __future__ import annotations

from typing import Any, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class SchedulerService:
    """Wrapper sobre AsyncIOScheduler para jobs diarios."""

    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()

    def add_daily_job(
        self,
        func: Callable[..., Any],
        hour: int,
        minute: int,
        timezone: str,
        job_id: str,
        **kwargs: Any,
    ) -> None:
        """Agrega un job que se ejecuta diariamente a una hora fija."""
        self._scheduler.add_job(
            func,
            CronTrigger(hour=hour, minute=minute, timezone=timezone),
            id=job_id,
            replace_existing=True,
            kwargs=kwargs,
        )

    def add_interval_job(
        self,
        func: Callable[..., Any],
        minutes: int,
        job_id: str,
        **kwargs: Any,
    ) -> None:
        """Agrega un job periódico que se ejecuta cada `minutes` minutos."""
        self._scheduler.add_job(
            func,
            IntervalTrigger(minutes=minutes),
            id=job_id,
            replace_existing=True,
            kwargs=kwargs,
        )

    def start(self) -> None:
        """Inicia el scheduler."""
        self._scheduler.start()

    def shutdown(self, wait: bool = True) -> None:
        """Detiene el scheduler."""
        self._scheduler.shutdown(wait=wait)

    def remove_job(self, job_id: str) -> None:
        """Remueve un job por su ID."""
        self._scheduler.remove_job(job_id)
