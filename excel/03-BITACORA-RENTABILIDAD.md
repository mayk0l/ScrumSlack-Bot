# Bitácora — Módulo de Rentabilidad

> Registro vivo del avance. Agregar una entrada por cada sesión de trabajo, decisión o hallazgo.
> Formato de fecha: `YYYY-MM-DD`. Las entradas más recientes van **arriba**.

---

## Cómo usar esta bitácora

- **Cada día/sesión de trabajo** → nueva entrada en la sección "Registro cronológico".
- **Decisiones importantes** (enfoque, fórmula, plantilla) → además anótalas en "Decisiones (ADR ligero)".
- **Pendientes/bloqueos** → mantener al día la tabla "Pendientes y bloqueos".
- Vincular cada tarea con su ID del plan (T1.1, T2.4, etc.) cuando aplique.

---

## Estado general

| Campo | Valor |
|---|---|
| Fase actual | Fase 1 — Núcleo funcional |
| Semana | S3 (jun-2026) |
| % avance estimado | ~26% |
| Hito próximo | M1 — Núcleo funcional (~30-jun-2026) |
| Bloqueos abiertos | Decisión de enfoque (T1.1); suite global roja (169 fallas, causa raíz FX) |

---

## Registro cronológico

### 2026-06-14 — Entorno levantado + estabilización de la suite de tests (A0.4 / A1.4)
- **Hecho**:
  - Levantado el backend en Docker apuntando a la **base de producción** vía túnel SSH
    (`docker-compose-backend.yml` + `docker-compose.local-override.yml`; app en :3000,
    DB prod por `host.docker.internal:6543`, `INIT_DB=false`, sidekiq apagado). Verificado
    contra prod: 9 users / 1290 accounts.
  - **Reescrito `spec/commands/report_for_sub_account_spec.rb`** al contrato actual del command
    (`profitability_accounts` + `target_currency` → `summary`/`monthly`/`last_year`/`current_year`).
    Antes probaba la API muerta (`for(sub_account:)` → `accumulated`). Test de caracterización
    con CLP (sin dependencia de tablas FX); valida fórmula absoluta y relativa.
  - **Arregladas factories rotas**: `profitability_accounts` (no cumplía validaciones del modelo)
    y `accounts` (faltaba `country`, un `belongs_to` requerido que rompía `create(:account)` en
    **toda** la suite).
  - **Suite ya carga y corre**: agregado `require 'pundit/rspec'` en `rails_helper` (4 specs de
    `policies/` abortaban la corrida completa con `undefined method 'permissions'`).
  - Removido `--format=Nc` de `.rspec` (rspec-nc → terminal-notifier crasheaba en Linux/Docker/CI).
  - **A1.2 (centralizar año)**: extraída la regla "año − 1" a un único método documentado
    `reference_year` en `report_for_sub_account.rb` (antes magic number suelto). Un solo punto
    de cambio cuando se cierre D2. Comportamiento idéntico (spec verde).
  - **A1.3 (conversión FX robusta)**: eliminado el fallback silencioso a `1.0` en
    `CurrencyConversionService`; ahora loguea y levanta `MissingRateError` cuando falta el
    precio FX. Nuevo `spec/services/currency_conversion_service_spec.rb` (6 examples verdes).
    ⚠️ Cambio de comportamiento: con FX faltante el reporte de cuentas no-CLP fallará visible
    en vez de mostrar números errados. Prod tiene las tablas FX pobladas. Cómo mostrarlo en UI
    queda para A5.2.
  - **Specs del modelo `ProfitabilityAccount`**: reemplazado el placeholder `pending` por specs
    reales (presencia, numericalidad, `belongs_to`, factory válida) con shoulda-matchers.
  - **Request spec del `ReportsController`**: caracteriza los 4 endpoints end-to-end con CLP.
  - **Commits**: rama `feature/rentabilidad-estabilizacion` (6 commits atómicos sobre `staging`).
    Total specs de rentabilidad: 38 examples verdes.
- **Hallazgos nuevos**:
  - **A3.2 reconsiderado**: la auth NO es un problema específico de rentabilidad. TODA la API
    `Api::V1` saltea `authenticate_user!` (Devise) y usa `before_action :authenticate_users!`,
    que está **definido vacío** en `Api::V1::BaseController` (no-op). O sea, la API entera está
    sin autenticación real. "Reactivar auth" requiere una decisión e implementación transversal
    (no es un cambio de rentabilidad). NO se tocó. Queda como hallazgo de seguridad a decidir.
  - El reporte serializa los montos como **string** en el JSON (BigDecimal → `"150.0"`); el
    frontend debe parsearlos. Se conecta con A2.1 (manejo de decimales).
- **Frontend (`valuelist-ng`, rama `feature/rentabilidad-frontend-decimales`)**:
  - **A2.1 (hecho)**: `saveEdits()` en `profitability-monthly-table-v2` usaba `parseInt` →
    truncaba decimales. Reemplazado por el helper existente `unformat()` (conserva decimales
    y tolera formato con separadores). Type-check OK.
  - **A2.4 (hecho)**: reemplazados los `alert()` por `MatSnackBar` (helper `notify()`, mismo
    patrón que `main-header`). Type-check OK. Falta smoke test visual (no ejecutable aquí).
  - Hallazgo: el "año − 1" también está hardcodeado en el front
    (`profitability-monthly-table-v2.component.ts:31`, `getFullYear() - 1`) — contraparte de A1.2.
  - **A2.2 (hecho)**: tras editar, la fila conservaba el % viejo. Ahora la tabla mensual emite
    `@Output dataUpdated` al guardar y `profitability-page` recarga el reporte (`fetchReport`),
    que reconstruye la tabla con la rentabilidad recalculada. Verificado con `ng build` (AOT +
    `strictTemplates: true`) → 0 errores; valida el binding del template, no solo el TS.
  - ⚠️ La rama parte del `staging` local que ya estaba **8 commits adelante de `origin/staging`
    sin pushear** (trabajo previo de profitability); la rama los arrastra.
- **Hallazgos**:
  - Confirmados contra código actual: auth desactivada en `Api::V1::ReportsController`
    (`skip_before_action :authenticate_user!`), "año − 1" hardcodeado
    (`report_for_sub_account.rb:5`) y fallback silencioso a `1.0` en
    `CurrencyConversionService` (`:26`).
  - **Baseline real de la suite: 380 examples, 169 failures, 36 pending.** Causa raíz dominante
    (~106 fallas): `membership.rb:101` divide `balance / dollar` y la DB de test no tiene
    registros de precios FX → `TypeError: nil can't be coerced into Integer`. Es rot
    **preexistente y ajeno a rentabilidad**. Los specs de rentabilidad quedan **verdes**
    (7 examples, 0 failures).
- **Decisiones**: Los specs reescritos son de *caracterización* (fijan comportamiento actual),
  NO consolidan como correctas la regla "año − 1" (D2/A1.2) ni la asimetría de `log_return`
  en retornos negativos (A1.1) — quedan marcadas como pendientes en el propio spec.
- **Bloqueos**: La suite global no se puede dejar verde sin decidir cómo sembrar/manejar precios
  FX en test (afecta `Membership#balance`). Excede el alcance de rentabilidad.
- **Próximo paso**: Definir rumbo — seguir con feature de rentabilidad (A1.2 centralizar año /
  A1.3 conversión FX robusta / A3.2 reactivar auth) vs. estabilización global de la suite.
- **Tareas tocadas**: A0.4 (parcial), A1.4 (hecho), A1.2 (hecho), A1.3 (hecho),
  specs de modelo y request del reporte (cobertura), A3.2 (analizado → escalado, no implementado),
  A2.1 (hecho, front), A2.4 (hecho, front), A2.2 (hecho, front, verificado con ng build).
- **Artefactos**: `spec/commands/report_for_sub_account_spec.rb`,
  `spec/factories/{profitability_accounts,accounts}.rb`, `spec/rails_helper.rb`, `.rspec`.

### 2026-05-30 — Análisis inicial del módulo
- **Hecho**: Revisión completa de `valuelist-ruby` y `valuelist-ng`. Mapeo de modelo,
  endpoints, cálculo, conversión de moneda y componentes Angular de rentabilidad.
- **Hallazgos clave**:
  - No existe carga de datos por UI (ni individual ni masiva). *(bloqueante)*
  - Migración a medio terminar: spec de `ReportForSubAccount` prueba una API vieja
    (`accumulated`, `sub_account.balance`), código actual usa snapshots de
    `ProfitabilityAccount` con contrato `last_year`/`current_year`.
  - Código muerto en `profitability-page.component.ts` (espera `accumulated`).
  - Edición pierde decimales (`parseInt`) y no recalcula rentabilidad.
  - Auth desactivada en `ReportsController`.
  - Lógica "año − 1" hardcodeada en backend y frontend.
- **Decisión**: Estructurar el trabajo en 3 fases / 3 meses (núcleo, carga masiva, pruebas).
- **Próximo paso**: Cerrar decisión de enfoque (T1.1) con negocio.
- **Artefactos**: `01-ANALISIS-RENTABILIDAD.md`, `02-PLANIFICACION-Y-GANTT.md`, esta bitácora.

<!--
### YYYY-MM-DD — Título corto
- **Hecho**:
- **Hallazgos**:
- **Decisiones**:
- **Bloqueos**:
- **Próximo paso**:
- **Tareas tocadas**: T_._
-->

---

## Decisiones (ADR ligero)

| # | Fecha | Decisión | Motivo | Estado |
|---|---|---|---|---|
| D1 | — | Enfoque de datos: snapshots manuales vs. cálculo desde wallet | — | ⏳ Pendiente (T1.1) |
| D2 | — | Regla "año actual = año − 1": ¿intencional? | Centralizada en `reference_year` (A1.2), lista para cambiar | ⏳ Pendiente validación negocio (T1.2) |
| D6 | 2026-06-14 | Auth de la API V1 está stubbeada (`authenticate_users!` vacío en BaseController) → toda la API sin auth real, no solo rentabilidad | Reactivar requiere decisión/implementación transversal | ⏳ Pendiente (escalado) |
| D3 | — | Contrato único de respuesta del reporte | — | ⏳ Pendiente (T1.3) |
| D4 | — | Formato de plantilla de carga masiva | — | ⏳ Pendiente (T2.1) |
| D5 | — | Campos realmente obligatorios en `ProfitabilityAccount` | — | ⏳ Pendiente (T2.1) |

---

## Pendientes y bloqueos

| ID | Descripción | Tipo | Prioridad | Estado | Responsable |
|---|---|---|---|---|---|
| T1.1 | Decidir enfoque de datos | Decisión | Alta | Abierto | — |
| T1.5 | Validar fórmula con casos reales | Validación | Alta | Abierto | — |
| T2.10 | Obtener/limpiar datos fuente de cuentas faltantes | Insumo | Alta | Abierto | — |
| T0.4 | Suite global roja: 169 fallas, raíz FX faltante en test (`Membership#balance`) | Deuda técnica | Media | Abierto | — |

---

## Métricas de seguimiento (opcional)

| Semana | Tareas planificadas | Tareas completadas | Bloqueos | Comentario |
|---|---|---|---|---|
| S1 | — | — | — | — |
