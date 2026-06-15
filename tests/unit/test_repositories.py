"""Módulo: test_repositories."""

import inspect
from pathlib import Path

import pytest

from src.domain.repositories import (
    MemberRepository,
    MetricRepository,
    PullRequestRepository,
    RiskRepository,
    SprintRepository,
    StandupResponseRepository,
    StandupSessionRepository,
    TeamRepository,
)

REPOSITORIES = [
    TeamRepository,
    MemberRepository,
    StandupSessionRepository,
    StandupResponseRepository,
    PullRequestRepository,
    SprintRepository,
    RiskRepository,
    MetricRepository,
]


@pytest.mark.parametrize("repo_class", REPOSITORIES)
def test_repository_is_abstract(repo_class) -> None:
    """Cada repositorio es una clase abstracta que no puede instanciarse."""
    assert inspect.isabstract(repo_class)
    with pytest.raises(TypeError):
        repo_class()


@pytest.mark.parametrize("repo_class", REPOSITORIES)
def test_repository_methods_are_async_and_abstract(repo_class) -> None:
    """Todos los métodos públicos son async y abstractmethod."""
    for name, method in inspect.getmembers(repo_class, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        assert inspect.iscoroutinefunction(method), f"{repo_class.__name__}.{name} no es async"
        assert getattr(method, "__isabstractmethod__", False), f"{repo_class.__name__}.{name} no es abstractmethod"


def test_repositories_module_has_no_sqlalchemy_imports() -> None:
    """El módulo de puertos no debe depender de SQLAlchemy."""
    source = (Path(__file__).resolve().parent.parent.parent / "src" / "domain" / "repositories.py").read_text(
        encoding="utf-8"
    )
    assert "sqlalchemy" not in source
    assert "from src.domain.models import" in source
