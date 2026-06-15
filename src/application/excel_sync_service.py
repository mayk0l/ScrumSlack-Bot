"""Módulo: excel_sync_service.

Servicio de aplicación para sincronización con archivo Excel.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from uuid import UUID

import openpyxl
from openpyxl.workbook.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from src.domain.models import MetricSnapshot, Risk
from src.domain.repositories import (
    MetricRepository,
    RiskRepository,
    SprintRepository,
)

SHEET_MODULES = "Módulos"
SHEET_GANTT = "Carta Gantt"
SHEET_TASKS = "Tareas"
SHEET_METRICS = "Métricas"
SHEET_RISKS = "Riesgos"


class ExcelSyncService:
    """Crea y actualiza el archivo Excel de seguimiento."""

    def __init__(
        self,
        excel_path: str,
        metric_repo: MetricRepository,
        risk_repo: RiskRepository,
        sprint_repo: SprintRepository,
    ):
        self._excel_path = Path(excel_path)
        self._metric_repo = metric_repo
        self._risk_repo = risk_repo
        self._sprint_repo = sprint_repo

    async def create_template(self) -> None:
        """Crea el archivo Excel con las 5 hojas y headers."""

        def _create() -> None:
            wb = openpyxl.Workbook()
            wb.remove(wb.active)

            self._setup_sheet(wb, SHEET_MODULES, ["ID", "Nombre", "Estado", "Progreso %"])
            self._setup_sheet(wb, SHEET_GANTT, ["Sprint", "Inicio", "Fin", "Estado"])
            self._setup_sheet(
                wb, SHEET_TASKS, ["ID", "Sprint", "Responsable", "Estado", "Descripción"]
            )
            self._setup_sheet(
                wb, SHEET_METRICS, ["Fecha", "Tipo", "Valor", "Sprint", "Metadata"]
            )
            self._setup_sheet(
                wb, SHEET_RISKS, ["Fecha", "Tipo", "Severidad", "Descripción", "Resuelto"]
            )

            self._excel_path.parent.mkdir(parents=True, exist_ok=True)
            wb.save(self._excel_path)

        await asyncio.to_thread(_create)

    def _setup_sheet(
        self, wb: Workbook, title: str, headers: list[str]
    ) -> Worksheet:
        """Crea una hoja con headers."""
        ws = wb.create_sheet(title=title)
        ws.append(headers)
        return ws

    async def sync_metrics(self, team_id: UUID) -> None:
        """Escribe las métricas del equipo en la hoja Métricas."""
        metric = await self._metric_repo.get_latest(team_id, "velocity")
        metrics = [metric] if metric else []

        def _sync(data: list[MetricSnapshot]) -> None:
            wb = openpyxl.load_workbook(self._excel_path)
            ws = wb[SHEET_METRICS]
            ws.delete_rows(2, ws.max_row)

            for item in data:
                ws.append(
                    [
                        item.date.isoformat(),
                        item.metric_type,
                        item.value,
                        item.metadata.get("sprint_id", ""),
                        str(item.metadata),
                    ]
                )
            wb.save(self._excel_path)

        await asyncio.to_thread(_sync, metrics)

    async def sync_risks(self, team_id: UUID) -> None:
        """Escribe los riesgos activos en la hoja Riesgos."""
        risks = await self._risk_repo.get_active_by_team(team_id)

        def _sync(data: list[Risk]) -> None:
            wb = openpyxl.load_workbook(self._excel_path)
            ws = wb[SHEET_RISKS]
            ws.delete_rows(2, ws.max_row)

            for risk in data:
                ws.append(
                    [
                        risk.created_at.isoformat(),
                        risk.type.value,
                        risk.severity.value,
                        risk.description,
                        "Sí" if risk.resolved else "No",
                    ]
                )
            wb.save(self._excel_path)

        await asyncio.to_thread(_sync, risks)

    async def get_module_progress(self) -> list[dict[str, Any]]:
        """Lee la hoja Módulos y retorna progreso."""

        def _read() -> list[dict]:
            import zipfile
            try:
                wb = openpyxl.load_workbook(self._excel_path)
            except (FileNotFoundError, zipfile.BadZipFile):
                return []
            if "Módulos" not in wb.sheetnames:
                return []
            ws = wb[SHEET_MODULES]
            rows = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is None:
                    continue
                rows.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "status": row[2],
                        "progress": row[3],
                    }
                )
            return rows

        return await asyncio.to_thread(_read)

    async def update_module(self, module_id: str, updates: dict[str, Any]) -> None:
        """Actualiza un módulo específico en la hoja Módulos."""

        def _update() -> None:
            wb = openpyxl.load_workbook(self._excel_path)
            ws = wb[SHEET_MODULES]
            for idx, row in enumerate(
                ws.iter_rows(min_row=2, values_only=True), start=2
            ):
                if row[0] == module_id:
                    if "name" in updates:
                        ws.cell(row=idx, column=2, value=updates["name"])
                    if "status" in updates:
                        ws.cell(row=idx, column=3, value=updates["status"])
                    if "progress" in updates:
                        ws.cell(row=idx, column=4, value=updates["progress"])
                    break
            wb.save(self._excel_path)

        await asyncio.to_thread(_update)
