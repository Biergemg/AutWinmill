#!/usr/bin/env bash
set -euo pipefail

# Simple deploy helper for VPS using Docker Compose.
# Usage:
#   ./scripts/deploy.sh base
#   ./scripts/deploy.sh cyn
#   ./scripts/deploy.sh saas

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPS_DIR="${ROOT_DIR}/ops"
if [ ! -d "${OPS_DIR}" ] && [ -d "${ROOT_DIR}/aut_windmill/ops" ]; then
  OPS_DIR="${ROOT_DIR}/aut_windmill/ops"
fi
TARGET="${1:-base}"

case "${TARGET}" in
  base)
    COMPOSE_FILE="${OPS_DIR}/docker-compose-infraestructure.yml"
    ;;
  cyn)
    COMPOSE_FILE="${OPS_DIR}/docker-compose-cyn.yml"
    ;;
  saas)
    COMPOSE_FILE="${OPS_DIR}/docker-compose-saas-control.yml"
    ;;
  *)
    echo "Unknown target: ${TARGET}"
    echo "Valid targets: base | cyn | saas"
    exit 1
    ;;
esac

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required"
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin is required"
  exit 1
fi

echo "Deploying target '${TARGET}' with ${COMPOSE_FILE}"
docker compose -f "${COMPOSE_FILE}" pull
docker compose -f "${COMPOSE_FILE}" up -d --remove-orphans
docker compose -f "${COMPOSE_FILE}" ps

echo "Deployment finished"
