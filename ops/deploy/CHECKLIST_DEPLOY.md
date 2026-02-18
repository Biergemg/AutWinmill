# 🚀 Checklist de Despliegue a Producción (Oracle Cloud VPS)

Este documento certifica que el código ha pasado la auditoría de seguridad pre-deployment y está listo para producción, sujeto a la ejecución de los siguientes pasos manuales.

## ✅ Estado del Código: GO
- **Docker Security:** Aprobado (Usuario `appuser` configurado).
- **Secret Management:** Aprobado (Fail-fast implementado en `auth.py`).
- **Network Security:** Aprobado (Headers HSTS/X-Frame-Options inyectados en Caddy).

## 📋 Pasos Finales para el Operador

### 1. Configuración en Oracle Cloud (OCI)
Antes de desplegar, configura el Firewall (Security Lists) en la consola de Oracle:

*   **Ingress Rules (Entrada):**
    *   TCP 22 (SSH): Restringir a tu IP (`TU_IP/32`) o usar VPN.
    *   TCP 80 (HTTP): Abierto (`0.0.0.0/0`) - Caddy manejará la redirección.
    *   TCP 443 (HTTPS): Abierto (`0.0.0.0/0`).
    *   **BLOQUEAR:** TCP 8088 (El puerto de la aplicación no debe ser público).

### 2. Preparación del VPS
Sube los archivos necesarios al servidor:

```bash
# Ejemplo usando scp (o usa git pull en el servidor)
scp -r ops/deploy/operator-console.vps.compose.yml usuario@tu-vps:/opt/winmill/
scp -r ops/deploy/.env.operator-console.vps.example usuario@tu-vps:/opt/winmill/.env
```

### 3. Configuración de Variables de Entorno (CRÍTICO)
En el servidor, edita el archivo `.env`:

```bash
nano /opt/winmill/.env
```

Asegúrate de establecer valores reales y seguros para:
- `OPERATOR_JWT_SECRET` (Mínimo 32 caracteres aleatorios)
- `OPERATOR_ADMIN_PASSWORD` (Contraseña fuerte)
- `OPERATOR_PUBLIC_DOMAIN` (Tu dominio, ej: ops.winmill.com)
- `OPERATOR_ENV=production`

### 4. Ejecución
Inicia los servicios:

```bash
cd /opt/winmill
docker compose -f operator-console.vps.compose.yml up -d --build
```

### 5. Verificación Post-Deploy
1.  Visita `https://tu-dominio.com`. Deberías ver el candado verde (SSL).
2.  Intenta acceder por HTTP; debería redirigir a HTTPS.
3.  Verifica los headers de seguridad usando `curl -I https://tu-dominio.com`:
    *   `Strict-Transport-Security` debe estar presente.
    *   `X-Frame-Options: DENY` debe estar presente.

---
**Firmado:** Senior Security & Infrastructure Architect Agent
