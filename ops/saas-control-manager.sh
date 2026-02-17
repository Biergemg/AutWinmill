#!/bin/bash
# 🚀 SISTEMA DE CONTROL DE PAGOS - Modelo GOOGLE
# Script para gestionar todo el ecosistema SaaS

echo "🏢 INICIANDO SISTEMA DE CONTROL DE PAGOS SAAS"
echo "=============================================="
echo ""

# Función para verificar estado
check_status() {
    echo "📊 ESTADO DEL SISTEMA:"
    echo "   🎯 Puerto 8000 → Sistema Base (Tu herramienta)"
    echo "   📊 Puerto 8501 → Dashboard de Control de Pagos"
    echo "   👤 Puerto 8001 → Cliente Cyn (Controlado por pagos)"
    echo ""
}

# Función para iniciar sistema completo
start_system() {
    echo "🚀 Iniciando sistema completo..."
    
    # Iniciar contenedores
    docker-compose -f docker-compose-saas-control.yml up -d
    
    echo ""
    echo "⏳ Esperando a que los servicios estén listos..."
    sleep 30
    
    echo ""
    echo "✅ SISTEMA INICIADO CORRECTAMENTE"
    check_status
    
    echo ""
    echo "🎯 ACCESOS DISPONIBLES:"
    echo "   🏢 Tu sistema de desarrollo: http://localhost:8000"
    echo "   📊 Dashboard de control: http://localhost:8501"
    echo "   👤 Sistema de Cyn: http://localhost:8001"
    echo ""
    echo "💡 COMO FUNCIONA:"
    echo "   1. Tú trabajas en localhost:8000 (desarrollo)"
    echo "   2. Controlas pagos en localhost:8501"
    echo "   3. Cyn accede a localhost:8001 (si pagó)"
    echo "   4. El sistema suspende automáticamente si no paga"
}

# Función para detener sistema
stop_system() {
    echo "🛑 Deteniendo sistema..."
    docker-compose -f docker-compose-saas-control.yml down
    echo "✅ Sistema detenido"
}

# Función para ver logs
show_logs() {
    echo "📋 Logs del sistema:"
    docker-compose -f docker-compose-saas-control.yml logs --tail=50
}

# Función para verificar pagos
check_payments() {
    echo "💳 Verificando estado de pagos..."
    cd /app && python f/payment_control_system.py
}

# Menú principal
show_menu() {
    echo ""
    echo "🏢 SISTEMA DE CONTROL DE PAGOS - MENÚ"
    echo "======================================"
    echo "1. 🚀 Iniciar sistema completo"
    echo "2. 🛑 Detener sistema"
    echo "3. 📊 Ver estado"
    echo "4. 📋 Ver logs"
    echo "5. 💳 Verificar pagos"
    echo "6. ❌ Salir"
    echo ""
}

# Bucle principal
while true; do
    show_menu
    read -p "Selecciona una opción (1-6): " option
    
    case $option in
        1)
            start_system
            ;;
        2)
            stop_system
            ;;
        3)
            check_status
            ;;
        4)
            show_logs
            ;;
        5)
            check_payments
            ;;
        6)
            echo "👋 ¡Hasta luego!"
            exit 0
            ;;
        *)
            echo "❌ Opción inválida. Por favor selecciona 1-6."
            ;;
    esac
    
    echo ""
    read -p "Presiona Enter para continuar..."
done