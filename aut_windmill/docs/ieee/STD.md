# Software Test Documentation (IEEE 829)

## Plan de Pruebas
- Objetivos: validar contratos, repositorio, funciones SQL y flujo E2E.
- Cobertura: ≥80% en new_code y global (M4+).

## Casos de Prueba
- Unit: validate_payload (válido/ inválido).
- Integration: repository insert/update vía Docker adapter.
- SQL: mask_payload, record_platform_action.
- E2E: validate_event_strategy con ejemplos.

## Ambiente de Prueba
- GitHub Actions con Postgres 15 y runner Python 3.12.
- SonarQube para análisis estático y cobertura.
