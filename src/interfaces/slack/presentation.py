"""Módulo: presentation.

Helpers de presentación para Slack: builders de Block Kit y un lenguaje
visual único (severidades, estados, barras de progreso). Centralizar esto
evita mensajes inconsistentes entre comandos y mantiene el `mrkdwn` válido
(Slack no soporta encabezados Markdown `#` ni `**`; usa `*negrita*`).
"""

from __future__ import annotations

from typing import Any

# Severidad de riesgo → (emoji, etiqueta en español).
SEVERITY_PRESENTATION = {
    "low": ("🟢", "BAJA"),
    "medium": ("🟡", "MEDIA"),
    "high": ("🟠", "ALTA"),
    "critical": ("🔴", "CRÍTICA"),
}

# Estado de tarea → emoji (semáforo coherente con el Excel).
STATUS_EMOJI = {
    "NO COMENZADO": "⬜",
    "EN CURSO": "🟡",
    "COMPLETADO": "✅",
    "BLOQUEADO": "🔴",
}


def severity_label(severity: Any) -> str:
    """Devuelve '🟠 ALTA' a partir de un enum Severity o un string."""
    key = str(getattr(severity, "value", severity)).strip().lower()
    emoji, text = SEVERITY_PRESENTATION.get(key, ("⚪", key.upper()))
    return f"{emoji} {text}"


def status_emoji(estado: Any) -> str:
    """Emoji para un estado de tarea."""
    return STATUS_EMOJI.get(str(estado).strip().upper(), "•")


def progress_bar(fraction: float, width: int = 10) -> str:
    """Barra de progreso de ancho fijo a partir de una fracción 0-1."""
    try:
        value = float(fraction or 0.0)
    except (TypeError, ValueError):
        value = 0.0
    value = max(0.0, min(1.0, value))
    filled = int(round(value * width))
    return "█" * filled + "░" * (width - filled)


# --- Builders de Block Kit ---

def header(text: str) -> dict:
    """Bloque header (texto plano, máx. 150 chars)."""
    return {"type": "header", "text": {"type": "plain_text", "text": text[:150], "emoji": True}}


def section(mrkdwn_text: str) -> dict:
    """Bloque section con texto mrkdwn."""
    return {"type": "section", "text": {"type": "mrkdwn", "text": mrkdwn_text}}


def context(mrkdwn_text: str) -> dict:
    """Bloque context (texto secundario)."""
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": mrkdwn_text}]}


def divider() -> dict:
    """Separador."""
    return {"type": "divider"}
