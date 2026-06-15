# Planificación y Carta Gantt — Módulo de Rentabilidad

> Horizonte: **3 meses** · Inicio sugerido: **2026-06-01** · Fin: **2026-08-31**
> Una persona dev full-time como supuesto base (ajustar si hay más manos).

---

## 1. Objetivos por fase

| Fase | Mes | Objetivo | Resultado esperado |
|---|---|---|---|
| **Fase 1 — Núcleo funcional** | Junio 2026 | Dejar el funcionamiento de rentabilidad sólido: subir fácil (alta individual), editar fácil, ver fácil y **calcular correctamente** | Módulo usable end-to-end para 1 cuenta, contrato único, cálculo validado, auth |
| **Fase 2 — Carga masiva** | Julio 2026 | Subir las cuentas faltantes de forma masiva y segura | Importador con plantilla, validación, preview, dedup; datos cargados |
| **Fase 3 — Pruebas y ajustes** | Agosto 2026 | QA, reconciliación, UAT y salida a producción | Módulo en producción, validado por negocio, documentado |

---

## 2. Desglose de tareas

### Fase 1 — Núcleo funcional (Mes 1: Junio)

**Semana 1 — Diagnóstico y decisiones (1-7 jun)**
- T1.1 Decidir enfoque definitivo: snapshots manuales vs. cálculo desde wallet. *(decisión de negocio + técnica)*
- T1.2 Validar la regla "año actual = año − 1" con negocio; documentarla.
- T1.3 Definir el contrato único de respuesta del reporte y el modelo de datos definitivo.
- T1.4 Reparar/estabilizar suite de tests existente para tener base verde.

**Semana 2 — Cálculo correcto (8-14 jun)**
- T1.5 Validar fórmula de rentabilidad contra 2 casos reales conocidos (absoluta y relativa).
- T1.6 Centralizar la lógica de año (sin hardcode repetido).
- T1.7 Conversión de moneda: eliminar fallback silencioso a 1.0; loguear/alertar faltantes de FX.
- T1.8 Tests del command de reporte reescritos para el contrato actual.

**Semana 3 — Edición y visualización (15-21 jun)**
- T1.9 Arreglar precisión decimal en edición (parseInt → decimal).
- T1.10 Recalcular rentabilidad inmediatamente tras editar.
- T1.11 Editar todos los campos relevantes (no sólo 4); definir key estable mes↔registro (no `period` string).
- T1.12 Reemplazar `alert()` por notificaciones de la app.

**Semana 4 — Alta individual + seguridad (22-30 jun)**
- T1.13 Formulario UI de alta/edición de una `ProfitabilityAccount` (subir fácil 1 cuenta).
- T1.14 Reactivar autenticación y autorización por rol en `ReportsController`.
- T1.15 Limpiar código muerto (emitters `accumulated`, componentes legacy v1).
- T1.16 QA interno de Fase 1 + demo.

### Fase 2 — Carga masiva (Mes 2: Julio)

**Semana 5 — Diseño del importador (1-7 jul)**
- T2.1 Definir plantilla CSV/Excel (columnas, formatos, moneda, fechas, campos obligatorios).
- T2.2 Definir reglas de validación, dedup e idempotencia (reimportar no duplica).
- T2.3 Mapeo de cuenta/subcuenta/institución/moneda existentes.

**Semana 6 — Backend del importador (8-14 jul)**
- T2.4 Endpoint/servicio de importación con parseo y validación fila a fila.
- T2.5 Reporte de errores por fila (qué falló y por qué) y modo "dry-run"/preview.
- T2.6 Tests del importador (casos válidos, inválidos, duplicados, multimoneda).

**Semana 7 — Frontend de carga (15-21 jul)**
- T2.7 Pantalla de carga: subir archivo, ver previsualización, ver errores, confirmar.
- T2.8 Descarga de plantilla y de reporte de errores.
- T2.9 Permisos de carga (sólo roles autorizados) + rollback/anulación de un lote.

**Semana 8 — Carga real de cuentas faltantes (22-31 jul)**
- T2.10 Preparar y limpiar los datos fuente de las cuentas faltantes.
- T2.11 Cargar por lotes en ambiente de pruebas; corregir; cargar en producción.
- T2.12 Verificación de integridad post-carga.

### Fase 3 — Pruebas y ajustes (Mes 3: Agosto)

**Semana 9 — Reconciliación (1-7 ago)**
- T3.1 Reconciliar reportes contra cartolas/fuentes oficiales de varias cuentas.
- T3.2 Casos borde: multimoneda, meses parciales, FX faltante, saldos cero/negativos.

**Semana 10 — Performance y robustez (8-14 ago)**
- T3.3 Performance del reporte con el dataset completo (muchas subcuentas/meses).
- T3.4 Endurecer manejo de errores y estados vacíos en UI.

**Semana 11 — UAT (15-21 ago)**
- T3.5 Pruebas de usuario con asesores/supervisores; recoger feedback.
- T3.6 Ajustes priorizados del feedback de UAT.

**Semana 12 — Cierre y rollout (22-31 ago)**
- T3.7 Documentación de uso (cómo cargar/editar) y de la fórmula.
- T3.8 Capacitación al equipo.
- T3.9 Despliegue final a producción + checklist DoD.
- T3.10 Retrospectiva y backlog de mejoras futuras.

---

## 3. Carta Gantt (Mermaid)

> Se renderiza en GitHub, GitLab, Notion, VS Code (con extensión Mermaid) y muchos editores Markdown.

```mermaid
gantt
    title Módulo de Rentabilidad — Plan 3 meses
    dateFormat  YYYY-MM-DD
    axisFormat  %d-%b
    excludes    weekends

    section Fase 1: Núcleo funcional
    Diagnóstico y decisiones        :f1a, 2026-06-01, 5d
    Cálculo correcto                :f1b, after f1a, 5d
    Edición y visualización         :f1c, after f1b, 5d
    Alta individual + seguridad     :f1d, after f1c, 6d
    Hito: Núcleo funcional          :milestone, m1, after f1d, 0d

    section Fase 2: Carga masiva
    Diseño del importador           :f2a, 2026-07-01, 5d
    Backend del importador          :f2b, after f2a, 5d
    Frontend de carga               :f2c, after f2b, 5d
    Carga real cuentas faltantes    :f2d, after f2c, 6d
    Hito: Cuentas cargadas          :milestone, m2, after f2d, 0d

    section Fase 3: Pruebas y ajustes
    Reconciliación                  :f3a, 2026-08-03, 5d
    Performance y robustez          :f3b, after f3a, 5d
    UAT                             :f3c, after f3b, 5d
    Cierre y rollout                :f3d, after f3c, 6d
    Hito: En producción             :milestone, m3, after f3d, 0d
```

---

## 4. Carta Gantt (vista ASCII, por si no renderiza Mermaid)

```
                          JUNIO              JULIO              AGOSTO
Tarea / Semana          S1  S2  S3  S4 | S5  S6  S7  S8 | S9 S10 S11 S12
─────────────────────────────────────────────────────────────────────────
FASE 1 Núcleo
  Diagnóstico/decisión  ███             |                |
  Cálculo correcto          ███         |                |
  Edición/visualización         ███     |                |
  Alta individual+seg              ████ |                |
  ◆ Hito núcleo                       ◆ |                |
FASE 2 Carga masiva
  Diseño importador                     |███             |
  Backend importador                    |    ███         |
  Frontend carga                        |        ███     |
  Carga real faltantes                  |           ████ |
  ◆ Hito cuentas cargadas               |              ◆ |
FASE 3 Pruebas/ajustes
  Reconciliación                        |                |███
  Performance/robustez                  |                |    ███
  UAT                                   |                |        ███
  Cierre y rollout                      |                |           ████
  ◆ Hito producción                     |                |              ◆
```

---

## 5. Hitos y entregables

| Hito | Fecha objetivo | Entregable verificable |
|---|---|---|
| **M1 — Núcleo funcional** | ~30-jun-2026 | Alta/edición de 1 cuenta por UI, cálculo validado, contrato único, auth activa, tests verdes |
| **M2 — Cuentas cargadas** | ~31-jul-2026 | Importador masivo operativo + cuentas faltantes cargadas y verificadas |
| **M3 — En producción** | ~31-ago-2026 | Módulo reconciliado, UAT aprobado, documentado y desplegado (DoD completo) |

---

## 6. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Indefinición del enfoque (snapshot vs wallet) | Alto — retrabajo | Cerrar la decisión en Semana 1 con negocio |
| Calidad de los datos fuente de cuentas faltantes | Alto — carga sucia | Limpieza previa + dry-run + reporte de errores |
| Fórmula de rentabilidad no validada | Alto — números erróneos en producción | Validar contra casos reales firmados por negocio (T1.5, T3.1) |
| Tipos de cambio faltantes | Medio | Eliminar fallback 1.0; alertar y completar FX |
| Una sola persona dev | Medio — cuello de botella | Priorizar bloqueantes; mover QA/UAT a apoyo de negocio |
| Alcance creciente | Medio | Congelar alcance por fase; mejoras a backlog (T3.10) |

---

## 7. Supuestos

- 1 desarrollador full-time; apoyo de negocio para validación/UAT.
- Acceso a datos fuente de las cuentas faltantes disponible antes de la Semana 8.
- Las estimaciones son en semanas de trabajo; las fechas se ajustan según feriados y carga real.
- La infraestructura de producción ya existe (ver memoria de infraestructura del proyecto).
