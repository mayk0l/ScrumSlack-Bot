# Plan de Ejecución: Scrum Master Bot

**Fecha:** 2026-06-15  
**Propósito:** Guía paso a paso para generar el código del proyecto con un modelo de IA.  
**Documento de referencia:** `Scrum_Master_Bot_Especificacion_Completa.md`  
**Estrategia:** Cada bloque es una instrucción atómica. Ejecutar en orden. No saltar bloques.

---

## Convenciones Globales

Antes de comenzar, el modelo generador debe respetar estas reglas en **todo** el código:

| Aspecto | Convención |
|---------|------------|
| Lenguaje | Python 3.12, tipado estricto (`from __future__ import annotations`) |
| Async | Todo I/O es `async/await`. Sin llamadas bloqueantes. |
| Imports | Absolutos desde `src.` (ej: `from src.domain.models import Team`) |
| Docstrings | Google style, en español solo si es comentario de negocio; inglés para API/código |
| Nombres | snake_case para archivos/funciones, PascalCase para clases, UPPER_CASE para constantes |
| IDs | UUID v4 en todas las entidades |
| Errores | Excepciones de dominio propias, nunca excepciones genéricas desnudas |
| Logging | `structlog` con contexto (team_id, user_id) |
| Config | `pydantic-settings` con `.env`, nunca hardcoded |
| Tests | pytest + pytest-asyncio, fixtures en conftest.py |

---

## Fase 0 — Infraestructura y Fundación

### Bloque 0.1 — Scaffolding del Proyecto

**Objetivo:** Crear la estructura de carpetas y archivos base vacíos.

**Acción:** Crear el siguiente árbol de directorios y archivos dentro de `/Users/admin/Documents/projects/ScrumSlack-Bot/`:

```
scrum-master-bot/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
├── alembic.ini
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── project_tracking.xlsx
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── exceptions.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── standup_service.py
│   │   ├── github_service.py
│   │   ├── risk_service.py
│   │   ├── report_service.py
│   │   ├── ai_service.py
│   │   ├── sprint_service.py
│   │   ├── excel_sync_service.py
│   │   └── notification_service.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── orm_models.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── team_repo.py
│   │   │   ├── member_repo.py
│   │   │   ├── standup_repo.py
│   │   │   ├── pr_repo.py
│   │   │   ├── sprint_repo.py
│   │   │   ├── risk_repo.py
│   │   │   └── metric_repo.py
│   │   ├── slack_client.py
│   │   ├── github_client.py
│   │   ├── ai_client.py
│   │   └── scheduler.py
│   └── interfaces/
│       ├── __init__.py
│       ├── slack/
│       │   ├── __init__.py
│       │   ├── bolt_app.py
│       │   ├── commands.py
│       │   ├── modals.py
│       │   └── events.py
│       └── api/
│           ├── __init__.py
│           ├── routes.py
│           └── dependencies.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── unit/
    │   ├── __init__.py
    │   ├── test_standup_service.py
    │   ├── test_risk_service.py
    │   └── test_github_service.py
    └── integration/
        ├── __init__.py
        └── test_slack_commands.py
```

**Criterio de aceptación:** Todos los archivos `.py` contienen solo `"""Módulo: <nombre>."""` como placeholder. Directorios con `__init__.py` vacío.

---

### Bloque 0.2 — Archivos de Configuración de Infraestructura

**Objetivo:** Docker, dependencias, variables de entorno.

#### 0.2.1 — `requirements.txt`

```
# Core
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic==2.10.3
pydantic-settings==2.7.0

# Slack
slack-bolt==1.22.0
slack-sdk==3.34.0

# Database
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0

# HTTP
httpx==0.28.1

# Scheduler
apscheduler==3.10.4

# Excel
openpyxl==3.1.5

# AI
openai==1.58.1

# Logging
structlog==24.4.0

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0

# Utils
python-dotenv==1.0.1
```

#### 0.2.2 — `.env.example`

```env
# === App ===
APP_ENV=development
APP_DEBUG=true
APP_PORT=3000

# === Database ===
DATABASE_URL=postgresql+asyncpg://scrum_bot:scrum_bot_pass@db:5432/scrum_bot_db

# === Slack ===
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token

# === GitHub ===
GITHUB_TOKEN=ghp_your_github_token
GITHUB_DEFAULT_ORG=your-org

# === OpenRouter (AI) ===
OPENROUTER_API_KEY=sk-or-your-key
OPENROUTER_MODEL=anthropic/claude-sonnet-4

# === Standup Config ===
STANDUP_CHANNEL_ID=C0123456789
STANDUP_TIME=09:00
SUMMARY_TIME=17:00
TIMEZONE=America/Santiago

# === Excel ===
EXCEL_FILE_PATH=project_tracking.xlsx
```

#### 0.2.3 — `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000", "--reload"]
```

#### 0.2.4 — `docker-compose.yml`

```yaml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "${APP_PORT:-3000}:3000"
    env_file:
      - .env
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: scrum_bot
      POSTGRES_PASSWORD: scrum_bot_pass
      POSTGRES_DB: scrum_bot_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scrum_bot -d scrum_bot_db"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

#### 0.2.5 — `.gitignore`

```
__pycache__/
*.pyc
.env
*.egg-info/
dist/
.venv/
venv/
.idea/
.vscode/
*.db
*.sqlite3
project_tracking.xlsx
```

**Criterio de aceptación:** `docker-compose up --build` levanta app + postgres. App responde en `http://localhost:3000`. Base de datos accesible.

---

### Bloque 0.3 — Configuración de la Aplicación (`src/config.py`)

**Objetivo:** Centralizar toda la configuración usando `pydantic-settings`.

**Debe contener:**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_env: str = "development"
    app_debug: bool = True
    app_port: int = 3000

    # Database
    database_url: str

    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    slack_app_token: str = ""

    # GitHub
    github_token: str
    github_default_org: str = ""

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4"

    # Standup
    standup_channel_id: str
    standup_time: str = "09:00"
    summary_time: str = "17:00"
    timezone: str = "America/Santiago"

    # Excel
    excel_file_path: str = "project_tracking.xlsx"

settings = Settings()
```

**Criterio de aceptación:** `from src.config import settings` funciona. Valores leídos de `.env`. Falla si faltan los campos obligatorios sin default.

---

## Fase 1 — Capa de Dominio

> [!IMPORTANT]
> Esta es la capa más crítica. No depende de ningún framework. Solo Python puro + dataclasses/Pydantic.

### Bloque 1.1 — Modelos de Dominio (`src/domain/models.py`)

**Objetivo:** Definir todas las entidades, value objects y enums del dominio.

**Entidades a implementar (como `dataclass` o Pydantic `BaseModel`):**

| Entidad | Campos | Notas |
|---------|--------|-------|
| `Team` | id (UUID), name, slack_bot_token, github_token, standup_channel_id, standup_schedule_time, timezone | Agregado raíz |
| `Member` | id, team_id, slack_user_id, display_name, role | role default = "developer" |
| `Sprint` | id, team_id, name, start_date, end_date, status (SprintStatus), goals | — |
| `StandupSession` | id, team_id, sprint_id (optional), date, status (SessionStatus), slack_channel_id, slack_thread_ts | — |
| `StandupResponse` | id, session_id, member_id, yesterday, today, blockers, created_at | — |
| `PullRequest` | id, team_id, repository, pr_number, title, author, state, created_at, updated_at, merged_at (optional), reviewers (list[str]), lead_time_hours (optional) | — |
| `Issue` | id, team_id, repository, issue_number, title, state, labels (list[str]), assignee (optional), created_at, updated_at | — |
| `Risk` | id, team_id, type (RiskType), description, severity (Severity), source_ref (dict), resolved, created_at | — |
| `MetricSnapshot` | id, team_id, metric_type, date, value (float), metadata (dict) | — |

**Enums:**

```python
class SprintStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"

class SessionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

class RiskType(str, Enum):
    PR_NO_REVIEW = "pr_no_review"
    CI_FAILURE = "ci_failure"
    BLOCKER = "blocker"
    STALE_BRANCH = "stale_branch"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MemberRole(str, Enum):
    DEVELOPER = "developer"
    TECH_LEAD = "tech_lead"
    SCRUM_MASTER = "scrum_master"
    PRODUCT_OWNER = "product_owner"
```

**Decisión de diseño:** Usar `dataclasses` con `field(default_factory=...)` para las entidades. Esto mantiene el dominio libre de dependencias de framework. Los IDs se generan con `uuid4()` por defecto.

**Criterio de aceptación:** Se puede importar cada entidad y enum. Se puede instanciar `Team(name="test", ...)` sin errores. Ningún import de SQLAlchemy, FastAPI o Slack en este archivo.

---

### Bloque 1.2 — Excepciones de Dominio (`src/domain/exceptions.py`)

**Objetivo:** Excepciones tipadas para errores de negocio.

```python
class DomainException(Exception):
    """Base para excepciones de dominio."""

class EntityNotFoundError(DomainException):
    """Entidad no encontrada."""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} con id '{entity_id}' no encontrado")

class StandupAlreadyRespondedError(DomainException):
    """El miembro ya respondió el standup de hoy."""

class SprintNotActiveError(DomainException):
    """No hay sprint activo."""

class InvalidConfigurationError(DomainException):
    """Configuración inválida."""

class ExternalServiceError(DomainException):
    """Error en servicio externo (GitHub, Slack, OpenRouter)."""
    def __init__(self, service: str, detail: str):
        self.service = service
        super().__init__(f"Error en {service}: {detail}")
```

**Criterio de aceptación:** Cada excepción se puede lanzar con mensajes claros. `isinstance(EntityNotFoundError(...), DomainException)` es `True`.

---

### Bloque 1.3 — Interfaces de Repositorios (`src/domain/repositories.py`)

**Objetivo:** Definir los contratos (puertos) que la infraestructura implementará.

**Patrón:** Clases abstractas (`ABC`) con métodos `async`.

```python
from abc import ABC, abstractmethod

class TeamRepository(ABC):
    @abstractmethod
    async def get_by_id(self, team_id: UUID) -> Team | None: ...
    @abstractmethod
    async def save(self, team: Team) -> Team: ...
    @abstractmethod
    async def get_all(self) -> list[Team]: ...

class MemberRepository(ABC):
    @abstractmethod
    async def get_by_id(self, member_id: UUID) -> Member | None: ...
    @abstractmethod
    async def get_by_slack_user_id(self, team_id: UUID, slack_user_id: str) -> Member | None: ...
    @abstractmethod
    async def get_by_team(self, team_id: UUID) -> list[Member]: ...
    @abstractmethod
    async def save(self, member: Member) -> Member: ...

class StandupSessionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, session_id: UUID) -> StandupSession | None: ...
    @abstractmethod
    async def get_today_session(self, team_id: UUID, date: date) -> StandupSession | None: ...
    @abstractmethod
    async def save(self, session: StandupSession) -> StandupSession: ...
    @abstractmethod
    async def update_status(self, session_id: UUID, status: SessionStatus) -> None: ...

class StandupResponseRepository(ABC):
    @abstractmethod
    async def save(self, response: StandupResponse) -> StandupResponse: ...
    @abstractmethod
    async def get_by_session(self, session_id: UUID) -> list[StandupResponse]: ...
    @abstractmethod
    async def get_by_member_and_session(self, member_id: UUID, session_id: UUID) -> StandupResponse | None: ...

class PullRequestRepository(ABC):
    @abstractmethod
    async def save(self, pr: PullRequest) -> PullRequest: ...
    @abstractmethod
    async def upsert(self, pr: PullRequest) -> PullRequest: ...
    @abstractmethod
    async def get_open_by_team(self, team_id: UUID) -> list[PullRequest]: ...
    @abstractmethod
    async def get_stale_prs(self, team_id: UUID, hours_threshold: int = 24) -> list[PullRequest]: ...

class SprintRepository(ABC):
    @abstractmethod
    async def get_active(self, team_id: UUID) -> Sprint | None: ...
    @abstractmethod
    async def save(self, sprint: Sprint) -> Sprint: ...
    @abstractmethod
    async def update_status(self, sprint_id: UUID, status: SprintStatus) -> None: ...

class RiskRepository(ABC):
    @abstractmethod
    async def save(self, risk: Risk) -> Risk: ...
    @abstractmethod
    async def get_active_by_team(self, team_id: UUID) -> list[Risk]: ...
    @abstractmethod
    async def resolve(self, risk_id: UUID) -> None: ...

class MetricRepository(ABC):
    @abstractmethod
    async def save(self, snapshot: MetricSnapshot) -> MetricSnapshot: ...
    @abstractmethod
    async def get_by_sprint(self, team_id: UUID, sprint_id: UUID) -> list[MetricSnapshot]: ...
    @abstractmethod
    async def get_latest(self, team_id: UUID, metric_type: str) -> MetricSnapshot | None: ...
```

**Criterio de aceptación:** Ningún import de SQLAlchemy. Todos los métodos son `abstractmethod` y `async`. Los tipos de retorno usan modelos de dominio.

---

## Fase 2 — Capa de Infraestructura

### Bloque 2.1 — Base de Datos (`src/infrastructure/database.py`)

**Objetivo:** Configurar SQLAlchemy async engine y session factory.

**Debe contener:**
- `create_async_engine` con la URL de `settings.database_url`
- `async_sessionmaker` configurado con `expire_on_commit=False`
- Función `async def get_session()` como async generator para inyección de dependencias
- Función `async def init_db()` para crear tablas (solo desarrollo)
- `Base = declarative_base()` para los modelos ORM

**Criterio de aceptación:** `async for session in get_session()` entrega una `AsyncSession` funcional.

---

### Bloque 2.2 — Modelos ORM (`src/infrastructure/orm_models.py`)

**Objetivo:** Mapear las entidades de dominio a tablas PostgreSQL.

**Regla clave:** Estos modelos son de infraestructura. Deben tener métodos `to_domain()` y `@classmethod from_domain(cls, entity)` para convertir entre ORM y dominio.

**Tablas a implementar (con tipos SQLAlchemy):**

| Tabla | Columnas especiales |
|-------|-------------------|
| `teams` | id UUID PK default `gen_random_uuid()` |
| `members` | FK → teams, unique (team_id, slack_user_id) |
| `sprints` | FK → teams, CHECK status IN ('planning','active','completed') |
| `standup_sessions` | FK → teams, FK → sprints (nullable), unique (team_id, date) |
| `standup_responses` | FK → standup_sessions, FK → members, unique (session_id, member_id) |
| `pull_requests` | FK → teams, `reviewers` como `ARRAY(String)`, unique (team_id, repository, pr_number) |
| `issues` | FK → teams, `labels` como `ARRAY(String)`, unique (team_id, repository, issue_number) |
| `risks` | FK → teams, `source_ref` como `JSONB` |
| `metric_snapshots` | FK → teams, `metadata` como `JSONB` |

**Índices a crear:**
- `ix_standup_sessions_team_date` en (team_id, date)
- `ix_pull_requests_team_state` en (team_id, state)
- `ix_risks_team_resolved` en (team_id, resolved)
- `ix_metric_snapshots_team_type_date` en (team_id, metric_type, date)

**Ejemplo de método de conversión:**
```python
class TeamORM(Base):
    __tablename__ = "teams"
    # ... columnas ...

    def to_domain(self) -> Team:
        return Team(
            id=self.id,
            name=self.name,
            # ...
        )

    @classmethod
    def from_domain(cls, team: Team) -> "TeamORM":
        return cls(
            id=team.id,
            name=team.name,
            # ...
        )
```

**Criterio de aceptación:** Alembic genera migración sin errores. Las tablas se crean en PostgreSQL con los tipos correctos.

---

### Bloque 2.3 — Configuración de Alembic

**Objetivo:** Configurar migraciones de base de datos.

**Archivos:**
- `alembic.ini` — apuntar `sqlalchemy.url` a un placeholder (se sobreescribe en runtime)
- `migrations/env.py` — importar `Base` de `orm_models`, configurar URL desde `settings`, soporte async

**Comandos que deben funcionar:**
```bash
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```

**Criterio de aceptación:** Migración se genera automáticamente detectando todos los modelos ORM. `alembic upgrade head` crea todas las tablas en PostgreSQL.

---

### Bloque 2.4 — Implementación de Repositorios

**Objetivo:** Implementar los puertos definidos en `domain/repositories.py`.

**Ubicación:** `src/infrastructure/repositories/`

**Patrón para cada repositorio:**
```python
class TeamRepositoryImpl(TeamRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, team_id: UUID) -> Team | None:
        result = await self._session.get(TeamORM, team_id)
        return result.to_domain() if result else None

    async def save(self, team: Team) -> Team:
        orm = TeamORM.from_domain(team)
        merged = await self._session.merge(orm)
        await self._session.flush()
        return merged.to_domain()
```

**Repositorios a implementar (en orden):**

1. **`team_repo.py`** — `TeamRepositoryImpl` — Métodos: get_by_id, save, get_all
2. **`member_repo.py`** — `MemberRepositoryImpl` — Métodos: get_by_id, get_by_slack_user_id, get_by_team, save
3. **`standup_repo.py`** — `StandupSessionRepositoryImpl` + `StandupResponseRepositoryImpl`
   - Consulta especial: `get_today_session` filtra por `date == today`
   - `get_by_member_and_session` para evitar respuestas duplicadas
4. **`pr_repo.py`** — `PullRequestRepositoryImpl`
   - `upsert` usa `on_conflict_do_update` de PostgreSQL
   - `get_stale_prs` filtra PRs abiertos donde `reviewers` está vacío y `created_at < now() - threshold`
5. **`sprint_repo.py`** — `SprintRepositoryImpl` — `get_active` filtra por `status == 'active'`
6. **`risk_repo.py`** — `RiskRepositoryImpl` — `get_active_by_team` filtra `resolved == False`
7. **`metric_repo.py`** — `MetricRepositoryImpl` — `get_latest` ordena por fecha desc, limit 1

**Criterio de aceptación:** Tests unitarios pasan con SQLite async in-memory o con PostgreSQL de Docker. Cada repo implementa todos los métodos de su interfaz abstracta.

---

### Bloque 2.5 — Clientes Externos

#### 2.5.1 — GitHub Client (`src/infrastructure/github_client.py`)

**Objetivo:** Wrapper async sobre la API REST de GitHub v3.

**Clase: `GitHubClient`**

```python
class GitHubClient:
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
            timeout=30.0,
        )

    async def get_open_pull_requests(self, org: str, repo: str) -> list[dict]: ...
    async def get_pr_reviews(self, org: str, repo: str, pr_number: int) -> list[dict]: ...
    async def get_open_issues(self, org: str, repo: str) -> list[dict]: ...
    async def close(self) -> None: ...
```

**Endpoints a implementar:**
- `GET /repos/{org}/{repo}/pulls?state=open`
- `GET /repos/{org}/{repo}/pulls/{pr_number}/reviews`
- `GET /repos/{org}/{repo}/issues?state=open`

**Manejo de errores:** Retry con backoff exponencial (3 intentos). Lanzar `ExternalServiceError("GitHub", detail)` en fallo.

**Criterio de aceptación:** Se puede listar PRs abiertos de un repo público. Maneja rate limits (HTTP 429) con retry.

---

#### 2.5.2 — Slack Client (`src/infrastructure/slack_client.py`)

**Objetivo:** Configurar Slack Bolt AsyncApp y exponer helpers.

**Contenido:**
```python
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

def create_slack_app(token: str, signing_secret: str) -> AsyncApp:
    return AsyncApp(token=token, signing_secret=signing_secret)

class SlackNotifier:
    def __init__(self, app: AsyncApp):
        self._app = app

    async def send_message(self, channel: str, text: str, blocks: list[dict] | None = None) -> dict: ...
    async def send_thread_reply(self, channel: str, thread_ts: str, text: str) -> dict: ...
    async def open_modal(self, trigger_id: str, view: dict) -> dict: ...
    async def update_message(self, channel: str, ts: str, text: str, blocks: list[dict] | None = None) -> dict: ...
```

**Criterio de aceptación:** `create_slack_app()` retorna una instancia de `AsyncApp`. `SlackNotifier.send_message()` envía mensaje a un canal de prueba.

---

#### 2.5.3 — AI Client (`src/infrastructure/ai_client.py`)

**Objetivo:** Wrapper para OpenRouter API (compatible con formato OpenAI).

**Clase: `AIClient`**

```python
class AIClient:
    def __init__(self, api_key: str, model: str, base_url: str = "https://openrouter.ai/api/v1"):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )
        self._model = model

    async def generate_summary(self, prompt: str, context: str, max_tokens: int = 1000) -> str:
        """Envía prompt + contexto al LLM y retorna texto generado."""
        ...

    async def analyze_risks(self, standup_data: str, pr_data: str) -> str:
        """Analiza datos de standup y PRs para detectar riesgos."""
        ...

    async def close(self) -> None: ...
```

**Criterio de aceptación:** Se puede generar un resumen de prueba. Maneja errores de API con `ExternalServiceError`.

---

#### 2.5.4 — Scheduler (`src/infrastructure/scheduler.py`)

**Objetivo:** Configurar APScheduler para tareas programadas.

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class SchedulerService:
    def __init__(self):
        self._scheduler = AsyncIOScheduler()

    def add_daily_job(self, func, hour: int, minute: int, timezone: str, job_id: str, **kwargs) -> None:
        """Agrega un job que se ejecuta diariamente a una hora fija."""
        self._scheduler.add_job(
            func, "cron", hour=hour, minute=minute, timezone=timezone,
            id=job_id, replace_existing=True, kwargs=kwargs,
        )

    def start(self) -> None: ...
    def shutdown(self) -> None: ...
```

**Criterio de aceptación:** Un job programado se ejecuta a la hora configurada. Se puede agregar y remover jobs dinámicamente.

---

## Fase 3 — Capa de Aplicación (Servicios)

> [!IMPORTANT]
> Los servicios orquestan la lógica de negocio. Reciben repositorios como dependencias (inyección manual). No acceden directamente a la BD ni a APIs externas.

### Bloque 3.1 — StandupService (`src/application/standup_service.py`)

**Responsabilidades:**
- Crear sesión de standup del día (si no existe)
- Registrar respuesta de un miembro
- Obtener respuestas del día
- Verificar si un miembro ya respondió
- Cerrar sesión al final del día

**Firma de clase:**
```python
class StandupService:
    def __init__(
        self,
        session_repo: StandupSessionRepository,
        response_repo: StandupResponseRepository,
        member_repo: MemberRepository,
    ): ...

    async def get_or_create_today_session(self, team_id: UUID) -> StandupSession: ...
    async def submit_response(self, team_id: UUID, slack_user_id: str, yesterday: str, today: str, blockers: str) -> StandupResponse: ...
    async def get_today_responses(self, team_id: UUID) -> list[StandupResponse]: ...
    async def get_missing_members(self, team_id: UUID) -> list[Member]: ...
    async def close_session(self, team_id: UUID) -> None: ...
```

**Reglas de negocio:**
- Si el miembro ya respondió hoy → lanzar `StandupAlreadyRespondedError`
- Si no existe sesión para hoy → crearla con status `OPEN`
- `get_missing_members` = todos los miembros del team - los que ya respondieron

**Criterio de aceptación:** Test unitario con repos mock: submit_response guarda correctamente; doble submit lanza excepción; get_missing_members retorna solo los faltantes.

---

### Bloque 3.2 — GitHubService (`src/application/github_service.py`)

**Responsabilidades:**
- Sincronizar PRs abiertos desde GitHub a la BD
- Consultar PRs abiertos del team
- Detectar PRs "envejecidos" (sin review >24h)

```python
class GitHubService:
    def __init__(
        self,
        github_client: GitHubClient,
        pr_repo: PullRequestRepository,
    ): ...

    async def sync_pull_requests(self, team_id: UUID, org: str, repos: list[str]) -> int:
        """Sincroniza PRs abiertos de los repos. Retorna cantidad sincronizada."""
        ...

    async def get_open_prs(self, team_id: UUID) -> list[PullRequest]: ...

    async def get_stale_prs(self, team_id: UUID, hours: int = 24) -> list[PullRequest]:
        """PRs sin reviewers asignados por más de `hours` horas."""
        ...
```

**Lógica de sync:** Para cada repo → fetch PRs de GitHub → upsert en BD (para no duplicar).

**Criterio de aceptación:** Sync trae PRs y los persiste. Llamar sync dos veces no duplica registros. `get_stale_prs` filtra correctamente.

---

### Bloque 3.3 — RiskService (`src/application/risk_service.py`)

**Responsabilidades:**
- Ejecutar detección automática de riesgos
- Consultar riesgos activos
- Resolver riesgo

```python
class RiskService:
    def __init__(
        self,
        risk_repo: RiskRepository,
        pr_repo: PullRequestRepository,
        response_repo: StandupResponseRepository,
    ): ...

    async def detect_risks(self, team_id: UUID) -> list[Risk]:
        """Ejecuta todas las reglas de detección y persiste riesgos nuevos."""
        ...

    async def get_active_risks(self, team_id: UUID) -> list[Risk]: ...
    async def resolve_risk(self, risk_id: UUID) -> None: ...
```

**Reglas de detección (MVP):**

| Regla | Tipo | Severidad |
|-------|------|-----------|
| PR abierto >24h sin reviewers | `pr_no_review` | HIGH |
| PR abierto >48h sin reviewers | `pr_no_review` | CRITICAL |
| Blocker reportado en standup | `blocker` | MEDIUM |
| PR abierto >72h en general | `stale_branch` | MEDIUM |

**Criterio de aceptación:** Con PRs de prueba que cumplan las condiciones, `detect_risks` genera los riesgos correctos. No duplica riesgos ya existentes.

---

### Bloque 3.4 — ReportService (`src/application/report_service.py`)

**Responsabilidades:**
- Generar resumen diario en Markdown
- Generar resumen con IA (opcional)

```python
class ReportService:
    def __init__(
        self,
        standup_service: StandupService,
        github_service: GitHubService,
        risk_service: RiskService,
        ai_client: AIClient | None = None,
    ): ...

    async def generate_daily_summary(self, team_id: UUID) -> str:
        """Genera resumen Markdown del día."""
        ...

    async def generate_ai_summary(self, team_id: UUID) -> str:
        """Genera resumen ejecutivo usando IA."""
        ...
```

**Formato del resumen diario (Markdown):**
```markdown
## 📋 Resumen Diario — {fecha}

### 👥 Standup ({respondieron}/{total} respondieron)
**{nombre}:**
- Ayer: {yesterday}
- Hoy: {today}
- Bloqueos: {blockers o "Ninguno"}

### 🔀 Pull Requests Abiertos ({cantidad})
- #{number} {title} — @{author} ({hours}h abierto)

### ⚠️ Riesgos Activos ({cantidad})
- [{severity}] {description}

### 🚫 Miembros sin responder
- {list}
```

**Criterio de aceptación:** El resumen contiene todas las secciones. Si no hay datos, muestra "Sin datos". El resumen IA agrega un párrafo de análisis al final.

---

### Bloque 3.5 — SprintService (`src/application/sprint_service.py`)

```python
class SprintService:
    def __init__(self, sprint_repo: SprintRepository, metric_repo: MetricRepository): ...

    async def get_active_sprint(self, team_id: UUID) -> Sprint | None: ...
    async def create_sprint(self, team_id: UUID, name: str, start: date, end: date, goals: str) -> Sprint: ...
    async def complete_sprint(self, team_id: UUID) -> Sprint: ...
    async def get_sprint_metrics(self, team_id: UUID) -> dict: ...
```

**Criterio de aceptación:** Solo un sprint activo por team a la vez. `complete_sprint` cambia status a COMPLETED.

---

### Bloque 3.6 — NotificationService (`src/application/notification_service.py`)

```python
class NotificationService:
    def __init__(self, slack_notifier: SlackNotifier): ...

    async def send_standup_reminder(self, channel_id: str) -> str:
        """Envía recordatorio con botón. Retorna message_ts."""
        ...

    async def send_daily_summary(self, channel_id: str, summary: str) -> None: ...
    async def notify_risk(self, channel_id: str, risk: Risk) -> None: ...
    async def send_stale_pr_alert(self, channel_id: str, pr: PullRequest) -> None: ...
```

**Bloques de Slack (Block Kit):** El recordatorio de standup debe usar Block Kit con un botón "✅ Responder Standup" que trigger el modal.

**Criterio de aceptación:** El mensaje del recordatorio aparece con formato Block Kit. El botón abre un modal funcional.

---

### Bloque 3.7 — ExcelSyncService (`src/application/excel_sync_service.py`)

```python
class ExcelSyncService:
    def __init__(
        self,
        excel_path: str,
        metric_repo: MetricRepository,
        risk_repo: RiskRepository,
        sprint_repo: SprintRepository,
    ): ...

    async def create_template(self) -> None:
        """Crea el archivo Excel con las 5 hojas vacías y headers."""
        ...

    async def sync_metrics(self, team_id: UUID) -> None:
        """Actualiza la hoja 'Métricas' con datos actuales."""
        ...

    async def sync_risks(self, team_id: UUID) -> None:
        """Actualiza la hoja 'Riesgos' con riesgos activos."""
        ...

    async def get_module_progress(self) -> list[dict]:
        """Lee la hoja 'Módulos' y retorna progreso."""
        ...

    async def update_module(self, module_id: str, updates: dict) -> None:
        """Actualiza un módulo específico en la hoja."""
        ...
```

**Hojas del Excel y sus columnas:** (Ver sección 12 de la especificación para el detalle completo de cada hoja: Módulos, Carta Gantt, Tareas, Métricas, Riesgos)

> [!WARNING]
> `openpyxl` es sincrónico. Las operaciones de Excel deben ejecutarse en un executor (`asyncio.to_thread`) para no bloquear el event loop.

**Criterio de aceptación:** `create_template` genera un archivo .xlsx con 5 hojas y headers correctos. `sync_metrics` escribe una fila nueva en la hoja Métricas.

---

### Bloque 3.8 — AIService (`src/application/ai_service.py`)

```python
class AIService:
    def __init__(self, ai_client: AIClient): ...

    async def summarize_standup(self, responses: list[StandupResponse]) -> str:
        """Genera resumen ejecutivo de las respuestas del standup."""
        ...

    async def analyze_sprint_risks(self, risks: list[Risk], prs: list[PullRequest]) -> str:
        """Análisis de riesgos con recomendaciones."""
        ...
```

**Prompts del sistema:** Definir prompts claros en constantes dentro del archivo. El bot debe responder en español, ser conciso, y enfocarse en accionables.

**Criterio de aceptación:** Genera texto coherente. Si la API falla, retorna un fallback sin romper la app.

---

## Fase 4 — Capa de Interfaces (Slack + API)

### Bloque 4.1 — Registro de la App Slack (`src/interfaces/slack/bolt_app.py`)

**Objetivo:** Crear la instancia de `AsyncApp` y registrar todos los handlers.

```python
def register_handlers(app: AsyncApp, services: dict) -> None:
    """Registra todos los comandos, eventos y acciones de Slack."""
    register_commands(app, services)
    register_events(app, services)
    register_modals(app, services)
```

**Criterio de aceptación:** Todos los slash commands, eventos y modals están registrados en un solo punto de entrada.

---

### Bloque 4.2 — Slash Commands (`src/interfaces/slack/commands.py`)

**Comandos a implementar:**

| Comando | Handler | Descripción |
|---------|---------|-------------|
| `/scrum` | `handle_scrum_command` | Abre modal de standup |
| `/riesgos` | `handle_riesgos_command` | Muestra riesgos activos |
| `/bloqueos` | `handle_bloqueos_command` | Muestra bloqueos del día |
| `/sprint` | `handle_sprint_command` | Info del sprint activo |
| `/metricas` | `handle_metricas_command` | Métricas del sprint |
| `/reporte` | `handle_reporte_command` | Genera reporte completo |
| `/progreso` | `handle_progreso_command` | Muestra progreso de módulos (Excel) |

**Patrón de implementación:**
```python
def register_commands(app: AsyncApp, services: dict):
    @app.command("/scrum")
    async def handle_scrum_command(ack, body, client):
        await ack()
        # Abrir modal
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=build_standup_modal()
        )
```

**Criterio de aceptación:** Cada comando responde en menos de 3 segundos (requisito de Slack). Los mensajes usan Block Kit para formato rico.

---

### Bloque 4.3 — Modales (`src/interfaces/slack/modals.py`)

**Modal de Standup:**

```python
def build_standup_modal() -> dict:
    """Construye el modal con 3 campos de texto."""
    return {
        "type": "modal",
        "callback_id": "standup_submission",
        "title": {"type": "plain_text", "text": "Daily Standup"},
        "submit": {"type": "plain_text", "text": "Enviar"},
        "blocks": [
            {
                "type": "input",
                "block_id": "yesterday_block",
                "label": {"type": "plain_text", "text": "¿Qué hiciste ayer?"},
                "element": {"type": "plain_text_input", "action_id": "yesterday_input", "multiline": True}
            },
            {
                "type": "input",
                "block_id": "today_block",
                "label": {"type": "plain_text", "text": "¿Qué harás hoy?"},
                "element": {"type": "plain_text_input", "action_id": "today_input", "multiline": True}
            },
            {
                "type": "input",
                "block_id": "blockers_block",
                "label": {"type": "plain_text", "text": "¿Tienes bloqueos?"},
                "element": {"type": "plain_text_input", "action_id": "blockers_input", "multiline": True},
                "optional": True
            }
        ]
    }
```

**Handler de submission:**
```python
def register_modals(app: AsyncApp, services: dict):
    @app.view("standup_submission")
    async def handle_standup_submission(ack, body, view):
        await ack()
        # Extraer valores del modal
        values = view["state"]["values"]
        yesterday = values["yesterday_block"]["yesterday_input"]["value"]
        today = values["today_block"]["today_input"]["value"]
        blockers = values["blockers_block"]["blockers_input"]["value"] or ""
        user_id = body["user"]["id"]

        # Llamar al servicio
        standup_service = services["standup_service"]
        await standup_service.submit_response(
            team_id=...,  # Resolver del contexto
            slack_user_id=user_id,
            yesterday=yesterday,
            today=today,
            blockers=blockers,
        )
```

**Criterio de aceptación:** Modal se abre correctamente. Submit guarda la respuesta. El usuario recibe confirmación efímera.

---

### Bloque 4.4 — Eventos (`src/interfaces/slack/events.py`)

**Eventos a manejar:**
- `app_mention` — Bot mencionado, responde con ayuda
- `action: standup_button_click` — Botón del recordatorio clickeado → abre modal

```python
def register_events(app: AsyncApp, services: dict):
    @app.event("app_mention")
    async def handle_mention(event, say):
        await say("¡Hola! Usa `/scrum` para enviar tu standup o `/riesgos` para ver riesgos activos. 🤖")

    @app.action("standup_button_click")
    async def handle_standup_button(ack, body, client):
        await ack()
        await client.views_open(
            trigger_id=body["trigger_id"],
            view=build_standup_modal()
        )
```

**Criterio de aceptación:** Mencionar al bot responde con help. Click en botón de recordatorio abre modal.

---

### Bloque 4.5 — FastAPI Routes (`src/interfaces/api/routes.py`)

**Objetivo:** Endpoints REST para dashboard futuro y health check.

```python
router = APIRouter(prefix="/api")

@router.get("/health")
async def health(): return {"status": "ok"}

@router.get("/teams/{team_id}/standup/today")
async def get_today_standup(team_id: UUID, session: AsyncSession = Depends(get_session)): ...

@router.get("/teams/{team_id}/risks")
async def get_risks(team_id: UUID, session: AsyncSession = Depends(get_session)): ...

@router.get("/teams/{team_id}/prs")
async def get_pull_requests(team_id: UUID, session: AsyncSession = Depends(get_session)): ...

@router.get("/teams/{team_id}/metrics")
async def get_metrics(team_id: UUID, session: AsyncSession = Depends(get_session)): ...
```

**Criterio de aceptación:** `GET /api/health` retorna 200. Los endpoints retornan JSON con datos del team.

---

### Bloque 4.6 — Dependencies (`src/interfaces/api/dependencies.py`)

**Objetivo:** Inyección de dependencias para FastAPI.

```python
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

def get_standup_service(session: AsyncSession = Depends(get_session)) -> StandupService:
    return StandupService(
        session_repo=StandupSessionRepositoryImpl(session),
        response_repo=StandupResponseRepositoryImpl(session),
        member_repo=MemberRepositoryImpl(session),
    )
# ... pattern similar para cada servicio
```

---

## Fase 5 — Punto de Entrada (`src/main.py`)

**Objetivo:** Ensamblar todo: FastAPI + Slack Bolt + Scheduler.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Scrum Master Bot...")
    scheduler.start()
    # Programar recordatorio diario
    scheduler.add_daily_job(send_standup_reminder, hour=9, minute=0, ...)
    # Programar resumen diario
    scheduler.add_daily_job(send_daily_summary, hour=17, minute=0, ...)
    # Programar sync GitHub cada 2h
    # Programar sync Excel diario
    yield
    # Shutdown
    scheduler.shutdown()
    await github_client.close()
    await ai_client.close()

app = FastAPI(title="Scrum Master Bot", lifespan=lifespan)

# Montar Slack
slack_app = create_slack_app(settings.slack_bot_token, settings.slack_signing_secret)
register_handlers(slack_app, services)
handler = AsyncSlackRequestHandler(slack_app)

@app.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

# Montar API routes
app.include_router(api_router)
```

**Criterio de aceptación:** `docker-compose up` levanta todo. Bot responde a `/scrum` en Slack. Scheduler ejecuta jobs. Health check responde.

---

## Fase 6 — Tests

### Bloque 6.1 — Configuración de Tests (`tests/conftest.py`)

- Fixtures para base de datos in-memory (SQLite async o PostgreSQL de test)
- Fixtures para repos mock
- Fixtures para servicios con dependencias mockeadas

### Bloque 6.2 — Tests Unitarios Prioritarios

| Test | Qué valida |
|------|-----------|
| `test_standup_service.py` | Submit, doble submit falla, missing members, close session |
| `test_risk_service.py` | Detección de PR envejecido, blocker en standup, no duplicar riesgos |
| `test_github_service.py` | Sync persiste PRs, upsert no duplica, stale_prs filtra correcto |
| `test_report_service.py` | Resumen contiene todas las secciones, maneja datos vacíos |

### Bloque 6.3 — Tests de Integración

| Test | Qué valida |
|------|-----------|
| `test_slack_commands.py` | Simular slash command, verificar que se abre modal, verificar respuesta |
| `test_db_repos.py` | CRUD real contra PostgreSQL de Docker |

---

## Orden de Ejecución Sugerido

> [!TIP]
> Pide al modelo generador que ejecute un bloque a la vez. Valida antes de pasar al siguiente.

```mermaid
graph TD
    A["0.1 Scaffolding"] --> B["0.2 Docker/Config"]
    B --> C["0.3 Settings"]
    C --> D["1.1 Modelos Dominio"]
    D --> E["1.2 Excepciones"]
    D --> F["1.3 Repositorios Abstractos"]
    E --> G["2.1 Database"]
    F --> G
    G --> H["2.2 ORM Models"]
    H --> I["2.3 Alembic"]
    I --> J["2.4 Repos Concretos"]
    J --> K["2.5.1 GitHub Client"]
    J --> L["2.5.2 Slack Client"]
    J --> M["2.5.3 AI Client"]
    J --> N["2.5.4 Scheduler"]
    K --> O["3.1 StandupService"]
    L --> O
    K --> P["3.2 GitHubService"]
    P --> Q["3.3 RiskService"]
    O --> Q
    O --> R["3.4 ReportService"]
    Q --> R
    L --> S["3.6 NotificationService"]
    N --> T["3.5 SprintService"]
    R --> U["3.7 ExcelSyncService"]
    M --> V["3.8 AIService"]
    O --> W["4.1-4.4 Slack Interface"]
    S --> W
    R --> X["4.5-4.6 API Routes"]
    W --> Y["5.0 main.py"]
    X --> Y
    Y --> Z["6.1-6.3 Tests"]
```

---

## Checklist Final

- [ ] `docker-compose up` levanta app + DB sin errores
- [ ] `alembic upgrade head` crea todas las tablas
- [ ] `/scrum` en Slack abre modal y guarda respuesta
- [ ] `/riesgos` muestra PRs sin review
- [ ] `/bloqueos` muestra bloqueos del standup del día
- [ ] Recordatorio se envía a las 9:00 AM
- [ ] Resumen diario se genera a las 17:00
- [ ] PRs se sincronizan desde GitHub periódicamente
- [ ] Riesgos se detectan automáticamente
- [ ] Excel se crea con template y se actualiza con métricas
- [ ] Tests unitarios pasan
- [ ] Health check responde en `/api/health`
