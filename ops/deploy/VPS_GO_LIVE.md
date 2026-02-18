# VPS Go-Live Checklist (GO/NO-GO)

## 1) Server hardening (mandatory)

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose-plugin ufw fail2ban
sudo systemctl enable --now docker
```

Firewall baseline:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

## 2) Deploy Cyn stack with TLS edge

1. Copy and edit env:

```bash
cp ops/deploy/.env.cyn.vps.example ops/deploy/.env.cyn.vps
```

2. Start stack:

```bash
chmod +x ops/deploy/preflight_vps.sh
/bin/bash ops/deploy/preflight_vps.sh ops/deploy/.env.cyn.vps ops/deploy/.env.operator-console.vps
docker compose --env-file ops/deploy/.env.cyn.vps -f ops/docker-compose-cyn.yml --profile vps up -d --remove-orphans
```

3. Validate:

```bash
docker compose -f ops/docker-compose-cyn.yml ps
curl -I https://<CYN_PUBLIC_DOMAIN>
```

## 3) Deploy Operator Console with TLS edge

Opcion recomendada en servidor compartido: levantar solo `operator-console.compose.yml`
en localhost (`127.0.0.1:8088`) y enrutar desde un proxy central.

1. Copy and edit env:

```bash
cp ops/deploy/.env.operator-console.vps.example ops/deploy/.env.operator-console.vps
```

2. Start stack (localhost only):

```bash
docker compose --env-file ops/deploy/.env.operator-console.vps -f ops/deploy/operator-console.compose.yml up -d --build --remove-orphans
```

3. Validate:

```bash
docker compose -f ops/deploy/operator-console.compose.yml ps
curl -I http://127.0.0.1:8088
```

Si lo vas a publicar con edge dedicado, usa:

```bash
docker compose --env-file ops/deploy/.env.operator-console.vps -f ops/deploy/operator-console.vps.compose.yml up -d --build --remove-orphans
```

## 4) Security checks before GO

- No hardcoded secrets in repo.
- `OPERATOR_ENV=production` and strong values in `OPERATOR_ADMIN_PASSWORD` and `OPERATOR_JWT_SECRET`.
- `OPERATOR_ALLOWED_ENDPOINT_HOSTS` configured.
- `OPERATOR_TOKEN_TARGET_HOSTS` configured (token is sent only to these hosts).
- Public ingress only on 80/443.

## 5) Backups and restore test (mandatory)

Daily backup via cron:

```bash
chmod +x ops/deploy/backup_pg.sh ops/deploy/restore_pg.sh
(crontab -l 2>/dev/null; echo "0 3 * * * /bin/bash /opt/autwinmill/ops/deploy/backup_pg.sh >> /var/log/autwinmill-backup.log 2>&1") | crontab -
```

Restore drill (at least once):

```bash
/bin/bash ops/deploy/restore_pg.sh /path/to/cyn_postgres_YYYYMMDDTHHMMSSZ.sql.gz
```

## 6) GO criteria

- HTTPS reachable for public domains.
- Internal ports not exposed externally.
- Backup created and restore drill passed.
- Operator smoke tests passed.
- Cyn services healthy in `docker compose ps`.
