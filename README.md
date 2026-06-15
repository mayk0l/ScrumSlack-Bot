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

## Primeros Pasos

### 1. Clonar y configurar

```bash
git clone <repo-url>
cd ScrumSlack-Bot
cp .env.example .env
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

**Estado actual:** 204 passed, 2 skipped. Los 2 skipped requieren Docker CLI y se ejecutan en el host.

---

## Comandos de Slack (MVP)

| Comando | Descripción |
|---------|-------------|
| `/scrum` | Abre el modal para enviar la actualización de standup. |
| `/riesgos` | Muestra los riesgos activos del equipo. |
| `/bloqueos` | Muestra bloqueos reportados hoy. |
| `/sprint` | Información del sprint activo. |
| `/metricas` | Métricas del sprint. |
| `/reporte` | Genera el reporte completo del día. |
| `/progreso` | Progreso de módulos desde Excel. |

---

## Jobs Programados

El `SchedulerService` ejecuta los siguientes jobs diarios:

| Job | Hora | Descripción |
|-----|------|-------------|
| Recordatorio standup | `STANDUP_TIME` (default 09:00) | Envía mensaje con botón "Responder Standup". |
| Resumen diario | `SUMMARY_TIME` (default 17:00) | Genera y envía el reporte del día. |

Además, se pueden agregar jobs periódicos para sync de GitHub y detección de riesgos.

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
