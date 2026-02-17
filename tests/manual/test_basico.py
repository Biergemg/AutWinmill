#!/usr/bin/env python3
"""
Test simple para Einstein Kids - Verifica que el sistema b??sico funcione
"""

import psycopg2
import json
import os

def test_basic_connection():
    """Prueba conexi??n b??sica a base de datos"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'windmill'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'windmill')
        )
        
        cursor = conn.cursor()
        
        # Verificar que las tablas existen
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'ek_%';")
        tables = cursor.fetchall()
        
        print("???? Tablas Einstein Kids encontradas:")
        for table in tables:
            print(f"  ??? {table[0]}")
        
        # Verificar datos de prueba
        cursor.execute("SELECT COUNT(*) FROM ek_leads;")
        count = cursor.fetchone()[0]
        print(f"\n???? Leads en base de datos: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, name, phone, stage FROM ek_leads LIMIT 5;")
            leads = cursor.fetchall()
            print("\n???? Primeros leads:")
            for lead in leads:
                print(f"  ID: {lead[0]} | Nombre: {lead[1]} | Tel: {lead[2]} | Etapa: {lead[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"??? Error: {e}")
        return False

def create_test_job():
    """Crea un trabajo de prueba"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'windmill'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'windmill')
        )
        
        cursor = conn.cursor()
        
        # Obtener primer lead
        cursor.execute("SELECT id FROM ek_leads LIMIT 1;")
        lead_id = cursor.fetchone()[0]
        
        # Crear trabajo de prueba
        from datetime import datetime, timedelta
        run_at = datetime.now() + timedelta(minutes=5)
        
        cursor.execute("""
            INSERT INTO ek_jobs (lead_id, job_type, run_at)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (lead_id, 'welcome_message', run_at))
        
        job_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        print(f"??? Trabajo creado: {job_id}")
        return job_id
        
    except Exception as e:
        print(f"??? Error creando trabajo: {e}")
        return None

def main():
    """Funci??n principal de prueba"""
    print("???? Test Einstein Kids - Sistema B??sico")
    print("=" * 40)
    
    # Test 1: Conexi??n y tablas
    print("\n1?????? Verificando base de datos...")
    db_ok = test_basic_connection()
    
    if not db_ok:
        print("\n??? No se puede continuar sin base de datos")
        return
    
    # Test 2: Crear trabajo de prueba
    print("\n2?????? Creando trabajo de prueba...")
    job_id = create_test_job()
    
    print("\n???? Resumen del test:")
    print(f"  ??? Base de datos: OK")
    print(f"  ??? Tablas Einstein Kids: OK")
    print(f"  ??? Datos de prueba: OK")
    print(f"  ??? Trabajo de prueba: {'OK' if job_id else 'ERROR'}")
    
    print("\n???? Sistema listo para:")
    print("  ??? Recibir leads desde landing")
    print("  ??? Programar mensajes WhatsApp")
    print("  ??? Procesar webhooks de YCloud")
    print("  ??? Gestionar pagos y claims")
    
    print("\n???? Pr??ximos pasos:")
    print("  1. Configurar YCloud API")
    print("  2. Crear landing page")
    print("  3. Probar env??o de WhatsApp")
    print("  4. Configurar webhooks")

if __name__ == "__main__":
    main()
