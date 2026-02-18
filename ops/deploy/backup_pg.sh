#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-${ROOT_DIR}/ops/docker-compose-cyn.yml}"
PG_SERVICE="${PG_SERVICE:-postgres-cyn}"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/ops/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

mkdir -p "${BACKUP_DIR}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_FILE="${BACKUP_DIR}/cyn_postgres_${TIMESTAMP}.sql.gz"

docker compose -f "${COMPOSE_FILE}" exec -T "${PG_SERVICE}" \
  sh -lc 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' | gzip > "${OUT_FILE}"

find "${BACKUP_DIR}" -type f -name "cyn_postgres_*.sql.gz" -mtime +"${BACKUP_RETENTION_DAYS}" -delete

echo "Backup created: ${OUT_FILE}"
