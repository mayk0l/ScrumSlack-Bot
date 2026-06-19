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

import structlog

log = structlog.get_logger(__name__)

# Severidad → etiqueta de Slack (emoji + español). Se mantiene local para no
# acoplar la capa de aplicación con la de presentación de Slack.
_SEVERITY_ES = {
    "low": "🟢 BAJA",
    "medium": "🟡 MEDIA",
    "high": "🟠 ALTA",
    "critical": "🔴 CRÍTICA",
}


class ReportService:
    """Genera el resumen diario en mrkdwn de Slack y con IA."""

    def __init__(
        self,
        standup_service: StandupService,
        github_service: GitHubService,
        risk_service: RiskService,
        ai_client: AIClient | None = None,
        valuelist_service=None,
        member_repo=None,
    ):
        self._standup_service = standup_service
        self._github_service = github_service
        self._risk_service = risk_service
        self._ai_client = ai_client
        self._valuelist_service = valuelist_service
        self._member_repo = member_repo

    async def generate_daily_summary(
        self, team_id: UUID, slack_channel_id: str
    ) -> str:
        """Genera el resumen del día en mrkdwn válido de Slack."""
        responses = await self._standup_service.get_today_responses(team_id, slack_channel_id)
        prs = await self._github_service.get_open_prs(team_id)
        risks = await self._risk_service.get_active_risks(team_id)
        missing = await self._standup_service.get_missing_members(team_id, slack_channel_id)

        # Mapa member_id -> slack_user_id para mostrar menciones reales (no UUIDs).
        mentions: dict = {}
        if self._member_repo is not None:
            try:
                for member in await self._member_repo.get_by_team(team_id):
                    mentions[member.id] = member.slack_user_id
            except Exception:
                mentions = {}

        def _mention(member_id) -> str:
            slack_id = mentions.get(member_id)
            return f"<@{slack_id}>" if slack_id else "Un miembro"

        total = len(responses) + len(missing)
        lines = [
            f"*📋 Resumen Diario — {date.today().isoformat()}*",
            "",
            f"*👥 Standup ({len(responses)}/{total} respondieron)*",
        ]

        if responses:
            for response in responses:
                lines.append(f"*{_mention(response.member_id)}*")
                lines.append(f"• Ayer: {response.yesterday}")
                lines.append(f"• Hoy: {response.today}")
                lines.append(f"• Bloqueos: {response.blockers or 'Ninguno'}")
        else:
            lines.append("Sin respuestas de standup.")

        lines.append("")
        lines.append(f"*🔀 Pull Requests Abiertos ({len(prs)})*")
        if prs:
            for pr in prs:
                lines.append(f"• #{pr.pr_number} {pr.title} — @{pr.author}")
        else:
            lines.append("Sin PRs abiertos.")

        lines.append("")
        lines.append(f"*⚠️ Riesgos Activos ({len(risks)})*")
        if risks:
            for risk in risks:
                sev = _SEVERITY_ES.get(str(risk.severity.value).lower(), str(risk.severity.value).upper())
                lines.append(f"• {sev} — {risk.description}")
        else:
            lines.append("Sin riesgos activos.")

        lines.append("")
        lines.append("*🚫 Miembros sin responder*")
        if missing:
            for member in missing:
                if member.slack_user_id:
                    lines.append(f"• <@{member.slack_user_id}>")
                else:
                    lines.append(f"• {member.display_name}")
        elif len(responses) > 0:
            lines.append("Todos respondieron. 🎉")
        else:
            lines.append("Nadie ha respondido aún.")

        # Unión con la planificación (Excel): avance por objetivo.
        if self._valuelist_service is not None:
            objectives = await self._valuelist_service.get_objective_progress()
            lines.append("")
            lines.append("*📈 Progreso del proyecto*")
            if objectives:
                for obj in objectives:
                    lines.append(
                        f"• {obj['id']}: {obj['progress'] * 100:.0f}% "
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
            return f"{summary}\n\n———\n*🤖 Análisis del Scrum Master (IA)*\n\n{analysis}"
        except Exception as e:
            log.warning("ai_summary_failed", error=str(e))
            return summary
