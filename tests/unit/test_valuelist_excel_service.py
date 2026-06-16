import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.application.valuelist_excel_service import ValuelistExcelService

@pytest.fixture
def service():
    # Usaremos un mock path para que no toque el excel real en tests unitarios simples
    # pero mockearemos openpyxl
    return ValuelistExcelService(excel_path="dummy.xlsx", user_mapping={"U123": "Emiliano J."})

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_get_my_tasks(mock_load_workbook, service):
    # Setup mock workbook
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    # Mock data for Planificación
    # Cols: Actividad, Descripción, Responsable, Comienzo, Fin, % esp, % logro, Entregable, Coment
    mock_ws.iter_rows.return_value = [
        ("Actividad", "Desc", "Responsable", "Inicio", "Fin", "% esp", "% logro", "Ent", "Com"),
        ("O0", "Obj 0", "Emiliano J.", datetime.now(), datetime.now(), None, None, None, None),
        ("A0.1", "Tarea 1", "Emiliano J.", datetime.now(), datetime.now(), 1.0, 0.5, "Doc", None),
        ("A0.2", "Tarea 2", "Otro", datetime.now(), datetime.now(), 1.0, 0.0, "Doc", None),
    ]
    
    tasks = await service.get_my_tasks("U123")
    
    # Assertions
    assert len(tasks) == 1
    assert tasks[0]["id"] == "A0.1"
    assert tasks[0]["desc"] == "Tarea 1"
    assert tasks[0]["progress"] == 0.5

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_get_bitacora_summary(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    # Mock data for Bitácora
    mock_ws.iter_rows.return_value = [
        (None, None, None),
        (None, "Objetivo General", None),
        (None, "OG", "Hacer cosas"),
        (None, "Objetivos Específicos", None),
        (None, "Objetivo", "Descripción"),
        (None, "OE1", "Cosa 1"),
    ]
    
    summary = await service.get_bitacora_summary()
    
    assert summary["og"] == "Hacer cosas"
    assert len(summary["oe"]) == 1
    assert summary["oe"][0]["id"] == "OE1"
    assert summary["oe"][0]["desc"] == "Cosa 1"

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_update_task_progress(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    # Mock data for Planificación
    # Actividad, Descripción, Responsable, Comienzo, Fin, % esp, % logro
    mock_row = [MagicMock(value="A2.1"), MagicMock(value="Test"), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(value=0)]
    mock_ws.iter_rows.return_value = [mock_row]
    
    found = await service.update_task_progress("A2.1", 1.0)
    
    assert found is True
    assert mock_row[6].value == 1.0
    mock_wb.save.assert_called_once_with("dummy.xlsx")

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_add_evidence(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws_plan = MagicMock()
    mock_ws_evi = MagicMock()
    
    def getitem_side_effect(sheet_name):
        if sheet_name == "Planificación": return mock_ws_plan
        if sheet_name == "Evidencia": return mock_ws_evi
        return MagicMock()
    
    mock_wb.__getitem__.side_effect = getitem_side_effect
    
    # Mock row in Planificación to find the description
    mock_row = [MagicMock(value="A2.1"), MagicMock(value="Test Description")]
    mock_ws_plan.iter_rows.return_value = [mock_row]
    
    success = await service.add_evidence("A2.1", "http://github.com/test")
    
    assert success is True
    mock_ws_evi.append.assert_called_once_with(["A2.1", "Test Description", "http://github.com/test"])
    mock_wb.save.assert_called_once_with("dummy.xlsx")

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_create_task(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    success = await service.create_task("A5.5", "Nueva Tarea", "Emiliano J.", "2026-06-20", "2026-06-25")
    
    assert success is True
    mock_wb.save.assert_called_once_with("dummy.xlsx")
    mock_wb.save.assert_called_once_with("dummy.xlsx")
    mock_wb.save.assert_called_once_with("dummy.xlsx")

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_generate_gantt(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    from datetime import datetime
    # Actividad, Descripción, Responsable, Comienzo, Fin
    mock_row = [
        MagicMock(value="A1.1"), 
        MagicMock(value="Test"), 
        MagicMock(), 
        MagicMock(value=datetime(2026, 6, 1)), 
        MagicMock(value=datetime(2026, 6, 5))
    ]
    mock_ws.iter_rows.return_value = [mock_row]
    
    gantt = await service.generate_gantt()
    
    assert "gantt" in gantt
    assert "A1.1" in gantt
    assert "2026-06-01" in gantt

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_get_task_by_id(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    mock_row = ["A1.2", "Desc", "Emiliano J.", "2026-06-01", "2026-06-05", None, None]
    mock_ws.iter_rows.return_value = [mock_row]
    
    task = await service.get_task_by_id("A1.2")
    assert task is not None
    assert task["id"] == "A1.2"
    assert task["desc"] == "Desc"
    assert task["resp"] == "Emiliano J."

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_update_task_details(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    mock_row = [
        MagicMock(value="A1.2"), MagicMock(value="Desc"), MagicMock(value="Emiliano J."), 
        MagicMock(value="2026-06-01"), MagicMock(value="2026-06-05"), MagicMock(), MagicMock()
    ]
    mock_ws.iter_rows.return_value = [mock_row]
    
    success = await service.update_task_details("A1.2", "Nueva Desc", "Diego C.", "2026-06-10", "2026-06-15")
    assert success is True
    assert mock_row[1].value == "Nueva Desc"
    assert mock_row[2].value == "Diego C."
    mock_wb.save.assert_called_once_with("dummy.xlsx")

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_delete_task_by_id(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    mock_cell = MagicMock(value="A1.2")
    mock_cell.row = 3
    mock_row = [mock_cell]
    mock_ws.iter_rows.return_value = [mock_row]
    
    success = await service.delete_task_by_id("A1.2")
    assert success is True
    mock_ws.delete_rows.assert_called_once_with(3)
    mock_wb.save.assert_called_once_with("dummy.xlsx")

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_update_bitacora(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    mock_wb.__getitem__.return_value = mock_ws
    
    mock_ws.cell.return_value.value = "Old OG"
    
    success = await service.update_bitacora("og", "New OG")
    assert success is True
    mock_wb.save.assert_called_once_with("dummy.xlsx")

@patch("src.application.valuelist_excel_service.openpyxl.load_workbook")
@pytest.mark.asyncio
async def test_get_all_active_tasks(mock_load_workbook, service):
    mock_wb = MagicMock()
    mock_load_workbook.return_value = mock_wb
    mock_ws = MagicMock()
    
    # Simula getitem para devolver la misma hoja
    mock_wb.__getitem__.return_value = mock_ws
    
    # ID, Desc, Resp, Start, End, % esp, % log
    mock_ws.iter_rows.return_value = [
        ["A1.1", "Hacer backend", "Emiliano J.", None, None, None, "50%"],
        ["A1.2", "Hacer frontend", "Diego C.", None, None, None, "10%"],
        ["A1.3", "Hacer base de datos", "Emiliano J.", None, None, None, "100%"] # Ignorado por completado
    ]
    
    grouped = await service.get_all_active_tasks()
    
    # Nota: como lee 2 hojas (Planificación y Administración) con el mismo mock_ws, devolverá dobles
    assert "Emiliano J." in grouped
    assert "Diego C." in grouped
    
    emiliano_tasks = grouped["Emiliano J."]
    assert any("A1.1" in t for t in emiliano_tasks)
    assert not any("A1.3" in t for t in emiliano_tasks)
