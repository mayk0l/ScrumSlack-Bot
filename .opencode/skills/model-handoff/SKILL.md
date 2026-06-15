---
name: model-handoff
description: Use when switching AI models, resuming work, or taking over the project after another model session. Loads current project state from the kanban and last completed block.
---

# Model Handoff

## First Action on Takeover

1. Read `docs/02-kanban.md`.
2. Identify columns:
   - **In Progress** — resume here if unfinished.
   - **Blocked** — resolve or escalate to user.
   - **Done** — do not repeat unless asked.
   - **Backlog** — next work items, ordered by priority.
3. Read the active block details in `docs/01-plan-de-ejecucion.md`.
4. Check recent git log and working tree status to see what was already committed or left uncommitted.

## State Recovery

- If a task is `🚧 In Progress` but no code exists, restart the block.
- If code exists but tests are missing, write tests before marking Done.
- If docs are out of sync with code, update docs before the next commit.

## Continuation Rules

- Do not start a new block until the current `🚧 In Progress` block is `✅ Done`.
- Preserve the established conventions (`docs/03-convenciones-de-desarrollo.md`).
- Ask the user only if a task is blocked or ambiguous.

## Handoff Summary Template

When leaving the project, consider appending a brief note to the active kanban task:

```
Notas de handoff:
- Archivos modificados: ...
- Tests: ...
- Bloqueador: ... (si aplica)
- Siguiente paso: ...
```
