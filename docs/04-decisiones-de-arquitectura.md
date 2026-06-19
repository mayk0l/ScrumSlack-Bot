# Decisiones de Arquitectura

Este documento describe las decisiones de diseño clave tomadas para el desarrollo del Scrum Master Bot.

## 1. Arquitectura Hexagonal (Clean Architecture)

El proyecto está estructurado utilizando una Arquitectura Hexagonal, separando claramente las responsabilidades en cuatro capas:

- **Dominio (`src/domain`):** Contiene la lógica de negocio core. Entidades, enums y excepciones. Esta capa no depende de ningún framework (ni SQLAlchemy, ni FastAPI, ni Slack).
- **Aplicación (`src/application`):** Contiene los casos de uso (servicios). Orquesta la interacción entre las entidades de dominio y los repositorios. Tampoco depende de frameworks externos, excepto inyección de repositorios abstractos.
- **Infraestructura (`src/infrastructure`):** Implementaciones concretas. Aquí reside la base de datos (SQLAlchemy ORM), los clientes HTTP (GitHub, Slack, AI), la sincronización con Excel y el Scheduler (APScheduler).
- **Interfaces (`src/interfaces`):** Puntos de entrada de la aplicación. Contiene la API REST (FastAPI) y los handlers de Slack (Slack Bolt).

## 2. Dataclasses sobre Modelos ORM

Decidimos utilizar `dataclasses` estándar de Python para los modelos de dominio, separándolos completamente de los modelos ORM de SQLAlchemy.
- **Ventaja:** El dominio se mantiene puro, facilitando las pruebas unitarias y evitando problemas con el _event loop_ asíncrono al realizar operaciones en la base de datos (lazy loading).
- **Costo:** Requiere mapear explícitamente entre objetos del dominio y registros ORM mediante métodos `to_domain()` y `from_domain()` en los repositorios.

## 3. Separación de Slack, FastAPI y Dominio

Las rutas web y los comandos de Slack actúan como capas de presentación que simplemente serializan datos a JSON o Block Kit y hacen llamadas a los servicios de la capa de aplicación. El núcleo nunca conoce de dónde provino la orden (HTTP, Slack, etc.).

## 4. Inyección de Dependencias

Evitamos librerías pesadas de inyección de dependencias (DI). En su lugar:
- En FastAPI, usamos `Depends()` para resolver la sesión y proveer repositorios.
- En Slack, proveemos un diccionario de servicios base o una _factory function_ `session_maker()` a través del constructor y resolvemos dinámicamente según sea necesario por la sesión.
- En los servicios, las dependencias se pasan mediante el constructor (Constructor Injection), lo que permite inyectar versiones "Mock" (Fakes) muy fácilmente en los tests.

## 5. Fuente de Verdad: Excel para planificación, DB para actividad

**Contexto.** El bot maneja dos tipos de información con ciclos de vida distintos:
la **planificación** (objetivos, tareas, fechas, % de logro, evidencia) que el
equipo edita y consulta de forma colaborativa, y la **actividad diaria** generada
por el propio sistema (respuestas de standup, riesgos detectados, pull requests,
métricas de sprint).

**Decisión.**
- El archivo **Excel (`project_tracking.xlsx`) es la fuente de verdad de la
  planificación.** `ValuelistExcelService` es el único componente que lo lee y
  escribe. Hojas: `Bitácora`, `Planificación`, `Administración`, `Evidencia`,
  `Gantt` y `Dashboard`.
- La **base de datos PostgreSQL es la fuente de verdad de la actividad diaria**
  (standups, riesgos, PRs, métricas), gestionada por los repositorios y servicios
  de aplicación.
- El **reporte diario y la hoja `Dashboard` son vistas de solo lectura** que
  *unen* ambos mundos: progreso de tareas (Excel) + standups/riesgos/PRs (DB).
  Ninguno de los dos es dueño de los datos del otro.

**Consecuencia.** Los comandos de Slack que tocan planificación delegan en
`ValuelistExcelService`; los que tocan actividad usan los servicios de DB. Se
elimina la ambigüedad previa donde existían dos esquemas de Excel paralelos.

## 6. Consolidación de los servicios de Excel

**Contexto.** Existían dos servicios de Excel con esquemas incompatibles:
`ValuelistExcelService` (conectado a todos los comandos) y `ExcelSyncService`
(hojas `Módulos`/`Métricas`/`Riesgos`). Este último nunca se instanciaba en
producción (solo en un script de prueba), y el archivo real no contiene esas
hojas. El esfuerzo de estilizado "para stakeholders" se había aplicado allí, por
lo que no tenía efecto sobre el archivo que el equipo descarga.

**Decisión.** Se elimina `ExcelSyncService`. Los primitivos de estilo reutilizables
(paleta corporativa, headers, bordes, tablas nativas, colores por severidad) se
extraen a `src/infrastructure/excel_styles.py` y los consume `ValuelistExcelService`.

**Consecuencia.** La sincronización de riesgos/métricas a Excel deja de existir
como tal; si en el futuro se quiere exponer esa información en el archivo, se hará
a través de la hoja `Dashboard` leyendo desde la DB, en línea con la decisión #5.
