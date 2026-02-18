#!/bin/bash
# Script de inicio para el ecosistema Cyn - Einstein Kids
# SEPARACIÓN CLARA: Cliente vs Desarrollador vs Sistema

set -e

echo "🚀 Iniciando ecosistema Cyn - Einstein Kids..."
echo "📋 Separación de credenciales: Cliente | Desarrollador | Sistema"

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

# Resolver comando compose (plugin o binario legacy)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
else
    echo "Docker Compose no esta instalado. Instala docker-compose-plugin."
    exit 1
fi

# Crear directorios necesarios
echo "📁 Creando directorios necesarios..."
mkdir -p monitoring
mkdir -p db/migrations
mkdir -p logs

# VERIFICACIÓN DE ARCHIVOS DE ENTORNO
echo "🔍 Verificando archivos de entorno..."

# Archivo del sistema (siempre debe existir)
if [ ! -f .env.system ]; then
    echo "⚠️  Archivo .env.system no encontrado. Usando valores por defecto del sistema."
fi

# Archivo del cliente (Cyn)
if [ ! -f .env.client ]; then
    echo "⚠️  Archivo .env.client no encontrado."
    echo "   📋 Para configuración del CLIENTE (Cyn):"
    echo "   1. Copia: cp .env.client.example .env.client"
    echo "   2. Edita con credenciales reales de Cyn"
    echo "   3. Las credenciales marcadas como 'CLIENT_*' son de Cyn"
fi

# Archivo del desarrollador (tú)
if [ ! -f .env.developer ]; then
    echo "⚠️  Archivo .env.developer no encontrado."
    echo "   🛠️  Para configuración del DESARROLLADOR (tú):"
    echo "   1. Copia: cp .env.developer.example .env.developer" 
    echo "   2. Edita con tus credenciales personales"
    echo "   3. Las credenciales marcadas como 'DEVELOPER_*' son tuyas"
fi

echo ""
echo "📊 RESUMEN DE CREDENCIALES:"
echo "   👤 CLIENTE (Cyn): Teléfono, APIs (YCloud, Zoom, Calendly, Clawbot)"
echo "   🛠️  DESARROLLADOR (Tú): GitHub, Docker Hub, SSH keys, alertas"
echo "   ⚙️  SISTEMA: PostgreSQL, Windmill, Redis, puertos, redes"
echo ""

# Detener contenedores existentes
echo "🛑 Deteniendo contenedores existentes..."
${COMPOSE_CMD} -f docker-compose-cyn.yml down --remove-orphans 2>/dev/null || true

# Cargar variables de entorno en orden: Sistema → Cliente → Desarrollador
echo "📦 Cargando configuraciones..."
ENV_FILES=""
[ -f .env.system ] && ENV_FILES="$ENV_FILES --env-file .env.system"
[ -f .env.client ] && ENV_FILES="$ENV_FILES --env-file .env.client"  
[ -f .env.developer ] && ENV_FILES="$ENV_FILES --env-file .env.developer"

# Construir e iniciar servicios
echo "🏗️  Construyendo e iniciando servicios..."
if [ -n "$ENV_FILES" ]; then
    ${COMPOSE_CMD} $ENV_FILES -f docker-compose-cyn.yml up -d
else
    ${COMPOSE_CMD} -f docker-compose-cyn.yml up -d
fi

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 30

# Verificar estado
echo "🔍 Verificando estado de los servicios..."
${COMPOSE_CMD} -f docker-compose-cyn.yml ps

echo ""
echo "✅ Ecosistema Cyn iniciado exitosamente!"
echo ""
echo "🌐 URLs de acceso:"
echo "   • Windmill: http://localhost:8001"
echo "   • PostgreSQL: localhost:5433"
echo "   • Redis: localhost:6380"
echo "   • Prometheus: http://localhost:9091"
echo ""
echo "📋 CRÉDITOS Y RESPONSABILIDADES:"
echo "   👤 CLIENTE (Cyn): Configurar .env.client con credenciales reales"
echo "   🛠️  DESARROLLADOR (Tú): Configurar .env.developer con tus datos"
echo "   ⚙️  SISTEMA: Configuración técnica automática"
echo ""
echo "🛑 Para detener: ${COMPOSE_CMD} -f docker-compose-cyn.yml down"
echo "🔄 Para reiniciar: ./start-cyn-ecosystem.sh"
echo ""
echo "❓ Dudas sobre credenciales? Revisa README-CREDENTIALS.md"