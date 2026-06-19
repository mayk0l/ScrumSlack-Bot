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

    async def validate_excel_file(self, file_content: bytes) -> tuple[bool, str]:
        """Valida que el contenido de un archivo Excel sea compatible con el sistema.
        
        Retorna (True, "") si es válido, o (False, "mensaje de error") si falla la validación.
        """
        import io
        from datetime import datetime, date
        
        def _validate() -> tuple[bool, str]:
            try:
                # 1. Cargar el libro en memoria
                wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
            except Exception as e:
                return False, f"El archivo no es un libro de Excel válido (.xlsx) o está corrupto. Error: {str(e)}"
            
            # 2. Verificar hojas requeridas
            required_sheets = ["Bitácora", "Planificación", "Administración", "Evidencia"]
            for s in required_sheets:
                if s not in wb.sheetnames:
                    return False, f"Falta la pestaña obligatoria: '{s}'."
            
            # 3. Validar hoja Bitácora
            ws_bit = wb["Bitácora"]
            if ws_bit.max_column < 3:
                return False, "La pestaña 'Bitácora' debe tener al menos 3 columnas (Identificador, Campo, Valor/Descripción)."
                
            # 4. Validar hojas de tareas (Planificación y Administración)
            for sheet_name in ["Planificación", "Administración"]:
                ws = wb[sheet_name]
                if ws.max_column < 7:
                    return False, f"La pestaña '{sheet_name}' debe tener al menos 7 columnas (ID, Descripción, Responsable, Inicio, Fin, Estado, % Logro)."
                
                # Validar unicidad de IDs de tareas y tipos de datos por fila
                seen_ids = set()
                row_idx = 1
                for row in ws.iter_rows(min_row=2, values_only=True):
                    row_idx += 1
                    act_id = row[0]
                    if not act_id:
                        continue
                    
                    act_str = str(act_id).strip()
                    if not (act_str.startswith("A") or act_str.startswith("AD")):
                        continue
                        
                    # Validar IDs duplicados
                    if act_str in seen_ids:
                        return False, f"ID de tarea duplicado '{act_str}' en la pestaña '{sheet_name}', fila {row_idx}."
                    seen_ids.add(act_str)
                    
                    # Validar Responsable
                    resp = row[2]
                    if not resp or not str(resp).strip():
                        return False, f"Falta el 'Responsable' para la tarea '{act_str}' en la pestaña '{sheet_name}', fila {row_idx}."
                        
                    # Validar Fechas (columnas index 3 y 4)
                    for col_name, col_idx in [("Comienzo", 3), ("Fin", 4)]:
                        val = row[col_idx]
                        if val is not None:
                            if not isinstance(val, (datetime, date)):
                                try:
                                    datetime.strptime(str(val).strip()[:10], "%Y-%m-%d")
                                except ValueError:
                                    return False, f"Formato de fecha inválido en la columna '{col_name}' para la tarea '{act_str}' en la pestaña '{sheet_name}', fila {row_idx}. Debe ser YYYY-MM-DD o formato de fecha de Excel."
                    
                    # Validar % logro (columna index 6)
                    logro = row[6]
                    if logro is not None:
                        try:
                            val_logro = float(logro)
                            if val_logro < 0.0 or val_logro > 100.0:
                                return False, f"El porcentaje de logro para la tarea '{act_str}' en la pestaña '{sheet_name}', fila {row_idx} debe estar entre 0 y 100 (o 0.0 y 1.0). Valor recibido: {logro}."
                        except ValueError:
                            return False, f"El porcentaje de logro para la tarea '{act_str}' en la pestaña '{sheet_name}', fila {row_idx} debe ser un valor numérico. Recibido: '{logro}'."
            
            return True, ""
            
        return await asyncio.to_thread(_validate)

    @staticmethod
    def _apply_gantt_and_styles(wb: openpyxl.Workbook):
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.table import Table, TableStyleInfo
        from openpyxl.formatting.rule import DataBarRule
        from datetime import datetime, timedelta

        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )

        headers = ["Actividad", "Descripción (resumen)", "Responsable", "Comienzo", "Fin (Esperado/logrado)", "% logro esperado", "% de logro", "Entregable", "Comentarios"]
        
        # 0. Format Bitácora (Executive Summary)
        if "Bitácora" in wb.sheetnames:
            ws_bit = wb["Bitácora"]
            ws_bit.freeze_panes = "A2"
            
            # Style headers
            for row in ws_bit.iter_rows(min_row=1, max_row=1):
                for cell in row:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = align_center
            
            # Column widths
            ws_bit.column_dimensions['A'].width = 8
            ws_bit.column_dimensions['B'].width = 25
            ws_bit.column_dimensions['C'].width = 70
            
            # Style data cells with alternating colors
            og_fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
            oe_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
            
            for row in ws_bit.iter_rows(min_row=2):
                field = str(row[1].value).strip().upper() if row[1].value else ""
                if field == "OG":
                    for cell in row:
                        cell.fill = og_fill
                        cell.font = Font(bold=True, size=11)
                elif field.startswith("OE"):
                    for cell in row:
                        cell.fill = oe_fill
                
                row[1].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
                row[2].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        
        # 1. Format Planificación and Administración
        for sheet_name in ["Planificación", "Administración"]:
            if sheet_name not in wb.sheetnames:
                continue
            ws = wb[sheet_name]
            
            # Freeze panes for UX (freeze row 1 and columns A, B)
            ws.freeze_panes = "C2"
            
            # Ensure headers
            for col_idx, h in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx)
                cell.value = h
                
            # Column widths
            ws.column_dimensions['A'].width = 12
            ws.column_dimensions['B'].width = 40
            ws.column_dimensions['C'].width = 20
            ws.column_dimensions['D'].width = 15
            ws.column_dimensions['E'].width = 15
            ws.column_dimensions['F'].width = 20
            ws.column_dimensions['G'].width = 15
            ws.column_dimensions['H'].width = 30
            ws.column_dimensions['I'].width = 30

            max_r = max(2, ws.max_row)

            # Native Tables for Premium look (Zebra stripes, auto filters)
            table_name = f"Tabla_{sheet_name.replace(' ', '')[:20]}"
            if table_name in ws.tables:
                ws.tables[table_name].ref = f"A1:I{max_r}"
            else:
                tab = Table(displayName=table_name, ref=f"A1:I{max_r}")
                style = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False,
                                       showLastColumn=False, showRowStripes=True, showColumnStripes=False)
                tab.tableStyleInfo = style
                ws.add_table(tab)

            # DataBars conditional formatting for percentage
            ws.conditional_formatting = type(ws.conditional_formatting)()
            rule = DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color="5A8AC6")
            ws.conditional_formatting.add(f"G2:G{max_r}", rule)

            # Cell formatting inside the table
            for row in ws.iter_rows(min_row=2, max_row=max_r, max_col=9):
                for cell in row:
                    if cell.column in (6, 7):
                        cell.number_format = '0%'
                    cell.alignment = align_left if cell.column in (2, 8, 9) else align_center
                    
        # 1.5. Format Evidencia
        if "Evidencia" in wb.sheetnames:
            ws_ev = wb["Evidencia"]
            
            # Freeze panes
            ws_ev.freeze_panes = "B2"
            
            ev_headers = ["Actividad", "Descripción", "Enlace / Ubicación"]
            for col_idx, h in enumerate(ev_headers, 1):
                cell = ws_ev.cell(row=1, column=col_idx)
                cell.value = h
            
            ws_ev.column_dimensions['A'].width = 12
            ws_ev.column_dimensions['B'].width = 40
            ws_ev.column_dimensions['C'].width = 60
            
            # Clean floating ghost rows
            last_valid_row = 1
            for row in ws_ev.iter_rows(min_row=2, max_col=3):
                if any(c.value for c in row):
                    last_valid_row = row[0].row
            if last_valid_row < ws_ev.max_row:
                ws_ev.delete_rows(last_valid_row + 1, ws_ev.max_row - last_valid_row)
                
            max_ev_row = max(2, ws_ev.max_row)
            
            # Native Table for Evidencia
            ev_table_name = "Tabla_Evidencia"
            if ev_table_name in ws_ev.tables:
                ws_ev.tables[ev_table_name].ref = f"A1:C{max_ev_row}"
            else:
                tab_ev = Table(displayName=ev_table_name, ref=f"A1:C{max_ev_row}")
                style_ev = TableStyleInfo(name="TableStyleMedium9", showFirstColumn=False,
                                       showLastColumn=False, showRowStripes=True, showColumnStripes=False)
                tab_ev.tableStyleInfo = style_ev
                ws_ev.add_table(tab_ev)
            
            for row in ws_ev.iter_rows(min_row=2, max_row=max_ev_row, max_col=3):
                for cell in row:
                    cell.alignment = align_left if cell.column in (2, 3) else align_center
                    
        # 2. Draw Gantt Chart
        tasks = []
        min_date = None
        max_date = None
        
        for sheet_name in ["Planificación", "Administración"]:
            if sheet_name not in wb.sheetnames:
                continue
            ws = wb[sheet_name]
            for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
                act_id = row[0].value
                desc = row[1].value
                start = row[3].value
                end = row[4].value
                if act_id and start and end:
                    # Parse dates
                    if isinstance(start, str):
                        try: start = datetime.strptime(start[:10], "%Y-%m-%d")
                        except: continue
                    if isinstance(end, str):
                        try: end = datetime.strptime(end[:10], "%Y-%m-%d")
                        except: continue
                        
                    if isinstance(start, datetime) and isinstance(end, datetime):
                        tasks.append({"id": act_id, "desc": desc, "start": start, "end": end})
                        if min_date is None or start < min_date: min_date = start
                        if max_date is None or end > max_date: max_date = end
        
        ws_gantt = wb["Gantt"] if "Gantt" in wb.sheetnames else wb["Carta Gantt"] if "Carta Gantt" in wb.sheetnames else None
        if not ws_gantt: return
        
        # Clear Gantt sheet
        ws_gantt.delete_rows(1, ws_gantt.max_row)
        ws_gantt.row_dimensions.clear()
        
        if not tasks or not min_date or not max_date:
            ws_gantt.cell(row=1, column=1).value = "No hay tareas con fechas válidas."
            return
            
        # Build timeline (weekly)
        current_date = min_date - timedelta(days=min_date.weekday())
        end_timeline = max_date + timedelta(days=(6 - max_date.weekday()))
        
        weeks = []
        while current_date <= end_timeline:
            weeks.append(current_date)
            current_date += timedelta(days=7)
            
        ws_gantt.cell(row=1, column=1).value = "ID"
        ws_gantt.cell(row=1, column=2).value = "Descripción"
        ws_gantt.cell(row=2, column=1).value = "ID"
        ws_gantt.cell(row=2, column=2).value = "Descripción"
        
        ws_gantt.column_dimensions['A'].width = 12
        ws_gantt.column_dimensions['B'].width = 30
        
        col_idx = 3
        current_month = None
        month_start_col = 3
        
        months_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        for w in weeks:
            month_str = f"{months_es[w.month - 1]} {w.year}"
            if current_month != month_str:
                if current_month is not None:
                    if month_start_col < col_idx - 1:
                        ws_gantt.merge_cells(start_row=1, start_column=month_start_col, end_row=1, end_column=col_idx-1)
                    cell = ws_gantt.cell(row=1, column=month_start_col)
                    cell.value = current_month
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = align_center
                    cell.border = thin_border
                current_month = month_str
                month_start_col = col_idx
                
            c2 = ws_gantt.cell(row=2, column=col_idx)
            c2.value = f"{w.day:02d}/{w.month:02d}"
            c2.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
            c2.font = Font(bold=True)
            c2.alignment = align_center
            c2.border = thin_border
            ws_gantt.column_dimensions[get_column_letter(col_idx)].width = 8
            
            col_idx += 1
            
        if current_month is not None:
            if month_start_col < col_idx - 1:
                ws_gantt.merge_cells(start_row=1, start_column=month_start_col, end_row=1, end_column=col_idx-1)
            cell = ws_gantt.cell(row=1, column=month_start_col)
            cell.value = current_month
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = align_center
            cell.border = thin_border

        # Draw tasks
        gantt_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        row_idx = 3
        for t in sorted(tasks, key=lambda x: x["start"]):
            c_id = ws_gantt.cell(row=row_idx, column=1)
            c_id.value = t["id"]
            c_id.alignment = align_center
            c_id.border = thin_border
            
            c_desc = ws_gantt.cell(row=row_idx, column=2)
            c_desc.value = t["desc"]
            c_desc.alignment = align_left
            c_desc.border = thin_border
            
            c_idx = 3
            for w in weeks:
                w_end = w + timedelta(days=6)
                c_cell = ws_gantt.cell(row=row_idx, column=c_idx)
                if t["start"] <= w_end and t["end"] >= w:
                    c_cell.fill = gantt_fill
                c_cell.border = thin_border
                c_idx += 1
                
            row_idx += 1

    async def get_my_tasks(self, target_name: str) -> list[dict[str, Any]]:
        """Busca las tareas asignadas al usuario en Planificación y Administración."""
        if not target_name:
            return []

        def _read() -> list[dict[str, Any]]:
            try:
                wb = openpyxl.load_workbook(self._excel_path, data_only=True)
                tasks = []
                for sheet_name in ["Planificación", "Administración"]:
                    if sheet_name not in wb.sheetnames:
                        continue
                    ws = wb[sheet_name]
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        # Cols: 0=Act, 1=Desc, 2=Resp, 3=Inicio, 4=Fin, 5=%esp, 6=%logro
                        act_id = row[0]
                        resp = row[2]
                        
                        if act_id and (str(act_id).startswith("A") or str(act_id).startswith("AD")) and resp == target_name:
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
                
                # Append manually to the first truly empty row to avoid ghost rows
                last_row = 1
                for i in range(2, ws_evi.max_row + 2):
                    if not ws_evi.cell(row=i, column=1).value and not ws_evi.cell(row=i, column=2).value:
                        last_row = i
                        break
                ws_evi.cell(row=last_row, column=1).value = task_id
                ws_evi.cell(row=last_row, column=2).value = desc
                ws_evi.cell(row=last_row, column=3).value = url
                
                self._apply_gantt_and_styles(wb)
                wb.save(self._excel_path)
                return True
            except Exception:
                return False

        return await asyncio.to_thread(_write)

    async def create_task(self, oe_id: str, desc: str, resp: str, start: str, end: str, entregable: str = "", comentarios: str = "") -> bool:
        """Agrega una nueva fila al final de la hoja correspondiente, autogenerando el ID."""
        def _write() -> bool:
            try:
                wb = openpyxl.load_workbook(self._excel_path)
                sheet_name = "Administración" if oe_id == "AD" else "Planificación"
                ws = wb[sheet_name]
                
                # Determine prefix
                if oe_id == "AD":
                    prefix = "AD"
                elif oe_id == "A":
                    prefix = "A0."
                elif oe_id.startswith("OE"):
                    num = oe_id.replace("OE", "").strip()
                    prefix = f"A{num}."
                else:
                    prefix = "A"

                # Find max suffix
                max_suffix = 0
                for r in ws.iter_rows(min_row=2, max_row=ws.max_row):
                    cell_val = r[0].value
                    if cell_val and str(cell_val).startswith(prefix):
                        suffix_str = str(cell_val)[len(prefix):]
                        try:
                            max_suffix = max(max_suffix, int(suffix_str))
                        except ValueError:
                            pass
                
                act_id = f"{prefix}{max_suffix + 1}"
                
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
                ws.cell(row=last_row, column=8).value = entregable
                ws.cell(row=last_row, column=9).value = comentarios
                self._apply_gantt_and_styles(wb)
                wb.save(self._excel_path)
                return True
            except Exception as e:
                print(f"Error create_task: {e}")
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
                                "end": _format_date(row[4]),
                                "entregable": str(row[7]) if len(row) > 7 and row[7] else "",
                                "comentarios": str(row[8]) if len(row) > 8 and row[8] else ""
                            }
                return None
            except Exception:
                return None

        return await asyncio.to_thread(_read)

    async def update_task_details(self, task_id: str, desc: str, resp: str, start: str, end: str, entregable: str = "", comentarios: str = "") -> bool:
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
                            # Ensure row has enough cells
                            while len(row) < 9:
                                ws.cell(row=cell_id.row, column=len(row)+1).value = ""
                                row = tuple(ws.iter_rows(min_row=cell_id.row, max_row=cell_id.row))[0]
                            row[7].value = entregable
                            row[8].value = comentarios
                            self._apply_gantt_and_styles(wb)
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
                            self._apply_gantt_and_styles(wb)
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
