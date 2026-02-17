"""
Sistema de Tracking para Masterclass EN VIVO
Adaptado de la arquitectura 2025 para show-up rate 60-70%
"""

import json
import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class MasterclassStatus(Enum):
    REGISTERED = "registered"
    CONFIRMED = "confirmed" 
    ATTENDED = "attended"
    NO_SHOW = "no_show"
    LEFT_EARLY = "left_early"
    STAYED_FULL = "stayed_full"

@dataclass
class LiveTrackingEvent:
    lead_id: str
    phone: str
    registration_time: datetime.datetime
    event_start: datetime.datetime
    check_in_time: Optional[datetime.datetime] = None
    exit_time: Optional[datetime.datetime] = None
    engagement_score: int = 0  # 0-100
    questions_asked: int = 0
    chat_messages: int = 0
    poll_responses: int = 0

class MasterclassLiveTracker:
    """
    Tracking en tiempo real para masterclass en vivo
    Sistema Godfather Offer para ticket medio
    """
    
    def __init__(self):
        self.active_sessions = {}
        self.engagement_thresholds = {
            "hot_lead": 70,      # Preguntó + participó
            "warm_lead": 40,     # Se quedó 45+ minutos
            "cold_lead": 20      # Entró pero salió temprano
        }
    
    def track_registration(self, lead_data: Dict) -> str:
        """Tracking inicial del registro"""
        tracking_id = f"MC_{lead_data['phone']}_{int(datetime.datetime.now().timestamp())}"
        
        session = LiveTrackingEvent(
            lead_id=lead_data['lead_id'],
            phone=lead_data['phone'],
            registration_time=datetime.datetime.now(),
            event_start=self.calculate_event_datetime()
        )
        
        self.active_sessions[tracking_id] = session
        return tracking_id
    
    def track_check_in(self, tracking_id: str, phone: str) -> bool:
        """Tracking cuando entra a la masterclass"""
        if tracking_id in self.active_sessions:
            session = self.active_sessions[tracking_id]
            session.check_in_time = datetime.datetime.now()
            
            # Trigger: Asistencia confirmada
            self.trigger_post_checkin_sequence(session)
            return True
        return False
    
    def track_engagement(self, tracking_id: str, event_type: str, data: Dict):
        """Tracking de participación en tiempo real"""
        if tracking_id not in self.active_sessions:
            return
            
        session = self.active_sessions[tracking_id]
        
        if event_type == "question_asked":
            session.questions_asked += 1
            session.engagement_score += 25
            
        elif event_type == "chat_message":
            session.chat_messages += 1
            session.engagement_score += 10
            
        elif event_type == "poll_response":
            session.poll_responses += 1  
            session.engagement_score += 15
            
        elif event_type == "time_spent":
            minutes = data.get('minutes', 0)
            session.engagement_score += min(minutes * 2, 40)  # Max 40 puntos por tiempo
    
    def calculate_lead_temperature(self, tracking_id: str) -> str:
        """Clasificación del lead basada en comportamiento"""
        if tracking_id not in self.active_sessions:
            return "unknown"
            
        session = self.active_sessions[tracking_id]
        score = session.engagement_score
        
        if score >= self.engagement_thresholds["hot_lead"]:
            return "HOT"      # Listo para cierre
        elif score >= self.engagement_thresholds["warm_lead"]:
            return "WARM"     # Necesita seguimiento
        else:
            return "COLD"     # Necesita nutrición
    
    def trigger_post_checkin_sequence(self, session: LiveTrackingEvent):
        """Secuencia post-checkin (A.I.M. modelo)"""
        from datetime import timedelta
        
        # Acknowledge: Inmediato
        self.send_whatsapp_message(
            session.phone,
            f"¡Bienvenida {session.lead_id}! 🎉 Veo que ya estás en la masterclass. Tu bebé de X meses va a tener un desarrollo acelerado hoy..."
        )
        
        # Include: 15 minutos después
        self.schedule_message(
            session.phone,
            "¿Sabías que mamás con bebés de la misma edad que el tuyo ya están viendo resultados? Únete al chat...",
            delay_minutes=15
        )
        
        # Mobilize: Antes del cierre
        self.schedule_message(
            session.phone,
            "En 10 minutos revelaré la oferta especial solo para asistentes. Estate atenta...",
            delay_minutes=75  # 10 min antes de final
        )
    
    def generate_godfather_offer(self, lead_temp: str, baby_age: int) -> Dict:
        """Godfather Offer adaptativa por temperatura del lead"""
        
        base_offer = {
            "main_product": "Masterclass Desarrollo Infantil + Acompañamiento 30 días",
            "base_price": 1997,
            "payment_options": [
                {"option": "Pago único", "price": 1997, "savings": 0},
                {"option": "3 pagos", "price": 665, "frequency": "mensual"}
            ]
        }
        
        if lead_temp == "HOT":
            # Stack masivo para leads calientes
            return {
                **base_offer,
                "bonuses": [
                    {"name": "Guía Estimulación 0-12 meses", "value": 497},
                    {"name": "Comunidad VIP WhatsApp", "value": 297},
                    {"name": "1:1 con Cyn (30 min)", "value": 997},
                    {"name": "Grabación Masterclass", "value": 197},
                    {"name": "Bonus Sorpresa Bebé", "value": 147}
                ],
                "total_value": 4135,
                "scarcity": "Solo 10 spots para esta cohort",
                "guarantee": "30 días o devolución completa"
            }
        
        elif lead_temp == "WARM":
            # Stack moderado
            return {
                **base_offer,
                "bonuses": [
                    {"name": "Guía Estimulación", "value": 497},
                    {"name": "Comunidad WhatsApp", "value": 297},
                    {"name": "Grabación", "value": 197}
                ],
                "total_value": 2988,
                "scarcity": "15 spots disponibles"
            }
        
        else:  # COLD
            # Stack básico
            return {
                **base_offer,
                "bonuses": [
                    {"name": "Guía Estimulación", "value": 497},
                    {"name": "Grabación", "value": 197}
                ],
                "total_value": 2691,
                "scarcity": "Acceso por tiempo limitado"
            }
    
    def calculate_event_datetime(self) -> datetime.datetime:
        """Calcula próximo evento en vivo (ej: martes 7PM)"""
        now = datetime.datetime.now()
        
        # Próximo martes 7PM
        days_ahead = 1 - now.weekday()  # 1 = martes
        if days_ahead <= 0:
            days_ahead += 7
            
        next_tuesday = now + timedelta(days=days_ahead)
        event_time = next_tuesday.replace(hour=19, minute=0, second=0, microsecond=0)
        
        return event_time
    
    def send_whatsapp_message(self, phone: str, message: str):
        """Envío de WhatsApp (integración con YCloud)"""
        # Integración con sistema existente
        pass
    
    def schedule_message(self, phone: str, message: str, delay_minutes: int):
        """Programa mensajes para secuencia A.I.M."""
        # Usar sistema de jobs de Windmill
        pass
    
    def get_session_summary(self, tracking_id: str) -> Dict:
        """Resumen para dashboard y cierre"""
        if tracking_id not in self.active_sessions:
            return {}
            
        session = self.active_sessions[tracking_id]
        temp = self.calculate_lead_temperature(tracking_id)
        
        return {
            "lead_temperature": temp,
            "engagement_score": session.engagement_score,
            "time_spent_minutes": self.calculate_time_spent(session),
            "questions_asked": session.questions_asked,
            "recommended_action": self.get_recommended_action(temp),
            "godfather_offer": self.generate_godfather_offer(temp, 6)  # baby_age dinámico
        }
    
    def calculate_time_spent(self, session: LiveTrackingEvent) -> int:
        """Calcula minutos en el evento"""
        if not session.check_in_time:
            return 0
            
        end_time = session.exit_time or datetime.datetime.now()
        duration = end_time - session.check_in_time
        return int(duration.total_seconds() / 60)
    
    def get_recommended_action(self, temp: str) -> str:
        """Acción recomendada para cierre"""
        actions = {
            "HOT": "Llamada de cierre inmediata - Enviar link de pago",
            "WARM": "WhatsApp personalizado con caso de éxito + link de pago",
            "COLD": "Enviar resumen + testimonios + link con descuento"
        }
        return actions.get(temp, "Seguimiento general")