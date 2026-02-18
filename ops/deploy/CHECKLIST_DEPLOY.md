# Production Deploy Checklist (Oracle Cloud VPS)

This checklist is the final operator guide before enabling production traffic.

## 1) Oracle Cloud firewall

Allow only:
- TCP `22` (restricted to your admin IP)
- TCP `80`
- TCP `443`

Do not expose:
- `8088`, `8001`, `5433`, `6380`, `9091`

## 2) Required env values (operator console)

Edit your VPS env file and set strong values:
- `OPERATOR_ADMIN_PASSWORD`
- `OPERATOR_JWT_SECRET`
- `OPERATOR_ENV=production`
- `OPERATOR_PUBLIC_DOMAIN`
- `OPERATOR_ALLOWED_ENDPOINT_HOSTS`
- `OPERATOR_TOKEN_TARGET_HOSTS`

Rule:
- `OPERATOR_TOKEN_TARGET_HOSTS` must be a subset of `OPERATOR_ALLOWED_ENDPOINT_HOSTS`.

## 3) Port conflict rule (important)

If `cyn` edge is running on `80/443`, do one of these:
- Use `ops/deploy/operator-console.compose.yml` (localhost only) and route through a shared proxy.
- Or change `EDGE_HTTP_PORT` / `EDGE_HTTPS_PORT` for operator edge.

Do not run two edge stacks on the same `80/443`.

## 4) Preflight gate

Run before deploy:

```bash
chmod +x ops/deploy/preflight_vps.sh
/bin/bash ops/deploy/preflight_vps.sh ops/deploy/.env.cyn.vps ops/deploy/.env.operator-console.vps
```

## 5) Deploy commands

Operator console (localhost mode, recommended when cyn edge already exists):

```bash
docker compose --env-file ops/deploy/.env.operator-console.vps -f ops/deploy/operator-console.compose.yml up -d --build --remove-orphans
```

Operator console (dedicated edge mode):

```bash
docker compose --env-file ops/deploy/.env.operator-console.vps -f ops/deploy/operator-console.vps.compose.yml up -d --build --remove-orphans
```

## 6) Post-deploy checks

- `docker compose ps` is healthy.
- `curl -I https://<domain>` returns security headers.
- login works and tenant isolation works.
- backup script runs and restore drill is tested.
