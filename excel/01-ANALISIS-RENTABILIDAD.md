# Análisis del Módulo de Rentabilidad — Valuelist

> Fecha del análisis: **2026-05-30**
> Autor: Emiliano Jofré / asistido por Claude
> Repos analizados: `valuelist-ruby` (backend Rails) · `valuelist-ng` (frontend Angular)

---

## 1. Resumen ejecutivo

El módulo de rentabilidad **existe y funciona parcialmente**: ya hay modelo de datos,
endpoints, cálculo mes a mes, conversión de moneda y una vista en Angular con varias
tablas (mensual, devengada, resumen, subcuentas). Sin embargo, **es una migración a
medio terminar** y le faltan piezas clave para considerarlo "terminado, listo y funcional":

- ⚠️ **No existe ninguna forma de cargar datos por la interfaz.** Hoy los registros de
  `ProfitabilityAccount` sólo se pueden crear por consola/SQL. No hay importador, ni
  formulario de alta, ni carga masiva. Esto es el bloqueante #1 para "subir las cuentas
  faltantes".
- ⚠️ **El backend y el frontend no están alineados.** El código fue migrado de un enfoque
  (saldos calculados desde `wallet`) a otro (snapshots manuales en `ProfitabilityAccount`),
  pero quedaron restos del enfoque viejo: specs que prueban una API que ya no existe,
  código muerto en la página, y dos "contratos" de respuesta distintos conviviendo.
- ⚠️ **La edición pierde precisión** (usa `parseInt`, descarta decimales) y **no recalcula**
  la rentabilidad tras editar.
- ⚠️ **Riesgos de cálculo**: lógica `año actual = año - 1` hardcodeada, fórmula de retorno
  logarítmico sumada entre meses, y suma de valores absolutos sin componer capital.
- ⚠️ **Seguridad**: el `ReportsController` tiene la autenticación desactivada
  (`skip_before_action :authenticate_user!`).

Con un plan de **3 meses** dividido en (1) dejar el núcleo funcional, (2) carga masiva,
y (3) pruebas y ajustes, el módulo queda en producción de forma sólida.

---

## 2. Arquitectura actual

### 2.1 Backend (`valuelist-ruby`)

| Componente | Archivo | Rol |
|---|---|---|
| Modelo | `app/models/profitability_account.rb` | Snapshot mensual por subcuenta (saldo inicial, depósitos, retiros, saldo final, dividendos, etc.) |
| Migración | `db/migrate/20240801014912_create_profitability_accounts.rb` | Define la tabla |
| Cálculo | `app/commands/report_for_sub_account.rb` | Arma el reporte: mensual del año, resumen año actual y año pasado |
| Conversión | `app/services/currency_conversion_service.rb` | Convierte CLP/USD/EUR/UF usando precios por fecha |
| Controlador | `app/controllers/api/v1/reports_controller.rb` | Endpoints de reporte, lectura cruda y edición mensual |
| Tarea | `lib/tasks/migrate_profitability_to_wallet.rb` | Migra depósitos/retiros a `WalletDeposit`/`WalletWithdrawal` |

**Campos de `profitability_accounts`** (todos `decimal 15,4`):
`sub_account_id`, `sub_account_name`, `account_id`, `account_name`, `currency`,
`institution`, `period`, `start_date`, `end_date`, `initial_balance`, `deposits`,
`withdrawals`, `final_balance`, `other_transactions`,
`dividends_interest_and_other_income`, `net_portfolio_change`, `updated_balance`, `status`.

**Endpoints (rutas):**
- `GET  /api/v1/sub_accounts/:id/report` — reporte de una subcuenta
- `POST /api/v1/sub_accounts/reports` — reporte de varias subcuentas (`ids[]`)
- `GET  /api/v1/sub_accounts/:id/reports/raw_monthly?monthly=...` — lectura cruda de un mes
- `PUT  /api/v1/sub_accounts/reports/monthly` — edición de un mes

**Estructura que devuelve el reporte hoy:**
```jsonc
{
  "currency": "CLP",
  "origin_currency": ["usd"],
  "summary_years": { "last_year": 2024, "current_year": 2025 },
  "summary": { "last_year": {...}, "current_year": {...} },
  "monthly": [ { "month": 1, "initial_capital": ..., "profit_relative": ... }, ... ],
  "last_year": {...},
  "current_year": {...}
}
```

### 2.2 Frontend (`valuelist-ng`)

Ruta `portal/views/profitability/` con componentes:
- `profitability-monthly-table-v2` — tabla mensual editable (la principal, **sí** usa el contrato nuevo)
- `profitability-resume-table` — resumen año pasado (usa `last_year`)
- `profitability-accrued-table` — devengado año actual
- `profitability-subaccounts-table`, `profitability-accounts-table`, `profitability-movements-table`, `porfitability-monthly-table` (v1, legacy)
- Página: `pages/profitability-page/`
- Servicio: `shared/services/profitability/profitability.service.ts`

---

## 3. Hallazgos detallados (qué falta / qué está mal)

### 🔴 Bloqueantes (impiden operar)

1. **No hay carga de datos por UI.** No existe importador masivo ni formulario de alta de
   `ProfitabilityAccount`. Sólo se puede crear por consola Rails o SQL. → *Es el foco de
   la Fase 1 y Fase 2.*

2. **Contrato backend/frontend inconsistente (migración incompleta).**
   - `report_for_sub_account_spec.rb` prueba una API vieja: recibe `sub_account`, usa
     `sub_account.balance`/`wallet` y espera `accumulated: { current, last }`. **El código
     actual ya no hace eso** → el spec está roto/obsoleto.
   - `profitability-page.component.ts` (`emitSingleReport`/`emitMultipleReport`) espera
     `report.accumulated` y `report.summary.accumulated`, que **el backend nunca devuelve**.
     Es código muerto: las tablas resumen/devengado en realidad piden sus propios datos.
   - Hay que **decidir el enfoque definitivo** (snapshots manuales vs. cálculo desde
     wallet) y dejar UN solo contrato.

### 🟠 Correctitud del cálculo (revisar con negocio)

3. **`current_year = Time.current.year - 1`** (en `report_for_sub_account.rb`) y
   `new Date().getFullYear() - 1` en varios componentes. Hoy (2026) el "año actual" del
   reporte es **2025**. Hay que validar si es intencional (mostrar último año cerrado) o
   un bug. Si es intencional, debe documentarse y centralizarse, no repetirse hardcodeado.

4. **Retorno relativo logarítmico**: `r>0 ? ln(1+r) : -ln(1+|r|)` y luego se **suma** el
   `profit_relative` entre meses. La suma de log-returns es válida para encadenar
   rentabilidades, pero mezclarla con la suma de `profit_absolute` (que no compone capital)
   puede dar números inconsistentes. Requiere validación con un caso real conocido.

5. **Conversión de moneda por fecha**: usa el primer precio `>= fecha`, o el último `< fecha`,
   o `1.0` por defecto. El fallback a `1.0` puede producir conversiones erróneas silenciosas
   si falta el tipo de cambio de un día. Conviene loguear/alertar en vez de asumir 1.0.

### 🟡 Edición y UX

6. **`saveEdits` usa `parseInt`** → trunca decimales (pierde centavos). Datos financieros
   deberían usar `parseFloat`/decimal.

7. **Tras editar, no se recalcula la rentabilidad**: el frontend conserva el
   `profitabilityPercent`/`profitability` anterior. El usuario edita capital/depósitos pero
   el % no cambia hasta recargar.

8. **`update_monthly_data` sólo actualiza 4 campos** (initial, deposits, withdrawals, final)
   y **no toca** `other_transactions`, `dividends_interest_and_other_income`,
   `net_portfolio_change`, `updated_balance`. Si esos campos alimentan algún cálculo, quedan
   desactualizados.

9. **Búsqueda por `period` frágil**: `raw_monthly` y `update_monthly_data` buscan por
   `period: <nombre del mes>`, mientras el reporte agrupa por `start_date.month`. Si `period`
   no contiene exactamente el mismo string que envía el frontend ("Enero", etc.), la edición
   falla silenciosamente. (La factory tiene `period { "MyString" }`, señal de que el campo
   no está estandarizado.)

10. **`alert()` nativo** para feedback de guardado/error — debería usar el sistema de
    notificaciones de la app.

### 🟢 Seguridad y calidad

11. **Auth desactivada** en `ReportsController` (`skip_before_action :authenticate_user!` y
    `verify_authenticity_token`). Cualquiera con la URL puede leer/editar rentabilidad.

12. **Sin control de acceso por rol en el backend**: el permiso de edición se decide en el
    frontend (`isAdviser || isSupervisor`), pero el endpoint `PUT` no valida rol.

13. **Specs desactualizados**: `report_for_sub_account_spec.rb` no refleja el código actual;
    `profitability_account_spec.rb` por revisar. Falta cobertura de los endpoints.

14. **Validaciones `presence: true`** en `other_transactions`, `net_portfolio_change`, etc.:
    cualquier carga masiva debe traer TODOS esos campos o fallará. Hay que definir cuáles son
    realmente obligatorios.

---

## 4. Qué significa "terminado, listo y funcional"

Definición de **Hecho (DoD)** propuesta para el módulo:

- [ ] Cargar una cuenta/subcuenta nueva con sus snapshots mensuales **desde la UI**, sin tocar la consola.
- [ ] Carga **masiva** vía plantilla (CSV/Excel) con validación, previsualización y reporte de errores.
- [ ] Editar y ver cualquier mes con **precisión decimal** y **recálculo inmediato** de la rentabilidad.
- [ ] Un **único contrato** backend↔frontend, sin código muerto ni specs obsoletos.
- [ ] Cálculo **validado contra al menos 2 cuentas reales** con resultados firmados por negocio.
- [ ] Endpoints **autenticados y autorizados por rol**.
- [ ] Conversión de moneda **sin fallbacks silenciosos**.
- [ ] Suite de **tests verde** (modelo, command de reporte, endpoints, importador).
- [ ] **Documentación** de uso (cómo cargar) y de la fórmula de cálculo.

---

## 5. Mapa de hallazgos → fases

| # | Hallazgo | Fase |
|---|---|---|
| 1 | No hay carga por UI (alta individual) | **Fase 1** |
| 1 | Carga masiva | **Fase 2** |
| 2 | Contrato inconsistente / código muerto / decidir enfoque | **Fase 1** |
| 3 | Lógica año-1 hardcodeada | **Fase 1** |
| 4 | Validar fórmula de rentabilidad | **Fase 1 / 3** |
| 5 | Conversión moneda sin fallback silencioso | **Fase 1** |
| 6 | parseInt → decimales | **Fase 1** |
| 7 | Recalcular tras editar | **Fase 1** |
| 8 | Editar todos los campos relevantes | **Fase 1** |
| 9 | Búsqueda por period frágil → key estable | **Fase 1** |
| 10 | Notificaciones en vez de alert() | **Fase 1** |
| 11-12 | Auth + autorización por rol | **Fase 1** |
| 13 | Reparar y ampliar specs | **Fase 1 / 3** |
| 14 | Definir campos obligatorios | **Fase 2** |
| — | QA, reconciliación, UAT, performance, rollout | **Fase 3** |
