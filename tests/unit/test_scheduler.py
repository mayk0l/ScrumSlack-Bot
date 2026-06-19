"""Módulo: test_scheduler."""

import pytest

from src.infrastructure.scheduler import SchedulerService


@pytest.fixture
def scheduler() -> SchedulerService:
    return SchedulerService()


def test_add_daily_job_creates_job(scheduler: SchedulerService) -> None:
    """Agregar un job diario lo registra en el scheduler."""
    calls = []

    def dummy_job(**kwargs):
        calls.append(kwargs)

    scheduler.add_daily_job(
        dummy_job,
        hour=9,
        minute=0,
        timezone="America/Santiago",
        job_id="standup_reminder",
        team_id="team-1",
    )
    job = scheduler._scheduler.get_job("standup_reminder")
    assert job is not None
    assert job.id == "standup_reminder"


@pytest.mark.asyncio
async def test_scheduler_start_and_shutdown() -> None:
    """El scheduler puede iniciarse y detenerse dentro de un event loop."""
    import asyncio

    scheduler = SchedulerService()
    scheduler.start()
    assert scheduler._scheduler.running
    scheduler.shutdown(wait=False)
    await asyncio.sleep(0.1)
    assert not scheduler._scheduler.running


def test_add_interval_job_creates_job(scheduler: SchedulerService) -> None:
    """Agregar un job de intervalo lo registra en el scheduler."""
    def dummy_job(**kwargs):
        pass

    scheduler.add_interval_job(dummy_job, minutes=30, job_id="github_sync")
    job = scheduler._scheduler.get_job("github_sync")
    assert job is not None
    assert job.id == "github_sync"


def test_remove_job(scheduler: SchedulerService) -> None:
    """Se puede remover un job por ID."""
    def dummy_job(**kwargs):
        pass

    scheduler.add_daily_job(
        dummy_job,
        hour=9,
        minute=0,
        timezone="America/Santiago",
        job_id="removable",
    )
    scheduler.remove_job("removable")
    assert scheduler._scheduler.get_job("removable") is None
