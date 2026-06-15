"""Módulo: ai_service.

Servicio de aplicación para orquestar prompts hacia el cliente de IA.
"""

from __future__ import annotations

from src.domain.models import Risk, StandupResponse
from src.infrastructure.ai_client import AIClient


class AIService:
    """Genera resúmenes y análisis usando un LLM."""

    def __init__(self, ai_client: AIClient):
        self._ai_client = ai_client

    async def summarize_standup(
        self, responses: list[StandupResponse]
    ) -> str:
        """Genera un resumen ejecutivo de las respuestas del standup."""
        if not responses:
            return "No hay respuestas de standup para resumir."

        lines = []
        for idx, response in enumerate(responses, start=1):
            lines.append(
                f"{idx}. Ayer: {response.yesterday}\n"
                f"   Hoy: {response.today}\n"
                f"   Bloqueos: {response.blockers or 'Ninguno'}"
            )
        context = "\n".join(lines)

        prompt = (
            "Eres un Scrum Master. Resume las siguientes respuestas de "
            "standup en un párrafo corto en español, destacando bloqueos "
            "y avances importantes."
        )
        return await self._ai_client.generate_summary(prompt, context)

    async def analyze_sprint_risks(
        self, risks: list[Risk], prs: list[dict]
    ) -> str:
        """Analiza riesgos y PRs para generar recomendaciones."""
        if not risks and not prs:
            return "No hay riesgos ni PRs abiertos para analizar."

        risk_lines = [
            f"- [{r.severity.value}] {r.description}" for r in risks
        ]
        pr_lines = [
            f"- #{pr.get('number')} {pr.get('title')} (@{pr.get('author')})"
            for pr in prs
        ]
        context = (
            "Riesgos:\n" + "\n".join(risk_lines) + "\n\nPRs:\n" + "\n".join(pr_lines)
        )

        prompt = (
            "Eres un Scrum Master. Analiza los siguientes riesgos y PRs "
            "abiertos. Proporciona recomendaciones accionables en español, "
            "de forma concisa."
        )
        return await self._ai_client.generate_summary(prompt, context)
