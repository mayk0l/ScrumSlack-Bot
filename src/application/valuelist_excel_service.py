import asyncio
import openpyxl
from typing import Any

class ValuelistExcelService:
    """
    Servicio para sincronizar y leer datos directamente desde 
    la Bitácora de Rentabilidad de Valuelist (Excel).
    """

    def __init__(self, excel_path: str):
        self._excel_path = excel_path

    async def get_my_tasks(self, target_name: str) -> list[dict[str, Any]]:
        """Busca las tareas asignadas al usuario en la Hoja 3 (Planificación)."""
        if not target_name:
            return []

        def _read() -> list[dict[str, Any]]:
            try:
                wb = openpyxl.load_workbook(self._excel_path, data_only=True)
                ws = wb["Planificación"]
                tasks = []
                for row in ws.iter_rows(min_row=2, values_only=True):
                    # Cols: 0=Act, 1=Desc, 2=Resp, 3=Inicio, 4=Fin, 5=%esp, 6=%logro
                    act_id = row[0]
                    resp = row[2]
                    
                    if act_id and str(act_id).startswith("A") and resp == target_name:
                        tasks.append({
                            "id": str(act_id),
                            "desc": str(row[1]) if row[1] else "",
                            "progress": float(row[6]) if row[6] is not None else 0.0
                        })
                return tasks
            except Exception:
                return []

        return await asyncio.to_thread(_read)

    async def get_bitacora_summary(self) -> dict[str, Any]:
        """Lee el OG y los OE de la Hoja 1 (Bitácora)."""
        def _read() -> dict[str, Any]:
            try:
                wb = openpyxl.load_workbook(self._excel_path, data_only=True)
                ws = wb["Bitácora"]
                
                summary = {"proyecto": "", "og": "", "oe": []}
                
                for row in ws.iter_rows(min_row=2, values_only=True):
                    col_b = row[1]
                    col_c = row[2]
                    if not col_b:
                        continue
                        
                    b_str = str(col_b).strip().upper()
                    c_str = str(col_c).strip() if col_c else ""
                    
                    if b_str == "PROYECTO":
                        summary["proyecto"] = c_str
                    elif b_str == "OG":
                        summary["og"] = c_str
                    elif b_str.startswith("OE"):
                        # Keep even if empty so it can be edited/deleted
                        summary["oe"].append({"id": b_str, "desc": c_str})
                            
                return summary
            except Exception:
                return {"proyecto": "", "og": "", "oe": []}

        return await asyncio.to_thread(_read)

    async def update_task_progress(self, task_id: str, progress: float) -> bool:
        """Actualiza el porcentaje de logro de una tarea en Planificación o Administración."""
        def _write() -> bool:
            try:
                wb = openpyxl.load_workbook(self._excel_path)
                for sheet_name in ["Planificación", "Administración"]:
                    ws = wb[sheet_name]
                    for row in ws.iter_rows(min_row=2):
                        if row[0].value and str(row[0].value) == task_id:
                            row[6].value = progress
                            wb.save(self._excel_path)
                            return True
                return False
            except Exception:
                return False

        return await asyncio.to_thread(_write)

    async def add_evidence(self, task_id: str, url: str) -> bool:
        """Añade un enlace de evidencia a la Hoja 5."""
        def _write() -> bool:
            try:
                wb = openpyxl.load_workbook(self._excel_path)
                
                # Primero buscar la descripción en Planificación
                ws_plan = wb["Planificación"]
                desc = ""
                for row in ws_plan.iter_rows(min_row=2):
                    cell_id = row[0]
                    if cell_id.value and str(cell_id.value) == task_id:
                        desc = str(row[1].value) if row[1].value else ""
                        break
                        
                if not desc:
                    return False
                    
                ws_evi = wb["Evidencia"]
                ws_evi.append([task_id, desc, url])
                wb.save(self._excel_path)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_write)

    async def create_task(self, act_id: str, desc: str, resp: str, start: str, end: str) -> bool:
        """Agrega una nueva fila al final de la hoja correspondiente."""
        def _write() -> bool:
            try:
                wb = openpyxl.load_workbook(self._excel_path)
                sheet_name = "Administración" if act_id.upper().startswith("AD") else "Planificación"
                ws = wb[sheet_name]
                
                # Encontrar la primera fila libre en la columna A
                last_row = 1
                for i in range(2, ws.max_row + 2):
                    if not ws.cell(row=i, column=1).value:
                        last_row = i
                        break
                
                from datetime import datetime
                try:
                    start_dt = datetime.strptime(start, "%Y-%m-%d")
                    end_dt = datetime.strptime(end, "%Y-%m-%d")
                except ValueError:
                    start_dt = start
                    end_dt = end

                ws.cell(row=last_row, column=1).value = act_id
                ws.cell(row=last_row, column=2).value = desc
                ws.cell(row=last_row, column=3).value = resp
                ws.cell(row=last_row, column=4).value = start_dt
                ws.cell(row=last_row, column=5).value = end_dt
                ws.cell(row=last_row, column=6).value = "NO COMENZADO"
                ws.cell(row=last_row, column=7).value = 0.0
                
                wb.save(self._excel_path)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_write)

    async def generate_gantt(self) -> str:
        """Genera un diagrama Mermaid a partir de las fechas en la Hoja 3."""
        def _read() -> str:
            try:
                wb = openpyxl.load_workbook(self._excel_path, data_only=True)
                ws = wb["Planificación"]
                
                lines = [
                    "```mermaid",
                    "gantt",
                    "    title Cronograma de Planificación (Excel)",
                    "    dateFormat  YYYY-MM-DD",
                    "    axisFormat  %d-%b"
                ]
                
                for row in ws.iter_rows(min_row=2):
                    act_id = row[0].value
                    desc = row[1].value
                    start = row[3].value
                    end = row[4].value
                    
                    if act_id and str(act_id).startswith("A") and start and end:
                        # Clean dates if they are datetime objects
                        from datetime import datetime
                        if isinstance(start, datetime): start_str = start.strftime("%Y-%m-%d")
                        else: start_str = str(start)[:10]
                        
                        if isinstance(end, datetime): end_str = end.strftime("%Y-%m-%d")
                        else: end_str = str(end)[:10]
                        
                        safe_desc = str(desc).replace(":", "") if desc else "Tarea"
                        lines.append(f"    {act_id} {safe_desc[:30]} : {act_id}, {start_str}, {end_str}")
                        
                if len(lines) == 5:
                    return "⚠️ No hay tareas con fechas de inicio y fin en la Planificación para graficar."
                    
                lines.append("```")
                return "\n".join(lines)
            except Exception as e:
                return f"Error generando Gantt: {e}"

        return await asyncio.to_thread(_read)

    async def get_task_by_id(self, task_id: str) -> dict[str, Any] | None:
        """Busca una tarea en Hoja 3 o Hoja 4 y devuelve sus detalles actuales."""
        def _read() -> dict[str, Any] | None:
            try:
                wb = openpyxl.load_workbook(self._excel_path, data_only=True)
                
                for sheet_name in ["Planificación", "Administración"]:
                    ws = wb[sheet_name]
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        act_id = row[0]
                        if act_id and str(act_id) == task_id:
                            from datetime import datetime
                            def _format_date(d):
                                if isinstance(d, datetime): return d.strftime("%Y-%m-%d")
                                return str(d)[:10] if d else ""
                                
                            return {
                                "id": str(act_id),
                                "desc": str(row[1]) if row[1] else "",
                                "resp": str(row[2]) if row[2] else "",
                                "start": _format_date(row[3]),
                                "end": _format_date(row[4])
                            }
                return None
            except Exception:
                return None

        return await asyncio.to_thread(_read)

    async def update_task_details(self, task_id: str, desc: str, resp: str, start: str, end: str) -> bool:
        """Sobrescribe los detalles de una tarea existente en Hoja 3 o 4."""
        def _write() -> bool:
            try:
                wb = openpyxl.load_workbook(self._excel_path)
                
                from datetime import datetime
                try:
                    start_dt = datetime.strptime(start, "%Y-%m-%d")
                    end_dt = datetime.strptime(end, "%Y-%m-%d")
                except ValueError:
                    start_dt = start
                    end_dt = end
                
                for sheet_name in ["Planificación", "Administración"]:
                    ws = wb[sheet_name]
                    for row in ws.iter_rows(min_row=2):
                        cell_id = row[0]
                        if cell_id.value and str(cell_id.value) == task_id:
                            row[1].value = desc
                            row[2].value = resp
                            row[3].value = start_dt
                            row[4].value = end_dt
                            wb.save(self._excel_path)
                            return True
                return False
            except Exception:
                return False

        return await asyncio.to_thread(_write)

    async def delete_task_by_id(self, task_id: str) -> bool:
        """Elimina una fila de la Hoja 3 o 4."""
        def _write() -> bool:
            try:
                wb = openpyxl.load_workbook(self._excel_path)
                
                for sheet_name in ["Planificación", "Administración"]:
                    ws = wb[sheet_name]
                    for row in ws.iter_rows(min_row=2):
                        cell_id = row[0]
                        if cell_id.value and str(cell_id.value) == task_id:
                            ws.delete_rows(cell_id.row)
                            wb.save(self._excel_path)
                            return True
                return False
            except Exception:
                return False

        return await asyncio.to_thread(_write)

    async def update_bitacora_full(self, updates: dict[str, str], new_oe: str = "") -> bool:
        """Actualiza todos los objetivos de la Bitácora dinámicamente, agrega un nuevo OE si se provee, y aplica estilos."""
        def _write() -> bool:
            try:
                wb = openpyxl.load_workbook(self._excel_path)
                ws = wb["Bitácora"]
                
                from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
                header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True, size=12)
                bold_font = Font(bold=True)
                align_center = Alignment(horizontal="center", vertical="center")
                align_left = Alignment(horizontal="left", vertical="top", wrap_text=True)
                thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                                     top=Side(style='thin'), bottom=Side(style='thin'))

                # 1. Extract current data in case something is missing in updates
                current_data = {"PROYECTO": "", "OG": ""}
                oes = []
                for r in range(2, ws.max_row + 1):
                    b = ws.cell(row=r, column=2).value
                    c = ws.cell(row=r, column=3).value
                    if b:
                        b_str = str(b).strip().upper()
                        c_str = str(c).strip() if c else ""
                        if b_str in ["PROYECTO", "OG"]:
                            current_data[b_str] = c_str
                        elif b_str.startswith("OE"):
                            oes.append({"id": b_str, "desc": c_str})
                
                # 2. Apply updates
                if "PROYECTO" in updates: current_data["PROYECTO"] = updates["PROYECTO"]
                if "OG" in updates: current_data["OG"] = updates["OG"]
                
                new_oes = []
                for oe in oes:
                    oe_id = oe["id"]
                    if oe_id in updates:
                        desc = str(updates[oe_id]).strip()
                        if desc: # If not empty, we keep it
                            new_oes.append({"id": oe_id, "desc": desc})
                    else:
                        if oe["desc"]: # Keep if it had text
                            new_oes.append(oe)
                            
                # 3. Add new OE if provided
                if new_oe.strip():
                    last_num = 0
                    for oe in new_oes:
                        try:
                            num = int(oe["id"].replace("OE", "").strip())
                            last_num = max(last_num, num)
                        except ValueError:
                            pass
                    new_oes.append({"id": f"OE{last_num + 1}", "desc": new_oe.strip()})
                    
                # 4. Clear existing rows and rewrite everything sequentially
                ws.delete_rows(2, ws.max_row)
                ws.row_dimensions.clear()
                
                ws.append(["", "PROYECTO", current_data["PROYECTO"]])
                ws.append(["", "OG", current_data["OG"]])
                for oe in new_oes:
                    ws.append(["", oe["id"], oe["desc"]])

                # 5. Apply Premium Styles
                ws.column_dimensions['B'].width = 15
                ws.column_dimensions['C'].width = 80
                
                # Header Style
                ws.cell(row=1, column=2).value = "ID Objetivo"
                ws.cell(row=1, column=3).value = "Descripción"
                for col in (2, 3):
                    cell = ws.cell(row=1, column=col)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = align_center
                    cell.border = thin_border
                
                # Content Style
                for row_idx in range(2, ws.max_row + 1):
                    val_b = ws.cell(row=row_idx, column=2).value
                    if val_b:
                        c_b = ws.cell(row=row_idx, column=2)
                        c_b.font = bold_font
                        c_b.alignment = align_center
                        c_b.border = thin_border
                        
                        c_c = ws.cell(row=row_idx, column=3)
                        c_c.alignment = align_left
                        c_c.border = thin_border
                
                wb.save(self._excel_path)
                return True
            except Exception as e:
                print(f"Error updating bitacora: {e}")
                return False

        return await asyncio.to_thread(_write)

    async def get_all_active_tasks(self) -> dict[str, list[str]]:
        """Devuelve todas las tareas no completadas agrupadas por responsable."""
        def _read() -> dict[str, list[str]]:
            from collections import defaultdict
            grouped = defaultdict(list)
            try:
                wb = openpyxl.load_workbook(self._excel_path, data_only=True)
                
                for sheet_name in ["Planificación", "Administración"]:
                    ws = wb[sheet_name]
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        act_id = row[0]
                        if not act_id: continue
                        
                        resp = str(row[2]).strip() if row[2] else "Sin asignar"
                        prog_str = str(row[6]).replace("%", "").strip() if row[6] else "0"
                        
                        try:
                            prog = float(prog_str)
                        except ValueError:
                            prog = 0.0
                            
                        if prog < 100:
                            grouped[resp].append(f"• *{act_id}*: {row[1]} (Progreso: {row[6] or '0%'})")
                            
                return dict(grouped)
            except Exception:
                return {}

        return await asyncio.to_thread(_read)

    async def get_all_edit_options(self) -> dict[str, list[dict[str, str]]]:
        """Devuelve opciones agrupadas de Tareas para el selector de Slack."""
        def _read() -> dict[str, list[dict[str, str]]]:
            options = {"tareas": [], "bitacora": []}
            try:
                wb = openpyxl.load_workbook(self._excel_path, data_only=True)
                
                # Tareas
                for sheet_name in ["Planificación", "Administración"]:
                    ws = wb[sheet_name]
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        act_id = row[0]
                        if act_id:
                            desc = str(row[1])[:50] if row[1] else "Sin descripción"
                            options["tareas"].append({
                                "text": {"type": "plain_text", "text": f"{act_id} - {desc}"},
                                "value": f"tarea|{act_id}"
                            })
                    
                return options
            except Exception:
                return options

        return await asyncio.to_thread(_read)
