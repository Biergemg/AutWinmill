# ???? GU??A DE CREDENCIALES - Separaci??n Cliente vs Desarrollador vs Sistema

## ???? OBJETIVO
Esta gu??a explica claramente qu?? credenciales pertenecen a **Cyn (cliente)**, cu??les son tuyas como **desarrollador**, y cu??les son del **sistema**.

---

## ???? **CLIENTE (Cyn - Einstein Kids)**

### ???? **Qu?? debe configurar Cyn:**
**Archivo**: `.env.client` (copiar de `.env.client.example`)

### ???? **Credenciales de APIs (Cyn debe conseguirlas):**
```bash
# WhatsApp Business API
YCLOUD_API_KEY=           # Cyn debe obtener de YCloud

# Zoom (para masterclasses)  
ZOOM_API_KEY=             # Cyn debe obtener de Zoom Marketplace
ZOOM_API_SECRET=          # Cyn debe obtener de Zoom Marketplace

# Calendly (para booking)
CALENDLY_API_KEY=         # Cyn debe obtener de Calendly
CALENDLY_WEBHOOK_SECRET=  # Cyn debe configurar en Calendly

# Clawbot.ai (AI agent)
CLAWBOT_API_KEY=          # Cyn debe obtener de Clawbot.ai
CLAWBOT_WEBHOOK_SECRET=   # Cyn debe configurar en Clawbot
```

### ???? **Informaci??n personal de Cyn:**
```bash
CLIENT_NAME=Cyn
CLIENT_PHONE=+1234567890          # Tel??fono real de Cyn
CLIENT_EMAIL=cyn@einstein-kids.com
CLIENT_WHATSAPP_NUMBER=+1234567890  # WhatsApp de Cyn
CLIENT_WEBSITE=https://einstein-kids.com
```

### ???? **Seguridad del cliente:**
```bash
CLIENT_JWT_SECRET=        # Cyn debe generar (m??nimo 32 caracteres)
CLIENT_ENCRYPTION_KEY=    # Cyn debe generar (32 caracteres)
```

### ???? **Configuraci??n del negocio:**
```bash
CLIENT_MASTERCLASS_DURATION_MINUTES=90
CLIENT_MASTERCLASS_MAX_ATTENDEES=100
CLIENT_BUSINESS_HOURS=9:00-18:00 America/New_York
CLIENT_TIMEZONE=America/New_York
```

---

## ??????? **DESARROLLADOR (T??)**

### ???? **Qu?? configuras t??:**
**Archivo**: `.env.developer` (copiar de `.env.developer.example`)

### ???? **Tus credenciales personales:**
```bash
# Tu informaci??n
DEVELOPER_NAME=Tu Nombre
DEVELOPER_EMAIL=tu@email.com
DEVELOPER_PHONE=+0000000000

# Tokens de desarrollo
DEVELOPER_GITHUB_TOKEN=     # Tu token de GitHub
DEVELOPER_DOCKER_HUB_TOKEN=# Tu token de Docker Hub
DEVELOPER_SSH_KEY_PATH=     # Tu ruta de SSH key
```

### ???? **Monitoreo y alertas (tuyas):**
```bash
DEVELOPER_SLACK_WEBHOOK=   # Tu webhook de Slack para alertas
DEVELOPER_EMAIL_ALERTS=    # Tu email para alertas
DEVELOPER_SMS_ALERTS=     # Tu n??mero para SMS de alertas
```

### ???? **Configuraci??n de despliegue (tuya):**
```bash
DEPLOY_SERVER=your-server.com
DEPLOY_USER=deploy-user
DEPLOY_KEY_PATH=~/.ssh/deploy_key
BUILD_ENVIRONMENT=development
DEBUG_MODE=true
```

### ???? **Configuraci??n local (tuya):**
```bash
LOCAL_BACKUP_PATH=/backups/cyn-project
LOCAL_LOGS_PATH=/logs/cyn-project
LOCAL_TEMP_PATH=/tmp/cyn-project
```

---

## ?????? **SISTEMA (Neutral)**

### ???? **Qu?? es del sistema:**
**Archivo**: `.env.system` (ya est?? configurado)

### ??????? **Configuraci??n de servicios:**
```bash
# PostgreSQL
POSTGRES_VERSION=15
POSTGRES_USER=cyn_user
POSTGRES_PASSWORD=<client_db_password>
POSTGRES_DB=cyn_einstein_kids

# Windmill
WINDMILL_VERSION=latest
WM_ADMIN_EMAIL=admin@system.local
WM_ADMIN_PASSWORD=system_admin_secure
WM_WORKSPACE=cyn-einstein-kids

# Redis
REDIS_VERSION=7-alpine

# Prometheus
PROMETHEUS_VERSION=latest
```

### ???? **Seguridad del sistema:**
```bash
SYSTEM_JWT_SECRET=system_jwt_secret_key_min_32_chars_here
SYSTEM_ENCRYPTION_KEY=system_encryption_key_32_chars_here
SYSTEM_API_RATE_LIMIT=1000
SYSTEM_WEBHOOK_TIMEOUT=30
```

### ???? **Red y puertos:**
```bash
SYSTEM_NETWORK_NAME=cyn_network
SYSTEM_RESTART_POLICY=unless-stopped
SYSTEM_HEALTHCHECK_INTERVAL=30s
```

---

## ???? **IMPORTANTE - NO CONFUNDIR**

### ??? **Cosas que NO son del cliente:**
- Puertos de Docker (5433, 8001, 6380, 9091) ??? **Sistema**
- Nombres de contenedores ??? **Sistema**
- Configuraci??n de redes ??? **Sistema**
- Tokens de GitHub/Docker ??? **Desarrollador**

### ??? **Cosas que NO son tuyas:**
- APIs de WhatsApp/Zoom/Calendly ??? **Cliente**
- Tel??fono de Cyn ??? **Cliente**
- Nombre del negocio ??? **Cliente**
- Horarios de atenci??n ??? **Cliente**

### ??? **Cosas que NO son del sistema:**
- Credenciales de APIs externas ??? **Cliente**
- Informaci??n personal ??? **Cliente**
- Configuraciones de negocio ??? **Cliente**

---

## ???? **SETUP INICIAL - Paso a paso**

### 1. **Configurar sistema** (autom??tico):
```bash
# El archivo .env.system ya existe
```

### 2. **Configurar cliente** (Cyn debe hacer):
```bash
cp .env.client.example .env.client
# Editar con credenciales reales de Cyn
```

### 3. **Configurar desarrollador** (t?? debes hacer):
```bash
cp .env.developer.example .env.developer
# Editar con tus credenciales personales
```

### 4. **Iniciar ecosistema**:
```bash
./start-cyn-ecosystem.sh
```

---

## ???? **D??NDE CONSEGUIR LAS CREDENCIALES**

### **Para Cyn (Cliente):**
- **YCloud**: https://ycloud.com ??? Registro ??? API Keys
- **Zoom**: https://marketplace.zoom.us ??? Develop ??? Build App ??? JWT
- **Calendly**: https://calendly.com ??? Integrations ??? API & Webhooks  
- **Clawbot**: https://clawbot.ai ??? Dashboard ??? API Settings

### **Para ti (Desarrollador):**
- **GitHub**: https://github.com ??? Settings ??? Developer settings ??? Personal access tokens
- **Docker Hub**: https://hub.docker.com ??? Settings ??? Security ??? Access tokens
- **Slack**: https://api.slack.com ??? Your Apps ??? Incoming Webhooks

---

## ???? **SOLUCI??N DE PROBLEMAS**

### **Si Cyn no puede ver su dashboard:**
1. Verificar que haya configurado `.env.client`
2. Revisar que las credenciales sean correctas
3. Ver logs: `docker-compose -f docker-compose-cyn.yml logs windmill-cyn`

### **Si no recibes alertas como desarrollador:**
1. Verificar `.env.developer`
2. Comprobar tus webhooks y tokens

### **Si el sistema no inicia:**
1. Verificar `.env.system`
2. Revisar puertos disponibles
3. Verificar Docker y Docker Compose

---

**??? RECUERDA: Mant??n siempre separadas las credenciales de cliente y desarrollador para seguridad y claridad.**
