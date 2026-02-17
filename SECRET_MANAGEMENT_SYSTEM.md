# 🔐 Sistema de Gestión de Secretos Enterprise

## Arquitectura de Vault

```yaml
# k8s/vault/values.yaml
global:
  enabled: true
  tlsDisable: false

server:
  ha:
    enabled: true
    replicas: 3
    raft:
      enabled: true
      setNodeId: true
      config: |
        ui = true
        listener "tcp" {
          address = "0.0.0.0:8200"
          cluster_address = "0.0.0.0:8201"
          tls_cert_file = "/vault/userconfig/vault-server-tls/vault.crt"
          tls_key_file = "/vault/userconfig/vault-server-tls/vault.key"
        }
        storage "raft" {
          path = "/vault/data"
        }
        seal "awskms" {
          region = "us-east-1"
          key_id = "vault-unseal-key"
        }
```

## Políticas de Seguridad

```hcl
# vault/policies/automation-platform.hcl
# Política para el servicio de automatizaciones
path "secret/data/automation-platform/*" {
  capabilities = ["read", "list"]
}

path "secret/data/integrations/*" {
  capabilities = ["read", "list"]
}

path "secret/data/billing/*" {
  capabilities = ["read", "list"]
}

# Rotación de secretos
path "secret/rotate/*" {
  capabilities = ["update"]
}
```

```hcl
# vault/policies/admin.hcl
# Política para administradores
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
```

## Configuración de Secret Engines

```bash
#!/bin/bash
# scripts/vault-init.sh

# Habilitar KV v2 para secretos
echo "🔐 Configurando Vault..."

vault secrets enable -path=secret kv-v2
vault secrets enable -path=automation-platform kv-v2
vault secrets enable -path=integrations kv-v2
vault secrets enable -path=billing kv-v2

# Habilitar AWS para rotación de credenciales
vault secrets enable aws
vault write aws/config/root \
    access_key=${AWS_ACCESS_KEY_ID} \
    secret_key=${AWS_SECRET_ACCESS_KEY} \
    region=us-east-1

# Habilitar database para rotación de passwords
vault secrets enable database
vault write database/config/postgres \
    plugin_name=postgresql-database-plugin \
    connection_url="postgresql://{{username}}:{{password}}@postgres:5432/windmill" \
    allowed_roles="automation-platform,readonly" \
    username="vault" \
    password="${VAULT_DB_PASSWORD}"

# Configurar roles de base de datos
vault write database/roles/automation-platform \
    db_name=postgres \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
                        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"
```

## Sistema de Gestión de API Keys

```python
# src/windmill_platform/secrets/api_key_manager.py
import hvac
import redis
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Gestión enterprise de API Keys con rotación automática"""
    
    def __init__(self, vault_url: str, vault_token: str, redis_url: str):
        self.vault = hvac.Client(url=vault_url, token=vault_token)
        self.redis = redis.from_url(redis_url)
        self._verify_vault_connection()
    
    def _verify_vault_connection(self):
        """Verificar conexión con Vault"""
        if not self.vault.is_authenticated():
            raise RuntimeError("❌ Vault authentication failed")
        logger.info("✅ Vault connection established")
    
    def create_api_key(
        self, 
        tenant_id: str, 
        service: str, 
        permissions: list,
        expires_in_days: int = 90
    ) -> Dict[str, Any]:
        """Crear nueva API key con permisos específicos"""
        
        key_id = f"{tenant_id}_{service}_{datetime.utcnow().timestamp()}"
        api_key = self._generate_secure_key()
        
        # Calcular fecha de expiración
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Almacenar en Vault
        secret_path = f"automation-platform/api-keys/{key_id}"
        secret_data = {
            "api_key": api_key,
            "tenant_id": tenant_id,
            "service": service,
            "permissions": permissions,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "is_active": True,
            "usage_count": 0,
            "last_used": None
        }
        
        self.vault.secrets.kv.v2.create_or_update_secret(
            path=secret_path,
            secret=secret_data
        )
        
        # Cache en Redis para performance
        cache_key = f"api_key:{api_key}"
        self.redis.setex(
            cache_key, 
            timedelta(hours=1), 
            json.dumps(secret_data)
        )
        
        logger.info(f"✅ API Key created for {tenant_id}/{service}")
        
        return {
            "key_id": key_id,
            "api_key": api_key,
            "expires_at": expires_at.isoformat(),
            "permissions": permissions
        }
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validar API key contra cache o Vault"""
        
        # Check Redis cache primero
        cache_key = f"api_key:{api_key}"
        cached_data = self.redis.get(cache_key)
        
        if cached_data:
            key_data = json.loads(cached_data)
        else:
            # Buscar en Vault (más lento pero completo)
            key_data = self._find_key_in_vault(api_key)
            if key_data:
                # Actualizar cache
                self.redis.setex(cache_key, timedelta(hours=1), json.dumps(key_data))
        
        if not key_data:
            return None
        
        # Verificar expiración
        expires_at = datetime.fromisoformat(key_data["expires_at"])
        if datetime.utcnow() > expires_at:
            logger.warning(f"⚠️ API Key expired: {key_data.get('key_id', 'unknown')}")
            return None
        
        # Verificar si está activa
        if not key_data.get("is_active", False):
            logger.warning(f"⚠️ API Key inactive: {key_data.get('key_id', 'unknown')}")
            return None
        
        # Actualizar último uso
        self._update_last_used(key_data["key_id"])
        
        return key_data
    
    def rotate_api_key(self, key_id: str) -> Dict[str, Any]:
        """Rotar API key manteniendo el ID"""
        
        # Obtener configuración actual
        secret_path = f"automation-platform/api-keys/{key_id}"
        response = self.vault.secrets.kv.v2.read_secret_version(path=secret_path)
        
        if not response or not response["data"]["data"]:
            raise ValueError(f"API Key not found: {key_id}")
        
        current_data = response["data"][data"]
        
        # Generar nuevo API key
        new_api_key = self._generate_secure_key()
        current_data["api_key"] = new_api_key
        current_data["rotated_at"] = datetime.utcnow().isoformat()
        current_data["previous_key"] = response["data"]["data"].get("api_key")
        
        # Actualizar en Vault
        self.vault.secrets.kv.v2.create_or_update_secret(
            path=secret_path,
            secret=current_data
        )
        
        # Invalidar cache
        if "previous_key" in current_data:
            self.redis.delete(f"api_key:{current_data['previous_key']}")
        
        logger.info(f"🔄 API Key rotated: {key_id}")
        
        return {
            "key_id": key_id,
            "new_api_key": new_api_key,
            "permissions": current_data["permissions"]
        }
    
    def revoke_api_key(self, key_id: str) -> bool:
        """Revocar API key"""
        
        secret_path = f"automation-platform/api-keys/{key_id}"
        
        # Marcar como inactiva
        response = self.vault.secrets.kv.v2.read_secret_version(path=secret_path)
        if response and response["data"]["data"]:
            data = response["data"]["data"]
            data["is_active"] = False
            data["revoked_at"] = datetime.utcnow().isoformat()
            
            self.vault.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret=data
            )
            
            # Limpiar cache
            self.redis.delete(f"api_key:{data['api_key']}")
            
            logger.info(f"🚫 API Key revoked: {key_id}")
            return True
        
        return False
    
    def _generate_secure_key(self) -> str:
        """Generar API key segura"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        key_part = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        return f"wm_{key_part}"
    
    def _find_key_in_vault(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Buscar API key en Vault (operación costosa)"""
        # Listar todas las keys (esto debería ser optimizado en producción)
        try:
            response = self.vault.secrets.kv.v2.list_secrets(
                path="automation-platform/api-keys"
            )
            
            if response and response["data"]["keys"]:
                for key_id in response["data"]["keys"]:
                    secret_path = f"automation-platform/api-keys/{key_id}"
                    secret_response = self.vault.secrets.kv.v2.read_secret_version(
                        path=secret_path
                    )
                    
                    if (secret_response and 
                        secret_response["data"]["data"]["api_key"] == api_key):
                        return secret_response["data"]["data"]
        
        except Exception as e:
            logger.error(f"Error searching in Vault: {e}")
        
        return None
    
    def _update_last_used(self, key_id: str):
        """Actualizar timestamp de último uso"""
        try:
            secret_path = f"automation-platform/api-keys/{key_id}"
            response = self.vault.secrets.kv.v2.read_secret_version(path=secret_path)
            
            if response and response["data"]["data"]:
                data = response["data"]["data"]
                data["last_used"] = datetime.utcnow().isoformat()
                data["usage_count"] = data.get("usage_count", 0) + 1
                
                self.vault.secrets.kv.v2.create_or_update_secret(
                    path=secret_path,
                    secret=data
                )
        except Exception as e:
            logger.error(f"Error updating last used: {e}")

# src/windmill_platform/secrets/__init__.py
from .api_key_manager import APIKeyManager
from .service_manager import ServiceSecretsManager
from .rotation_scheduler import RotationScheduler

__all__ = ["APIKeyManager", "ServiceSecretsManager", "RotationScheduler"]
```

## Sistema de Rotación Automática

```python
# src/windmill_platform/secrets/rotation_scheduler.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class RotationScheduler:
    """Programador de rotación de secretos"""
    
    def __init__(self, api_key_manager: APIKeyManager):
        self.api_key_manager = api_key_manager
        self.rotation_schedule = {
            "api_keys": timedelta(days=90),          # Cada 90 días
            "database_passwords": timedelta(days=30), # Cada 30 días
            "oauth_tokens": timedelta(days=60),      # Cada 60 días
            "webhook_secrets": timedelta(days=45),   # Cada 45 días
        }
    
    async def start_rotation_scheduler(self):
        """Iniciar scheduler de rotación"""
        logger.info("🔄 Starting rotation scheduler")
        
        while True:
            try:
                await self._check_and_rotate_secrets()
                await asyncio.sleep(3600)  # Revisar cada hora
            except Exception as e:
                logger.error(f"Error in rotation scheduler: {e}")
                await asyncio.sleep(300)   # Esperar 5 minutos en caso de error
    
    async def _check_and_rotate_secrets(self):
        """Verificar y rotar secretos que necesiten rotación"""
        
        for secret_type, rotation_interval in self.rotation_schedule.items():
            try:
                await self._rotate_secrets_by_type(secret_type, rotation_interval)
            except Exception as e:
                logger.error(f"Error rotating {secret_type}: {e}")
    
    async def _rotate_secrets_by_type(self, secret_type: str, interval: timedelta):
        """Rotar secretos por tipo"""
        
        if secret_type == "api_keys":
            await self._rotate_api_keys(interval)
        elif secret_type == "database_passwords":
            await self._rotate_database_passwords(interval)
        elif secret_type == "oauth_tokens":
            await self._rotate_oauth_tokens(interval)
        elif secret_type == "webhook_secrets":
            await self._rotate_webhook_secrets(interval)
    
    async def _rotate_api_keys(self, interval: timedelta):
        """Rotar API keys vencidas"""
        
        # Listar todas las API keys
        response = self.api_key_manager.vault.secrets.kv.v2.list_secrets(
            path="automation-platform/api-keys"
        )
        
        if response and response["data"]["keys"]:
            for key_id in response["data"]["keys"]:
                secret_path = f"automation-platform/api-keys/{key_id}"
                secret_response = self.api_key_manager.vault.secrets.kv.v2.read_secret_version(
                    path=secret_path
                )
                
                if secret_response and secret_response["data"]["data"]:
                    data = secret_response["data"]["data"]
                    
                    # Verificar si necesita rotación
                    created_at = datetime.fromisoformat(data["created_at"])
                    if datetime.utcnow() - created_at > interval:
                        
                        # Verificar si ya fue rotada recientemente
                        if "rotated_at" in data:
                            rotated_at = datetime.fromisoformat(data["rotated_at"])
                            if datetime.utcnow() - rotated_at < timedelta(days=1):
                                continue  # Ya fue rotada hace menos de 1 día
                        
                        logger.info(f"🔄 Rotating API key: {key_id}")
                        
                        # Rotar la key
                        result = self.api_key_manager.rotate_api_key(key_id)
                        
                        # Notificar al tenant
                        await self._notify_rotation(
                            tenant_id=data["tenant_id"],
                            service=data["service"],
                            key_id=key_id,
                            new_key=result["new_api_key"]
                        )
    
    async def _notify_rotation(self, tenant_id: str, service: str, key_id: str, new_key: str):
        """Notificar rotación de API key"""
        
        # Aquí implementarías la lógica de notificación
        # Email, Slack, webhook, etc.
        logger.info(f"📧 Notifying tenant {tenant_id} about key rotation for {service}")
    
    async def _rotate_database_passwords(self, interval: timedelta):
        """Rotar passwords de base de datos"""
        # Implementar rotación de passwords DB
        pass
    
    async def _rotate_oauth_tokens(self, interval: timedelta):
        """Rotar tokens OAuth"""
        # Implementar rotación de tokens OAuth
        pass
    
    async def _rotate_webhook_secrets(self, interval: timedelta):
        """Rotar secrets de webhooks"""
        # Implementar rotación de webhook secrets
        pass
```

## Configuración de Seguridad

```yaml
# k8s/security/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vault-network-policy
  namespace: vault
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: vault
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: windmill-platform
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: windmill-platform
    ports:
    - protocol: TCP
      port: 8200
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to:
    - namespaceSelector:
        matchLabels:
          name: postgres
    ports:
    - protocol: TCP
      port: 5432
```

```yaml
# k8s/security/rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: vault-secrets-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["serviceaccounts"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: vault-secrets-reader-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: vault-secrets-reader
subjects:
- kind: ServiceAccount
  name: windmill-platform
  namespace: windmill-platform
```

## Comandos de Inicialización

```bash
#!/bin/bash
# scripts/init-vault.sh

set -euo pipefail

echo "🚀 Inicializando Vault..."

# Verificar si Vault ya está inicializado
if kubectl exec -n vault vault-0 -- vault status 2>/dev/null; then
    echo "✅ Vault ya está inicializado"
    exit 0
fi

# Inicializar Vault
kubectl exec -n vault vault-0 -- vault operator init \
    -key-shares=5 \
    -key-threshold=3 \
    -format=json > vault-init.json

# Guardar keys de forma segura
export VAULT_UNSEAL_KEY_1=$(jq -r '.unseal_keys_b64[0]' vault-init.json)
export VAULT_UNSEAL_KEY_2=$(jq -r '.unseal_keys_b64[1]' vault-init.json)
export VAULT_UNSEAL_KEY_3=$(jq -r '.unseal_keys_b64[2]' vault-init.json)
export VAULT_ROOT_TOKEN=$(jq -r '.root_token' vault-init.json)

# Desbloquear Vault
kubectl exec -n vault vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY_1
kubectl exec -n vault vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY_2
kubectl exec -n vault vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY_3

# Configurar autenticación con Kubernetes
kubectl exec -n vault vault-0 -- vault login $VAULT_ROOT_TOKEN
kubectl exec -n vault vault-0 -- vault auth enable kubernetes

# Configurar Kubernetes auth
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/config \
    token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
    kubernetes_host="https://${KUBERNETES_PORT_443_TCP_ADDR}:443" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Crear políticas
kubectl cp vault/policies/automation-platform.hcl vault/vault-0:/tmp/automation-platform.hcl
kubectl cp vault/policies/admin.hcl vault/vault-0:/tmp/admin.hcl

kubectl exec -n vault vault-0 -- vault policy write automation-platform /tmp/automation-platform.hcl
kubectl exec -n vault vault-0 -- vault policy write admin /tmp/admin.hcl

# Crear roles de auth
kubectl exec -n vault vault-0 -- vault write auth/kubernetes/role/windmill-platform \
    bound_service_account_names=windmill-platform \
    bound_service_account_namespaces=windmill-platform \
    policies=automation-platform \
    ttl=24h

echo "✅ Vault inicializado y configurado"
echo "⚠️  Guarda el root token de forma segura: $VAULT_ROOT_TOKEN"
```