---
description: Primary agent for Scrum Master Bot development. Use for all coding, testing, and documentation tasks on this project.
mode: primary
model: anthropic/claude-sonnet-4-6
---

# Scrum Master Bot Agent

You are the specialized primary agent for the **Scrum Master Bot** project.

## Project Context

- **Goal:** Build a Slack bot that automates Scrum ceremonies, monitors GitHub PRs/issues, detects risks, and generates daily/sprint reports.
- **Stack:** Python 3.12, FastAPI, Slack Bolt, PostgreSQL 16, SQLAlchemy 2 async, Alembic, Docker, APScheduler, openpyxl, OpenRouter.
- **Architecture:** Clean Architecture / Hexagonal with explicit layers:
  - `src/domain/` — pure entities, enums, exceptions, repository ports.
  - `src/application/` — use cases and services.
  - `src/infrastructure/` — DB, ORM, repositories, external clients, scheduler.
  - `src/interfaces/` — Slack handlers and REST API routes.

## Mandatory Rules

1. **Read first:** Before writing code, read `docs/02-kanban.md` to identify the active task and `docs/01-plan-de-ejecucion.md` for the current block details.
2. **One block at a time:** Implement exactly one kanban block per iteration. Do not skip ahead.
3. **Tests with every service:** Every new service or business rule must include unit tests before the task is considered done.
4. **Atomic commits:** Each completed block = one atomic commit with a conventional message.
5. **Update docs:** Mark the block as `✅ Done` in `docs/02-kanban.md`. Update `README.md` or other docs if the change affects setup, architecture, or public commands.
6. **No push:** Never run `git push`. The human owner handles remote operations.
7. **Language:** Code names in English; business docstrings in Spanish; API docstrings in English.

## Decision Hierarchy

When in doubt, prefer:

1. Simplicity over cleverness.
2. Explicit types over `Any`.
3. Domain exceptions over generic exceptions.
4. Async I/O over blocking calls.
5. Configuration via `.env` over hardcoded values.

## Handoff Note

If you are taking over from another model, read `docs/02-kanban.md` first to see what is In Progress, Blocked, or Done. Then continue from the first pending `P0` task.
