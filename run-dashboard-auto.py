#!/usr/bin/env python3
# 🏢 DASHBOARD DE CONTROL DE PAGOS - Versión Automática
# Script para ver el dashboard sin interacción

import subprocess
import sys
import os
import time

def run_dashboard_auto():
    """Ejecutar el dashboard automáticamente sin interacción"""
    print("🚀 Iniciando dashboard de control automáticamente...")
    print("📊 Accede a: http://localhost:8501")
    print("")
    
    # Cambiar al directorio correcto
    os.chdir("aut_windmill")
    
    # Configurar variables de entorno para evitar interacción
    env = os.environ.copy()
    env['STREAMLIT_SERVER_HEADLESS'] = 'true'
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    try:
        # Ejecutar con subprocess para controlar mejor
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "f/payment_dashboard.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--global.developmentMode=false",
            "--browser.gatherUsageStats=false"
        ], env=env)
        
        print("✅ Dashboard iniciado correctamente")
        print("⏳ Manteniendo ejecutando...")
        
        # Mantener el proceso vivo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo dashboard...")
            process.terminate()
            
    except Exception as e:
        print(f"❌ Error ejecutando dashboard: {e}")

if __name__ == "__main__":
    print("🏢 SISTEMA DE CONTROL DE PAGOS - DASHBOARD AUTOMÁTICO")
    print("=" * 50)
    print("")
    run_dashboard_auto()