"""Módulo: report_service.

Servicio de aplicación para generar resúmenes diarios.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from src.application.github_service import GitHubService
from src.application.risk_service import RiskService
from src.application.standup_service import StandupService
from src.infrastructure.ai_client import AIClient


class ReportService:
    """Genera resúmenes diarios en Markdown y con IA."""

    def __init__(
        self,
        standup_service: StandupService,
        github_service: GitHubService,
        risk_service: RiskService,
        ai_client: AIClient | None = None,
        valuelist_service = None,
    ):
        self._standup_service = standup_service
        self._github_service = github_service
        self._risk_service = risk_service
        self._ai_client = ai_client
        self._valuelist_service = valuelist_service

    async def generate_daily_summary(
        self, team_id: UUID, slack_channel_id: str
    ) -> str:
        """Genera un resumen Markdown del día."""
        responses = await self._standup_service.get_today_responses(team_id, slack_channel_id)
        prs = await self._github_service.get_open_prs(team_id)
        risks = await self._risk_service.get_active_risks(team_id)
        missing = await self._standup_service.get_missing_members(team_id, slack_channel_id)

        lines = [
            f"## 📋 Resumen Diario — {date.today().isoformat()}",
            "",
            f"### 👥 Standup ({len(responses)}/{len(responses) + len(missing)} respondieron)",
        ]

        if responses:
            for response in responses:
                lines.append(f"**{response.member_id}:**")
                lines.append(f"- Ayer: {response.yesterday}")
                lines.append(f"- Hoy: {response.today}")
                lines.append(
                    f"- Bloqueos: {response.blockers or 'Ninguno'}"
                )
        else:
            lines.append("Sin respuestas de standup.")

        lines.append("")
        lines.append(f"### 🔀 Pull Requests Abiertos ({len(prs)})")
        if prs:
            for pr in prs:
                lines.append(
                    f"- #{pr.pr_number} {pr.title} — @{pr.author}"
                )
        else:
            lines.append("Sin PRs abiertos.")

        lines.append("")
        lines.append(f"### ⚠️ Riesgos Activos ({len(risks)})")
        if risks:
            for risk in risks:
                lines.append(f"- [{risk.severity.value}] {risk.description}")
        else:
            lines.append("Sin riesgos activos.")

        lines.append("")
        lines.append("### 🚫 Miembros sin responder")
        if missing:
            for member in missing:
                lines.append(f"- {member.display_name}")
        elif len(responses) > 0:
            lines.append("Todos respondieron.")
        else:
            lines.append("Nadie ha respondido aún.")

        # Unión con la planificación (Excel): avance por objetivo.
        if self._valuelist_service is not None:
            objectives = await self._valuelist_service.get_objective_progress()
            lines.append("")
            lines.append("### 📈 Progreso del proyecto")
            if objectives:
                for obj in objectives:
                    lines.append(
                        f"- {obj['id']}: {obj['progress'] * 100:.0f}% "
                        f"({obj['done']}/{obj['total']} tareas)"
                    )
            else:
                lines.append("Sin tareas registradas en la planilla.")

        return "\n".join(lines)

    async def generate_ai_summary(
        self, team_id: UUID, slack_channel_id: str
    ) -> str:
        """Genera un resumen ejecutivo usando IA."""
        summary = await self.generate_daily_summary(team_id, slack_channel_id)
        
        context_prompt = ""
        if self._valuelist_service:
            bitacora = await self._valuelist_service.get_bitacora_summary()
            if bitacora and bitacora.get("og"):
                context_prompt = f"El Objetivo General del proyecto es: {bitacora['og']}. "

        if self._ai_client is None:
            return summary

        try:
            analysis = await self._ai_client.generate_summary(
                prompt=(
                    f"Eres un Scrum Master. {context_prompt}Genera un resumen ejecutivo "
                    "conciso en español del siguiente reporte diario. "
                    "Enfócate en accionables y riesgos."
                ),
                context=summary,
            )
            return f"{summary}\n\n## 🤖 Análisis IA\n\n{analysis}"
        except Exception as e:
            print(f"⚠️ Error generando resumen con IA: {e}", flush=True)
            return summary
