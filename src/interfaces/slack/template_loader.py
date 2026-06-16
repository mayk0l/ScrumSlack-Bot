import json
import os
import copy
from typing import Any

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def load_template(filename: str) -> dict[str, Any]:
    with open(os.path.join(TEMPLATE_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

def _replace_placeholders(obj: Any, replacements: dict[str, str]) -> Any:
    if isinstance(obj, str):
        for k, v in replacements.items():
            obj = obj.replace(f"{{{k}}}", str(v))
        return obj
    elif isinstance(obj, dict):
        return {k: _replace_placeholders(v, replacements) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_placeholders(i, replacements) for i in obj]
    return obj

def build_standup_modal() -> dict[str, Any]:
    return load_template("standup_modal.json")

def build_crear_tarea_modal() -> dict[str, Any]:
    return load_template("crear_tarea_modal.json")

def build_editar_selector_modal(grouped_options: dict) -> dict[str, Any]:
    template = load_template("editar_selector_modal.json")
    option_groups = []
    
    if grouped_options.get("tareas"):
        option_groups.append({
            "label": {"type": "plain_text", "text": "Tareas"},
            "options": grouped_options["tareas"][:100]
        })
        
    if grouped_options.get("bitacora"):
        option_groups.append({
            "label": {"type": "plain_text", "text": "Bitácora"},
            "options": grouped_options["bitacora"][:100]
        })
        
    if not option_groups:
        option_groups.append({
            "label": {"type": "plain_text", "text": "Vacío"},
            "options": [{"text": {"type": "plain_text", "text": "No hay elementos editables"}, "value": "none|none"}]
        })
        
    template["blocks"][0]["element"]["option_groups"] = option_groups
    return template

def build_editar_tarea_modal(task: dict) -> dict[str, Any]:
    template = load_template("editar_tarea_modal.json")
    replacements = {
        "task_id": task.get("id", ""),
        "task_desc": task.get("desc", ""),
        "task_start": task.get("start", ""),
        "task_end": task.get("end", "")
    }
    return _replace_placeholders(template, replacements)

def build_editar_bitacora_modal(obj_id: str, current_desc: str) -> dict[str, Any]:
    template = load_template("editar_bitacora_modal.json")
    replacements = {
        "obj_id": obj_id,
        "current_desc": current_desc
    }
    return _replace_placeholders(template, replacements)
