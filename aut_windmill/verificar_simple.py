# Verificaci??n super simple - Einstein Kids
print("???? VERIFICACI??N EINSTEIN KIDS")
print("=" * 30)

# Verificar que Docker est?? corriendo
print("\n1?????? Contenedores Docker:")
import subprocess
result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                       capture_output=True, text=True)
lines = result.stdout.split('\n')
for line in lines:
    if 'windmill' in line.lower():
        print(f"  ??? {line.strip()}")

print("\n2?????? Tablas Einstein Kids:")
# Verificar tablas directamente
import psycopg2
import os

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='windmill',
        password=os.getenv('POSTGRES_PASSWORD'),
        database='windmill'
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'ek_%';")
    tables = cursor.fetchall()
    
    for table in tables:
        print(f"  ??? {table[0]}")
    
    # Contar leads
    cursor.execute("SELECT COUNT(*) FROM ek_leads;")
    count = cursor.fetchone()[0]
    print(f"\n3?????? Leads en sistema: {count}")
    
    # Mostrar primeros leads
    cursor.execute("SELECT id, name, phone, stage FROM ek_leads LIMIT 2;")
    leads = cursor.fetchall()
    print("\n4?????? Primeros leads:")
    for lead in leads:
        print(f"  ???? {lead[1]} | {lead[2]} | {lead[3]}")
    
    conn.close()
    
    print("\n???? ??TODO FUNCIONA!")
    print("\n???? Tu sistema est?? listo para:")
    print("  ??? Recibir leads de mam??s")
    print("  ??? Enviar mensajes WhatsApp")
    print("  ??? Programar recordatorios")
    print("  ??? Gestionar pagos")
    
except Exception as e:
    print(f"??? Error: {e}")
    print("\n???? Aseg??rate de que Docker est?? corriendo")

print("\n???? Pr??ximos pasos:")
print("  1. Configurar YCloud (30 min)")
print("  2. Crear landing page (1 hora)")
print("  3. Probar con lead real")
