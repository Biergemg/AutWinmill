#!/usr/bin/env python3
# 🏢 DASHBOARD DE CONTROL DE PAGOS - Versión Manual
# Script para ver el dashboard sin contenedor

import subprocess
import sys
import os

def install_requirements():
    """Instalar dependencias necesarias"""
    print("📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "pandas", "plotly", "requests"])
        print("✅ Dependencias instaladas")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def run_dashboard():
    """Ejecutar el dashboard de control"""
    print("🚀 Iniciando dashboard de control...")
    print("📊 Accede a: http://localhost:8501")
    print("")
    
    # Cambiar al directorio correcto
    os.chdir("aut_windmill")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "f/payment_dashboard.py",
            "--server.port=8501",
            "--server.address=0.0.0.0"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard detenido")
    except Exception as e:
        print(f"❌ Error ejecutando dashboard: {e}")

def main():
    print("🏢 SISTEMA DE CONTROL DE PAGOS - DASHBOARD MANUAL")
    print("=" * 50)
    print("")
    
    # Instalar dependencias
    if not install_requirements():
        return
    
    # Ejecutar dashboard
    run_dashboard()

if __name__ == "__main__":
    main()