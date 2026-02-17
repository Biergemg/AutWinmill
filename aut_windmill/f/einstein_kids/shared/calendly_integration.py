"""
CALENDLY INTEGRATION - Einstein Kids
Integraci??n completa de Calendly para booking de masterclass
Basado en arquitectura 2025 de embudo de ventas
"""

import requests
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class CalendlyAPIClient:
    """Cliente para Calendly API v2"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('CALENDLY_API_KEY')
        self.base_url = "https://api.calendly.com"
        self.webhook_secret = os.getenv('CALENDLY_WEBHOOK_SECRET')
        
        if not self.api_key:
            raise ValueError("CALENDLY_API_KEY no configurada")
    
    def get_headers(self) -> Dict[str, str]:
        """Headers para autenticaci??n con Calendly"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_user_info(self) -> Dict[str, any]:
        """Obtiene informaci??n del usuario de Calendly"""
        url = f"{self.base_url}/users/me"
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error obteniendo usuario: {response.status_code}")
            return {}
    
    def get_event_types(self) -> List[Dict[str, any]]:
        """Obtiene tipos de eventos disponibles (masterclass)"""
        url = f"{self.base_url}/event_types"
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            data = response.json()
            return data.get('collection', [])
        else:
            print(f"Error obteniendo tipos de evento: {response.status_code}")
            return []
    
    def get_scheduled_events(self, status: str = "active", count: int = 50) -> List[Dict[str, any]]:
        """Obtiene eventos programados"""
        url = f"{self.base_url}/scheduled_events"
        params = {
            'status': status,
            'count': count,
            'sort': 'start_time'
        }
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('collection', [])
        else:
            print(f"Error obteniendo eventos: {response.status_code}")
            return []
    
    def get_event_details(self, event_uri: str) -> Dict[str, any]:
        """Obtiene detalles de un evento espec??fico"""
        url = f"{self.base_url}/scheduled_events/{event_uri}"
        response = requests.get(url, headers=self.get_headers())
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error obteniendo detalles del evento: {response.status_code}")
            return {}
    
    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """Valida firma del webhook de Calendly"""
        if not self.webhook_secret:
            print("Advertencia: CALENDLY_WEBHOOK_SECRET no configurado")
            return True
        
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

class CalendlyEinsteinKidsIntegration:
    """Integraci??n espec??fica para Einstein Kids"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.calendly_client = CalendlyAPIClient()
        
        # Configuraci??n de eventos para Einstein Kids
        self.event_type_names = {
            'masterclass_moms': 'Masterclass para Mam??s - Einstein Kids',
            'masterclass_therapists': 'Masterclass para Terapeutas - Einstein Kids',
            'discovery_call': 'Llamada de Descubrimiento - Einstein Kids'
        }
    
    def process_booking_created(self, webhook_data: Dict[str, any]) -> Dict[str, any]:
        """Procesa cuando alguien agenda una masterclass"""
        
        event_data = webhook_data.get('payload', {})
        invitee = event_data.get('invitee', {})
        event = event_data.get('event', {})
        
        # Extraer informaci??n del lead
        email = invitee.get('email', '')
        name = invitee.get('name', '')
        phone = self.extract_phone_from_questions(invitee.get('questions_and_answers', []))
        event_type = self.get_event_type_from_uri(event.get('uri', ''))
        event_start = event.get('start_time')
        
        # Determinar tipo de evento y flujo correspondiente
        if 'moms' in event_type.lower() or 'mam??' in event_type.lower():
            lead_type = 'mom'
            funnel_type = 'moms_funnel'
        elif 'therapist' in event_type.lower() or 'terapeuta' in event_type.lower():
            lead_type = 'therapist'
            funnel_type = 'therapists_funnel'
        else:
            lead_type = 'general'
            funnel_type = 'general_funnel'
        
        # Crear o actualizar lead
        lead_data = {
            'email': email,
            'name': name,
            'phone': phone,
            'source': 'calendly',
            'event_type': event_type,
            'event_start_at': event_start,
            'lead_type': lead_type,
            'stage': 'EVENT_BOOKED',
            'score': 50  # Puntuaci??n base por agendar
        }
        
        # Guardar en base de datos
        lead_id = self.create_or_update_lead(lead_data)
        
        # Trigger: Iniciar secuencia de confirmaci??n
        self.trigger_confirmation_sequence(lead_data)
        
        # Trigger: Programar recordatorios
        self.schedule_reminders(lead_data)
        
        return {
            'success': True,
            'lead_id': lead_id,
            'message': f'Lead procesado: {name} ({email})',
            'funnel': funnel_type,
            'next_steps': ['confirmation', 'reminders', 'pre_event_sequence']
        }
    
    def process_booking_cancelled(self, webhook_data: Dict[str, any]) -> Dict[str, any]:
        """Procesa cuando alguien cancela su booking"""
        
        event_data = webhook_data.get('payload', {})
        invitee = event_data.get('invitee', {})
        email = invitee.get('email', '')
        
        # Actualizar lead en BD
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE ek_leads 
            SET stage = 'EVENT_CANCELLED',
                updated_at = NOW()
            WHERE email = %s
            AND stage IN ('EVENT_BOOKED', 'EVENT_CONFIRMED')
            RETURNING lead_id, name;
        """, (email,))
        
        result = cursor.fetchone()
        self.db.commit()
        
        if result:
            lead_id, name = result
            
            # Cancelar jobs programados
            self.cancel_scheduled_jobs(lead_id)
            
            # Notificar a Cyn
            self.notify_cyn_cancellation(email, name)
            
            return {
                'success': True,
                'lead_id': lead_id,
                'message': f'Booking cancelado: {name} ({email})',
                'action': 'cancelled_jobs_and_notified'
            }
        
        return {
            'success': False,
            'message': f'No se encontr?? lead activo para: {email}'
        }
    
    def extract_phone_from_questions(self, questions: List[Dict]) -> str:
        """Extrae tel??fono de las preguntas de Calendly"""
        
        for question in questions:
            question_text = question.get('question', '').lower()
            answer = question.get('answer', '')
            
            if any(keyword in question_text for keyword in ['tel??fono', 'phone', 'whatsapp', 'contacto']):
                # Limpiar y normalizar tel??fono
                phone = ''.join(filter(str.isdigit, answer))
                if len(phone) >= 10:  # Asumir n??mero v??lido
                    return f"+52{phone[-10:]}"  # Formato M??xico
        
        return ''
    
    def get_event_type_from_uri(self, uri: str) -> str:
        """Determina tipo de evento desde URI de Calendly"""
        
        if 'moms' in uri.lower() or 'mama' in uri.lower():
            return 'masterclass_moms'
        elif 'therapist' in uri.lower() or 'terapeuta' in uri.lower():
            return 'masterclass_therapists'
        else:
            return 'discovery_call'
    
    def create_or_update_lead(self, lead_data: Dict) -> str:
        """Crea o actualiza lead en base de datos"""
        
        cursor = self.db.cursor()
        
        # Buscar lead existente por email
        cursor.execute("""
            SELECT lead_id FROM ek_leads 
            WHERE email = %s 
            LIMIT 1;
        """, (lead_data['email'],))
        
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar lead existente
            lead_id = existing[0]
            cursor.execute("""
                UPDATE ek_leads 
                SET name = %s,
                    phone_normalized = %s,
                    source = %s,
                    event_type = %s,
                    event_start_at = %s,
                    lead_type = %s,
                    stage = %s,
                    score = %s,
                    updated_at = NOW()
                WHERE lead_id = %s;
            """, (
                lead_data['name'],
                lead_data['phone'],
                lead_data['source'],
                lead_data['event_type'],
                lead_data['event_start_at'],
                lead_data['lead_type'],
                lead_data['stage'],
                lead_data['score'],
                lead_id
            ))
        else:
            # Crear nuevo lead
            cursor.execute("""
                INSERT INTO ek_leads (
                    email, name, phone_normalized, source, event_type, 
                    event_start_at, lead_type, stage, score, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING lead_id;
            """, (
                lead_data['email'],
                lead_data['name'],
                lead_data['phone'],
                lead_data['source'],
                lead_data['event_type'],
                lead_data['event_start_at'],
                lead_data['lead_type'],
                lead_data['stage'],
                lead_data['score']
            ))
            
            lead_id = cursor.fetchone()[0]
        
        # Registrar evento
        cursor.execute("""
            INSERT INTO ek_lead_events (lead_id, event_type, payload)
            VALUES (%s, 'calendly_booking', %s);
        """, (lead_id, json.dumps(lead_data)))
        
        self.db.commit()
        return lead_id
    
    def trigger_confirmation_sequence(self, lead_data: Dict):
        """Trigger: Inicia secuencia de confirmaci??n"""
        
        # Determinar qu?? secuencia usar basado en el tipo de lead
        if lead_data['lead_type'] == 'mom':
            sequence_type = 'M10_pre_event_sequence'
        elif lead_data['lead_type'] == 'therapist':
            sequence_type = 'T10_pre_event_sequence'
        else:
            sequence_type = 'general_confirmation'
        
        # Programar secuencia en Windmill
        self.schedule_windmill_job(
            script_path=f"f/einstein_kids/{lead_data['lead_type']}s/{sequence_type}.py",
            lead_phone=lead_data['phone'],
            event_datetime=lead_data['event_start_at']
        )
    
    def schedule_reminders(self, lead_data: Dict):
        """Programa recordatorios para el evento"""
        
        from datetime import datetime, timedelta
        
        event_time = datetime.fromisoformat(lead_data['event_start_at'])
        
        # Calcular tiempos de recordatorio
        reminders = [
            {'hours_before': 24, 'template': 'reminder_24h'},
            {'hours_before': 1, 'template': 'reminder_1h'},
            {'minutes_before': 10, 'template': 'reminder_10m'}
        ]
        
        for reminder in reminders:
            if 'hours_before' in reminder:
                send_time = event_time - timedelta(hours=reminder['hours_before'])
            else:
                send_time = event_time - timedelta(minutes=reminder['minutes_before'])
            
            # Programar env??o de recordatorio
            self.schedule_windmill_job(
                script_path="f/einstein_kids/shared/ycloud_send_template.py",
                lead_phone=lead_data['phone'],
                template_name=reminder['template'],
                scheduled_time=send_time
            )
    
    def schedule_windmill_job(self, script_path: str, **kwargs):
        """Programa un job en Windmill"""
        # Esta funci??n se conectar??a con Windmill para programar jobs
        # Por ahora es un placeholder
        print(f"Job programado: {script_path} con args: {kwargs}")
    
    def cancel_scheduled_jobs(self, lead_id: str):
        """Cancela jobs programados para un lead"""
        # Implementar cancelaci??n de jobs en Windmill
        print(f"Jobs cancelados para lead: {lead_id}")
    
    def notify_cyn_cancellation(self, email: str, name: str):
        """Notifica a Cyn sobre cancelaci??n"""
        # Enviar notificaci??n a Cyn (email, WhatsApp, dashboard)
        print(f"Notificaci??n: {name} ({email}) cancel?? su cita")
    
    def get_booking_stats(self, days: int = 30) -> Dict[str, any]:
        """Obtiene estad??sticas de booking"""
        
        cursor = self.db.cursor()
        
        # Total de bookings en el per??odo
        cursor.execute("""
            SELECT COUNT(*) as total_bookings,
                   COUNT(CASE WHEN stage = 'EVENT_BOOKED' THEN 1 END) as active,
                   COUNT(CASE WHEN stage = 'EVENT_CANCELLED' THEN 1 END) as cancelled,
                   COUNT(CASE WHEN stage = 'EVENT_ATTENDED' THEN 1 END) as attended
            FROM ek_leads 
            WHERE source = 'calendly'
            AND created_at >= NOW() - INTERVAL '%s days';
        """, (days,))
        
        stats = cursor.fetchone()
        
        # Por tipo de evento
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM ek_leads 
            WHERE source = 'calendly'
            AND created_at >= NOW() - INTERVAL '%s days'
            GROUP BY event_type;
        """, (days,))
        
        by_type = cursor.fetchall()
        
        return {
            'total_bookings': stats[0],
            'active_bookings': stats[1],
            'cancelled_bookings': stats[2],
            'attended_bookings': stats[3],
            'conversion_rate': (stats[3] / max(stats[0], 1)) * 100,
            'by_event_type': {row[0]: row[1] for row in by_type}
        }

# Funci??n principal para Windmill
def main(webhook_type: str, webhook_data: Dict[str, any]):
    """
    Procesa webhooks de Calendly
    
    Args:
        webhook_type: 'booking_created' o 'booking_cancelled'
        webhook_data: Datos del webhook de Calendly
    """
    import psycopg2
    import os
    
    # Conectar a BD
    conn = psycopg2.connect(
        host=os.getenv('PGHOST', 'localhost'),
        port=os.getenv('PGPORT', '5432'),
        user=os.getenv('POSTGRES_USER', 'windmill'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB', 'windmill')
    )
    
    try:
        calendly_integration = CalendlyEinsteinKidsIntegration(conn)
        
        if webhook_type == 'booking_created':
            result = calendly_integration.process_booking_created(webhook_data)
        elif webhook_type == 'booking_cancelled':
            result = calendly_integration.process_booking_cancelled(webhook_data)
        else:
            result = {
                'success': False,
                'error': f'Tipo de webhook no soportado: {webhook_type}'
            }
        
        # Agregar estad??sticas
        stats = calendly_integration.get_booking_stats()
        result['booking_stats'] = stats
        
        return result
        
    finally:
        conn.close()
