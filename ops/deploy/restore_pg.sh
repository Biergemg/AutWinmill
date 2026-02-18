#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 /path/to/backup.sql.gz"
  exit 1
fi

BACKUP_FILE="${1}"
if [ ! -f "${BACKUP_FILE}" ]; then
  echo "Backup file not found: ${BACKUP_FILE}"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-${ROOT_DIR}/ops/docker-compose-cyn.yml}"
PG_SERVICE="${PG_SERVICE:-postgres-cyn}"

gunzip -c "${BACKUP_FILE}" | docker compose -f "${COMPOSE_FILE}" exec -T "${PG_SERVICE}" \
  sh -lc 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

echo "Restore completed from: ${BACKUP_FILE}"
