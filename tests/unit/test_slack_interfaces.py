"""Módulo: test_slack_interfaces."""

import json

from slack_bolt.async_app import AsyncApp

from src.interfaces.slack.bolt_app import register_handlers
from src.interfaces.slack.modals import build_standup_modal
from src.interfaces.slack.template_loader import (
    build_crear_tarea_modal,
    build_avance_modal,
    build_avance_individual_modal,
)


def test_build_standup_modal_structure() -> None:
    """El modal tiene la estructura esperada."""
    modal = build_standup_modal()
    assert modal["type"] == "modal"
    assert modal["callback_id"] == "standup_submission"
    # Verificamos los inputs esenciales en lugar de un conteo fijo de bloques,
    # ya que el modal puede incluir bloques de contexto/divisores opcionales.
    input_block_ids = [
        b.get("block_id") for b in modal["blocks"] if b.get("type") == "input"
    ]
    assert "yesterday_block" in input_block_ids
    assert "today_block" in input_block_ids
    assert "blockers_block" in input_block_ids


def test_build_standup_modal_with_tasks_has_completed_checkboxes() -> None:
    """Con tareas activas, el modal ofrece marcar las completadas."""
    tasks = [
        {"id": "A1.1", "desc": "Backend", "progress": 0.5, "estado": "EN CURSO"},
        {"id": "A1.2", "desc": "Ya lista", "progress": 1.0, "estado": "COMPLETADO"},
    ]
    modal = build_standup_modal(tasks)
    completed = [b for b in modal["blocks"] if b.get("block_id") == "completed_block"]
    assert len(completed) == 1
    values = [o["value"] for o in completed[0]["element"]["options"]]
    assert "A1.1" in values        # incompleta: se puede marcar
    assert "A1.2" not in values    # ya completada: no se ofrece


def test_register_handlers_does_not_raise() -> None:
    """El registro de handlers no lanza excepciones."""
    app = AsyncApp(token="xoxb-test", signing_secret="test")
    class FakeSession:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def commit(self): pass

    services = {
        "session_maker": lambda: FakeSession(),
        "github_client": None,
        "default_team_id": "00000000-0000-0000-0000-000000000000",
        "default_channel_id": "C000",
    }
    register_handlers(app, services)
    assert app is not None


def test_crear_tarea_modal_has_hint_and_placeholder() -> None:
    modal = build_crear_tarea_modal([{"id": "OE1", "desc": "Objetivo"}])
    blob = json.dumps(modal, ensure_ascii=False)
    assert "se genera automáticamente" in blob
    desc = next(b for b in modal["blocks"] if b.get("block_id") == "desc_block")
    assert "placeholder" in desc["element"]


def test_avance_individual_modal_notes_completion() -> None:
    modal = build_avance_individual_modal("A1.1", 0.5)
    blob = json.dumps(modal, ensure_ascii=False)
    assert "100%" in blob
    assert "COMPLETADO" in blob


def test_avance_modal_input_has_placeholder() -> None:
    options = [{"text": {"type": "plain_text", "text": "A1.1"}, "value": "tarea|A1.1"}]
    modal = build_avance_modal(options)
    prog = next(b for b in modal["blocks"] if b.get("block_id") == "progress_block")
    assert "placeholder" in prog["element"]
