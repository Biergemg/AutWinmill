#!/usr/bin/env python3
"""
Test script para Einstein Kids - Verifica que el sistema est?? funcionando
"""

import psycopg2
import json
import os
from datetime import datetime, timedelta

def test_database_connection():
    """Prueba conexi??n a base de datos"""
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
        tables = ['ek_leads', 'ek_jobs', 'ek_lead_events', 'ek_ycloud_messages', 'ek_sales', 'ek_partners', 'ek_groups', 'ek_group_memberships']
        
        print("???? Verificando tablas de Einstein Kids...")
        for table in tables:
            cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}');")
            exists = cursor.fetchone()[0]
            print(f"  {table}: {'???' if exists else '???'}")
        
        # Verificar ??ndices
        print("\n???? Verificando ??ndices...")
        cursor.execute("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE tablename LIKE 'ek_%' 
            ORDER BY tablename, indexname;
        """)
        indexes = cursor.fetchall()
        for index_name, table_name in indexes:
            print(f"  {table_name}.{index_name}: ???")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"??? Error conectando a base de datos: {e}")
        return False

def test_contracts():
    """Prueba que los contratos JSON existen"""
    print("\n???? Verificando contratos JSON...")
    
    contracts_dir = "contracts/einstein_kids"
    contracts = [
        "ycloud_inbound_message.schema.json",
        "lead_optin.schema.json", 
        "payment_claim.schema.json"
    ]
    
    for contract in contracts:
        path = f"{contracts_dir}/{contract}"
        if os.path.exists(path):
            print(f"  {contract}: ???")
        else:
            print(f"  {contract}: ???")

def test_flows():
    """Prueba que los flows existen"""
    print("\n???? Verificando flows...")
    
    flows = [
        "einstein_kids_moms_funnel.yaml",
        "einstein_kids_webhook_inbound.yaml"
    ]
    
    for flow in flows:
        path = f"flows/{flow}"
        if os.path.exists(path):
            print(f"  {flow}: ???")
        else:
            print(f"  {flow}: ???")

def test_scripts():
    """Prueba que los scripts cr??ticos existen"""
    print("\n???? Verificando scripts cr??ticos...")
    
    scripts = [
        "f/einstein_kids/shared/ycloud_webhook_inbound.py",
        "f/einstein_kids/shared/upsert_lead.py",
        "f/einstein_kids/shared/ycloud_send_template.py",
        "f/einstein_kids/shared/schedule_jobs.py",
        "f/einstein_kids/shared/payment_claim_create.py",
        "f/einstein_kids/shared/payment_claim_decide.py"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            print(f"  {script}: ???")
        else:
            print(f"  {script}: ???")

def create_test_lead():
    """Crea un lead de prueba"""
    print("\n???? Creando lead de prueba...")
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'windmill'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'windmill')
        )
        
        cursor = conn.cursor()
        
        # Insertar lead de prueba
        test_lead = {
            "name": "Mar??a Garc??a",
            "email": "maria@test.com",
            "phone": "55 1234 5678",
            "phone_normalized": "+525512345678",
            "avatar": "mother",
            "utm_source": "facebook",
            "utm_campaign": "test_campaign",
            "landing_id": "test_landing",
            "event_start_at": datetime.now() + timedelta(days=3),
            "stage": "NEW_LEAD",
            "score": 0,
            "whatsapp_consent_ts": datetime.now(),
            "email_consent_ts": datetime.now()
        }
        
        cursor.execute("""
            INSERT INTO ek_leads (
                name, email, phone, phone_normalized, avatar,
                utm_source, utm_campaign, landing_id, event_start_at,
                stage, score, whatsapp_consent_ts, email_consent_ts
            ) VALUES (
                %(name)s, %(email)s, %(phone)s, %(phone_normalized)s, %(avatar)s,
                %(utm_source)s, %(utm_campaign)s, %(landing_id)s, %(event_start_at)s,
                %(stage)s, %(score)s, %(whatsapp_consent_ts)s, %(email_consent_ts)s
            ) RETURNING lead_id;
        """, test_lead)
        
        lead_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"??? Lead creado: {lead_id}")
        
        # Crear evento
        cursor.execute("""
            INSERT INTO ek_lead_events (lead_id, event_type, payload)
            VALUES (%s, %s, %s);
        """, (lead_id, 'lead_created', json.dumps(test_lead)))
        
        conn.commit()
        conn.close()
        
        return lead_id
        
    except Exception as e:
        print(f"??? Error creando lead de prueba: {e}")
        return None

def main():
    """Funci??n principal de prueba"""
    print("???? Iniciando pruebas de Einstein Kids...\n")
    
    # Test 1: Base de datos
    db_ok = test_database_connection()
    
    if not db_ok:
        print("\n??? No se puede continuar sin base de datos")
        return
    
    # Test 2: Contratos
    test_contracts()
    
    # Test 3: Flows
    test_flows()
    
    # Test 4: Scripts
    test_scripts()
    
    # Test 5: Crear lead de prueba
    lead_id = create_test_lead()
    
    print(f"\n???? Resumen:")
    print(f"  Base de datos: {'???' if db_ok else '???'}")
    print(f"  Lead de prueba: {'???' if lead_id else '???'} ({lead_id})")
    
    if lead_id:
        print(f"\n???? Puedes usar este lead_id para pruebas: {lead_id}")
    
    print("\n???? Pr??ximos pasos:")
    print("  1. Configurar YCloud API key en resources/einstein_kids/config.yaml")
    print("  2. Crear templates en YCloud")
    print("  3. Configurar webhooks")
    print("  4. Probar env??o de mensajes")

if __name__ == "__main__":
    main()
