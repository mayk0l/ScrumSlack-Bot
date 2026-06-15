# Convenciones de Desarrollo: Scrum Master Bot

Este documento define las reglas de trabajo para mantener el proyecto ordenado, testeado y documentado. Aplica tanto para desarrollo manual como para ejecución en modo agente.

---

## 1. Estructura de Documentación

Toda la documentación vive en `docs/` y sigue numeración por orden de lectura:

| Archivo | Contenido |
|---------|-----------|
| `docs/00-especificacion-completa.md` | Especificación funcional y técnica completa. |
| `docs/01-plan-de-ejecucion.md` | Plan de implementación bloque por bloque. |
| `docs/02-kanban.md` | Tablero de tareas y estado actual. |
| `docs/03-convenciones-de-desarrollo.md` | Este archivo. |
| `docs/04-decisiones-de-arquitectura.md` | ADRs y decisiones técnicas importantes (futuro). |
| `docs/05-changelog.md` | Registro de cambios por versión (futuro). |

**Reglas:**
- Nunca modificar los documentos originales sin actualizar las referencias.
- Si un cambio de código altera la arquitectura o los flujos, actualizar `docs/00-especificacion-completa.md` o crear `docs/04-decisiones-de-arquitectura.md`.
- El `README.md` de raíz debe mantenerse al día con el estado actual y los pasos de inicio.

---

## 2. Configuración del Agente (`opencode`)

La carpeta `.opencode/` contiene la configuración del agente para este proyecto:

```text
.opencode/
├── opencode.json              # Configuración principal del proyecto
├── agents/
│   └── claude.md              # Agente primario especializado en el proyecto
└── skills/
    ├── scrum-bot/SKILL.md     # Contexto y reglas del proyecto
    ├── atomic-commits/SKILL.md # Convenciones de commits atómicos
    ├── model-handoff/SKILL.md # Recuperación de estado al cambiar de modelo
    └── caveman-mode/SKILL.md  # Modo conciso para ahorrar tokens (siempre activo)
```

**Reglas:**
- `opencode.json` carga automáticamente `README.md` y todos los documentos de `docs/` como instrucciones.
- Las skills locales se escanean desde `.opencode/skills/`.
- El agente por defecto es `claude`, definido en `.opencode/agents/claude.md`.
- Al cambiar de modelo, el skill `model-handoff` debe activarse para leer el estado actual desde `docs/02-kanban.md`.

**Importante:** Después de modificar cualquier archivo dentro de `.opencode/`, es necesario reiniciar opencode para que los cambios surtan efecto.

---

## 3. Convención de Commits

### 3.1 Commits Atómicos

Cada commit debe representar **un único cambio lógico** que compile/pase sus tests:

- ✅ Correcto: `feat(standup): add submit_response with duplicate protection`
- ❌ Incorrecto: `various changes`
- ❌ Incorrecto: mezclar refactor de dominio + nuevo comando de Slack + fix de typo en el mismo commit.

### 3.2 Formato del Mensaje

```
<type>(<scope>): <descripción corta>

<cuerpo opcional: explicación del cambio y por qué>

<referencias opcionales: issues, tareas del kanban>
```

**Tipos:**

| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad. |
| `fix` | Corrección de bug. |
| `docs` | Cambios solo de documentación. |
| `test` | Agregar o modificar tests. |
| `refactor` | Reestructuración de código sin cambiar comportamiento. |
| `chore` | Tareas de mantenimiento (deps, config, scripts). |
| `style` | Cambios de formato sin cambiar lógica. |

**Ejemplos:**

```
feat(domain): add StandupResponse and SessionStatus enums

fix(github): handle 429 rate limit with exponential backoff

docs(kanban): mark 0.1 scaffolding as done

test(standup): reject duplicate daily responses
```

### 3.3 Idioma

- Mensajes de commit en **inglés técnico**.
- Descripción en imperativo presente (`add`, `fix`, `update`).

---

## 4. Flujo de Trabajo con Agente

Cuando el agente trabaje en modo loop autónomo, debe seguir este ciclo por cada bloque del kanban:

```
1. Leer tarea activa en docs/02-kanban.md
2. Implementar el bloque correspondiente
3. Escribir o actualizar tests
4. Ejecutar tests y verificar que pasan
5. Actualizar docs/02-kanban.md (mover a Done)
6. Actualizar README.md u otros docs si es necesario
7. Hacer commit atómico
8. Pasar a la siguiente tarea
```

**Reglas estrictas:**

- No avanzar a la siguiente tarea sin validar el criterio de aceptación actual.
- Cada servicio nuevo debe tener al menos su test unitario antes del commit.
- Cada cambio en configuración o arquitectura debe reflejarse en documentación.
- No mezclar en un solo commit implementación de distintas fases (dominio + infraestructura + interfaz).
- Si una tarea se bloquea, moverla a la columna **Blocked** en `docs/02-kanban.md` y explicar el bloqueador.

---

## 5. Convenciones de Código

Resumen de las reglas globales definidas en `docs/01-plan-de-ejecucion.md`:

| Aspecto | Convención |
|---------|------------|
| Lenguaje | Python 3.12, tipado estricto (`from __future__ import annotations`) |
| Async | Todo I/O es `async/await`. Sin llamadas bloqueantes. |
| Imports | Absolutos desde `src.` (ej: `from src.domain.models import Team`) |
| Docstrings | Google style. Español para comentarios de negocio; inglés para API/código. |
| Nombres | `snake_case` archivos/funciones, `PascalCase` clases, `UPPER_CASE` constantes. |
| IDs | UUID v4 en todas las entidades. |
| Errores | Excepciones de dominio propias, nunca excepciones genéricas desnudas. |
| Logging | `structlog` con contexto (`team_id`, `user_id`). |
| Config | `pydantic-settings` con `.env`, nunca hardcoded. |
| Tests | pytest + pytest-asyncio, fixtures en `conftest.py`. |

---

## 6. Testing

### 6.1 Obligatoriedad

- Todo servicio de aplicación debe tener tests unitarios.
- Todo repositorio debe tener tests de integración contra PostgreSQL.
- Todo handler de Slack debe tener al menos un test de integración simulado.

### 6.2 Pirámide de Tests

```
        /\\
       /  \\     Integration (Slack, DB)
      /____\\
     /      \\
    /________\\   Unit (services, domain)
```

### 6.3 Ejecución

```bash
# Unitarios
pytest tests/unit

# Integración (requiere DB de Docker)
docker-compose up -d db
pytest tests/integration

# Con cobertura
pytest --cov=src
```

---

## 7. Documentación de Cambios

Después de cada bloque completado:

1. Marcar la tarea como `✅ Done` en `docs/02-kanban.md`.
2. Si el cambio introduce una decisión técnica, agregar entrada a `docs/04-decisiones-de-arquitectura.md`.
3. Si el cambio es visible para el usuario, agregar línea a `docs/05-changelog.md`.

---

## 8. Checklist antes de Commit

- [ ] Código pasa el linter/formateador configurado (futuro).
- [ ] Tests nuevos pasan.
- [ ] Tests existentes no se rompen.
- [ ] Documentación actualizada (`docs/` y/o `README.md`).
- [ ] Mensaje de commit sigue la convención.
- [ ] Commit es atómico (un solo cambio lógico).

---

## 9. Notas para el Propietario del Repositorio

El push a GitHub queda a cargo del usuario humano. El agente:

- No ejecutará `git push` sin autorización explícita.
- Puede ejecutar `git add`, `git status` y `git diff` para preparar commits.
- Hará commits atómicos localmente como parte del flujo de trabajo.
