# 🏢 SISTEMA DE CONTROL DE PAGOS - Modelo SaaS
# Este script monitorea pagos y controla acceso a clientes

import os
import json
import datetime
import subprocess
from typing import Dict, List
import requests
import sqlite3

class PaymentControlSystem:
    def __init__(self):
        self.db_path = "payment_control.db"
        self.init_database()
        
    def init_database(self):
        """Inicializa base de datos de control de pagos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY,
                client_name TEXT UNIQUE,
                port INTEGER UNIQUE,
                email TEXT,
                monthly_fee REAL,
                status TEXT DEFAULT 'active',  -- active, suspended, cancelled
                last_payment DATE,
                next_payment DATE,
                grace_days INTEGER DEFAULT 3,
                created_at DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY,
                client_id INTEGER,
                amount REAL,
                payment_date DATE,
                payment_method TEXT,
                status TEXT,  -- completed, pending, failed
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')
        
        # Insertar cliente Cyn como ejemplo
        cursor.execute('''
            INSERT OR IGNORE INTO clients 
            (client_name, port, email, monthly_fee, last_payment, next_payment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Cyn_Einstein_Kids', 8001, 'cyn@einstein-kids.com', 297.0, 
              datetime.date.today(), datetime.date.today() + datetime.timedelta(days=30)))
        
        conn.commit()
        conn.close()
    
    def check_payment_status(self, client_name: str) -> Dict:
        """Verifica estado de pago de un cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, last_payment, next_payment, grace_days, port
            FROM clients WHERE client_name = ?
        ''', (client_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'error': 'Cliente no encontrado'}
        
        status, last_payment, next_payment, grace_days, port = result
        today = datetime.date.today()
        
        # Convertir strings a fechas si es necesario
        if isinstance(next_payment, str):
            next_payment = datetime.datetime.strptime(next_payment, '%Y-%m-%d').date()
        
        days_overdue = (today - next_payment).days
        
        return {
            'client': client_name,
            'port': port,
            'status': status,
            'last_payment': str(last_payment),
            'next_payment': str(next_payment),
            'days_overdue': days_overdue,
            'grace_days': grace_days,
            'should_suspend': days_overdue > grace_days and status == 'active'
        }
    
    def process_payment(self, client_name: str, amount: float, payment_method: str = 'stripe') -> bool:
        """Procesa pago de cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener ID del cliente
        cursor.execute('SELECT id FROM clients WHERE client_name = ?', (client_name,))
        client_result = cursor.fetchone()
        
        if not client_result:
            conn.close()
            return False
        
        client_id = client_result[0]
        today = datetime.date.today()
        next_payment = today + datetime.timedelta(days=30)
        
        try:
            # Registrar pago
            cursor.execute('''
                INSERT INTO payments (client_id, amount, payment_date, payment_method, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (client_id, amount, today, payment_method, 'completed'))
            
            # Actualizar cliente
            cursor.execute('''
                UPDATE clients 
                SET last_payment = ?, next_payment = ?, status = 'active'
                WHERE id = ?
            ''', (today, next_payment, client_id))
            
            conn.commit()
            
            # Reactivar contenedor si estaba suspendido
            self.reactivate_client(client_name)
            
            conn.close()
            return True
            
        except Exception as e:
            conn.close()
            print(f"Error procesando pago: {e}")
            return False
    
    def suspend_client(self, client_name: str) -> bool:
        """Suspende acceso a cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener puerto del cliente
        cursor.execute('SELECT port FROM clients WHERE client_name = ?', (client_name,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False
        
        port = result[0]
        
        try:
            # Suspender contenedor Docker
            container_name = f"client_{port}_windmill"
            subprocess.run(['docker', 'stop', container_name], check=True)
            subprocess.run(['docker', 'rm', container_name], check=True)
            
            # Actualizar estado en BD
            cursor.execute('UPDATE clients SET status = ? WHERE client_name = ?', 
                          ('suspended', client_name))
            conn.commit()
            conn.close()
            
            print(f"🚫 Cliente {client_name} suspendido. Puerto {port} cerrado.")
            return True
            
        except subprocess.CalledProcessError as e:
            conn.close()
            print(f"Error suspendiendo cliente: {e}")
            return False
    
    def reactivate_client(self, client_name: str) -> bool:
        """Reactiva acceso a cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE clients SET status = ? WHERE client_name = ?', 
                      ('active', client_name))
        conn.commit()
        conn.close()
        
        # Reiniciar contenedor (implementar según tu arquitectura)
        print(f"✅ Cliente {client_name} reactivado.")
        return True
    
    def check_all_clients(self) -> List[Dict]:
        """Verifica estado de todos los clientes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT client_name FROM clients')
        clients = cursor.fetchall()
        conn.close()
        
        results = []
        for client in clients:
            status = self.check_payment_status(client[0])
            results.append(status)
            
            # Suspender automáticamente si debe estarlo
            if status.get('should_suspend', False):
                self.suspend_client(client[0])
        
        return results
    
    def generate_payment_link(self, client_name: str) -> str:
        """Genera link de pago para cliente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT monthly_fee FROM clients WHERE client_name = ?', (client_name,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return ""
        
        amount = result[0]
        
        # Aquí integrarías con Stripe, PayPal, etc.
        # Por ahora generamos un link simulado
        return f"https://payment-link.com/pay?client={client_name}&amount={amount}&month=2024-02"
    
    def send_payment_reminder(self, client_name: str) -> bool:
        """Envía recordatorio de pago"""
        status = self.check_payment_status(client_name)
        
        if status.get('days_overdue', 0) > 0:
            payment_link = self.generate_payment_link(client_name)
            
            # Aquí integrarías con email (SendGrid, etc.)
            print(f"📧 Recordatorio enviado a {client_name}")
            print(f"💳 Link de pago: {payment_link}")
            print(f"⏰ Días de gracia restantes: {status.get('grace_days', 0) - status.get('days_overdue', 0)}")
            
            return True
        
        return False

def main():
    """Función principal de control"""
    control = PaymentControlSystem()
    
    print("🏢 SISTEMA DE CONTROL DE PAGOS SAAS")
    print("=" * 50)
    
    # Verificar todos los clientes
    clients_status = control.check_all_clients()
    
    for client in clients_status:
        print(f"\n📊 Cliente: {client['client']}")
        print(f"   Puerto: {client['port']}")
        print(f"   Estado: {client['status']}")
        print(f"   Próximo pago: {client['next_payment']}")
        print(f"   Días vencidos: {client['days_overdue']}")
        
        if client.get('should_suspend', False):
            print("   🚨 ACCIÓN: Suspendiendo acceso...")
        else:
            print("   ✅ Acceso activo")
    
    # Ejemplo: Procesar pago de Cyn
    print(f"\n💳 Ejemplo: Procesando pago de Cyn...")
    success = control.process_payment('Cyn_Einstein_Kids', 297.0)
    if success:
        print("✅ Pago procesado correctamente")
    else:
        print("❌ Error procesando pago")

if __name__ == "__main__":
    main()