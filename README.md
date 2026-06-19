# Scrum Master Bot

Asistente digital para equipos Scrum que automatiza daily standups, monitorea pull requests, detecta riesgos y genera reportes directamente en Slack. Integrado con GitHub y potenciado con IA generativa a través de OpenRouter.

> **Estado:** MVP funcional. Todos los bloques del plan de ejecución están implementados y la suite de tests pasa. Ver [`docs/02-kanban.md`](docs/02-kanban.md) para el detalle de tareas.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.12 |
| Framework Web | FastAPI + Uvicorn |
| Integraciones | Slack Bolt, GitHub REST API, OpenRouter API |
| Base de Datos | PostgreSQL 16 + SQLAlchemy 2.0 async + Alembic |
| Scheduler | APScheduler |
| Excel | openpyxl |
| Logging | structlog |
| Testing | pytest + pytest-asyncio |
| Infraestructura | Docker + Docker Compose |

---

## Arquitectura

El proyecto sigue una arquitectura limpia / hexagonal con separación de capas:

```text
src/
├── domain/           # Entidades, enums, excepciones, puertos (interfaces)
├── application/      # Casos de uso y servicios de aplicación
├── infrastructure/   # Repositorios SQLAlchemy, clientes externos, scheduler, ORM
└── interfaces/       # Adaptadores Slack y API REST
```

| Directorio | Responsabilidad |
|------------|-----------------|
| `src/domain/` | Modelos de dominio puros (`Team`, `Member`, `Sprint`, `StandupResponse`, etc.), excepciones de negocio y repositorios abstractos. Sin dependencias de frameworks. |
| `src/application/` | Servicios que orquestan la lógica de negocio (`StandupService`, `GitHubService`, `RiskService`, `ReportService`, etc.). |
| `src/infrastructure/` | Implementaciones concretas: repositorios SQLAlchemy, `GitHubClient`, `SlackNotifier`, `AIClient`, `SchedulerService`, modelos ORM y configuración de DB. |
| `src/interfaces/` | Handlers de Slack Bolt (comandos, modales, eventos) y endpoints FastAPI. |
| `tests/` | Tests unitarios e integración. |

Más detalles en [`docs/00-especificacion-completa.md`](docs/00-especificacion-completa.md).

---

## Documentación del Proyecto

| Archivo | Propósito |
|---------|-----------|
| [`docs/00-especificacion-completa.md`](docs/00-especificacion-completa.md) | Visión, objetivos, arquitectura, modelo de dominio y backlog completo. |
| [`docs/01-plan-de-ejecucion.md`](docs/01-plan-de-ejecucion.md) | Plan de implementación bloque por bloque. |
| [`docs/02-kanban.md`](docs/02-kanban.md) | Tablero de desarrollo con tareas, prioridades y estado actual. |
| [`docs/03-convenciones-de-desarrollo.md`](docs/03-convenciones-de-desarrollo.md) | Convenciones de código, commits, tests y documentación. |
| [`docs/04-decisiones-de-arquitectura.md`](docs/04-decisiones-de-arquitectura.md) | Decisiones técnicas importantes (ADRs). |
| [`docs/05-changelog.md`](docs/05-changelog.md) | Registro de cambios por versión. |

---

## Instalación en Slack (para desarrolladores)

El bot funciona con **Socket Mode** (no necesitas exponer una URL pública). La forma
más rápida de crear la app de Slack con todos los comandos, scopes y eventos es con
el **App Manifest**:

### 1. Crear la app desde el manifiesto

1. Ve a [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From an app manifest**.
2. Elige tu workspace y pega este manifiesto (YAML):

```yaml
display_information:
  name: Scrum Master Bot
  description: Asistente Scrum que automatiza dailies, reportes y seguimiento en Excel.
  background_color: "#1f4e78"
features:
  bot_user:
    display_name: scrum-bot
    always_online: true
  app_home:
    home_tab_enabled: true
    messages_tab_enabled: true
    messages_tab_read_only_enabled: false
  slash_commands:
    - { command: /scrum, description: Abre el modal de daily standup }
    - { command: /mis-tareas, description: Tus tareas activas }
    - { command: /todas-las-tareas, description: Tareas activas por responsable }
    - { command: /crear-tarea, description: Crea una tarea (modal) }
    - { command: /editar, description: Edita o elimina una tarea }
    - { command: /avance, description: "Actualiza el % de una tarea", usage_hint: "[ID] [0-100]" }
    - { command: /evidencia, description: "Adjunta un enlace de evidencia", usage_hint: "[ID] [URL]" }
    - { command: /progreso, description: Avance por objetivo }
    - { command: /gantt, description: Cronograma en Mermaid }
    - { command: /bitacora, description: Proyecto, objetivo general y específicos }
    - { command: /editar-bitacora, description: Edita la bitácora (modal) }
    - { command: /descargar-excel, description: Descarga la última versión del Excel }
    - { command: /riesgos, description: Riesgos activos }
    - { command: /bloqueos, description: Bloqueos reportados hoy }
    - { command: /sprint, description: Información del sprint activo }
    - { command: /metricas, description: Métricas del sprint }
    - { command: /reporte, description: Reporte diario con IA }
    - { command: /github, description: Sincroniza Pull Requests }
    - { command: /set-canal-reportes, description: Define el canal de reportes }
    - { command: /ayuda-scrum, description: Guía rápida de uso }
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - chat:write
      - commands
      - files:read
      - files:write
      - im:history
      - users:read
settings:
  event_subscriptions:
    bot_events:
      - app_home_opened
      - app_mention
      - message.im
  interactivity:
    is_enabled: true
  socket_mode_enabled: true
  org_deploy_enabled: false
  token_rotation_enabled: false
```

### 2. Generar tokens

- **Socket Mode token (`xapp-...`):** *Basic Information* → *App-Level Tokens* → *Generate Token* con el scope `connections:write`. Va en `SLACK_APP_TOKEN`.
- **Bot token (`xoxb-...`):** *OAuth & Permissions* → *Install to Workspace*. Copia el *Bot User OAuth Token* en `SLACK_BOT_TOKEN`.
- **Signing secret:** *Basic Information* → *App Credentials* → *Signing Secret* en `SLACK_SIGNING_SECRET`.

### 3. Invitar el bot y configurar el canal

1. En el canal de tu equipo: `/invite @scrum-bot`.
2. Ejecuta `/set-canal-reportes` en ese canal para que reciba los reportes automáticos.
3. Para sincronizar el Excel manualmente, envíaselo por **mensaje directo** (DM) al bot.

> El bot detecta el `SLACK_APP_TOKEN` (`xapp-...`) y abre la conexión Socket Mode
> automáticamente al arrancar; no necesitas Request URLs ni túnel.

---

## Primeros Pasos

### 1. Clonar y configurar

```bash
git clone <repo-url>
cd ScrumSlack-Bot
cp .env.example .env
cp project_tracking.example.xlsx project_tracking.xlsx
```

Edita el `.env` con tus credenciales. 
**Importante:** Para desarrollo local sin exponer un endpoint HTTP, rellena `SLACK_APP_TOKEN` con un token `xapp-...` de tu app en Slack y asegúrate de activar el **Socket Mode**. El bot lo detectará y se conectará automáticamente.

### 2. Levantar la aplicación

```bash
docker compose up --build
```

### 3. Aplicar migraciones

```bash
docker compose exec app alembic upgrade head
```

### 4. Verificar health check

```bash
curl http://localhost:3000/api/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

---

## Tests

Se recomienda ejecutar los tests dentro del contenedor Docker para garantizar un entorno consistente:

```bash
# Levantar app + base de datos
docker compose up -d --build

# Ejecutar toda la suite dentro del contenedor
docker compose exec app pytest -q

# Ejecutar tests de Docker build/compose en el host (requiere Docker CLI)
python -m pytest tests/test_infrastructure.py -q
```

**Estado actual:** 240 passed, 2 skipped. Los 2 skipped requieren Docker CLI y se ejecutan en el host.

---

## Comandos de Slack

**Planificación (Excel)**

| Comando | Descripción |
|---------|-------------|
| `/bitacora` | Muestra proyecto, objetivo general y objetivos específicos. |
| `/editar-bitacora` | Edita la bitácora (proyecto, OG, OEs) desde un modal. |
| `/crear-tarea` | Crea una tarea (ID autogenerado, estado inicial NO COMENZADO). |
| `/editar` | Edita o elimina una tarea existente. |
| `/avance [ID] [0-100]` | Actualiza el % de una tarea (deriva el Estado). |
| `/evidencia [ID] [URL]` | Adjunta un enlace de evidencia (queda como hipervínculo). |
| `/mis-tareas` | Tus tareas activas con botón para actualizar. |
| `/todas-las-tareas` | Tareas activas agrupadas por responsable. |
| `/progreso` | Avance por objetivo (OE) con barra de progreso. |
| `/gantt` | Cronograma en formato Mermaid. |
| `/descargar-excel` | Descarga la última versión del Excel. |

**Actividad del equipo (DB)**

| Comando | Descripción |
|---------|-------------|
| `/scrum` | Abre el modal de daily standup (permite marcar tareas completadas). |
| `/riesgos` | Riesgos activos con severidad (🟢 BAJA … 🔴 CRÍTICA). |
| `/bloqueos` | Bloqueos reportados hoy. |
| `/sprint` | Información del sprint activo. |
| `/metricas` | Métricas del sprint. |
| `/reporte` | Reporte diario (standups + PRs + riesgos + progreso del Excel). |
| `/github` | Sincroniza Pull Requests desde GitHub. |
| `/set-canal-reportes` | Define el canal de reportes automáticos. |
| `/ayuda-scrum` | Guía rápida de uso. |

> El Excel (`project_tracking.xlsx`) es la fuente de verdad de la planificación
> (hojas `Dashboard`, `Bitácora`, `Planificación`, `Administración`, `Evidencia`,
> `Gantt`); la base de datos lo es de la actividad diaria. Ver
> [`docs/04-decisiones-de-arquitectura.md`](docs/04-decisiones-de-arquitectura.md).

---

## Jobs Programados

El `SchedulerService` ejecuta:

| Job | Frecuencia | Descripción |
|-----|------------|-------------|
| Recordatorio standup | diario `STANDUP_TIME` (09:00) | Envía mensaje con botón "Responder Standup". |
| Resumen diario | diario `SUMMARY_TIME` (17:00) | Genera y envía el reporte del día. |
| Sync de GitHub | cada `GITHUB_SYNC_INTERVAL_MINUTES` (30) | Sincroniza Pull Requests (si hay `GITHUB_DEFAULT_ORG`). |
| Detección de riesgos | cada `RISK_DETECTION_INTERVAL_MINUTES` (60) | Detecta riesgos nuevos y los notifica al canal. |

> Los intervalos se pueden desactivar poniendo su valor en `0`.

---

## Convenciones Rápidas

- **Commits atómicos:** un cambio lógico por commit.
- **Tests obligatorios:** cada servicio o regla de negocio debe incluir tests.
- **Documentación actualizada:** cualquier cambio de arquitectura, configuración o flujo debe reflejarse en `docs/`.
- **Idioma del código:** nombres en inglés, docstrings de negocio en español, docstrings de API en inglés.

Para el detalle completo ver [`docs/03-convenciones-de-desarrollo.md`](docs/03-convenciones-de-desarrollo.md).

---

## Contribuir

1. Leer `docs/01-plan-de-ejecucion.md` y `docs/02-kanban.md`.
2. Trabajar un bloque a la vez.
3. Escribir tests antes o junto con la implementación.
4. Actualizar documentación y kanban antes de hacer commit.
5. Seguir las convenciones de commits de `docs/03-convenciones-de-desarrollo.md`.

---

## Licencia

Por definir.
