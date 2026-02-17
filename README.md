# AutWinmill

Plataforma interna de automatizaciones multi-cliente para vender servicio gestionado.

## Estructura

- `src/`: codigo Python principal (arquitectura base).
- `flows/`: flujos de orquestacion de automatizaciones.
- `f/`: implementaciones por cliente y scripts de negocio.
- `contracts/`: contratos JSON Schema y ejemplos.
- `ops/`: infraestructura, compose, migraciones, runbooks operativos.
- `resources/`: configuraciones de ejemplo.
- `scripts/`: utilidades tecnicas de plataforma.
- `scripts_yaml/`: versiones YAML de scripts para Windmill.
- `tests/`: pruebas automatizadas y utilidades manuales.
- `docs/`: documentacion funcional, tecnica y plan de refactor.
- `tools/`: CLI y herramientas de soporte local.

## Inicio rapido

1. Configura variables de entorno basadas en `resources/env.example`.
2. Levanta infraestructura local con los compose de `ops/`.
3. Ejecuta pruebas y validaciones desde `tests/`.

## CI

El workflow de CI esta en `.github/workflows/ci.yml` y valida:

- lint y typing
- pruebas unitarias/e2e
- smoke de migraciones SQL
- escaneo de secretos

## Seguridad

- No guardar credenciales reales en el repo.
- Usar archivos `.example` y variables de entorno.
- Rotar cualquier secreto historico expuesto previamente.
