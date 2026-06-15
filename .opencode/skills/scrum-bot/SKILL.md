---
name: scrum-bot
description: Use when working on the Scrum Master Bot project. Loads project context, architecture rules, kanban flow, and conventions.
---

# Scrum Master Bot — Project Context

## Documentation Map

| File | Purpose |
|------|---------|
| `README.md` | Project overview, stack, quick start, conventions summary. |
| `docs/00-especificacion-completa.md` | Full product spec, domain model, DB schema, roadmap. |
| `docs/01-plan-de-ejecucion.md` | Step-by-step build plan with atomic blocks. |
| `docs/02-kanban.md` | Current kanban board: Backlog / In Progress / Blocked / Done. |
| `docs/03-convenciones-de-desarrollo.md` | Commits, testing, docs, and agent workflow rules. |

## Architecture Reminders

- **Domain layer must be framework-free.** No SQLAlchemy, FastAPI, or Slack imports in `src/domain/`.
- **Application services receive repositories as dependencies.** No direct DB or API access.
- **Infrastructure implements repository ports.** Each ORM model must provide `to_domain()` and `from_domain()`.
- **Interfaces are thin.** Slack handlers and API routes delegate to application services.

## Global Conventions

- Python 3.12 with `from __future__ import annotations`.
- All I/O is async (`async/await`).
- Absolute imports from `src.*`.
- UUID v4 IDs for all entities.
- `structlog` for logging with context.
- `pydantic-settings` for configuration.
- pytest + pytest-asyncio for tests.

## Workflow

1. Check `docs/02-kanban.md` for the active task.
2. Read the corresponding block in `docs/01-plan-de-ejecucion.md`.
3. Implement, test, and validate acceptance criteria.
4. Update `docs/02-kanban.md` and any other affected docs.
5. Create an atomic commit.
