"""Módulo: container.

Inversión de Control (IoC) y Contenedor de Dependencias nativo.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import get_async_session_maker

# Repositories
from src.infrastructure.repositories.member_repo import MemberRepositoryImpl
from src.infrastructure.repositories.metric_repo import MetricRepositoryImpl
from src.infrastructure.repositories.pr_repo import PullRequestRepositoryImpl
from src.infrastructure.repositories.risk_repo import RiskRepositoryImpl
from src.infrastructure.repositories.sprint_repo import SprintRepositoryImpl
from src.infrastructure.repositories.standup_repo import (
    StandupResponseRepositoryImpl,
    StandupSessionRepositoryImpl,
)
from src.infrastructure.repositories.team_repo import TeamRepositoryImpl

# Services
from src.application.github_service import GitHubService
from src.application.report_service import ReportService
from src.application.risk_service import RiskService
from src.application.sprint_service import SprintService
from src.application.standup_service import StandupService
from src.application.valuelist_excel_service import ValuelistExcelService


class Container:
    """Contenedor de dependencias principal."""

    def __init__(self, settings, github_client, ai_client=None):
        """Inicializa los singletons y la configuración."""
        self.settings = settings
        self.github_client = github_client
        self.ai_client = ai_client

        # Servicios stateless (singletons lógicos)
        self.valuelist_svc = ValuelistExcelService(settings.excel_file_path)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provee una sesión con commit/rollback."""
        maker = get_async_session_maker()
        async with maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    class UnitOfWork:
        """Agrupa repositorios y servicios atados a una sesión."""
        
        def __init__(self, session: AsyncSession, container: Container):
            self.session = session
            
            # Repositorios
            self.team_repo = TeamRepositoryImpl(session)
            self.standup_repo = StandupSessionRepositoryImpl(session)
            self.response_repo = StandupResponseRepositoryImpl(session)
            self.member_repo = MemberRepositoryImpl(session)
            self.risk_repo = RiskRepositoryImpl(session)
            self.pr_repo = PullRequestRepositoryImpl(session)
            self.sprint_repo = SprintRepositoryImpl(session)
            self.metric_repo = MetricRepositoryImpl(session)

            # Servicios
            self.standup_svc = StandupService(
                self.standup_repo, self.response_repo, self.member_repo
            )
            self.github_svc = GitHubService(container.github_client, self.pr_repo)
            self.risk_svc = RiskService(
                self.risk_repo, self.pr_repo, self.response_repo, self.standup_repo
            )
            self.sprint_svc = SprintService(self.sprint_repo, self.metric_repo)
            self.report_svc = ReportService(
                self.standup_svc,
                self.github_svc,
                self.risk_svc,
                ai_client=container.ai_client,
                valuelist_service=container.valuelist_svc,
            )
            
            # Passthrough de singletons útiles
            self.valuelist_svc = container.valuelist_svc
            self.settings = container.settings

    @asynccontextmanager
    async def uow(self) -> AsyncGenerator[UnitOfWork, None]:
        """Inicia una Unidad de Trabajo (Transaction scope)."""
        async with self.session() as session:
            yield self.UnitOfWork(session, self)


# Singleton global
_container: Container | None = None


def init_container(settings, github_client, ai_client=None) -> Container:
    """Inicializa el contenedor global."""
    global _container
    _container = Container(settings, github_client, ai_client)
    return _container


def get_container() -> Container:
    """Obtiene el contenedor global."""
    if _container is None:
        raise RuntimeError("Contenedor no inicializado")
    return _container
