# AutWinmill

Plataforma interna multi-cliente para operar y vender automatizaciones gestionadas.

## Arquitectura

- `src/windmill_automation/domain`: entidades y excepciones de dominio.
- `src/windmill_automation/application`: servicios de caso de uso.
- `src/windmill_automation/ports`: contratos (interfaces) para desacoplar infraestructura.
- `src/windmill_automation/infrastructure`: persistencia y base de datos.
- `src/windmill_automation/adapters`: integraciones externas.
- `apps/operator_console`: API/UI para operación diaria multi-tenant.
- `f/`, `flows/`, `resources/`, `contracts/`: assets operativos por vertical/cliente.

## Inicio rápido local

1. Crea venv e instala dependencias Python:
   `pip install -e .`
2. Instala tooling Node para sync de scripts:
   `npm ci`
3. Levanta servicios locales:
   `docker compose -f ops/docker-compose.yml up -d`
4. Corre validación base:
   `pytest -q tests/unit tests/e2e tests/operator_console`

## Operator Console

- Código: `apps/operator_console/`
- Compose local: `ops/deploy/operator-console.compose.yml`
- Compose VPS + TLS edge: `ops/deploy/operator-console.vps.compose.yml`
- Env ejemplo local: `ops/deploy/.env.operator-console.example`
- Env ejemplo VPS: `ops/deploy/.env.operator-console.vps.example`

### Reglas de runtime (producción)

- `OPERATOR_ENV=production`
- `OPERATOR_DB_URL` obligatorio (no fallback a SQLite)
- `OPERATOR_ALLOWED_ORIGINS` obligatorio y sin `*`
- `OPERATOR_ALLOWED_ENDPOINT_HOSTS` obligatorio
- `OPERATOR_TOKEN_TARGET_HOSTS` debe ser subset de `OPERATOR_ALLOWED_ENDPOINT_HOSTS`

## Deploy VPS

- Workflow: `.github/workflows/deploy_vps.yml`
- Preflight de secretos: `ops/deploy/preflight_vps.sh`
- Runbook operativo: `ops/deploy/VPS_GO_LIVE.md`
- Backup/restore: `ops/deploy/backup_pg.sh` y `ops/deploy/restore_pg.sh`

Nota: el job `deploy-vps` hace skip automático en push si faltan secrets de repositorio (`VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_DEPLOY_PATH`).

## Sync de scripts a Windmill

Script: `tools/deploy_scripts.js`

Variables requeridas:

- `WM_TOKEN`
- `WM_BASE_URL` (ejemplo `https://windmill.tudominio.com/api`)
- `WM_WORKSPACE`
- opcional `WM_SCRIPTS_ROOT`

Ejecución:

- `npm run deploy:scripts`

## Testing

- Suite base CI/local:
  `pytest -q tests/unit tests/e2e tests/operator_console`
- Suite completa (incluye manual/integración/load):
  `pytest -q --run-integration --run-manual --run-load`

## Seguridad

- Nunca subir secretos reales al repo.
- Usar únicamente archivos `.example` para configuración.
- Rotar cualquier secreto histórico y mantener allowlists cerradas en producción.
