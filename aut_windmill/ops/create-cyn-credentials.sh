#!/usr/bin/env bash
# Script para crear credenciales de acceso del cliente en Windmill

set -euo pipefail

echo "Creando credenciales de acceso para cliente en Windmill..."

docker exec -it cyn_einstein_kids_windmill windmill user create \
  --email "${WM_ADMIN_EMAIL:-admin@client.local}" \
  --password "${WM_ADMIN_PASSWORD:-change_me}" \
  --superadmin || true

echo "Credenciales creadas (o ya existentes)."
echo "  1. URL: ${WM_URL:-http://localhost:8001}"
echo "  2. Usuario: ${WM_ADMIN_EMAIL:-admin@client.local}"
echo "  3. Password: <definida-en-variables-de-entorno>"
