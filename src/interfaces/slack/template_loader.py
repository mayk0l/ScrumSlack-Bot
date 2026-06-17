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

def build_crear_tarea_modal(oes: list[dict[str, str]] = None) -> dict[str, Any]:
    """Genera el modal de crear tarea dinámicamente con las opciones de OE."""
    if oes is None:
        oes = []
        
    oe_options = []
    for oe in oes:
        desc = oe['desc'][:50] + "..." if len(oe['desc']) > 50 else oe['desc']
        oe_options.append({
            "text": {"type": "plain_text", "text": f"{oe['id']} - {desc}"},
            "value": oe["id"]
        })
        
    oe_options.append({
        "text": {"type": "plain_text", "text": "Administración (AD)"},
        "value": "AD"
    })
    
    if not oes:
        oe_options.insert(0, {
            "text": {"type": "plain_text", "text": "General (A)"},
            "value": "A"
        })

    return {
        "type": "modal",
        "callback_id": "crear_tarea_submission",
        "title": {"type": "plain_text", "text": "Crear Tarea"},
        "submit": {"type": "plain_text", "text": "Guardar"},
        "blocks": [
            {
                "type": "input",
                "block_id": "oe_block",
                "label": {"type": "plain_text", "text": "Objetivo Asociado"},
                "element": {
                    "type": "static_select",
                    "action_id": "oe_input",
                    "options": oe_options,
                    "initial_option": oe_options[0]
                }
            },
            {
                "type": "input",
                "block_id": "desc_block",
                "label": {"type": "plain_text", "text": "Descripción (resumen)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "desc_input"
                }
            },
            {
                "type": "input",
                "block_id": "resp_block",
                "label": {"type": "plain_text", "text": "Responsable"},
                "element": {
                    "type": "users_select",
                    "action_id": "resp_input"
                }
            },
            {
                "type": "input",
                "block_id": "start_block",
                "label": {"type": "plain_text", "text": "Fecha Inicio"},
                "element": {
                    "type": "datepicker",
                    "action_id": "start_input",
                    "placeholder": {"type": "plain_text", "text": "Selecciona fecha"}
                }
            },
            {
                "type": "input",
                "block_id": "end_block",
                "label": {"type": "plain_text", "text": "Fecha Fin Esperado"},
                "element": {
                    "type": "datepicker",
                    "action_id": "end_input",
                    "placeholder": {"type": "plain_text", "text": "Selecciona fecha"}
                }
            },
            {
                "type": "input",
                "block_id": "entregable_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "Entregable"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "entregable_input"
                }
            },
            {
                "type": "input",
                "block_id": "comentarios_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "Comentarios"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "comentarios_input",
                    "multiline": True
                }
            }
        ]
    }

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
    """Genera dinámicamente el modal para editar una tarea."""
    start_element = {
        "type": "datepicker",
        "action_id": "start_input",
        "placeholder": {"type": "plain_text", "text": "Selecciona fecha"}
    }
    if task.get("start"):
        start_element["initial_date"] = task.get("start")[:10]
        
    end_element = {
        "type": "datepicker",
        "action_id": "end_input",
        "placeholder": {"type": "plain_text", "text": "Selecciona fecha"}
    }
    if task.get("end"):
        end_element["initial_date"] = task.get("end")[:10]

    return {
        "type": "modal",
        "callback_id": "editar_tarea_submission",
        "private_metadata": task.get("id", ""),
        "title": {
            "type": "plain_text",
            "text": f"Editar {task.get('id', '')}"
        },
        "submit": {
            "type": "plain_text",
            "text": "Guardar"
        },
        "blocks": [
            {
                "type": "input",
                "block_id": "desc_block",
                "label": {"type": "plain_text", "text": "Descripción (resumen)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "desc_input",
                    "initial_value": task.get("desc", "")
                }
            },
            {
                "type": "input",
                "block_id": "resp_block",
                "label": {"type": "plain_text", "text": "Responsable"},
                "element": {
                    "type": "users_select",
                    "action_id": "resp_input"
                }
            },
            {
                "type": "input",
                "block_id": "start_block",
                "label": {"type": "plain_text", "text": "Fecha Inicio"},
                "element": start_element
            },
            {
                "type": "input",
                "block_id": "end_block",
                "label": {"type": "plain_text", "text": "Fecha Fin Esperado"},
                "element": end_element
            },
            {
                "type": "input",
                "block_id": "entregable_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "Entregable"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "entregable_input",
                    "initial_value": task.get("entregable", "")
                }
            },
            {
                "type": "input",
                "block_id": "comentarios_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "Comentarios"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "comentarios_input",
                    "multiline": True,
                    "initial_value": task.get("comentarios", "")
                }
            },
            {
                "type": "input",
                "block_id": "delete_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "Opciones de Peligro"},
                "element": {
                    "type": "checkboxes",
                    "action_id": "delete_input",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "🗑️ Eliminar esta tarea"
                            },
                            "value": "delete"
                        }
                    ]
                }
            }
        ]
    }

def build_bitacora_completa_modal(bitacora: dict[str, Any]) -> dict[str, Any]:
    """Genera dinámicamente un modal con todos los objetivos."""
    blocks = []
    
    # Nombre del Proyecto
    blocks.append({
        "type": "input",
        "block_id": "proyecto_block",
        "label": {"type": "plain_text", "text": "Nombre del Proyecto"},
        "element": {
            "type": "plain_text_input",
            "action_id": "proyecto_input",
            "initial_value": bitacora.get("proyecto", ""),
            "multiline": False
        }
    })
    
    # Objetivo General
    blocks.append({
        "type": "input",
        "block_id": "og_block",
        "label": {"type": "plain_text", "text": "Objetivo General (OG)"},
        "element": {
            "type": "plain_text_input",
            "action_id": "og_input",
            "initial_value": bitacora.get("og", ""),
            "multiline": True
        }
    })
    
    # Objetivos Específicos (OEs)
    for oe in bitacora.get("oe", []):
        blocks.append({
            "type": "input",
            "block_id": f"oe_{oe['id']}_block",
            "optional": True,
            "label": {"type": "plain_text", "text": oe["id"] + " (Borra el texto para eliminar)"},
            "element": {
                "type": "plain_text_input",
                "action_id": f"{oe['id']}_input",
                "initial_value": oe["desc"],
                "multiline": True
            }
        })
        
    # Campo para agregar uno nuevo
    blocks.append({
        "type": "input",
        "block_id": "nuevo_oe_block",
        "optional": True,
        "label": {"type": "plain_text", "text": "➕ Agregar Nuevo Objetivo Específico"},
        "element": {
            "type": "plain_text_input",
            "action_id": "nuevo_oe_input",
            "multiline": True,
            "placeholder": {"type": "plain_text", "text": "Escribe un nuevo OE aquí..."}
        }
    })
    
    return {
        "type": "modal",
        "callback_id": "bitacora_completa_submission",
        "title": {"type": "plain_text", "text": "Editar Bitácora"},
        "submit": {"type": "plain_text", "text": "Guardar Todo"},
        "blocks": blocks
    }

def build_avance_modal(tareas: list[dict[str, Any]]) -> dict[str, Any]:
    if not tareas:
        tareas = [{"text": {"type": "plain_text", "text": "No hay tareas activas"}, "value": "none"}]
    return {
        "type": "modal",
        "callback_id": "avance_submission",
        "title": {"type": "plain_text", "text": "Registrar Avance"},
        "submit": {"type": "plain_text", "text": "Guardar"},
        "blocks": [
            {
                "type": "input",
                "block_id": "task_block",
                "label": {"type": "plain_text", "text": "Selecciona la Tarea"},
                "element": {
                    "type": "static_select",
                    "action_id": "task_input",
                    "placeholder": {"type": "plain_text", "text": "Elige una tarea"},
                    "options": tareas[:100]
                }
            },
            {
                "type": "input",
                "block_id": "progress_block",
                "label": {"type": "plain_text", "text": "Porcentaje de Avance (0 a 100)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "progress_input"
                }
            }
        ]
    }
