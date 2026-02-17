# Einstein Kids - Ecosistema Cyn

Este directorio contiene toda la configuración Docker específica para el ecosistema de Cyn en Einstein Kids.

## 🚀 Inicio Rápido

```bash
# Hacer el script ejecutable
chmod +x start-cyn-ecosystem.sh

# Iniciar todo el ecosistema
./start-cyn-ecosystem.sh

# O usar Docker Compose directamente
docker-compose -f docker-compose-cyn.yml up -d
```

## 📋 Servicios Incluidos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| PostgreSQL | 5433 | Base de datos principal |
| Windmill | 8001 | Motor de automatizaciones |
| Redis | 6380 | Caché y colas |
| Prometheus | 9091 | Monitoreo y métricas |

## 🔧 Configuración

1. **Copiar archivo de entorno:**
   ```bash
   cp .env.cyn.example .env
   ```

2. **Editar .env con tus credenciales:**
   - `CYN_PHONE_NUMBER`: Teléfono de Cyn
   - `YCLOUD_API_KEY`: API de WhatsApp
   - `ZOOM_API_KEY`: Para masterclasses
   - `CALENDLY_API_KEY`: Para booking
   - `CLAWBOT_API_KEY`: AI agent

3. **Verificar logs:**
   ```bash
   docker-compose -f docker-compose-cyn.yml logs -f
   ```

## 📊 Monitoreo

- **Prometheus**: http://localhost:9091
- **Windmill**: http://localhost:8001

## 🛠️ Comandos Útiles

```bash
# Ver estado
docker-compose -f docker-compose-cyn.yml ps

# Ver logs de un servicio específico
docker-compose -f docker-compose-cyn.yml logs windmill-cyn

# Reiniciar un servicio
docker-compose -f docker-compose-cyn.yml restart windmill-cyn

# Detener todo
docker-compose -f docker-compose-cyn.yml down

# Eliminar volúmenes (CUIDADO: borra datos)
docker-compose -f docker-compose-cyn.yml down -v
```

## 🔐 Seguridad

- Todos los servicios están aislados en la red `cyn_network`
- Las contraseñas por defecto deben cambiarse en producción
- Los puertos están configurados para evitar conflictos

## 📁 Estructura

```
ops/
├── docker-compose-cyn.yml      # Configuración principal
├── .env.cyn.example          # Ejemplo de variables
├── start-cyn-ecosystem.sh    # Script de inicio
└── monitoring/
    └── prometheus.yml         # Config de monitoreo
```

## 🆘 Solución de Problemas

### PostgreSQL no inicia
```bash
# Verificar permisos
docker-compose -f docker-compose-cyn.yml logs postgres-cyn
```

### Windmill no conecta a BD
```bash
# Verificar variables de entorno
docker-compose -f docker-compose-cyn.yml exec windmill-cyn env | grep DATABASE
```

### Puerto ya en uso
```bash
# Cambiar puertos en docker-compose-cyn.yml
# Ejemplo: 8001 → 8002, 5433 → 5434, etc.
```