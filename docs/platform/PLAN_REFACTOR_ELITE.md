# PLAN REFACTOR V2 - PLATAFORMA DE AUTOMATIZACIONES MULTICLIENTE

## 1) Objetivo de negocio

Construir una plataforma interna de automatizaciones para vender servicio gestionado (no vender software), con:

- Core reutilizable por industria.
- Aislamiento fuerte por cliente (datos, secretos, dashboards, billing).
- Deploy estable en VPS primero, y opcion Kubernetes despues.
- Estandar de seguridad y operacion para subir a Git sin fugas.

---

## 2) Hallazgos criticos de la revision final (17-feb-2026)

Estos puntos bloquean produccion y publicacion segura:

1. Secretos y credenciales hardcodeadas en codigo y docs.
2. Scripts de negocio con TODO/stub en rutas criticas de cobro y mensajeria.
3. Pipeline CI/CD de raiz apunta a archivos inexistentes (docker/, helm/, scripts/).
4. `scripts/deploy.sh` en raiz no es script ejecutable, es un documento markdown con bloques.
5. No hay `.gitignore` (riesgo de subir `node_modules`, caches, env, credenciales).
6. Error funcional en reintentos del runner de jobs (`attempts` no se selecciona en query).
7. Webhook inbound permite flujo sin verificacion fuerte de firma (modo "trust source").
8. `compute_attendance.py` esta incompleto y retorna exito aunque no procesa nada.

---

## 3) Principios de arquitectura objetivo

1. Separar plataforma (core) de implementacion por cliente.
2. Todo secreto fuera de repo (Vault/ENV/secret manager).
3. Un contrato unico de integraciones por plugin/adapter.
4. Observabilidad por tenant (`tenant_id`, `request_id`) en logs/metricas.
5. Entrega incremental: primero VPS estable, luego hardening enterprise.

---

## 4) Estructura de repositorio objetivo

```text
/
|-- platform-core/                 # dominio comun, validadores, adapters base
|-- platform-cli/                  # wmctl y utilidades operativas
|-- platform-api/                  # control plane (auth, tenants, billing, metrics)
|-- connectors/                    # plugins de integracion (ycloud, calendly, etc)
|-- customers/
|   |-- einstein_kids/
|   |   |-- flows/
|   |   |-- scripts/
|   |   |-- dashboard/
|   |   `-- config/
|   `-- _template/
|-- infra/
|   |-- docker/
|   |-- compose/
|   `-- k8s/                       # opcional fase posterior
|-- ops/
|-- docs/
|-- tests/
`-- .github/workflows/
```

---

## 5) Roadmap de ejecucion (realista y bloqueado por riesgo)

## Fase P0 - Contencion de riesgo (24-48h)

Objetivo: poder subir a Git sin exponer credenciales ni basura.

Tareas:

1. Crear `.gitignore` en raiz y en submodulos necesarios.
2. Mover/renombrar archivos sensibles:
   - `CREDENCIALES-SISTEMA.txt` -> `CREDENCIALES-SISTEMA.example.txt`
   - reemplazar passwords reales por placeholders.
3. Eliminar defaults inseguros en scripts (`admin123`, `CynAdmin2024!`, `windmillpass`).
4. Cambiar `gitleaks` a modo bloqueante (sin `continue-on-error`).
5. Rotar inmediatamente todas las credenciales ya expuestas.

Criterio de salida:

- Secret scan limpio.
- Ningun password real en repo.
- Repo listo para `git init` y primer commit seguro.

---

## Fase P1 - Correcciones funcionales criticas (2-4 dias)

Objetivo: que la automatizacion principal no "simule" exito.

Tareas:

1. Implementar de verdad:
   - `payment_claim_create.py`
   - `payment_claim_decide.py`
   - `cancel_jobs.py`
   - `ycloud_webhook_status.py`
2. Corregir `job_runner_cron.py`:
   - incluir `attempts` en el SELECT.
   - actualizar estado final despues de max retries.
3. Endurecer `ycloud_webhook_inbound.py`:
   - parseo real de firma.
   - rechazo explicito si no valida en prod.
4. Reescribir `compute_attendance.py` para que procese y falle cuando corresponda.

Criterio de salida:

- Flujos de cobro/seguimiento actualizan BD real.
- No hay stubs en rutas de negocio criticas.

---

## Fase P2 - Separacion core vs cliente (4-6 dias)

Objetivo: producto interno reutilizable para cualquier industria.

Tareas:

1. Extraer codigo comun a `platform-core/`.
2. Mover Einstein Kids a `customers/einstein_kids/`.
3. Definir interfaces de connector (`ConnectorBase`) y adaptar integraciones.
4. Estandarizar contratos:
   - core: contratos genericos.
   - customer: contratos especificos por vertical.

Criterio de salida:

- Onboarding de nuevo cliente sin copiar/pegar caotico.
- Cliente nuevo nace desde template.

---

## Fase P3 - Deploy VPS productivo (3-5 dias)

Objetivo: deployment confiable para vender servicio desde ya.

Tareas:

1. Crear `infra/compose/compose.prod.yml` real y probado.
2. Corregir healthchecks, dependencia de servicios y persistencia.
3. Generar script de deploy ejecutable real (no markdown disfrazado):
   - `infra/scripts/deploy_vps.sh`
4. Definir backup y restore (Postgres + configuraciones).

Criterio de salida:

- Deploy en VPS reproducible en < 15 min.
- Runbook de rollback validado.

---

## Fase P4 - CI/CD minimo viable y verdadero (2-3 dias)

Objetivo: pipeline que refleje el repo real, no uno hipotetico.

Tareas:

1. Depurar `.github/workflows/cd-pipeline.yml` de referencias inexistentes.
2. Agregar jobs minimos:
   - lint
   - tests unitarios
   - secret scan bloqueante
   - build de imagen
3. Deploy manual por tag a VPS (primera etapa).
4. Artefactos de release y versionado semantico.

Criterio de salida:

- Un push/tag ejecuta pipeline util de punta a punta.

---

## Fase P5 - Multi-tenant y dashboards elite (5-8 dias)

Objetivo: cada cliente con su app/panel propio sobre la misma plataforma.

Tareas:

1. Tenant model en control plane:
   - `tenant_id`, `plan`, `estado`, `limites`.
2. Aislamiento de datos:
   - esquema por tenant o RLS por `tenant_id`.
3. RBAC por tenant (`owner`, `ops`, `viewer`).
4. Dashboard por tenant con metricas:
   - ejecuciones, conversion, latencia, errores, consumo plan.

Criterio de salida:

- Cliente A no puede ver ni inferir nada de cliente B.

---

## Fase P6 - Billing, observabilidad y hardening (5-7 dias)

Objetivo: operar como servicio premium con control total.

Tareas:

1. Billing por uso y limites por plan.
2. Alertas operativas (error rate, DLQ, latencia p95, cuota).
3. Auditoria de acciones administrativas.
4. Hardening:
   - TLS extremo a extremo.
   - politicas de secretos y rotacion.
   - pruebas de recuperacion.

Criterio de salida:

- Operacion con SLO definidos y alertas accionables.

---

## 6) Checklist para subir a Git hoy (obligatorio)

1. Inicializar repo en raiz correcta (`git init`).
2. Crear `.gitignore` fuerte:
   - `.env*`, `credentials*`, `node_modules/`, `__pycache__/`, `.pytest_cache/`, `.coverage`, `htmlcov/`.
3. Sanitizar archivos de credenciales/documentacion.
4. Ejecutar secret scan local.
5. Commit inicial con estructura limpia.

---

## 7) KPIs de exito (version realista)

- Tiempo alta nuevo cliente: < 2 horas.
- Tiempo deploy VPS: < 15 minutos.
- Error rate ejecucion automatizaciones: < 1%.
- MTTR incidentes P1: < 30 minutos.
- Cero credenciales expuestas en repositorio.

---

## 8) Orden recomendado de trabajo inmediato

1. P0 seguridad.
2. P1 correcciones funcionales.
3. P3 deploy VPS real.
4. P4 CI/CD real.
5. P2 separacion core/cliente.
6. P5 + P6 para escalar servicio.

---

## 9) Nota operativa

No avanzar a Kubernetes/Helm hasta que VPS + CI/CD + seguridad basica esten estables.
Primero negocio funcionando y seguro; luego escala enterprise.

