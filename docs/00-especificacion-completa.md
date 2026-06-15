Aquí tienes el documento completo dentro de un solo bloque de código Markdown, listo para copiar y pegar en un archivo `.md`:

```markdown
# Especificaciones del Proyecto: Scrum Master Bot

**Versión:** 1.0  
**Fecha:** 2026-06-15  
**Autor:** Arquitecto de Software / Tech Lead  
**Stack:** Python 3.12, FastAPI, Slack Bolt, GitHub API, PostgreSQL, Docker, OpenRouter  
**Arquitectura:** Clean Architecture, Domain-Driven Design, Hexagonal, Event-Driven (parcial)

---

## 1. Visión General del Sistema

**Scrum Master Bot** es un asistente digital inteligente que automatiza las tareas operativas de Scrum para equipos de desarrollo de software. Se integra profundamente con Slack (comunicación) y GitHub (repositorios, PRs, Issues) para:

- Ejecutar daily standups automáticos en Slack.
- Recopilar y almacenar respuestas de los desarrolladores.
- Analizar actividad de GitHub (PRs, issues, CI/CD).
- Detectar bloqueos y riesgos automáticamente (reglas + IA).
- Monitorear pull requests e issues.
- Generar reportes diarios y de sprint.
- Utilizar IA generativa (OpenRouter) para resúmenes ejecutivos y análisis de riesgos.
- Responder a comandos en Slack (`/scrum`, `/riesgos`, `/bloqueos`, `/sprint`, `/metricas`, `/reporte`).
- Mantener métricas históricas y sincronizarlas con una planilla Excel de gestión de proyecto.
- Ser multi-tenant, escalable y cloud-ready.

El producto está dirigido a equipos ágiles que desean reducir la sobrecarga administrativa de Scrum y tener visibilidad en tiempo real del estado del proyecto.

---

## 2. Objetivos del Sistema

### Objetivos Generales
- Automatizar el 80% de las tareas operativas del Scrum Master.
- Proporcionar transparencia sobre bloqueos, avances y riesgos.
- Mejorar la puntualidad y completitud de los daily standups.
- Generar reportes ejecutivos con ayuda de IA.
- Centralizar la información del sprint en Slack y una planilla Excel.

### Objetivos Específicos (MVP)
1. Envío automático programado del recordatorio de daily standup con modal interactivo.
2. Recepción y persistencia de respuestas de standup.
3. Comando `/scrum` para iniciar un standup manual o enviar respuestas.
4. Consulta de pull requests abiertos desde GitHub.
5. Detección de PRs sin revisión por más de 24 horas (riesgo).
6. Comando `/riesgos` que muestre riesgos activos.
7. Comando `/bloqueos` que muestre bloqueos reportados en el standup del día.
8. Generación de resumen diario (Markdown) automático al final del día.
9. Comandos `/sprint`, `/metricas`, `/reporte` (versión básica).
10. Sincronización con planilla Excel (módulos, carta Gantt, tareas, métricas).

---

## 3. Arquitectura de Alto Nivel

Se adopta una arquitectura hexagonal (puertos y adaptadores) combinada con Domain-Driven Design y principios de Clean Architecture.

```
+------------------------------------------------------------------+
|                         ADAPTADORES                              |
| +----------------+ +----------------+ +---------+ +------------+ |
| | Slack Bolt     | | Slack Events   | | GitHub  | | OpenRouter | |
| | (comandos,     | | (eventos,      | | API     | | API        | |
| |  modales)      | |  interacciones)| |         | |            | |
| +-------+--------+ +-------+--------+ +----+----+ +-----+------+ |
+---------+------------------+---------------+-------------+--------+
          |                  |               |             |
+---------v------------------v---------------v-------------v--------+
|                         APLICACIÓN                                |
|  +------------------+  +-------------------+  +----------------+ |
|  | StandupService   |  | RiskDetectionSvc  |  | ReportService  | |
|  +------------------+  +-------------------+  +----------------+ |
|  | GitHubService    |  | SprintMetricsSvc  |  | AIService      | |
|  +------------------+  +-------------------+  +----------------+ |
|  | NotificationSvc  |  | ExcelSyncService  |  | Scheduler      | |
|  +---------+--------+--+---------+---------+--+-------+--------+ |
+------------+--------------------+--------------------+-----------+
             |                    |                    |
+------------v--------------------v--------------------v-----------+
|                          DOMINIO                                  |
|  Entidades: Team, Member, StandupSession, StandupResponse,       |
|             PullRequest, Issue, Sprint, Risk, MetricSnapshot     |
|  Value Objects: RiskType, Severity, StandupSessionStatus         |
|  Puertos (interfaces): repositorios abstractos                   |
+-------------------------------------------------------------------+
             |                    |                    |
+------------v--------------------v--------------------v-----------+
|                    INFRAESTRUCTURA                                |
|  +-----------------+  +-------------------+  +----------------+  |
|  | PostgreSQL      |  | SQLAlchemy ORM    |  | Alembic        |  |
|  +-----------------+  +-------------------+  +----------------+  |
|  | APScheduler     |  | GitHub Client     |  | Slack Client   |  |
|  +-----------------+  +-------------------+  +----------------+  |
|  | OpenRouter      |  | Excel (openpyxl)  |  | Docker         |  |
|  +-----------------+  +-------------------+  +----------------+  |
+-------------------------------------------------------------------+
```

**Principios:**
- El dominio es independiente de frameworks.
- La aplicación orquesta casos de uso usando puertos (repositorios).
- La infraestructura implementa los puertos.
- Los adaptadores externos (Slack, GitHub) se comunican solo con la capa de aplicación.
- Inyección de dependencias manual o con contenedor ligero (fase inicial manual).

---

## 4. Modelo de Dominio

### Entidades y Agregados

- **Team** (agregado raíz): id, name, slack_bot_token, github_token, standup_channel_id, standup_schedule_time, timezone.
- **Member**: id, team_id, slack_user_id, display_name, role.
- **StandupSession**: id, team_id, sprint_id, date, status (open/closed), slack_channel_id, slack_thread_ts.
- **StandupResponse**: id, session_id, member_id, yesterday, today, blockers, created_at.
- **PullRequest**: id, team_id, repository, pr_number, title, author, state, created_at, updated_at, merged_at, reviewers, lead_time_hours.
- **Issue**: (similar a PR, pero para issues).
- **Sprint**: id, team_id, name, start_date, end_date, status (planning/active/completed), goals.
- **Risk**: id, team_id, type (pr_no_review, ci_failure, blocker, stale_branch), description, severity (low/medium/high/critical), source_ref, resolved, created_at.
- **MetricSnapshot**: id, team_id, metric_type, date, value, metadata (JSON).

### Repositorios (Puertos)
- TeamRepository, MemberRepository, StandupSessionRepository, StandupResponseRepository, PullRequestRepository, SprintRepository, RiskRepository, MetricRepository.
- Cada uno define métodos abstractos (get, save, find_by_...).

---

## 5. Stack Tecnológico

### Backend
- **Lenguaje:** Python 3.12
- **Framework Web:** FastAPI (para endpoints REST y recepción de eventos Slack)
- **Async:** async/await con uvicorn

### Integraciones
- **Slack:** Slack Bolt for Python (AsyncApp), Slack Events API, Slash Commands, Modals
- **GitHub:** httpx para llamadas a API REST (GitHub API v3)
- **IA:** OpenRouter API (modelos de lenguaje)

### Persistencia
- **Base de datos:** PostgreSQL 16
- **ORM:** SQLAlchemy 2.0 asíncrono
- **Migraciones:** Alembic

### Infraestructura
- **Contenedores:** Docker, Docker Compose
- **Scheduler:** APScheduler (para tareas programadas como recordatorios, sincronización)
- **Manejo de Excel:** openpyxl (lectura/escritura de planilla de gestión)

### Calidad
- **Testing:** pytest, pytest-asyncio
- **CI/CD:** GitHub Actions (opcional en MVP)

---

## 6. Estructura del Proyecto (Clean Architecture)

```
scrum-master-bot/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── .env.example
├── alembic.ini
├── migrations/
├── project_tracking.xlsx          # Planilla Excel sincronizada
├── src/
│   ├── __init__.py
│   ├── config.py                  # Settings con pydantic-settings
│   ├── main.py                    # FastAPI app, startup, shutdown
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py              # Entidades, Value Objects, Enums
│   │   ├── repositories.py        # Interfaces abstractas (puertos)
│   │   └── exceptions.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── standup_service.py
│   │   ├── github_service.py
│   │   ├── risk_service.py
│   │   ├── report_service.py
│   │   ├── ai_service.py
│   │   ├── sprint_service.py
│   │   ├── excel_sync_service.py  # Sincronización con planilla Excel
│   │   └── notification_service.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py            # Engine, async_session_maker
│   │   ├── models.py              # Modelos ORM (SQLAlchemy)
│   │   ├── repositories/          # Implementaciones concretas
│   │   │   ├── team_repo.py
│   │   │   ├── member_repo.py
│   │   │   ├── standup_repo.py
│   │   │   ├── pr_repo.py
│   │   │   ├── sprint_repo.py
│   │   │   ├── risk_repo.py
│   │   │   └── metric_repo.py
│   │   ├── slack_client.py        # Configuración AsyncApp
│   │   ├── github_client.py       # httpx wrapper
│   │   ├── ai_client.py           # OpenRouter wrapper
│   │   └── scheduler.py           # APScheduler jobs
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── slack/
│   │   │   ├── bolt_app.py        # Registro de comandos y eventos
│   │   │   ├── commands.py        # /scrum, /riesgos, /bloqueos, etc.
│   │   │   ├── modals.py          # Vistas modales
│   │   │   └── events.py          # Eventos (app_mention, etc.)
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── routes.py          # Endpoints dashboard
│   │       └── dependencies.py    # FastAPI Depends
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

---

## 7. Diseño de Base de Datos (PostgreSQL)

Tablas principales (esquema SQL simplificado):

```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slack_bot_token TEXT NOT NULL,
    github_token TEXT NOT NULL,
    standup_channel_id VARCHAR(50) NOT NULL,
    standup_schedule_time VARCHAR(5) NOT NULL, -- HH:MM
    timezone VARCHAR(50) DEFAULT 'UTC'
);

CREATE TABLE members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    slack_user_id VARCHAR(50) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'developer'
);

CREATE TABLE sprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    name VARCHAR(255),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) CHECK (status IN ('planning','active','completed')),
    goals TEXT
);

CREATE TABLE standup_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    sprint_id UUID REFERENCES sprints(id),
    date DATE NOT NULL,
    status VARCHAR(20) CHECK (status IN ('open','closed')),
    slack_channel_id VARCHAR(50),
    slack_thread_ts VARCHAR(50)
);

CREATE TABLE standup_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES standup_sessions(id),
    member_id UUID REFERENCES members(id),
    yesterday TEXT,
    today TEXT,
    blockers TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE pull_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    repository VARCHAR(255),
    pr_number INTEGER,
    title TEXT,
    author VARCHAR(100),
    state VARCHAR(20),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    merged_at TIMESTAMPTZ,
    reviewers TEXT[],
    lead_time_hours FLOAT
);

CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    repository VARCHAR(255),
    issue_number INTEGER,
    title TEXT,
    state VARCHAR(20),
    labels TEXT[],
    assignee VARCHAR(100),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);

CREATE TABLE risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    type VARCHAR(50) NOT NULL, -- 'pr_no_review','ci_failure','blocker','stale_branch'
    description TEXT,
    severity VARCHAR(20) CHECK (severity IN ('low','medium','high','critical')),
    source_ref JSONB,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE metric_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id),
    metric_type VARCHAR(50),
    date DATE,
    value FLOAT,
    metadata JSONB
);
```

Índices recomendados: en team_id, fechas, y combinaciones para consultas frecuentes.

---

## 8. Funcionalidades MVP (Detalladas)

1. **Daily Standup Automático**
   - El scheduler publica un mensaje a las 9:00 AM en el canal configurado con un botón "Responder standup".
   - Al hacer clic, se abre un modal con campos: ¿Qué hiciste ayer?, ¿Qué harás hoy?, ¿Tienes bloqueos?
   - Las respuestas se guardan en `standup_responses` y se asocian a una `standup_session` del día.
   - También se puede iniciar manualmente con `/scrum`.

2. **Comando /scrum**
   - Abre el mismo modal para que cualquier miembro envíe su actualización en cualquier momento.

3. **Comando /riesgos**
   - Muestra los riesgos activos detectados automáticamente:
     - PRs abiertos sin reviewers por más de 24h.
     - (Opcional) Estado de CI/CD si está disponible.
   - Posibilidad de agregar riesgos manualmente.

4. **Comando /bloqueos**
   - Lista los bloqueos reportados en las respuestas del standup del día actual (campo `blockers` no vacío).

5. **Resumen Diario**
   - Al final del día (ej. 17:00), se genera un mensaje en el canal con:
     - Resumen de lo que cada miembro reportó (hoy, ayer, bloqueos).
     - PRs abiertos y su estado.
     - Riesgos detectados.
   - Formato Markdown atractivo.

6. **Integración con GitHub**
   - El sistema sincroniza periódicamente los PRs abiertos (usando token del equipo) y guarda en BD.
   - Se consultan bajo demanda para los comandos.

7. **Sincronización con Planilla Excel**
   - Se mantiene una planilla `project_tracking.xlsx` con hojas:
     - **Módulos**: lista de módulos con objetivos, estado, % avance, fechas.
     - **Carta Gantt**: sprints con fechas, progreso.
     - **Tareas**: tareas diarias con responsable y estado.
     - **Métricas**: KPIs diarios del sprint.
     - **Riesgos**: riesgos activos.
   - El sistema actualiza automáticamente estas hojas (métricas, riesgos) diariamente.
   - Comandos Slack: `/progreso`, `/actualizar-modulo`, `/gantt` para interactuar con el Excel.

8. **Comandos adicionales (fase MVP extendida)**
   - `/sprint`: información del sprint activo.
   - `/metricas`: velocidad, PRs, tiempo ciclo.
   - `/reporte`: genera un reporte más completo del sprint.

---

## 9. Roadmap y Backlog Priorizado

### Fase 0 – Fundación (Sprint 1-2)
- [ ] Configurar proyecto Docker + FastAPI + PostgreSQL + SQLAlchemy.
- [ ] Modelado de dominio y migraciones iniciales.
- [ ] Implementar repositorios base (Team, Member).
- [ ] Slack App básica: conexión Bolt, manejo de slash commands.
- [ ] Comando `/scrum` funcional con modal y persistencia.
- [ ] GitHub client: consulta de PRs abiertos.
- [ ] Scheduler para recordatorio diario.

### Fase 1 – Core MVP (Sprint 3-4)
- [ ] Comando `/riesgos` con reglas simples.
- [ ] Comando `/bloqueos` basado en standups del día.
- [ ] Generación de resumen diario (sin IA).
- [ ] Notificaciones proactivas de riesgos (PR envejecido).
- [ ] Integración con Excel (creación inicial y sincronización básica de métricas).

### Fase 2 – Inteligencia y Reportes (Sprint 5-6)
- [ ] Integración OpenRouter: resúmenes con IA.
- [ ] Comandos `/sprint`, `/metricas`, `/reporte`.
- [ ] Dashboard API básica (REST).
- [ ] Sincronización completa con Excel (actualización de módulos, tareas, Gantt).

### Fase 3 – Escalabilidad (Sprint 7+)
- [ ] Soporte multi-tenant real (gestión de múltiples equipos).
- [ ] Webhooks de GitHub para detección en tiempo real.
- [ ] Workers asíncronos para tareas pesadas.
- [ ] Panel de administración web.

---

## 10. Historias de Usuario (Principales)

1. **Como desarrollador**, quiero que el bot publique un recordatorio cada mañana a las 9am para no olvidar el daily standup.
2. **Como desarrollador**, quiero responder mis avances mediante un modal fácil de llenar.
3. **Como Scrum Master**, quiero que el bot recoja las respuestas y las publique en un resumen.
4. **Como Scrum Master**, quiero ejecutar `/riesgos` para ver PRs sin revisión y builds rotas.
5. **Como desarrollador**, quiero usar `/bloqueos` para ver quién está bloqueado y en qué.
6. **Como Scrum Master**, quiero recibir un resumen diario automático con el estado del equipo.
7. **Como desarrollador**, quiero que el bot me alerte si uno de mis PRs lleva más de 24h sin revisores.
8. **Como Scrum Master**, quiero ver el progreso del sprint y métricas con `/metricas`.
9. **Como administrador**, quiero configurar los canales y tokens vía variables de entorno.
10. **Como Scrum Master**, quiero que el bot mantenga actualizada automáticamente nuestra planilla Excel de gestión.

---

## 11. Primer Sprint de Desarrollo (Detalle de Tareas)

**Duración:** 2 semanas  
**Objetivo:** Base funcional con Slack, GitHub y persistencia; comando `/scrum` operativo, Excel inicial.

| ID | Tarea | Responsable | Tipo | Esfuerzo |
|----|-------|-------------|------|----------|
| T01 | Inicializar proyecto (Docker, FastAPI, estructura de carpetas) | Dev Backend | Infra | 4h |
| T02 | Configurar variables de entorno y clase Settings | Dev Backend | Config | 1h |
| T03 | Crear modelos de dominio (entidades) y enums | Dev Backend | Dominio | 3h |
| T04 | Definir interfaces de repositorios abstractos | Dev Backend | Dominio | 2h |
| T05 | Configurar SQLAlchemy asíncrono y modelos ORM | Dev Backend | Infra | 3h |
| T06 | Crear migraciones Alembic iniciales | Dev Backend | Infra | 2h |
| T07 | Implementar repositorio Team (TeamRepositoryImpl) | Dev Backend | Infra | 2h |
| T08 | Implementar repositorio Member | Dev Backend | Infra | 2h |
| T09 | Configurar Slack Bolt AsyncApp y endpoint de eventos | Dev Backend | Integración | 3h |
| T10 | Registrar comando `/scrum` que abra modal | Dev Backend | Interfaz | 4h |
| T11 | Manejar view_submission: guardar StandupResponse y StandupSession | Dev Backend | Aplicación | 5h |
| T12 | Implementar GitHubClient con método fetch_open_prs | Dev Backend | Integración | 3h |
| T13 | Crear GitHubService y PullRequestRepository | Dev Backend | Aplicación | 4h |
| T14 | Crear scheduler (APScheduler) para envío de recordatorio diario | Dev Backend | Infra | 3h |
| T15 | Implementar lógica de resumen diario simple (Markdown) | Dev Backend | Aplicación | 4h |
| T16 | Implementar ExcelSyncService: crear template Excel con hojas base | Dev Backend | Aplicación | 5h |
| T17 | Comando `/progreso` que lea Excel y muestre avance | Dev Backend | Interfaz | 3h |
| T18 | Pruebas unitarias básicas (servicios) | Dev Backend | Calidad | 4h |
| T19 | Documentación README y configuración de entorno | Dev Backend | Docs | 2h |

---

## 12. Integración con Planilla Excel (Detalle)

La planilla `project_tracking.xlsx` tendrá las siguientes hojas y columnas:

### Hoja "Módulos"
| ID Módulo | Módulo | Objetivo Principal | Objetivos Específicos | Prioridad | Estado | % Avance | Fecha Inicio | Fecha Fin Estimada | Fecha Fin Real | Responsable | Dependencias | Sprint Actual | Notas |
|-----------|--------|-------------------|-----------------------|-----------|--------|----------|--------------|--------------------|----------------|-------------|--------------|---------------|-------|

### Hoja "Carta Gantt"
| Sprint | Fecha Inicio | Fecha Fin | Duración | Módulos Incluidos | Hitos Principales | Estado | % Completado | Burndown Actual | Burndown Ideal | Velocidad Planificada | Velocidad Real |
|--------|--------------|-----------|----------|-------------------|-------------------|--------|--------------|-----------------|----------------|------------------------|----------------|

### Hoja "Tareas"
| ID Tarea | Fecha | Sprint | Módulo | Tarea | Tipo | Responsable | Estado | Bloqueos | Horas Estimadas | Horas Reales | Comentarios |
|----------|-------|--------|--------|-------|------|-------------|--------|----------|-----------------|--------------|-------------|

### Hoja "Métricas"
| Fecha | Sprint | Día Sprint | Velocidad | PRs Abiertos | PRs Mergeados | PRs en Revisión | Tiempo Ciclo Prom. (h) | Tiempo Lead (h) | Bloqueos Activos | Riesgos Detectados | Índice de Salud |
|-------|--------|------------|-----------|--------------|---------------|-----------------|------------------------|-----------------|------------------|--------------------|-----------------|

### Hoja "Riesgos"
| ID Riesgo | Fecha Detección | Tipo | Descripción | Severidad | Fuente | Estado | Fecha Resolución | PR/Issue Relacionado | Acciones Tomadas |
|-----------|-----------------|------|-------------|-----------|--------|--------|------------------|----------------------|------------------|

**Sincronización automática:** El `ExcelSyncService` ejecutará jobs programados para actualizar métricas y riesgos diariamente. Los comandos de Slack permiten actualización manual de módulos y visualización de la carta Gantt.

---

## 13. Consideraciones Técnicas

- **Manejo de secretos:** Usar variables de entorno (`.env`) y nunca commitear tokens.
- **Escalabilidad:** En fase inicial, single tenant. Preparar desde el inicio tablas con `team_id` para multi-tenant futuro.
- **Async:** Toda operación de I/O (DB, HTTP) debe ser asíncrona.
- **Inyección de dependencias:** En el MVP se hará de forma manual o con un diccionario de servicios. En el futuro se puede migrar a un contenedor (ej. `punq`).
- **Logging:** Usar `structlog` o `logging` estándar para trazabilidad.
- **Errores:** Manejo de excepciones con retry policies para llamadas externas.

---

## 14. Conclusión

Este documento proporciona la especificación completa para iniciar el desarrollo del Scrum Master Bot. Contiene la visión, arquitectura, modelo de dominio, stack, estructura del código, diseño de BD, backlog, historias de usuario y detalles del primer sprint. Sirve como punto de partida autónomo para el equipo de desarrollo.
```

Copia todo el contenido dentro del bloque de código y pégalo en un archivo con extensión `.md`. El markdown se conservará intacto y podrás visualizarlo en cualquier visor de Markdown o editor.