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
