# Changelog y Corrección de Bugs

## Fase H — Pulido y Conexión Real (2026-06-19)

Iniciativa para convertir el MVP en un bot que aporte valor real: conectar el
Excel con los comandos y la base de datos, pulir mensajes y modales, y mejorar
la robustez. Cada feature pasa la suite de tests antes de un commit atómico.

### Fase 0 — Base limpia
- **Baseline de tests verde** (220 passed, 2 skipped) realineando tests
  obsoletos: `test_valuelist_excel_service` reescrito con archivos `.xlsx`
  reales, y aserciones frágiles de modales/comandos/scaffolding actualizadas.
- **Migración inicial versionada** (`24a4b5857e1c_initial_schema`); antes el
  esquema solo existía vía `create_all`.
- **Fuente de verdad definida** (ADR #5) y **`ExcelSyncService` eliminado**
  (ADR #6). Sus estilos reutilizables se movieron a
  `src/infrastructure/excel_styles.py`.
  > **Corrección a Fase G:** el estilizado "para stakeholders" descrito abajo se
  > había aplicado a `excel_sync_service.py`, un servicio huérfano que no
  > afectaba el archivo real que descarga el equipo. El estilizado efectivo vive
  > en `ValuelistExcelService` y ahora consume el módulo compartido de estilos.
- **Limpieza de repo**: `.DS_Store` ignorado y desindexado, `fix_responsables.py`
  movido a `scripts/`, y artefactos de prueba sueltos eliminados.

---

## Fase G — Mejoras de Presentación para Stakeholders (2026-06-18)

### Estilo Premium del Excel para Reportes Ejecutivos
**Objetivo:** Mejorar la presentación visual de los archivos Excel generados por el bot para hacerlos más profesionales y fáciles de interpretar por stakeholders externos e internos.

**Mejoras implementadas:**

#### 1. Hoja de Riesgos (`excel_sync_service.py`)
- ✅ **Colores por severidad**:
  - 🟢 Low: Verde (#A9D08E)
  - 🟡 Medium: Amarillo (#FFD966)
  - 🟠 High: Naranja (#F4B084)
  - 🔴 Critical: Rojo (#FF6B6B)
- ✅ **Formato de fechas**: DD/MM/AAAA (formato Excel nativo)
- ✅ **Estado visual**: ✅ Sí / ⚠️ No con emojis
- ✅ **Tablas nativas** con filtros automáticos
- ✅ **Text wrapping** en descripciones largas
- ✅ **Actualización dinámica** del rango de tabla

#### 2. Hoja de Métricas (`excel_sync_service.py`)
- ✅ **Formato numérico** con 2 decimales
- ✅ **Formato de fechas** DD/MM/AAAA
- ✅ **Tabla nativa** con zebra stripes
- ✅ **Alineación centrada** optimizada
- ✅ **Rango dinámico** de tabla

#### 3. Hoja de Bitácora (Resumen Ejecutivo) (`valuelist_excel_service.py`)
- ✅ **Headers corporativos**: Azul oscuro (#1F4E78) con texto blanco
- ✅ **Freeze panes** en fila 2
- ✅ **Column widths** ajustados (ID: 8, Campo: 25, Descripción: 70)
- ✅ **Colores diferenciados**:
  - OG (Objetivo General): Gris (#E7E6E6) con negrita
  - OE (Objetivos Específicos): Gris claro (#F2F2F2)
- ✅ **Text wrapping** en columna de descripción

**Impacto:**
- Escaneo visual rápido de prioridades por color
- Aspecto profesional con estilos corporativos nativos de Excel
- Usabilidad mejorada con filtros y freeze panes
- Trazabilidad visual con DataBars en porcentajes (ya existente desde Fase E)

**Archivos modificados:**
- `src/application/excel_sync_service.py`: Mejoras en `_setup_sheet()`, `sync_metrics()`, `sync_risks()`
- `src/application/valuelist_excel_service.py`: Mejoras en `_apply_gantt_and_styles()` para Bitácora

**Documentación:**
- Nuevo archivo: `docs/mejoras-excel-stakeholders.md` con comparativa visual y checklist

---

## Correcciones Fase A (Estabilización)

### 1. Error de Dependency Injection en `routes.py`
**Problema:** Los endpoints intentaban llamar a `.to_domain()` sobre objetos que ya eran instancias del dominio, dado que los repositorios fueron refactorizados previamente para retornar directamente modelos del dominio (Dataclasses) en vez de modelos ORM.
**Solución:** Se removieron todas las llamadas `.to_domain()` en los endpoints de `routes.py` y se reemplazaron por FastAPI serialization directo o por un helper `_serialize()`.

### 2. Error de Dependency Injection en Slack Handlers (`main.py` / `commands.py`)
**Problema:** `main.py` instanciaba los servicios de aplicación pasándoles un diccionario con `None` (ej. `services={"standup_service": None}`) lo cual causaba crasheos al recibir comandos o acciones de Slack, porque los métodos intentaban ejecutarse sobre `None`.
**Solución:** Se implementó una _factory function_ (`session_maker`) dentro del diccionario `services`. Ahora, cada handler (`/riesgos`, `/reporte`, modal submit) invoca a un helper interno `_get_services()` que obtiene una sesión asíncrona nueva, instancia los repositorios concretos inyectando esa sesión, y luego instancia los servicios pasándole los repositorios. Esto garantiza un _scoped lifetime_ por cada request de Slack, que es el patrón ideal para SQLAlchemy `AsyncSession`.

### 3. Falta del Repositorio de Standup en RiskService
**Problema:** El `RiskService` no contaba con acceso al repositorio de sesiones de Standup, imposibilitando la detección de bloqueos del día.
**Solución:** Se añadió `session_repo` a la inicialización de `RiskService` en `main.py`, `commands.py` y las pruebas unitarias, implementando finalmente el método `_detect_standup_blockers` de forma correcta y eficiente.

### 4. Implementación de Slash Commands Faltantes
**Problema:** Múltiples comandos devolvían "implementación pendiente".
**Solución:**
- `/bloqueos`: Implementado para extraer y listar usuarios con bloqueos activos en la sesión de hoy.
- `/sprint`: Agregado para mostrar detalles, fechas y estado del sprint activo.
- `/metricas`: Añadido para retornar la lista de métricas (velocity, completion, etc.) del sprint en curso.
- `/progreso`: Implementado para invocar a `ExcelSyncService` y leer la pestaña "Módulos", mostrando en Slack el avance de cada módulo.

### 5. Generación de la Migración Inicial
**Problema:** Existía un archivo de migración vacío o inconsistente con los modelos SQLAlchemy definidos en `src/infrastructure/orm_models.py`.
**Solución:** Se borró la migración residual, se limpió la tabla `alembic_version` del contenedor local de PostgreSQL y se regeneró la migración inicial usando el contenedor de la aplicación.
