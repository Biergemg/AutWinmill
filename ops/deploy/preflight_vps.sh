#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CYN_ENV="${1:-${ROOT_DIR}/ops/deploy/.env.cyn.vps}"
OP_ENV="${2:-${ROOT_DIR}/ops/deploy/.env.operator-console.vps}"

placeholder_regex='(change_me|replace|CLIENT_.*_HERE|your_.*_here)'

read_var() {
  local file="$1"
  local key="$2"
  local line
  line="$(grep -E "^${key}=" "$file" | tail -n 1 || true)"
  echo "${line#*=}"
}

assert_var_safe() {
  local file="$1"
  local key="$2"
  local value
  value="$(read_var "$file" "$key")"
  if [ -z "$value" ]; then
    echo "Missing ${key} in ${file}"
    exit 1
  fi
  if echo "$value" | grep -Eq "$placeholder_regex"; then
    echo "Unsafe value for ${key} in ${file}"
    exit 1
  fi
}

if [ -f "$CYN_ENV" ]; then
  assert_var_safe "$CYN_ENV" "CYN_PUBLIC_DOMAIN"
  assert_var_safe "$CYN_ENV" "POSTGRES_PASSWORD"
  assert_var_safe "$CYN_ENV" "WM_ADMIN_PASSWORD"
  assert_var_safe "$CYN_ENV" "CLIENT_JWT_SECRET"
  assert_var_safe "$CYN_ENV" "CLIENT_ENCRYPTION_KEY"
fi

if [ -f "$OP_ENV" ]; then
  assert_var_safe "$OP_ENV" "OPERATOR_PUBLIC_DOMAIN"
  assert_var_safe "$OP_ENV" "OPERATOR_ADMIN_PASSWORD"
  assert_var_safe "$OP_ENV" "OPERATOR_JWT_SECRET"
fi

echo "VPS preflight passed"
