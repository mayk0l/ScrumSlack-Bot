"""Módulo: test_presentation."""

from src.domain.models import Severity
from src.interfaces.slack import presentation as pres


def test_severity_label_from_enum_and_string():
    assert pres.severity_label(Severity.HIGH) == "🟠 ALTA"
    assert pres.severity_label(Severity.CRITICAL) == "🔴 CRÍTICA"
    assert pres.severity_label("low") == "🟢 BAJA"
    assert pres.severity_label("medium") == "🟡 MEDIA"
    # Valor desconocido: no rompe, lo muestra en mayúsculas.
    assert pres.severity_label("weird") == "⚪ WEIRD"


def test_status_emoji():
    assert pres.status_emoji("EN CURSO") == "🟡"
    assert pres.status_emoji("completado") == "✅"
    assert pres.status_emoji("NO COMENZADO") == "⬜"
    assert pres.status_emoji("BLOQUEADO") == "🔴"
    assert pres.status_emoji("otro") == "•"


def test_progress_bar():
    assert pres.progress_bar(0.0) == "░" * 10
    assert pres.progress_bar(1.0) == "█" * 10
    assert pres.progress_bar(0.5) == "█" * 5 + "░" * 5
    assert pres.progress_bar(None) == "░" * 10
    # Se recorta fuera de rango.
    assert pres.progress_bar(2.0) == "█" * 10


def test_block_builders():
    assert pres.header("Hola")["type"] == "header"
    assert pres.section("*x*")["text"]["type"] == "mrkdwn"
    assert pres.context("nota")["type"] == "context"
    assert pres.divider() == {"type": "divider"}
    # El header recorta a 150 chars.
    assert len(pres.header("a" * 200)["text"]["text"]) == 150
