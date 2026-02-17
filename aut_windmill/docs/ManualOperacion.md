# Manual de Operación

## RBAC
- Grupos: Admins, Developers, Operators, Auditors.
- Auditoría de cambios en `audit_log` y función `record_platform_action`.

## PII Safety
- Uso de `events_masked` y función `mask_payload`.

## Incidencias
- Envío a DLQ y reproceso con scripts/core/requeue_event.py o Repository.

## Health/Readiness
- `python scripts/ops/health_check.py` para verificación rápida de Postgres.

## Observabilidad
- Logs JSON estructurados; OTel opcional si está disponible.
