# Scrum Master Bot

Asistente digital para equipos Scrum que automatiza daily standups, monitorea pull requests, detecta riesgos y genera reportes directamente en Slack. Integrado con GitHub y potenciado con IA generativa a través de OpenRouter.

> **Estado:** En fase de fundación. Ver [`docs/02-kanban.md`](docs/02-kanban.md) para el avance actual.

---

## Stack Tecnológico

- **Lenguaje:** Python 3.12
- **Framework Web:** FastAPI + Uvicorn
- **Integraciones:** Slack Bolt, GitHub REST API, OpenRouter API
- **Base de Datos:** PostgreSQL 16 + SQLAlchemy 2.0 async + Alembic
- **Scheduler:** APScheduler
- **Excel:** openpyxl
- **Logging:** structlog
- **Testing:** pytest + pytest-asyncio
- **Infraestructura:** Docker + Docker Compose

---

## Arquitectura

Clean Architecture / Hexagonal:

- `src/domain/` — Entidades, value objects, enums, excepciones y puertos (interfaces de repositorios).
- `src/application/` — Casos de uso y servicios de aplicación.
- `src/infrastructure/` — Implementación de repositorios, clientes externos, scheduler y ORM.
- `src/interfaces/` — Adaptadores Slack (comandos, modales, eventos) y API REST.
- `tests/` — Tests unitarios e integración.

Más detalles en [`docs/00-especificacion-completa.md`](docs/00-especificacion-completa.md).

---

## Documentación del Proyecto

| Archivo | Propósito |
|---------|-----------|
| [`docs/00-especificacion-completa.md`](docs/00-especificacion-completa.md) | Visión, objetivos, arquitectura, modelo de dominio y backlog completo. |
| [`docs/01-plan-de-ejecucion.md`](docs/01-plan-de-ejecucion.md) | Plan paso a paso para generar el código bloque por bloque. |
| [`docs/02-kanban.md`](docs/02-kanban.md) | Tablero de desarrollo con tareas, prioridades y criterios de aceptación. |
| [`docs/03-convenciones-de-desarrollo.md`](docs/03-convenciones-de-desarrollo.md) | Convenciones de código, commits, tests y documentación. |

---

## Primeros Pasos

1. Clonar el repositorio.
2. Copiar `.env.example` a `.env` y completar las variables.
3. Levantar la aplicación:

```bash
docker-compose up --build
```

4. Ejecutar migraciones:

```bash
docker-compose exec app alembic upgrade head
```

5. Verificar health check:

```bash
curl http://localhost:3000/api/health
```

---

## Convenciones Rápidas

- **Commits atómicos:** un cambio lógico por commit.
- **Tests obligatorios:** cada servicio o regla de negocio debe incluir tests.
- **Documentación actualizada:** cualquier cambio de arquitectura, configuración o flujo debe reflejarse en `docs/`.
- **Idioma del código:** nombres en inglés, docstrings de negocio en español, docstrings de API en inglés.

Para el detalle completo ver [`docs/03-convenciones-de-desarrollo.md`](docs/03-convenciones-de-desarrollo.md).

---

## Comandos de Slack (MVP)

- `/scrum` — Enviar actualización de standup.
- `/riesgos` — Ver riesgos activos.
- `/bloqueos` — Ver bloqueos reportados hoy.
- `/sprint` — Información del sprint activo.
- `/metricas` — Métricas del sprint.
- `/reporte` — Reporte completo del día.
- `/progreso` — Progreso de módulos desde Excel.

---

## Licencia

Por definir.
