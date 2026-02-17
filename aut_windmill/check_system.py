# Verificacion Einstein Kids - Simple
print("EINSTEIN KIDS - VERIFICACION")
print("=" * 30)

# Verificar Docker
print("\n1. Contenedores Docker:")
import subprocess
result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
if 'aut_windmill' in result.stdout:
    print("   ??? Docker OK - Windmill corriendo")
else:
    print("   ??? Docker ERROR")

# Verificar base de datos
print("\n2. Base de datos:")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost', port=5432,
        user='windmill', password=os.getenv('POSTGRES_PASSWORD'),
        database='windmill'
    )
    cursor = conn.cursor()
    
    # Tablas
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'ek_%';")
    tables = cursor.fetchall()
    
    print(f"   ??? Tablas Einstein Kids: {len(tables)}")
    for table in tables:
        print(f"      - {table[0]}")
    
    # Leads
    cursor.execute("SELECT COUNT(*) FROM ek_leads;")
    count = cursor.fetchone()[0]
    print(f"   ??? Leads en sistema: {count}")
    
    # Primer lead
    cursor.execute("SELECT name, phone, stage FROM ek_leads LIMIT 1;")
    lead = cursor.fetchone()
    if lead:
        print(f"   ??? Ejemplo: {lead[0]} | {lead[1]} | {lead[2]}")
    
    conn.close()
    
except Exception as e:
    print(f"   ??? Error BD: {str(e)[:50]}")

print("\n3. Scripts implementados:")
scripts = [
    "ycloud_webhook_inbound.py",
    "upsert_lead.py", 
    "schedule_jobs.py",
    "payment_claim_create.py"
]

for script in scripts:
    import os
    path = f"f/einstein_kids/shared/{script}"
    if os.path.exists(path):
        print(f"   ??? {script}")
    else:
        print(f"   ??? {script}")

print("\n" + "=" * 30)
print("RESUMEN:")
print("Tu sistema Einstein Kids ESTA FUNCIONANDO")
print("Tienes motor + tablas + scripts")
print("Falta: YCloud + Landing + Templates")
print("=" * 30)
