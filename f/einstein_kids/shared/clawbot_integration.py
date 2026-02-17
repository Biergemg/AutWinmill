"""
Clawbot.ai Integration para Einstein Kids
Agente AI con guardrails y seguridad para responder como Cyn
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import hashlib
import hmac

class ClawbotEinsteinKids:
    """Integración con clawbot.ai para Einstein Kids"""
    
    def __init__(self):
        self.api_key = os.getenv('CLAWBOT_API_KEY')
        self.api_secret = os.getenv('CLAWBOT_API_SECRET')
        self.base_url = os.getenv('CLAWBOT_BASE_URL', 'https://api.clawbot.ai')
        self.knowledge_base = self.load_knowledge_context()
        
    def load_knowledge_context(self) -> Dict[str, Any]:
        """Carga contexto específico de Einstein Kids"""
        return {
            "business_context": {
                "name": "Einstein Kids",
                "type": "Desarrollo Infantil Temprano",
                "target": "Mamás de bebés 0-3 años",
                "specialist": "Cynthia Rodriguez",
                "experience": "8+ años",
                "method": "Estimulación temprana basada en neurociencia"
            },
            "guardrails": {
                "no_medical_advice": True,
                "no_diagnosis": True,
                "escalate_emergencies": True,
                "maintain_empathy": True,
                "personalize_by_age": True,
                "avoid_pressure": True
            },
            "response_guidelines": {
                "tone": "amigable, profesional, empática",
                "language": "español neutro, evitar tecnicismos",
                "approach": "escuchar primero, entender, ofrecer soluciones",
                "always_offer_value": True,
                "include_cta": False  # No presionar por venta
            }
        }
    
    def generate_secure_response(self, message: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Genera respuesta segura usando clawbot.ai"""
        
        # Preparar contexto completo
        context = self.build_clawbot_context(message, lead_context)
        
        # Llamar a clawbot.ai API
        try:
            response = self.call_clawbot_api(context)
            
            # Aplicar guardrails
            safe_response = self.apply_guardrails(response, lead_context)
            
            # Verificar si necesita escalación
            needs_escalation = self.check_escalation_needed(message, safe_response, lead_context)
            
            return {
                "success": True,
                "response": safe_response["text"],
                "confidence": safe_response.get("confidence", 0.8),
                "needs_escalation": needs_escalation,
                "escalation_reason": safe_response.get("escalation_reason"),
                "suggested_actions": safe_response.get("suggested_actions", []),
                "metadata": {
                    "original_response": response,
                    "guardrails_applied": safe_response.get("guardrails_applied", []),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "fallback_response": self.get_fallback_response(lead_context),
                "needs_escalation": True,
                "escalation_reason": "clawbot_error"
            }
    
    def build_clawbot_context(self, message: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Construye contexto completo para clawbot"""
        
        # Información del lead
        lead_info = {
            "name": lead_context.get("name", "Mamá"),
            "baby_age_months": self.estimate_baby_age(lead_context),
            "stage": lead_context.get("stage", "new_lead"),
            "score": lead_context.get("score", 0),
            "previous_interactions": lead_context.get("interaction_history", []),
            "preferences": lead_context.get("preferences", {})
        }
        
        # Contexto de negocio
        business_context = {
            "business_type": "educational_service",
            "product": "masterclass_desarrollo_infantil",
            "price_range": "1997-9997_MXN",
            "specialist": "Cynthia_Rodriguez",
            "methodology": "estimulacion_temprana_neurociencia",
            "target_audience": "mamás_bebeés_0_3_años"
        }
        
        # Reglas de respuesta
        response_rules = {
            "tone": "empático, profesional, sin presión",
            "avoid": ["diagnósticos médicos", "promesas específicas", "comparaciones negativas"],
            "include": ["valor educativo", "experiencia personal", "empatía"],
            "call_to_action": "suave, orientado a valor",
            "escalation_triggers": ["emergencia", "problema médico", "depresión", "crisis"]
        }
        
        return {
            "message": message,
            "lead_info": lead_info,
            "business_context": business_context,
            "response_rules": response_rules,
            "knowledge_base": self.knowledge_base,
            "timestamp": datetime.now().isoformat(),
            "request_id": self.generate_request_id()
        }
    
    def call_clawbot_api(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Llama a clawbot.ai API"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Request-Signature": self.generate_signature(context)
        }
        
        payload = {
            "context": context,
            "mode": "conversational",
            "personality": "cyn_einstein_kids",
            "temperature": 0.7,
            "max_tokens": 500,
            "language": "es",
            "safety_mode": "strict"
        }
        
        response = requests.post(
            f"{self.base_url}/v1/generate",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Clawbot API error: {response.status_code} - {response.text}")
    
    def apply_guardrails(self, response: Dict[str, Any], lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica guardrails de seguridad"""
        
        guardrails_applied = []
        safe_response = response.copy()
        
        # Guardrail 1: No medical advice
        if self.contains_medical_advice(response.get("text", "")):
            safe_response["text"] = self.replace_with_safe_medical_response(response["text"], lead_context)
            guardrails_applied.append("medical_advice_replaced")
        
        # Guardrail 2: No specific promises
        if self.contains_specific_promises(response.get("text", "")):
            safe_response["text"] = self.replace_with_general_promises(response["text"], lead_context)
            guardrails_applied.append("specific_promises_replaced")
        
        # Guardrail 3: Emergency detection
        if self.detects_emergency(response.get("text", ""), lead_context):
            safe_response["needs_escalation"] = True
            safe_response["escalation_reason"] = "emergency_detected"
            guardrails_applied.append("emergency_escalation")
        
        # Guardrail 4: Pressure detection
        if self.detects_high_pressure(response.get("text", "")):
            safe_response["text"] = self.reduce_pressure(response["text"], lead_context)
            guardrails_applied.append("pressure_reduced")
        
        # Guardrail 5: Age-appropriate content
        baby_age = self.estimate_baby_age(lead_context)
        if baby_age:
            safe_response["text"] = self.personalize_by_age(response["text"], baby_age)
            guardrails_applied.append("age_personalization")
        
        safe_response["guardrails_applied"] = guardrails_applied
        return safe_response
    
    def check_escalation_needed(self, original_message: str, response: Dict[str, Any], lead_context: Dict[str, Any]) -> bool:
        """Verifica si necesita escalación humana"""
        
        # Razones para escalar
        escalation_reasons = []
        
        # 1. Emergencias médicas
        if self.detects_emergency(original_message, lead_context):
            escalation_reasons.append("emergency_medical")
        
        # 2. Problemas complejos de desarrollo
        if self.detects_complex_development_issue(original_message):
            escalation_reasons.append("complex_development")
        
        # 3. Objeciones fuertes o frustración
        if self.detects_strong_objection(original_message, lead_context):
            escalation_reasons.append("strong_objection")
        
        # 4. Solicitud explícita de hablar con humano
        if self.detects_human_request(original_message):
            escalation_reasons.append("human_requested")
        
        # 5. Baja confianza en respuesta
        if response.get("confidence", 1.0) < 0.6:
            escalation_reasons.append("low_confidence")
        
        # 6. Temas sensibles
        if self.detects_sensitive_topic(original_message):
            escalation_reasons.append("sensitive_topic")
        
        if escalation_reasons:
            response["escalation_reasons"] = escalation_reasons
            return True
        
        return False
    
    def get_fallback_response(self, lead_context: Dict[str, Any]) -> str:
        """Respuesta de respaldo cuando clawbot falla"""
        name = lead_context.get("name", "Mamá")
        
        return f"""Hola {name}, gracias por tu mensaje.\n\nPara darte la mejor respuesta posible, quiero que Cynthia te conteste personalmente.\n\nElla te responderá en las próximas horas con información específica para tu situación.\n\n¿Mientras tanto, podrías decirme cuántos meses tiene tu bebé? Así Cynthia puede prepararte información personalizada."""
    
    # Métodos auxiliares de guardrails
    def contains_medical_advice(self, text: str) -> bool:
        """Detecta si contiene consejo médico"""
        medical_keywords = [
            "diagnosticar", "tratamiento", "medicina", "pídale a su pediatra",
            "debe tomar", "medicamento", "enfermedad", "síntoma",
            "problema médico", "condición", "tratar"
        ]
        return any(keyword in text.lower() for keyword in medical_keywords)
    
    def contains_specific_promises(self, text: str) -> bool:
        """Detecta promesas específicas"""
        promise_patterns = [
            r"en \d+ días", r"en \d+ semanas", r"siempre", "nunca",
            "garantizado al 100%", "resultados exactos", "sin falta"
        ]
        return any(re.search(pattern, text.lower()) for pattern in promise_patterns)
    
    def detects_emergency(self, text: str, context: Dict[str, Any]) -> bool:
        """Detecta emergencias"""
        emergency_keywords = [
            "emergency", "emergencia", "urgente", "urgencia", "911",
            "no respira", "convulsión", "fiebre alta", "inconsciente",
            "no reacciona", "crisis", "emergency room", "hospital"
        ]
        return any(keyword in text.lower() for keyword in emergency_keywords)
    
    def detects_high_pressure(self, text: str) -> bool:
        """Detecta presión alta de ventas"""
        pressure_keywords = [
            "compra ahora", "oferta limitada", "última oportunidad",
            "solo hoy", "se acaba", "últimos lugares", "compra inmediata"
        ]
        return any(keyword in text.lower() for keyword in pressure_keywords)
    
    def estimate_baby_age(self, lead_context: Dict[str, Any]) -> int:
        """Estima edad del bebé en meses"""
        # Implementar lógica para estimar edad
        # Por ahora, default 6 meses
        return 6
    
    def personalize_by_age(self, text: str, age_months: int) -> str:
        """Personaliza texto según edad del bebé"""
        # Reemplazar con información específica por edad
        age_specific = f"para bebés de {age_months} meses como el tuyo"
        return text.replace("tu bebé", f"tu bebé de {age_months} meses")
    
    def replace_with_safe_medical_response(self, text: str, context: Dict[str, Any]) -> str:
        """Reemplaza consejo médico con respuesta segura"""
        return "Para temas específicos de salud, te recomiendo consultar con tu pediatra. Yo me enfoco en el desarrollo y estimulación temprana."
    
    def replace_with_general_promises(self, text: str, context: Dict[str, Any]) -> str:
        """Reemplaza promesas específicas con generales"""
        return text.replace("en 7 días", "en las próximas semanas").replace("siempre", "generalmente")
    
    def reduce_pressure(self, text: str, context: Dict[str, Any]) -> str:
        """Reduce presión en el texto"""
        return text.replace("compra ahora", "cuando te sientas lista").replace("solo hoy", "cuando estés preparada")
    
    def detects_complex_development_issue(self, text: str) -> bool:
        """Detecta problemas complejos de desarrollo"""
        complex_keywords = [
            "retraso severo", "no desarrolla", "problema grave",
            "no progresa", "preocupación seria", "muy atrasado"
        ]
        return any(keyword in text.lower() for keyword in complex_keywords)
    
    def detects_strong_objection(self, text: str, context: Dict[str, Any]) -> bool:
        """Detecta objeciones fuertes"""
        objection_keywords = [
            "no me interesa", "no quiero", "estafadores", "fraude",
            "muy caro", "no tengo dinero", "imposible", "no puedo"
        ]
        return any(keyword in text.lower() for keyword in objection_keywords)
    
    def detects_human_request(self, text: str) -> bool:
        """Detecta solicitud de hablar con humano"""
        human_keywords = [
            "hablar con cyn", "quiero hablar con alguien", "persona real",
            "no eres real", "humano", "cynthia", "cyn"
        ]
        return any(keyword in text.lower() for keyword in human_keywords)
    
    def detects_sensitive_topic(self, text: str) -> bool:
        """Detecta temas sensibles"""
        sensitive_keywords = [
            "depresión", "suicidio", "abuso", "violencia", "divorcio",
            "problema legal", "demanda", "abogado"
        ]
        return any(keyword in text.lower() for keyword in sensitive_keywords)
    
    def generate_signature(self, context: Dict[str, Any]) -> str:
        """Genera firma HMAC para seguridad"""
        payload_str = json.dumps(context, sort_keys=True)
        return hmac.new(
            self.api_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def generate_request_id(self) -> str:
        """Genera ID único para request"""
        import uuid
        return str(uuid.uuid4())

# Función principal para Windmill
def main(phone: str, message: str, lead_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Procesa mensaje con clawbot.ai integración
    
    Args:
        phone: Número de teléfono del lead
        message: Mensaje recibido
        lead_context: Contexto del lead (opcional)
    """
    
    if not lead_context:
        # Obtener contexto del lead
        from ai_agent_cyn import EinsteinKidsAIAgent
        agent = EinsteinKidsAIAgent()
        lead_context = agent.get_lead_context(phone)
        agent.close()
    
    clawbot = ClawbotEinsteinKids()
    
    try:
        result = clawbot.generate_secure_response(message, lead_context)
        
        # Si necesita escalación, notificar
        if result.get("needs_escalation"):
            print(f"ESCALACIÓN NECESARIA - Lead: {phone}")
            print(f"Razón: {result.get('escalation_reason', 'general')}")
            # Aquí iría la notificación a Cyn
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback_response": "Gracias por tu mensaje. Cynthia te responderá personalmente en breve.",
            "needs_escalation": True,
            "escalation_reason": "system_error"
        }