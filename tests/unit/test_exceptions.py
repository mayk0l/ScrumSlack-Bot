"""Módulo: test_exceptions."""

import pytest

from src.domain.exceptions import (
    DomainException,
    EntityNotFoundError,
    ExternalServiceError,
    InvalidConfigurationError,
    SprintNotActiveError,
    StandupAlreadyRespondedError,
)


@pytest.mark.parametrize(
    "exception_class, args",
    [
        (EntityNotFoundError, ("Team", "123")),
        (StandupAlreadyRespondedError, ()),
        (SprintNotActiveError, ()),
        (InvalidConfigurationError, ()),
        (ExternalServiceError, ("GitHub", "rate limit")),
    ],
)
def test_exceptions_are_domain_exceptions(exception_class, args) -> None:
    """Todas las excepciones heredan de DomainException."""
    exc = exception_class(*args)
    assert isinstance(exc, DomainException)


def test_entity_not_found_error_message_and_attributes() -> None:
    """EntityNotFoundError guarda tipo, id y genera mensaje claro."""
    exc = EntityNotFoundError("Member", "abc-123")
    assert exc.entity_type == "Member"
    assert exc.entity_id == "abc-123"
    assert "Member con id 'abc-123' no encontrado" in str(exc)


def test_external_service_error_message_and_attributes() -> None:
    """ExternalServiceError guarda servicio y detalle."""
    exc = ExternalServiceError("Slack", "timeout")
    assert exc.service == "Slack"
    assert "Error en Slack: timeout" in str(exc)


def test_simple_exceptions_have_default_messages() -> None:
    """Excepciones sin constructor personalizado tienen docstring como mensaje."""
    assert "El miembro ya respondió el standup de hoy" in str(StandupAlreadyRespondedError())
    assert "No hay sprint activo" in str(SprintNotActiveError())
    assert "Configuración inválida" in str(InvalidConfigurationError())
