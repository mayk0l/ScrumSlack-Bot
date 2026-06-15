import asyncio
import openpyxl
from typing import Any

class ValuelistExcelService:
    """
    Servicio para sincronizar y leer datos directamente desde 
    la Bitácora de Rentabilidad de Valuelist (Excel).
    """

    def __init__(self, excel_path: str, user_mapping: dict[str, str] = None):
        self._excel_path = excel_path
        self._user_mapping = user_mapping or {}

    async def get_my_tasks(self, slack_user_id: str) -> list[dict[str, Any]]:
        """Busca las tareas asignadas al usuario en la Hoja 3 (Planificación)."""
        target_name = self._user_mapping.get(slack_user_id)
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
                
                summary = {"og": "", "oe": []}
                reading_oe = False
                
                for row in ws.iter_rows(min_row=1, max_row=50, values_only=True):
                    col_b = row[1]
                    col_c = row[2]
                    
                    if col_b == "OG" and col_c:
                        summary["og"] = str(col_c)
                    
                    if col_b == "Objetivo" and col_c == "Descripción":
                        reading_oe = True
                        continue
                        
                    if reading_oe:
                        if not col_b and not col_c:
                            reading_oe = False
                        elif col_b and str(col_b).startswith("OE"):
                            summary["oe"].append({
                                "id": str(col_b),
                                "desc": str(col_c) if col_c else ""
                            })
                            
                return summary
            except Exception:
                return {"og": "", "oe": []}

        return await asyncio.to_thread(_read)

    async def update_task_progress(self, task_id: str, progress: float) -> bool:
        """Actualiza el porcentaje de logro de una tarea en la Hoja 3."""
        def _write() -> bool:
            try:
                wb = openpyxl.load_workbook(self._excel_path)
                ws = wb["Planificación"]
                
                for row in ws.iter_rows(min_row=2):
                    cell_id = row[0]
                    if cell_id.value and str(cell_id.value) == task_id:
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
