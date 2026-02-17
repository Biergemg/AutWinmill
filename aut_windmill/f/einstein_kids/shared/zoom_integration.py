"""
Zoom API Integration para Einstein Kids
Conecta con Zoom para obtener asistencia real de los webinars
"""

import requests
import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os

class ZoomAPIClient:
    """Cliente para Zoom API v2"""
    
    def __init__(self):
        self.api_key = os.getenv('ZOOM_API_KEY')
        self.api_secret = os.getenv('ZOOM_API_SECRET')
        self.base_url = "https://api.zoom.us/v2"
        
    def generate_jwt_token(self) -> str:
        """Genera JWT token para autenticaci??n"""
        payload = {
            'iss': self.api_key,
            'exp': int(time.time()) + 3600  # 1 hora
        }
        return jwt.encode(payload, self.api_secret, algorithm='HS256')
    
    def get_meeting_participants(self, meeting_id: str) -> List[Dict[str, Any]]:
        """Obtiene participantes de una reuni??n/zoom"""
        token = self.generate_jwt_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/report/meetings/{meeting_id}/participants"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('participants', [])
        else:
            print(f"Error obteniendo participantes: {response.status_code}")
            return []
    
    def get_meeting_details(self, meeting_id: str) -> Dict[str, Any]:
        """Obtiene detalles de una reuni??n"""
        token = self.generate_jwt_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/meetings/{meeting_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error obteniendo detalles: {response.status_code}")
            return {}
    
    def get_past_meetings(self, user_id: str = "me", days: int = 30) -> List[Dict[str, Any]]:
        """Obtiene reuniones pasadas de un usuario"""
        token = self.generate_jwt_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'page_size': 100
        }
        
        url = f"{self.base_url}/users/{user_id}/meetings"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('meetings', [])
        else:
            print(f"Error obteniendo reuniones: {response.status_code}")
            return []

class ZoomAttendanceProcessor:
    """Procesa asistencia de Zoom para Einstein Kids"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.zoom_client = ZoomAPIClient()
        self.attendance_threshold = 45  # minutos para considerar asistencia
    
    def process_meeting_attendance(self, meeting_id: str, event_start_at: datetime):
        """Procesa asistencia de una reuni??n espec??fica"""
        participants = self.zoom_client.get_meeting_participants(meeting_id)
        
        if not participants:
            print(f"No hay participantes para la reuni??n {meeting_id}")
            return
        
        # Obtener leads que deber??an haber asistido
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT lead_id, email, phone_normalized, name
            FROM ek_leads 
            WHERE DATE(event_start_at) = DATE(%s)
            AND stage IN ('EVENT_REGISTERED', 'REMINDER_SENT')
        """, (event_start_at,))
        
        expected_leads = cursor.fetchall()
        
        # Procesar cada participante
        attendance_records = []
        for participant in participants:
            email = participant.get('user_email', '').lower()
            name = participant.get('name', '')
            join_time = participant.get('join_time')
            leave_time = participant.get('leave_time')
            duration = participant.get('duration', 0)
            
            # Buscar lead por email o nombre
            lead_info = self.find_matching_lead(email, name, expected_leads)
            
            if lead_info:
                status = 'attended' if duration >= self.attendance_threshold else 'partial'
                
                attendance_records.append({
                    'lead_id': lead_info['lead_id'],
                    'meeting_id': meeting_id,
                    'status': status,
                    'duration_minutes': duration,
                    'join_time': join_time,
                    'leave_time': leave_time
                })
                
                # Actualizar lead en BD
                self.update_lead_attendance(lead_info['lead_id'], status, duration)
        
        # Marcar no-shows
        self.mark_no_shows(event_start_at, attendance_records)
        
        return attendance_records
    
    def find_matching_lead(self, email: str, name: str, expected_leads: List) -> Dict[str, Any]:
        """Encuentra el lead que corresponde al participante"""
        # Buscar por email exacto
        for lead in expected_leads:
            if email and lead[1] and email.lower() == lead[1].lower():
                return {
                    'lead_id': lead[0],
                    'email': lead[1],
                    'phone': lead[2],
                    'name': lead[3]
                }
        
        # Buscar por nombre aproximado
        for lead in expected_leads:
            lead_name = lead[3].lower() if lead[3] else ''
            participant_name = name.lower() if name else ''
            
            if lead_name and participant_name:
                # Coincidencia parcial
                if lead_name in participant_name or participant_name in lead_name:
                    return {
                        'lead_id': lead[0],
                        'email': lead[1],
                        'phone': lead[2],
                        'name': lead[3]
                    }
        
        return None
    
    def update_lead_attendance(self, lead_id: str, status: str, duration: int):
        """Actualiza el estado del lead basado en asistencia"""
        cursor = self.db.cursor()
        
        new_stage = 'EVENT_ATTENDED' if status == 'attended' else 'EVENT_PARTIAL'
        
        cursor.execute("""
            UPDATE ek_leads 
            SET stage = %s, 
                updated_at = NOW()
            WHERE lead_id = %s;
        """, (new_stage, lead_id))
        
        # Registrar evento
        cursor.execute("""
            INSERT INTO ek_lead_events (lead_id, event_type, payload)
            VALUES (%s, %s, %s);
        """, (lead_id, 'zoom_attendance', json.dumps({
            'status': status,
            'duration_minutes': duration,
            'meeting_id': 'zoom_meeting_id',
            'timestamp': datetime.now().isoformat()
        })))
        
        self.db.commit()
        
        print(f"Lead {lead_id} actualizado: {status} ({duration} min)")
    
    def mark_no_shows(self, event_date: datetime, attendance_records: List[Dict]):
        """Marca como no-show a los leads que no asistieron"""
        attended_lead_ids = [record['lead_id'] for record in attendance_records]
        
        if not attended_lead_ids:
            attended_lead_ids = ['00000000-0000-0000-0000-000000000000']  # Dummy para SQL
        
        cursor = self.db.cursor()
        
        cursor.execute("""
            UPDATE ek_leads 
            SET stage = 'EVENT_NO_SHOW',
                updated_at = NOW()
            WHERE DATE(event_start_at) = DATE(%s)
            AND stage IN ('EVENT_REGISTERED', 'REMINDER_SENT')
            AND lead_id NOT IN %s;
        """, (event_date, tuple(attended_lead_ids)))
        
        # Registrar eventos de no-show
        cursor.execute("""
            SELECT lead_id FROM ek_leads 
            WHERE DATE(event_start_at) = DATE(%s)
            AND stage = 'EVENT_NO_SHOW'
            AND lead_id NOT IN %s;
        """, (event_date, tuple(attended_lead_ids)))
        
        no_shows = cursor.fetchall()
        
        for (lead_id,) in no_shows:
            cursor.execute("""
                INSERT INTO ek_lead_events (lead_id, event_type, payload)
                VALUES (%s, %s, %s);
            """, (lead_id, 'zoom_no_show', json.dumps({
                'reason': 'did_not_attend',
                'timestamp': datetime.now().isoformat()
            })))
        
        self.db.commit()
        
        print(f"Marcados {len(no_shows)} no-shows")
    
    def get_attendance_report(self, event_date: datetime) -> Dict[str, Any]:
        """Genera reporte de asistencia para un evento"""
        cursor = self.db.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registrados,
                COUNT(CASE WHEN stage = 'EVENT_ATTENDED' THEN 1 END) as asistieron,
                COUNT(CASE WHEN stage = 'EVENT_NO_SHOW' THEN 1 END) as no_show,
                COUNT(CASE WHEN stage = 'EVENT_PARTIAL' THEN 1 END) as parcial
            FROM ek_leads 
            WHERE DATE(event_start_at) = DATE(%s);
        """, (event_date,))
        
        stats = cursor.fetchone()
        
        total, asistieron, no_show, parcial = stats
        
        return {
            'fecha': event_date.strftime('%Y-%m-%d'),
            'total_registrados': total,
            'asistieron': asistieron,
            'no_show': no_show,
            'parcial': parcial,
            'tasa_asistencia': round((asistieron / max(total, 1)) * 100, 1),
            'tasa_no_show': round((no_show / max(total, 1)) * 100, 1)
        }

# Funci??n principal para Windmill
def main(meeting_id: str, event_start_at: str):
    """
    Procesa asistencia de Zoom para Einstein Kids
    
    Args:
        meeting_id: ID de la reuni??n en Zoom
        event_start_at: Fecha/hora del evento (ISO format)
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
        processor = ZoomAttendanceProcessor(conn)
        
        # Procesar asistencia
        from datetime import datetime
        event_date = datetime.fromisoformat(event_start_at)
        
        attendance_records = processor.process_meeting_attendance(meeting_id, event_date)
        
        # Generar reporte
        report = processor.get_attendance_report(event_date)
        
        print(f"Asistencia procesada para {event_date.strftime('%Y-%m-%d')}")
        print(f"Participantes procesados: {len(attendance_records)}")
        print(f"Tasa de asistencia: {report['tasa_asistencia']}%")
        
        return {
            'success': True,
            'attendance_records': len(attendance_records),
            'report': report
        }
        
    finally:
        conn.close()
