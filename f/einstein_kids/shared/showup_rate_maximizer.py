"""
Sistema de Show-up Rate Maximization (60-70%) para Masterclass EN VIVO
Basado en arquitectura 2025 - A.I.M. Model
"""

import datetime
from typing import Dict, List
from dataclasses import dataclass

@dataclass 
class ShowUpSequence:
    name: str
    trigger_time: datetime.datetime
    message_type: str
    content: str
    channel: str  # whatsapp, email, sms
    urgency_level: int  # 1-5

class ShowUpRateMaximizer:
    """
    Sistema completo para maximizar asistencia a masterclass en vivo
    Target: 60-70% show-up rate vs 35-45% industry standard
    """
    
    def __init__(self):
        self.sequences = {}
        self.urgency_triggers = {
            "registration": 1,
            "confirmation": 2, 
            "24h_reminder": 3,
            "1h_reminder": 4,
            "10min_reminder": 5,
            "live_now": 5
        }
    
    def create_showup_sequence(self, lead_data: Dict, event_datetime: datetime.datetime) -> List[ShowUpSequence]:
        """Crea secuencia personalizada A.I.M. para maximizar asistencia"""
        
        baby_age = lead_data.get('baby_age_months', 0)
        lead_name = lead_data.get('name', 'Mamá')
        phone = lead_data.get('phone')
        
        sequences = []
        
        # === FASE A: ACKNOWLEDGE (Días -3 a -1) ===
        
        # Inmediato después del registro
        sequences.append(ShowUpSequence(
            name="welcome_confirmation",
            trigger_time=datetime.datetime.now() + datetime.timedelta(minutes=5),
            message_type="acknowledge",
            content=self.get_welcome_message(baby_age, lead_name),
            channel="whatsapp",
            urgency_level=1
        ))
        
        # Día -2: Valor pre-evento
        sequences.append(ShowUpSequence(
            name="value_bomb",
            trigger_time=event_datetime - datetime.timedelta(days=2, hours=10),
            message_type="acknowledge", 
            content=f"{lead_name}, ¿sabías que bebés de {baby_age} meses pueden estimularse 50% más rápido? Te comparto 3 ejercicios que puedes hacer HOY 👶✨",
            channel="whatsapp",
            urgency_level=2
        ))
        
        # === FASE I: INCLUDE (Día -1) ===
        
        # Día -1: Sentido de comunidad
        sequences.append(ShowUpSequence(
            name="community_belonging",
            trigger_time=event_datetime - datetime.timedelta(days=1, hours=8),
            message_type="include",
            content=f"{lead_name}, más de 200 mamás con bebés de {baby_age} meses ya confirmaron su asistencia. ¿Lista para conocerlas? 💕",
            channel="whatsapp", 
            urgency_level=3
        ))
        
        # === FASE M: MOBILIZE (Día del evento) ===
        
        # 24h antes - Recordatorio emocional
        sequences.append(ShowUpSequence(
            name="24h_emotional_reminder",
            trigger_time=event_datetime - datetime.timedelta(hours=24),
            message_type="mobilize",
            content=self.get_24h_reminder(baby_age, lead_name),
            channel="whatsapp",
            urgency_level=3
        ))
        
        # 1h antes - Últimos preparativos
        sequences.append(ShowUpSequence(
            name="1h_final_prep",
            trigger_time=event_datetime - datetime.timedelta(hours=1),
            message_type="mobilize",
            content=f"🚨 {lead_name}, faltan 60 minutos. Tienes todo listo? Copita de café ☕, cuaderno 📝, y tu bebé cerca?",
            channel="whatsapp",
            urgency_level=4
        ))
        
        # 10min antes - Urgencia máxima
        sequences.append(ShowUpSequence(
            name="10min_urgency_peak",
            trigger_time=event_datetime - datetime.timedelta(minutes=10),
            message_type="mobilize",
            content=f"🔥 {lead_name}, YA ESTAMOS EN VIVO! Entra ahora antes de que comience. Link: [ZOOM_LINK]",
            channel="whatsapp",
            urgency_level=5
        ))
        
        # Momento exacto - LIVE NOW
        sequences.append(ShowUpSequence(
            name="live_now_alert",
            trigger_time=event_datetime,
            message_type="mobilize",
            content=f"🎬 ESTAMOS EN VIVO Ahora! {lead_name}, tu bebé de {baby_age} meses va a tener un desarrollo acelerado hoy. ¡ENTRA YA! 👉 [ZOOM_LINK]",
            channel="whatsapp",
            urgency_level=5
        ))
        
        return sequences
    
    def get_welcome_message(self, baby_age: int, name: str) -> str:
        """Mensaje de bienvenida personalizado por edad"""
        
        if baby_age <= 3:
            return f"¡Bienvenida {name}! 🌟 Veo que tu bebé tiene {baby_age} meses. Es el momento MÁGICO para estimular su desarrollo. Guarda este chat, te enviaré recordatorios importantes. ¿Emocionada?"
        elif baby_age <= 6:
            return f"¡Hola {name}! 💕 Tu bebé de {baby_age} meses está en la etapa PERFECTA. En la masterclass te mostraré ejercicios que potenciarán su desarrollo motriz. ¿Lista?"
        elif baby_age <= 12:
            return f"¡Qué emoción {name}! 👶 Tu bebé de {baby_age} meses está listo para técnicas avanzadas. La masterclass será reveladora. Guarda este número."
        else:
            return f"¡Bienvenida {name}! 🧠 Veo que tu bebé tiene más de 1 año. La masterclass tiene técnicas específicas para su etapa. ¡Será increíble!"
    
    def get_24h_reminder(self, baby_age: int, name: str) -> str:
        """Recordatorio 24h emocionalmente cargado"""
        
        base_message = f"{name}, mañana a esta hora tu bebé de {baby_age} meses estará experimentando un desarrollo acelerado 🚀"
        
        if baby_age <= 3:
            specific = "¿Te imaginas ver cómo tu bebé responde a los estímulos por primera vez?"
        elif baby_age <= 6:
            specific = "¿Listas para ver cómo tu bebé empieza a sentarse más fuerte y seguro?"
        elif baby_age <= 12:
            specific = "¿Emocionada por ver cómo tu bebé da sus primeros pasos más rápido?"
        else:
            specific = "¿Lista para potenciar el desarrollo cognitivo de tu pequeño?"
            
        return f"{base_message}\n\n{specific}\n\n⏰ Faltan 24 horas. ¿Confirmas tu asistencia?"
    
    def get_behavioral_triggers(self) -> Dict:
        """Triggers basados en comportamiento para mensajes adicionales"""
        
        return {
            "opened_multiple_times": {
                "condition": "lead_opened_confirmation > 3",
                "message": "Veo que has revisado la confirmación varias veces 😊 ¿Tienes dudas? Responde DUDAS y te ayudo.",
                "timing": "immediate"
            },
            "no_response_48h": {
                "condition": "no_response_48h",
                "message": "Hola 👋 Solo quiero confirmar que recibiste toda la info. Responde CONFIRMADO si estás lista para mañana.",
                "timing": "immediate"
            },
            "group_joiner": {
                "condition": "joined_whatsapp_group",
                "message": "¡Genial que te uniste al grupo! 💕 Las otras mamás están emocionadas. ¿Nos vemos mañana?",
                "timing": "immediate"
            }
        }
    
    def calculate_showup_probability(self, lead_data: Dict) -> float:
        """Calcula probabilidad de asistencia basada en comportamiento"""
        
        score = 50  # Base score
        
        # Factores positivos
        if lead_data.get('opened_confirmation', 0) > 2:
            score += 15
        if lead_data.get('joined_whatsapp_group', False):
            score += 20
        if lead_data.get('asked_questions', 0) > 0:
            score += 15
        if lead_data.get('baby_age_months', 0) <= 6:  # Mayor urgencia
            score += 10
            
        # Factores negativos  
        if lead_data.get('no_response_days', 0) > 3:
            score -= 25
        if lead_data.get('declined_previous_events', 0) > 0:
            score -= 20
            
        return min(score, 95)  # Max 95%
    
    def get_intervention_sequence(self, probability: float) -> List[Dict]:
        """Secuencia de intervención para leads de baja probabilidad"""
        
        if probability >= 70:
            return []  # No intervention needed
            
        interventions = []
        
        if probability < 40:
            # Alta intervención
            interventions.append({
                "type": "personal_call",
                "message": "¿Podemos hablar 5 min? Tengo algo especial para tu bebé.",
                "channel": "whatsapp",
                "timing": "immediate"
            })
            
        elif probability < 60:
            # Media intervención
            interventions.append({
                "type": "social_proof",
                "message": "Mira lo que logró María con su bebé de la misma edad...",
                "channel": "whatsapp", 
                "timing": "immediate"
            })
            
        else:  # 60-70%
            # Baja intervención
            interventions.append({
                "type": "reminder_boost",
                "message": "No olvides mañana 🙏 Tu bebé te lo va a agradecer.",
                "channel": "whatsapp",
                "timing": "4h_before"
            })
            
        return interventions
    
    def generate_urgency_escalation(self, hours_before: int, lead_data: Dict) -> str:
        """Genera mensajes de urgencia escalonada"""
        
        name = lead_data.get('name', 'Mamá')
        baby_age = lead_data.get('baby_age_months', 0)
        
        if hours_before <= 24:
            return f"⏰ {name}, faltan {hours_before}h. Los spots se están llenando..."
        elif hours_before <= 4:
            return f"🔥 {name}, últimas horas! ¿Confirmas tu asistencia?"
        elif hours_before <= 1:
            return f"🚨 {name}, YA ESTAMOS EN VIVO! Únete ahora 👉"
        else:
            return f"{name}, faltan {hours_before}h para transformar el desarrollo de tu bebé 🚀"
    
    def track_sequence_performance(self, lead_phone: str, sequence_name: str, action_taken: str):
        """Tracking de performance de cada mensaje"""
        
        # Guardar en base de datos para optimización
        performance_data = {
            "phone": lead_phone,
            "sequence": sequence_name,
            "action": action_taken,  # opened, clicked, replied, attended
            "timestamp": datetime.datetime.now(),
            "baby_age": self.get_lead_baby_age(lead_phone)
        }
        
        # Actualizar modelo de predicción
        self.update_prediction_model(performance_data)
        
    def get_optimized_timing(self, lead_phone: str) -> datetime.datetime:
        """Obtiene mejor hora para enviar basada en histórico"""
        
        # Analizar cuando el lead suele responder
        historical_data = self.get_lead_response_history(lead_phone)
        
        if historical_data:
            # Encontrar hora óptima (ej: 7-9PM suele ser mejor)
            optimal_hour = self.calculate_optimal_hour(historical_data)
            return datetime.datetime.now().replace(hour=optimal_hour, minute=0)
        
        # Default: 7PM
        return datetime.datetime.now().replace(hour=19, minute=0)
    
    # Métodos auxiliares
    def get_lead_baby_age(self, phone: str) -> int:
        """Obtiene edad del bebé del lead"""
        # Consultar base de datos
        pass
        
    def get_lead_response_history(self, phone: str) -> Dict:
        """Obtiene historial de respuestas del lead"""
        # Consultar base de datos
        pass
        
    def calculate_optimal_hour(self, historical_data: Dict) -> int:
        """Calcula hora óptima basada en respuestas previas"""
        # Análisis de datos históricos
        pass
        
    def update_prediction_model(self, performance_data: Dict):
        """Actualiza modelo ML de predicción"""
        # Machine learning para mejorar predicciones
        pass