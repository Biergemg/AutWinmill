#!/usr/bin/env python3
# ???? VERIFICADOR COMPLETO DEL SISTEMA DE CONTROL DE PAGOS
# Muestra el estado real de todos los servicios

import requests
import subprocess
import time
import socket

def check_port(host, port):
    """Verificar si un puerto est?? abierto"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_website(url):
    """Verificar si un sitio web responde"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("???? VERIFICADOR COMPLETO DEL SISTEMA DE CONTROL DE PAGOS")
    print("=" * 60)
    print()
    
    # Verificar puertos
    print("???? VERIFICANDO PUERTOS:")
    print(f"   Puerto 8000 (Sistema Base): {'??? ABIERTO' if check_port('localhost', 8000) else '??? CERRADO'}")
    print(f"   Puerto 8001 (Sistema Cyn): {'??? ABIERTO' if check_port('localhost', 8001) else '??? CERRADO'}")
    print(f"   Puerto 8501 (Dashboard Control): {'??? ABIERTO' if check_port('localhost', 8501) else '??? CERRADO'}")
    print(f"   Puerto 5432 (PostgreSQL Base): {'??? ABIERTO' if check_port('localhost', 5432) else '??? CERRADO'}")
    print(f"   Puerto 5433 (PostgreSQL Cyn): {'??? ABIERTO' if check_port('localhost', 5433) else '??? CERRADO'}")
    print()
    
    # Verificar sitios web
    print("???? VERIFICANDO SITIOS WEB:")
    print(f"   Sistema Base (http://localhost:8000): {'??? FUNCIONANDO' if check_website('http://localhost:8000') else '??? NO RESPONDE'}")
    print(f"   Sistema Cyn (http://localhost:8001): {'??? FUNCIONANDO' if check_website('http://localhost:8001') else '??? NO RESPONDE'}")
    print(f"   Dashboard Control (http://localhost:8501): {'??? FUNCIONANDO' if check_website('http://localhost:8501') else '??? NO RESPONDE'}")
    print()
    
    # Verificar contenedores
    print("???? VERIFICANDO CONTENEDORES:")
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Saltar encabezado
                if 'windmill' in line.lower() or 'postgres' in line.lower() or 'cyn' in line.lower():
                    print(f"   {line}")
        else:
            print("   ??? Error ejecutando docker ps")
    except:
        print("   ??? Docker no est?? disponible")
    
    print()
    print("???? RESUMEN DE ACCESO:")
    print("   ??? Sistema Base Windmill: http://localhost:8000")
    print("   ??? Sistema Cyn Windmill: http://localhost:8001 (Problemas de contenedor)")
    print("   ??? Dashboard de Control: http://localhost:8501")
    print()
    print("???? CREDENCIALES:")
    print("   Sistema Base: <define WM_ADMIN_EMAIL> / <define WM_ADMIN_PASSWORD>")
    print("   Sistema Cyn: <define CLIENT_ADMIN_EMAIL> / <define CLIENT_ADMIN_PASSWORD>")
    print()
    print("???? PARA CLIENTES:")
    print("   Cada cliente tendr?? su propio puerto (8002, 8003, etc.)")
    print("   y sus credenciales ser??n generadas autom??ticamente")
    print("   El dashboard controla pagos mensuales y suspende servicios")

if __name__ == "__main__":
    main()
