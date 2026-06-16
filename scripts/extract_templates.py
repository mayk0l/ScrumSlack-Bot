import os
import json

base_dir = "src/interfaces/slack/templates"
os.makedirs(base_dir, exist_ok=True)

# 1. standup_modal.json
standup = {
    "type": "modal",
    "callback_id": "standup_submission",
    "title": {"type": "plain_text", "text": "Daily Standup"},
    "submit": {"type": "plain_text", "text": "Enviar"},
    "blocks": [
        {
            "type": "input",
            "block_id": "yesterday_block",
            "label": {"type": "plain_text", "text": "¿Qué hiciste ayer?"},
            "element": {"type": "plain_text_input", "action_id": "yesterday_input", "multiline": True},
        },
        {
            "type": "input",
            "block_id": "today_block",
            "label": {"type": "plain_text", "text": "¿Qué harás hoy?"},
            "element": {"type": "plain_text_input", "action_id": "today_input", "multiline": True},
        },
        {
            "type": "input",
            "block_id": "blockers_block",
            "label": {"type": "plain_text", "text": "¿Tienes bloqueos?"},
            "element": {"type": "plain_text_input", "action_id": "blockers_input", "multiline": True},
            "optional": True,
        },
    ],
}
with open(f"{base_dir}/standup_modal.json", "w", encoding="utf-8") as f:
    json.dump(standup, f, indent=4, ensure_ascii=False)


# 2. crear_tarea_modal.json
crear_tarea = {
    "type": "modal",
    "callback_id": "crear_tarea_submission",
    "title": {"type": "plain_text", "text": "Crear Tarea"},
    "submit": {"type": "plain_text", "text": "Guardar"},
    "blocks": [
        {
            "type": "input",
            "block_id": "id_block",
            "label": {"type": "plain_text", "text": "ID Tarea (Ej. A2.5)"},
            "element": {"type": "plain_text_input", "action_id": "id_input"},
        },
        {
            "type": "input",
            "block_id": "desc_block",
            "label": {"type": "plain_text", "text": "Descripción"},
            "element": {"type": "plain_text_input", "action_id": "desc_input"},
        },
        {
            "type": "input",
            "block_id": "resp_block",
            "label": {"type": "plain_text", "text": "Responsable"},
            "element": {"type": "users_select", "action_id": "resp_input"},
        },
        {
            "type": "input",
            "block_id": "start_block",
            "label": {"type": "plain_text", "text": "Fecha Inicio (YYYY-MM-DD)"},
            "element": {"type": "plain_text_input", "action_id": "start_input"},
        },
        {
            "type": "input",
            "block_id": "end_block",
            "label": {"type": "plain_text", "text": "Fecha Fin (YYYY-MM-DD)"},
            "element": {"type": "plain_text_input", "action_id": "end_input"},
        },
    ],
}
with open(f"{base_dir}/crear_tarea_modal.json", "w", encoding="utf-8") as f:
    json.dump(crear_tarea, f, indent=4, ensure_ascii=False)


# 3. editar_selector_modal.json
editar_selector = {
    "type": "modal",
    "callback_id": "editar_selector_submission",
    "title": {"type": "plain_text", "text": "Centro de Edición"},
    "submit": {"type": "plain_text", "text": "Siguiente"},
    "blocks": [
        {
            "type": "input",
            "block_id": "seleccion_block",
            "label": {"type": "plain_text", "text": "¿Qué elemento deseas editar?"},
            "element": {
                "type": "static_select",
                "action_id": "seleccion_input",
                "option_groups": [] # Injected via code
            }
        }
    ]
}
with open(f"{base_dir}/editar_selector_modal.json", "w", encoding="utf-8") as f:
    json.dump(editar_selector, f, indent=4, ensure_ascii=False)


# 4. editar_tarea_modal.json
editar_tarea = {
    "type": "modal",
    "callback_id": "editar_tarea_submission",
    "private_metadata": "{task_id}",
    "title": {"type": "plain_text", "text": "Editar {task_id}"},
    "submit": {"type": "plain_text", "text": "Guardar"},
    "blocks": [
        {
            "type": "input",
            "block_id": "desc_block",
            "label": {"type": "plain_text", "text": "Descripción"},
            "element": {"type": "plain_text_input", "action_id": "desc_input", "initial_value": "{task_desc}"},
        },
        {
            "type": "input",
            "block_id": "resp_block",
            "label": {"type": "plain_text", "text": "Responsable"},
            "element": {"type": "users_select", "action_id": "resp_input"},
        },
        {
            "type": "input",
            "block_id": "start_block",
            "label": {"type": "plain_text", "text": "Fecha Inicio (YYYY-MM-DD)"},
            "element": {"type": "plain_text_input", "action_id": "start_input", "initial_value": "{task_start}"},
        },
        {
            "type": "input",
            "block_id": "end_block",
            "label": {"type": "plain_text", "text": "Fecha Fin (YYYY-MM-DD)"},
            "element": {"type": "plain_text_input", "action_id": "end_input", "initial_value": "{task_end}"},
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
                    {"text": {"type": "plain_text", "text": "🗑️ Eliminar esta tarea"}, "value": "delete"}
                ]
            }
        }
    ],
}
with open(f"{base_dir}/editar_tarea_modal.json", "w", encoding="utf-8") as f:
    json.dump(editar_tarea, f, indent=4, ensure_ascii=False)


# 5. editar_bitacora_modal.json
editar_bitacora = {
    "type": "modal",
    "callback_id": "editar_bitacora_submission",
    "private_metadata": "{obj_id}",
    "title": {"type": "plain_text", "text": "Editar {obj_id}"},
    "submit": {"type": "plain_text", "text": "Guardar"},
    "blocks": [
        {
            "type": "input",
            "block_id": "desc_block",
            "label": {"type": "plain_text", "text": "Descripción"},
            "element": {
                "type": "plain_text_input", 
                "action_id": "desc_input", 
                "initial_value": "{current_desc}",
                "multiline": True
            },
        }
    ],
}
with open(f"{base_dir}/editar_bitacora_modal.json", "w", encoding="utf-8") as f:
    json.dump(editar_bitacora, f, indent=4, ensure_ascii=False)

print("JSON templates created.")
