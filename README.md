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

## Operator Console MVP (deploy hoy)

UI propia para operar clientes y automatizaciones usando Windmill/API como motor.

- Codigo: `apps/operator_console/`
- Compose: `ops/deploy/operator-console.compose.yml`
- Compose VPS TLS (edge dedicado): `ops/deploy/operator-console.vps.compose.yml`
- Env ejemplo: `ops/deploy/.env.operator-console.example`

Despliegue rapido:

1. Copiar variables:
   `cp ops/deploy/.env.operator-console.example ops/deploy/.env`
2. Ajustar credenciales seguras en `ops/deploy/.env`.
3. Levantar:
   `docker compose --env-file ops/deploy/.env -f ops/deploy/operator-console.compose.yml up -d --build`
4. Abrir:
   `http://<tu-servidor>:8088`

Checklist lanzamiento real:

1. Define `OPERATOR_ENV=production`.
2. Cambia `OPERATOR_ADMIN_PASSWORD` y `OPERATOR_JWT_SECRET` por valores fuertes.
3. Usa `OPERATOR_DB_URL` contra PostgreSQL administrado (evita SQLite en VPS).
4. En la UI entra con un tenant (ejemplo `cyn`, `acme`, `clinic_01`).
5. Cada request queda aislado por tenant via header `X-Operator-Tenant`.
6. Configura `OPERATOR_ALLOWED_ENDPOINT_HOSTS` y `OPERATOR_TOKEN_TARGET_HOSTS`.
7. En produccion define `OPERATOR_ALLOWED_ORIGINS` sin wildcard y `OPERATOR_DB_URL` obligatorio.

## VPS production checklist

- Runbook completo: `ops/deploy/VPS_GO_LIVE.md`
- Variables Cyn VPS: `ops/deploy/.env.cyn.vps.example`
- Variables Operator VPS: `ops/deploy/.env.operator-console.vps.example`
- Backup PostgreSQL: `ops/deploy/backup_pg.sh`
- Restore PostgreSQL: `ops/deploy/restore_pg.sh`
- Preflight de secretos VPS: `ops/deploy/preflight_vps.sh`
- CI/CD deploy: `.github/workflows/deploy_vps.yml`

## Script sync to Windmill

El script `tools/deploy_scripts.js` ya no usa tokens hardcodeados.
Dependencias Node reproducibles en `package.json` + `package-lock.json`.

Variables requeridas:

- `WM_TOKEN`
- `WM_BASE_URL` (ejemplo: `https://windmill.tudominio.com/api`)
- `WM_WORKSPACE`
- opcional `WM_SCRIPTS_ROOT`

Instalacion y uso:

- `npm ci`
- `npm run deploy:scripts`

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
