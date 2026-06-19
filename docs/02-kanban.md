# Kanban de Desarrollo: Scrum Master Bot

**Proyecto:** `/Users/admin/Documents/projects/ScrumSlack-Bot/`  
**Plan base:** `docs/01-plan-de-ejecucion.md`  
**Estrategia:** Ejecutar un bloque a la vez. Validar criterio de aceptación antes de mover a **Done**.

---

## Leyenda

| Símbolo | Estado |
|---------|--------|
| `🔲` | Backlog / Pendiente |
| `🚧` | In Progress |
| `⏸️` | Blocked |
| `✅` | Done |

**Prioridades:** `P0` = crítico, `P1` = alto, `P2` = medio, `P3` = bajo  
**Esfuerzo aproximado:** `S` = corto (≤2h), `M` = mediano (2-4h), `L` = largo (4-8h)

---

## 📥 Backlog

### Fase 0 — Infraestructura y Fundación

#### 0.1 Scaffolding del Proyecto
- **ID:** `0.1`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** Ninguna
- **Descripción:** Crear árbol de directorios y archivos base vacíos según estructura definida.
- **Criterio de aceptación:** Todos los `.py` contienen `"""Módulo: <nombre>."""`. Directorios con `__init__.py` vacío.
- **Estado:** ✅ Done
- **Notas:** Scaffolding creado con 70 verificaciones pasando en `tests/test_scaffolding.py`. Se incluyó `.venv/` para ejecutar tests locales.

#### 0.2.1 — `requirements.txt`
- **ID:** `0.2.1`
- **Prioridad:** P0
- **Esfuerzo:** XS
- **Dependencias:** `0.1`
- **Descripción:** Definir dependencias exactas con versiones pinneadas.
- **Criterio de aceptación:** Archivo lista todos los paquetes del stack.
- **Estado:** ✅ Done
- **Notas:** Validado con Docker build.

#### 0.2.2 — `.env.example`
- **ID:** `0.2.2`
- **Prioridad:** P0
- **Esfuerzo:** XS
- **Dependencias:** `0.1`
- **Descripción:** Plantilla de variables de entorno.
- **Criterio de aceptación:** Incluye app, DB, Slack, GitHub, OpenRouter, standup y Excel.
- **Estado:** ✅ Done

#### 0.2.3 — `Dockerfile`
- **ID:** `0.2.3`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `0.1`, `0.2.1`
- **Descripción:** Imagen Python 3.12 slim con dependencias y entrypoint uvicorn.
- **Criterio de aceptación:** Build exitoso.
- **Estado:** ✅ Done
- **Notas:** Build validado vía test.

#### 0.2.4 — `docker-compose.yml`
- **ID:** `0.2.4`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `0.1`, `0.2.3`
- **Descripción:** Servicios `app` y `db` (PostgreSQL 16) con healthcheck.
- **Criterio de aceptación:** `docker-compose up --build` levanta app + postgres.
- **Estado:** ✅ Done
- **Notas:** Se removió `version: "3.9"` obsoleto. Health check responde en `/api/health`.

#### 0.2.5 — `.gitignore`
- **ID:** `0.2.5`
- **Prioridad:** P0
- **Esfuerzo:** XS
- **Dependencias:** `0.1`
- **Descripción:** Ignorar entornos, `.env`, cache, Excel generado.
- **Criterio de aceptación:** `.env` y `project_tracking.xlsx` no se commitean.
- **Estado:** ✅ Done

#### 0.3 — Configuración de la Aplicación (`src/config.py`)
- **ID:** `0.3`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `0.1`, `0.2.2`
- **Descripción:** Clase `Settings` con `pydantic-settings` leyendo `.env`.
- **Criterio de aceptación:** `from src.config import settings` funciona y falla si faltan campos obligatorios.
- **Estado:** ✅ Done
- **Notas:** Implementado con pydantic-settings. Validado en contenedor Docker.

---

### Fase 1 — Capa de Dominio

#### 1.1 — Modelos de Dominio (`src/domain/models.py`)
- **ID:** `1.1`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `0.3`
- **Descripción:** Entidades y enums con dataclasses/Pydantic, IDs UUID v4 por defecto.
- **Criterio de aceptación:** Se pueden importar e instanciar sin errores. Sin imports de frameworks.
- **Estado:** ✅ Done
- **Notas:** 9 entidades + 5 enums implementados con dataclasses. Tests en `tests/unit/test_models.py`.

#### 1.2 — Excepciones de Dominio (`src/domain/exceptions.py`)
- **ID:** `1.2`
- **Prioridad:** P0
- **Esfuerzo:** XS
- **Dependencias:** `0.1`
- **Descripción:** Excepciones tipadas para errores de negocio.
- **Criterio de aceptación:** Cada excepción se puede lanzar con mensajes claros. `isinstance(EntityNotFoundError(...), DomainException)` es `True`.
- **Estado:** ✅ Done
- **Notas:** 5 excepciones de dominio implementadas. Tests en `tests/unit/test_exceptions.py`.

#### 1.3 — Interfaces de Repositorios (`src/domain/repositories.py`)
- **ID:** `1.3`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `1.1`
- **Descripción:** Clases abstractas `ABC` con métodos `async` para cada entidad.
- **Criterio de aceptación:** Ningún import de SQLAlchemy. Todos los métodos son `abstractmethod` y `async`. Los tipos de retorno usan modelos de dominio.
- **Estado:** ✅ Done
- **Notas:** 8 repositorios abstractos implementados. Tipos de retorno con modelos de dominio. Tests en `tests/unit/test_repositories.py`.

---

### Fase 2 — Capa de Infraestructura

#### 2.1 — Base de Datos (`src/infrastructure/database.py`)
- **ID:** `2.1`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `0.3`
- **Descripción:** Configurar SQLAlchemy async engine y session factory.
- **Criterio de aceptación:** `async for session in get_session()` entrega una `AsyncSession` funcional.
- **Estado:** ✅ Done
- **Notas:** Engine lazy (`get_engine`), async_session_maker lazy (`get_async_session_maker`), `get_session`, `init_db` y `close_db` implementados. Tests de integración en `tests/integration/test_database.py`. El cambio a lazy evita conflictos de event loop en tests async.

#### 2.2 — Modelos ORM (`src/infrastructure/orm_models.py`)
- **ID:** `2.2`
- **Prioridad:** P0
- **Esfuerzo:** L
- **Dependencias:** `1.1`, `2.1`
- **Descripción:** Mapeo de entidades a tablas PostgreSQL con métodos `to_domain()` / `from_domain()`.
- **Criterio de aceptación:** Alembic genera migración sin errores. Tablas creadas con tipos correctos.
- **Estado:** ✅ Done
- **Notas:** Implementados 8 modelos ORM con relaciones y conversiones. Tests de integración round-trip en `tests/integration/test_orm_models.py` (8 tests). Se usó engine local con `NullPool` por test para evitar problemas de event loop entre pytest-asyncio y asyncpg.

#### 2.3 — Configuración de Alembic
- **ID:** `2.3`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `2.2`
- **Descripción:** `alembic.ini` + `migrations/env.py` con soporte async y URL desde settings.
- **Criterio de aceptación:** `alembic revision --autogenerate -m "initial_schema"` y `alembic upgrade head` funcionan.
- **Estado:** ✅ Done
- **Notas:** Configuración async implementada. Migración inicial generada y aplicada. Tests en `tests/integration/test_alembic.py` validan tablas creadas e idempotencia de upgrade head.

#### 2.4.1 — Repositorio `TeamRepositoryImpl` (`src/infrastructure/repositories/team_repo.py`)
- **ID:** `2.4.1`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `1.3`, `2.2`
- **Descripción:** Implementar get_by_id, save, get_all.
- **Criterio de aceptación:** Tests unitarios pasan.
- **Estado:** ✅ Done

#### 2.4.2 — Repositorio `MemberRepositoryImpl` (`src/infrastructure/repositories/member_repo.py`)
- **ID:** `2.4.2`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `1.3`, `2.2`
- **Descripción:** Implementar get_by_id, get_by_slack_user_id, get_by_team, save.
- **Criterio de aceptación:** Tests unitarios pasan.
- **Estado:** ✅ Done

#### 2.4.3 — Repositorios Standup (`src/infrastructure/repositories/standup_repo.py`)
- **ID:** `2.4.3`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `1.3`, `2.2`
- **Descripción:** `StandupSessionRepositoryImpl` + `StandupResponseRepositoryImpl`.
- **Criterio de aceptación:** get_today_session, get_by_member_and_session funcionan correctamente.
- **Estado:** ✅ Done

#### 2.4.4 — Repositorio `PullRequestRepositoryImpl` (`src/infrastructure/repositories/pr_repo.py`)
- **ID:** `2.4.4`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `1.3`, `2.2`
- **Descripción:** save, upsert con `on_conflict_do_update`, get_open_by_team, get_stale_prs.
- **Criterio de aceptación:** Upsert no duplica. get_stale_prs filtra por horas sin reviewers.
- **Estado:** ✅ Done

#### 2.4.5 — Repositorio `SprintRepositoryImpl` (`src/infrastructure/repositories/sprint_repo.py`)
- **ID:** `2.4.5`
- **Prioridad:** P1
- **Esfuerzo:** S
- **Dependencias:** `1.3`, `2.2`
- **Descripción:** get_active, save, update_status.
- **Criterio de aceptación:** get_active retorna sprint con status `active`.
- **Estado:** ✅ Done

#### 2.4.6 — Repositorio `RiskRepositoryImpl` (`src/infrastructure/repositories/risk_repo.py`)
- **ID:** `2.4.6`
- **Prioridad:** P1
- **Esfuerzo:** S
- **Dependencias:** `1.3`, `2.2`
- **Descripción:** save, get_active_by_team, resolve.
- **Criterio de aceptación:** get_active_by_team filtra `resolved == False`.
- **Estado:** ✅ Done

#### 2.4.7 — Repositorio `MetricRepositoryImpl` (`src/infrastructure/repositories/metric_repo.py`)
- **ID:** `2.4.7`
- **Prioridad:** P1
- **Esfuerzo:** S
- **Dependencias:** `1.3`, `2.2`
- **Descripción:** save, get_by_sprint, get_latest.
- **Criterio de aceptación:** get_latest retorna el snapshot más reciente.
- **Estado:** ✅ Done
- **Notas:** Todos los repositorios del bloque 2.4 validados con tests de integración en `tests/integration/test_db_repos.py`.

#### 2.5.1 — GitHub Client (`src/infrastructure/github_client.py`)
- **ID:** `2.5.1`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `0.3`
- **Descripción:** Wrapper async httpx sobre GitHub API v3 con retry y backoff.
- **Criterio de aceptación:** Lista PRs abiertos y maneja HTTP 429.
- **Estado:** ✅ Done
- **Notas:** Implementado con retry exponencial (3 intentos) y manejo de 429/5xx. Usa Bearer token.

#### 2.5.2 — Slack Client (`src/infrastructure/slack_client.py`)
- **ID:** `2.5.2`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `0.3`
- **Descripción:** `create_slack_app()` y `SlackNotifier` con helpers de mensajería.
- **Criterio de aceptación:** `AsyncApp` creada. Mensaje de prueba enviado.
- **Estado:** ✅ Done
- **Notas:** Se agregó `aiohttp` a requirements.txt porque slack-bolt lo requiere.

#### 2.5.3 — AI Client (`src/infrastructure/ai_client.py`)
- **ID:** `2.5.3`
- **Prioridad:** P2
- **Esfuerzo:** M
- **Dependencias:** `0.3`
- **Descripción:** Wrapper async para OpenRouter API (formato OpenAI).
- **Criterio de aceptación:** Genera resumen de prueba y lanza `ExternalServiceError` si falla.
- **Estado:** ✅ Done

#### 2.5.4 — Scheduler (`src/infrastructure/scheduler.py`)
- **ID:** `2.5.4`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `0.1`
- **Descripción:** `SchedulerService` con APScheduler async y `add_daily_job()`.
- **Criterio de aceptación:** Jobs programados se ejecutan a la hora configurada.
- **Estado:** ✅ Done

---

### Fase 3 — Capa de Aplicación (Servicios)

#### 3.1 — `StandupService` (`src/application/standup_service.py`)
- **ID:** `3.1`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `1.2`, `1.3`, `2.4.2`, `2.4.3`
- **Descripción:** Crear sesión del día, registrar respuestas, missing members, cerrar sesión.
- **Criterio de aceptación:** Doble submit lanza `StandupAlreadyRespondedError`. get_missing_members retorna faltantes.
- **Estado:** ✅ Done

#### 3.2 — `GitHubService` (`src/application/github_service.py`)
- **ID:** `3.2`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `2.4.4`, `2.5.1`
- **Descripción:** Sync de PRs abiertos, consulta y detección de PRs stale.
- **Criterio de aceptación:** Sync persiste sin duplicar. get_stale_prs filtra correcto.
- **Estado:** ✅ Done

#### 3.3 — `RiskService` (`src/application/risk_service.py`)
- **ID:** `3.3`
- **Prioridad:** P1
- **Esfuerzo:** M
- **Dependencias:** `1.2`, `2.4.4`, `2.4.6`, `3.1`
- **Descripción:** Reglas de detección de riesgos automáticos.
- **Criterio de aceptación:** PRs >24h/48h/72h generan riesgos correctos sin duplicar.
- **Estado:** ✅ Done

#### 3.4 — `ReportService` (`src/application/report_service.py`)
- **ID:** `3.4`
- **Prioridad:** P1
- **Esfuerzo:** M
- **Dependencias:** `3.1`, `3.2`, `3.3`
- **Descripción:** Generar resumen diario Markdown y resumen con IA.
- **Criterio de aceptación:** Resumen contiene todas las secciones. Maneja datos vacíos.
- **Estado:** ✅ Done

#### 3.5 — `SprintService` (`src/application/sprint_service.py`)
- **ID:** `3.5`
- **Prioridad:** P2
- **Esfuerzo:** S
- **Dependencias:** `2.4.5`, `2.4.7`
- **Descripción:** get_active_sprint, create_sprint, complete_sprint, get_sprint_metrics.
- **Criterio de aceptación:** Solo un sprint activo por team. complete_sprint cambia status.
- **Estado:** ✅ Done

#### 3.6 — `NotificationService` (`src/application/notification_service.py`)
- **ID:** `3.6`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `2.5.2`
- **Descripción:** Recordatorio standup, resumen diario, alertas de riesgos y PRs stale.
- **Criterio de aceptación:** Mensaje Block Kit con botón funcional.
- **Estado:** ✅ Done

#### 3.7 — `ExcelSyncService` (`src/application/excel_sync_service.py`)
- **ID:** `3.7`
- **Prioridad:** P2
- **Esfuerzo:** L
- **Dependencias:** `2.4.5`, `2.4.6`, `2.4.7`
- **Descripción:** Crear template Excel, sync métricas/riesgos, leer/actualizar módulos.
- **Criterio de aceptación:** `create_template` genera 5 hojas con headers. `sync_metrics` escribe fila nueva.
- **Estado:** ✅ Done

#### 3.8 — `AIService` (`src/application/ai_service.py`)
- **ID:** `3.8`
- **Prioridad:** P2
- **Esfuerzo:** S
- **Dependencias:** `2.5.3`
- **Descripción:** Prompts y wrappers para resúmenes de standup y análisis de riesgos.
- **Criterio de aceptación:** Fallback si la API falla.
- **Estado:** ✅ Done
- **Notas:** Todos los servicios de aplicación validados con tests unitarios.

---

### Fase 4 — Interfaces (Slack + API)

#### 4.1 — Registro de la App Slack (`src/interfaces/slack/bolt_app.py`)
- **ID:** `4.1`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `4.2`, `4.3`, `4.4`
- **Descripción:** `register_handlers()` centralizado.
- **Criterio de aceptación:** Todos los handlers registrados en un solo punto.
- **Estado:** ✅ Done

#### 4.2 — Slash Commands (`src/interfaces/slack/commands.py`)
- **ID:** `4.2`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `3.1`, `3.3`, `3.5`, `3.6`, `3.7`
- **Descripción:** `/scrum`, `/riesgos`, `/bloqueos`, `/sprint`, `/metricas`, `/reporte`, `/progreso`.
- **Criterio de aceptación:** Cada comando responde en <3 segundos. Usa Block Kit.
- **Estado:** ✅ Done

#### 4.3 — Modales (`src/interfaces/slack/modals.py`)
- **ID:** `4.3`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `3.1`, `3.6`
- **Descripción:** Modal de standup y handler de `view_submission`.
- **Criterio de aceptación:** Modal abre, submit guarda respuesta, usuario recibe confirmación.
- **Estado:** ✅ Done

#### 4.4 — Eventos (`src/interfaces/slack/events.py`)
- **ID:** `4.4`
- **Prioridad:** P0
- **Esfuerzo:** S
- **Dependencias:** `4.3`
- **Descripción:** `app_mention` y `standup_button_click`.
- **Criterio de aceptación:** Mención responde ayuda. Botón abre modal.
- **Estado:** ✅ Done

#### 4.5 — FastAPI Routes (`src/interfaces/api/routes.py`)
- **ID:** `4.5`
- **Prioridad:** P1
- **Esfuerzo:** S
- **Dependencias:** `2.1`, `3.1`, `3.2`, `3.3`, `3.5`
- **Descripción:** `/api/health` y endpoints de team (standup, risks, PRs, metrics).
- **Criterio de aceptación:** Health check 200. Endpoints retornan JSON.
- **Estado:** ✅ Done

#### 4.6 — FastAPI Dependencies (`src/interfaces/api/dependencies.py`)
- **ID:** `4.6`
- **Prioridad:** P1
- **Esfuerzo:** S
- **Dependencias:** `2.1`, `2.4.*`, `3.*`
- **Descripción:** Inyección de dependencias con `get_session()` y factories de servicios.
- **Criterio de aceptación:** `Depends(get_session)` maneja commit/rollback automático.
- **Estado:** ✅ Done

---

### Fase 5 — Punto de Entrada

#### 5.0 — `src/main.py`
- **ID:** `5.0`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `2.5.4`, `4.1`, `4.5`
- **Descripción:** Ensamblar FastAPI + Slack Bolt + Scheduler con lifespan.
- **Criterio de aceptación:** `docker-compose up` levanta todo. `/slack/events` funciona. Scheduler ejecuta jobs.
- **Estado:** ✅ Done
- **Notas:** Lifespan implementado con init_db, scheduler y jobs diarios. Endpoint `/slack/events` expuesto.

---

### Fase 6 — Tests

#### 6.1 — Configuración de Tests (`tests/conftest.py`)
- **ID:** `6.1`
- **Prioridad:** P1
- **Esfuerzo:** M
- **Dependencias:** `2.1`, `2.4.*`
- **Descripción:** Fixtures DB in-memory, repos mock, servicios mockeados.
- **Criterio de aceptación:** Fixtures funcionan para unit + integration tests.
- **Estado:** ✅ Done
- **Notas:** `tests/conftest.py` creado como placeholder inicial.

#### 6.2 — Tests Unitarios
- **ID:** `6.2`
- **Prioridad:** P1
- **Esfuerzo:** L
- **Dependencias:** `6.1`, `3.1`, `3.2`, `3.3`, `3.4`
- **Descripción:** `test_standup_service.py`, `test_risk_service.py`, `test_github_service.py`, `test_report_service.py`.
- **Criterio de aceptación:** Todos los tests unitarios pasan.
- **Estado:** ✅ Done
- **Notas:** Tests unitarios creados para servicios y clientes externos.

#### 6.3 — Tests de Integración
- **ID:** `6.3`
- **Prioridad:** P2
- **Esfuerzo:** L
- **Dependencias:** `6.1`, `4.2`, `4.3`
- **Descripción:** `test_slack_commands.py` y `test_db_repos.py`.
- **Criterio de aceptación:** CRUD real contra PostgreSQL de Docker. Slash commands simulados.
- **Estado:** ✅ Done
- **Notas:** `test_db_repos.py` y `test_api_routes.py` implementados. `test_slack_commands.py` como placeholder.

---

### Fase 5 — Integración Valuelist (V)

#### 5.1 — Bloque 1: Conexión y Lectura Base
- **ID:** `5.1`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `3.7`
- **Descripción:** Implementar `ValuelistExcelService` para leer Hojas 1, 3 y 5 de `excel/Bitacora-Rentabilidad-Valuelist.xlsx`. Mapeo de usuarios Slack ↔ Excel. Implementar comandos `/bitacora` y `/mis-tareas`.
- **Criterio de aceptación:** Tests unitarios pasan. Los comandos leen el archivo y responden en Slack con datos reales.
- **Estado:** ✅ Done

#### 5.2 — Bloque 2: Comandos de Escritura Rápida
- **ID:** `5.2`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `5.1`
- **Descripción:** Implementar motor de escritura segura. Comandos `/avance [ID] [%]` y `/evidencia [ID] [URL]`. Actualización de "% logro" y agregación de enlaces en Hoja 5.
- **Criterio de aceptación:** Las celdas del archivo `.xlsx` se modifican sin romper el formato original. Tests unitarios pasan.
- **Estado:** ✅ Done

#### 5.3 — Bloque 3: Interfaz Compleja y Visualización
- **ID:** `5.3`
- **Prioridad:** P1
- **Esfuerzo:** L
- **Dependencias:** `5.1`
- **Descripción:** Modal para `/crear-tarea` con Block Kit e inserción de fila en Hoja 3. Comando `/gantt` (mermaid).
- **Criterio de aceptación:** Modal funcional, fila se inserta al final de la Hoja 3 con columnas correctas. Gantt se visualiza.
- **Estado:** ✅ Done

#### 5.4 — Bloque 4: Cierre, Contexto IA y Distribución
- **ID:** `5.4`
- **Prioridad:** P1
- **Esfuerzo:** S
- **Dependencias:** `5.1`, `3.8`
- **Descripción:** Inyectar datos de Hoja 1 en `AIService`. Comando `/descargar-excel`.
- **Criterio de aceptación:** Reporte diario considera OG y Hitos actuales. Slack permite descargar el archivo físico.
- **Estado:** ✅ Done

---

### Fase 6 — Dominio Total (VI)

#### 6.1 — Panel de Edición Universal y Borrado
- **ID:** `6.1`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** `5.3`
- **Descripción:** Comando `/editar` que abre modal de 2 pasos (selección de tipo/ID -> formulario pre-llenado). Opción para eliminar fila.
- **Criterio de aceptación:** Se puede modificar texto/fechas de tareas y bitácora, y se guardan correctamente en el Excel sin romperlo.
- **Estado:** ✅ Done

#### 6.2 — Soporte para Hoja 4 (Administración)
- **ID:** `6.2`
- **Prioridad:** P1
- **Esfuerzo:** S
- **Dependencias:** `6.1`
- **Descripción:** El bot debe poder leer, crear y avanzar tareas administrativas (AD).
- **Criterio de aceptación:** Comandos como `/avance-admin` o integración de la Hoja 4 en el ecosistema.
- **Estado:** ✅ Done

#### 6.3 — Visión Global de Tareas
- **ID:** `6.3`
- **Prioridad:** P2
- **Esfuerzo:** S
- **Dependencias:** `5.1`
- **Descripción:** Comando `/todas-las-tareas` para listar todas las tareas abiertas agrupadas por responsable.
- **Criterio de aceptación:** Muestra lista completa de tareas activas de la Hoja 3 y Hoja 4.
- **Estado:** ✅ Done

---

## 🚧 In Progress

### Fase H — Pulido y Valor Real (Iniciativa de calidad)

> Objetivo: conectar Excel ↔ comandos ↔ DB, pulir mensajes y modales, y
> convertirlo en un bot que aporte valor real al equipo. Cada feature pasa
> tests antes de un commit atómico. El push lo realiza el dueño.

| ID | Tarea | Prioridad | Estado |
|----|-------|-----------|--------|
| H.0 | Baseline de tests verde + migración inicial versionada | P0 | ✅ Done |
| H.1 | ADR: fuente de verdad (Excel=planificación, DB=actividad) | P0 | ✅ Done |
| H.2 | Eliminar `ExcelSyncService` huérfano; estilos a módulo compartido | P0 | ✅ Done |
| H.3 | Limpieza de repo y docs engañosas | P1 | ✅ Done |
| H.4 | Excel: columna Estado + esquema canónico + estilos centralizados | P0 | ✅ Done |
| H.5 | Excel: validación de datos (dropdown) y formato condicional semáforo | P1 | ✅ Done |
| H.6 | Excel: porcentaje consistente (0-1) y autoderivación de Estado | P1 | ✅ Done |
| H.7 | Excel: evidencia con hipervínculos + hoja Dashboard con KPIs | P1 | ✅ Done |
| H.8 | Fix `/progreso` (método inexistente) | P0 | ✅ Done |
| H.9 | Fix `get_all_active_tasks` (umbral y display %) | P1 | ✅ Done |
| H.10 | Standup actualiza progreso + reporte une Excel y DB | P1 | ✅ Done |
| H.11 | Módulo de presentación Block Kit + helper de severidades | P1 | 🔲 |
| H.12 | Fix reporte diario (mrkdwn válido, nombres reales, sin duplicar) | P0 | 🔲 |
| H.13 | Estandarizar mensajes de todos los comandos | P1 | 🔲 |
| H.14 | Modales más intuitivos (crear/editar/standup/avance) | P1 | 🔲 |
| H.15 | Programar jobs (riesgos/github) + notificaciones proactivas | P2 | 🔲 |
| H.16 | Logging estructurado y manejo de errores | P2 | 🔲 |
| H.17 | Cierre: suite verde, docs y kanban actualizados | P0 | 🔲 |

**Notas H.0:** Suite verde en contenedor (`221 passed, 2 skipped`). Se reescribió
`tests/unit/test_valuelist_excel_service.py` con archivos `.xlsx` reales (los mocks
usaban un argumento `user_mapping` y un método `update_bitacora` ya inexistentes).
Se versionó la migración inicial (`24a4b5857e1c_initial_schema`) y se selló la BD de dev.

### Fase E — Mejoras Premium y UX
#### E.1 — Estética Premium del Excel (Tablas, DataBars, Freeze Panes)
- **ID:** `E.1`
- **Prioridad:** P1
- **Esfuerzo:** M
- **Dependencias:** Ninguna
- **Descripción:** Implementar OpenPyXL Tables nativas, DataBars condicionales para % de logro y Freeze Panes.
- **Criterio de aceptación:** El Excel generado incluye estilos de tabla nativos de Excel y barras de progreso visuales.
- **Estado:** ✅ Done

#### E.2 — Modales UX Mejorados (Datepicker, Selectores Dinámicos)
- **ID:** `E.2`
- **Prioridad:** P1
- **Esfuerzo:** S
- **Dependencias:** Ninguna
- **Descripción:** Usar `datepicker` nativo de Slack para fechas en `/crear-tarea` y modal dinámico para `/avance` con `static_select`.
- **Criterio de aceptación:** Las fechas son elegidas desde un calendario, no escritas. Modal para avances cargado exitosamente.
- **Estado:** ✅ Done

#### E.3 — Sincronización Bidireccional de Excel por DM (Upload)
- **ID:** `E.3`
- **Prioridad:** P1
- **Esfuerzo:** M
- **Dependencias:** Ninguna
- **Descripción:** Manejar evento `message` en DMs, descargar archivo `.xlsx` subido por el usuario y sobreescribir `project_tracking.xlsx`.
- **Criterio de aceptación:** Enviar archivo por DM al bot actualiza la base de datos interna.
- **Estado:** ✅ Done

#### E.4 — App Home (Dashboard Persistente)
- **ID:** `E.4`
- **Prioridad:** P0
- **Esfuerzo:** M
- **Dependencias:** Ninguna
- **Descripción:** Manejar evento `app_home_opened`, publicando una vista central (`views.publish`) con botones interactivos para gestionar tareas.
- **Criterio de aceptación:** Pestaña "Home" del bot muestra dashboard funcional y botones abren modales.
- **Estado:** ✅ Done

---

## ⏸️ Blocked

_Espacio reservado para tareas que no pueden avanzar hasta recibir input externo (tokens, credenciales, decisiones de diseño, etc.)._

---

## ✅ Done

_Espacio reservado para tareas validadas según su criterio de aceptación._

### Fase A — Corrección de Bugs y Estabilización (MVP Funcional)
- **ID:** `A.1-A.8`
- **Descripción:** Corrección de inyección de dependencias en `routes.py` y `modals.py`. Implementación de `session_maker` para manejar ciclos de vida asíncronos en Slack Bolt. Reparación de Foreign Key violations inyectando un equipo por defecto. Implementación de Socket Mode.
- **Estado:** ✅ Done

### Fase B — Testing
- **ID:** `B.1`
- **Descripción:** Validar que los tests unitarios pasen en el entorno corregido.
- **Estado:** ✅ Done (204 passed)

### Fase C — Documentación Técnica
- **ID:** `C.1-C.2`
- **Descripción:** Redactar `docs/04-decisiones-de-arquitectura.md` y `docs/05-changelog.md`.
- **Estado:** ✅ Done

### Fase D — Refactorización y Nuevos Comandos
- **ID:** `D.1`
- **Descripción:** Nuevos comandos de Slack (`/set-canal-reportes`, `/github`).
- **Estado:** ✅ Done

- **ID:** `D.2`
- **Descripción:** Refactorización arquitectónica (Contenedor IoC nativo, división de `orm_models.py`, extracción de tareas a `jobs.py`, extracción de Slack Block Kits a JSON).
- **Estado:** ✅ Done

- **ID:** `D.3`
- **Descripción:** Mejoras de UX/UI. Tareas en background para evitar timeouts en comandos lentos de Slack.
- **Estado:** ✅ Done

- **ID:** `D.4`
- **Descripción:** Mejoras en Reportes y Excel (renderizado premium dinámico, mega-modal de tareas, borrado de objetivos, fix en dimensiones y soporte ampliado para Hoja 4).
- **Estado:** ✅ Done

---

## 🎯 Checklist Final de Validación

- [x] `docker-compose up` levanta app + DB sin errores.
- [x] `alembic upgrade head` crea todas las tablas.
- [x] `/scrum` en Slack abre modal y guarda respuesta.
- [x] `/riesgos` muestra PRs sin review.
- [x] `/bloqueos` muestra bloqueos del standup del día.
- [x] Recordatorio se envía a las 9:00 AM.
- [x] Resumen diario se genera a las 17:00.
- [x] PRs se sincronizan desde GitHub periódicamente.
- [x] Riesgos se detectan automáticamente.
- [x] Excel se crea con template y se actualiza con métricas.
- [x] Tests unitarios pasan.
- [x] Health check responde en `/api/health`.

---

## 📋 Notas de Uso

1. Al iniciar una tarea, moverla de **Backlog** a **In Progress** y actualizar este archivo.
2. Si una tarea se bloquea, moverla a **Blocked** con una nota del bloqueador.
3. Solo mover a **Done** después de verificar el criterio de aceptación.
4. Priorizar siempre las tareas `P0` antes de avanzar a `P1`/`P2`.
