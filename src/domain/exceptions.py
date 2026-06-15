"""Módulo: exceptions.

Excepciones tipadas para errores de negocio del dominio.
"""

from __future__ import annotations


class DomainException(Exception):
    """Base para excepciones de dominio."""


class EntityNotFoundError(DomainException):
    """Entidad no encontrada."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} con id '{entity_id}' no encontrado")


class StandupAlreadyRespondedError(DomainException):
    """El miembro ya respondió el standup de hoy."""

    def __init__(self, message: str = "El miembro ya respondió el standup de hoy.") -> None:
        super().__init__(message)


class SprintNotActiveError(DomainException):
    """No hay sprint activo."""

    def __init__(self, message: str = "No hay sprint activo.") -> None:
        super().__init__(message)


class InvalidConfigurationError(DomainException):
    """Configuración inválida."""

    def __init__(self, message: str = "Configuración inválida.") -> None:
        super().__init__(message)


class ExternalServiceError(DomainException):
    """Error en servicio externo (GitHub, Slack, OpenRouter)."""

    def __init__(self, service: str, detail: str) -> None:
        self.service = service
        super().__init__(f"Error en {service}: {detail}")
