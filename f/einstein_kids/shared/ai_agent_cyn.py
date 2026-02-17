"""
Sistema de Respuestas Inteligentes para Einstein Kids
Usa clawbot.ai + contexto de Cyn + Knowledge Base
"""

import yaml
import psycopg2
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import re

class EinsteinKidsAIAgent:
    """Agente AI que responde como Cyn usando clawbot.ai"""
    
    def __init__(self):
        self.knowledge = self.load_knowledge_base()
        self.db_connection = self.connect_to_db()
        self.context = {}
        
    def load_knowledge_base(self) -> Dict[str, Any]:
        """Carga la base de conocimientos de Cyn"""
        kb_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge_base', 'cyn_knowledge.yaml')
        with open(kb_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    def connect_to_db(self):
        """Conecta a base de datos"""
        return psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'windmill'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'windmill')
        )
    
    def get_lead_context(self, phone: str) -> Dict[str, Any]:
        """Obtiene contexto del lead desde BD"""
        cursor = self.db_connection.cursor()
        
        cursor.execute("""
            SELECT lead_id, name, avatar, stage, score, event_start_at, created_at
            FROM ek_leads 
            WHERE phone_normalized = %s
            ORDER BY created_at DESC 
            LIMIT 1;
        """, (phone,))
        
        lead = cursor.fetchone()
        if lead:
            return {
                "lead_id": str(lead[0]),
                "name": lead[1],
                "avatar": lead[2],
                "stage": lead[3],
                "score": lead[4],
                "event_start": lead[5].strftime("%Y-%m-%d") if lead[5] else None,
                "registered_date": lead[6].strftime("%Y-%m-%d")
            }
        return {}
    
    def detect_intent(self, message: str) -> Dict[str, Any]:
        """Detecta la intenci??n del mensaje"""
        message_lower = message.lower().strip()
        
        # Patrones de intenci??n
        intents = {
            "precio": [
                "cu??nto cuesta", "precio", "costo", "valor", "dinero", 
                "cu??nto es", "barato", "caro", "econ??mico", "presupuesto"
            ],
            "edad": [
                "qu?? edad", "desde cu??ndo", "cu??ndo empezar", "edad", 
                "meses", "a??os", "bebe", "ni??o", "temprano"
            ],
            "tiempo": [
                "cu??nto tiempo", "duraci??n", "cu??ndo ver", "cu??ndo resultados",
                "cu??nto dura", "tiempo", "r??pido", "lento"
            ],
            "m??todo": [
                "qu?? m??todo", "c??mo funciona", "t??cnica", "proceso", 
                "sistema", "m??todo", "forma", "manera"
            ],
            "seguridad": [
                "seguro", "riesgo", "da??o", "peligro", "seguridad",
                "confiable", "garant??a", "riesgos"
            ],
            "urgencia": [
                "quiero ya", "ap??rate", "urgente", "r??pido", "ya",
                "inmediato", "ahora", "pronto"
            ],
            "resultados": [
                "resultados", "cambios", "mejora", "progreso", "??xito",
                "testimonios", "casos", "ejemplos", "antes despu??s"
            ],
            "comparaci??n": [
                "otros", "comparaci??n", "diferente", "mejor", "peor",
                "similar", "igual", "distinto"
            ],
            "objeci??n": [
                "muy caro", "no puedo", "no tengo", "dudoso", "skeptical",
                "no creo", "dif??cil", "complicado"
            ],
            "confirmaci??n": [
                "confirmar", "pagar", "comprar", "listo", "adelante",
                "s?? quiero", "me interesa", "cu??l es el siguiente"
            ]
        }
        
        detected_intents = []
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_intents.append(intent)
        
        # Detectar edad espec??fica
        age_match = re.search(r'(\d+)\s*(mes|a??o)', message_lower)
        age_months = None
        if age_match:
            age = int(age_match.group(1))
            unit = age_match.group(2)
            if 'mes' in unit:
                age_months = age
            elif 'a??o' in unit:
                age_months = age * 12
        
        return {
            "intents": detected_intents,
            "age_months": age_months,
            "confidence": len(detected_intents) / max(len(message_lower.split()), 1)
        }
    
    def generate_response(self, message: str, phone: str) -> Dict[str, Any]:
        """Genera respuesta personalizada usando clawbot.ai + contexto"""
        
        # Obtener contexto del lead
        lead_context = self.get_lead_context(phone)
        
        # Detectar intenci??n
        intent_data = self.detect_intent(message)
        
        # Construir contexto completo
        context = {
            "message": message,
            "lead": lead_context,
            "intent": intent_data,
            "timestamp": datetime.now().isoformat(),
            "business_info": self.knowledge.get("business_info", {}),
            "instructor": self.knowledge.get("instructor", {})
        }
        
        # Generar respuesta basada en intenci??n y contexto
        response = self.build_response(context)
        
        # Registrar interacci??n
        self.log_interaction(phone, message, response, context)
        
        return response
    
    def build_response(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Construye respuesta basada en contexto"""
        
        message = context["message"]
        intents = context["intent"]["intents"]
        lead = context["lead"]
        age_months = context["intent"]["age_months"]
        
        # Respuesta base
        response = {
            "text": "",
            "suggested_actions": [],
            "needs_escalation": False,
            "confidence": 0.8,
            "context_used": context
        }
        
        # Saludo personalizado
        if not lead:
            # Nuevo lead
            response["text"] = f"??Hola! Soy {self.knowledge['instructor']['name']}, especialista en desarrollo infantil temprano. ??Cu??ntos meses tiene tu beb??? Quiero enviarte informaci??n personalizada."
            response["suggested_actions"] = ["compartir_edad", "ver_info_general"]
            return response
        
        # Respuestas por intenci??n
        if "precio" in intents:
            response["text"] = self.get_price_response(lead, age_months)
            response["suggested_actions"] = ["ver_planes_pago", "comparar_productos"]
            
        elif "edad" in intents or age_months:
            response["text"] = self.get_age_response(age_months or 6)  # Default 6 meses
            response["suggested_actions"] = ["ver_tecnicas_edad", "programar_demo"]
            
        elif "tiempo" in intents:
            response["text"] = self.get_time_response(lead)
            response["suggested_actions"] = ["ver_testimonios", "ver_cronograma"]
            
        elif "m??todo" in intents:
            response["text"] = self.get_method_response(lead)
            response["suggested_actions"] = ["ver_t??cnicas", "conocer_cyn"]
            
        elif "seguridad" in intents:
            response["text"] = self.get_safety_response(lead)
            response["suggested_actions"] = ["ver_garant??a", "ver_testimonios"]
            
        elif "urgencia" in intents:
            response["text"] = self.get_urgency_response(lead)
            response["suggested_actions"] = ["procesar_pago", "agendar_llamada"]
            
        elif "resultados" in intents:
            response["text"] = self.get_results_response(lead, age_months)
            response["suggested_actions"] = ["ver_testimonios", "ver_estad??sticas"]
            
        elif "objeci??n" in intents:
            response["text"] = self.get_objection_response(lead, message)
            response["suggested_actions"] = ["ofrecer_plan_pagos", "compartir_valor"]
            
        elif "confirmaci??n" in intents:
            response["text"] = self.get_confirmation_response(lead)
            response["suggested_actions"] = ["procesar_pago", "enviar_link"]
            
        else:
            # Respuesta gen??rica pero personalizada
            response["text"] = self.get_generic_response(lead, message)
            response["suggested_actions"] = ["m??s_informaci??n", "hablar_con_cyn"]
        
        # Verificar si necesita escalaci??n
        if self.needs_escalation(message, lead):
            response["needs_escalation"] = True
            response["escalation_reason"] = "pregunta_compleja_o_objeci??n_fuerte"
        
        return response
    
    def get_price_response(self, lead: Dict, age_months: int) -> str:
        """Respuesta sobre precios"""
        name = lead.get("name", "")
        personalized = f"{name}, " if name else ""
        
        return f"""{personalized}La masterclass tiene un valor de $1,997 MXN. Es una inversi??n en el futuro de tu beb?? que te durar?? a??os. 

Incluye:
??? 90 minutos conmigo en vivo
??? T??cnicas espec??ficas para beb??s de {age_months} meses
??? Acceso al grupo VIP
??? Material digital de apoyo

Tambi??n tengo opciones de pago. ??Te gustar??a conocerlas?"""
    
    def get_age_response(self, age_months: int) -> str:
        """Respuesta basada en edad del beb??"""
        if age_months <= 3:
            return f"??Perfecto! A {age_months} meses es el momento IDEAL para empezar. Los primeros 3 meses son cruciales para el desarrollo visual y auditivo.\n\nTe ense??ar?? t??cnicas espec??ficas como:\n??? Tarjetas de contraste blanco/negro\n??? Estimulaci??n visual con m??viles\n??? Ejercicios de seguimiento ocular\n??? M??sica cl??sica para desarrollo auditivo"
            
        elif age_months <= 6:
            return f"??Excelente edad! A {age_months} meses tu beb?? est?? en una etapa clave para el desarrollo de la coordinaci??n mano-ojo y la percepci??n auditiva.\n\nTrabajaremos en:\n??? Coordinaci??n viso-motora\n??? Desarrollo del agarre\n??? Estimulaci??n t??ctil\n??? Primeros sonidos y vocalizaciones"
            
        elif age_months <= 9:
            return f"??Incre??ble momento! A {age_months} meses tu beb?? est?? listo para desarrollar la motricidad m??s compleja y la comprensi??n auditiva.\n\nNos enfocaremos en:\n??? Desarrollo del gateo\n??? Coordinaci??n bilateral\n??? Primera comprensi??n de palabras\n??? Exploraci??n del entorno"
            
        else:  # 10-12 meses
            return f"??Nunca es tarde! A {age_months} meses a??n hay much??simo que podemos hacer. Tu beb?? est?? preparado para sus primeros pasos y palabras.\n\nTrabajaremos en:\n??? Estimulaci??n para primeros pasos\n??? Desarrollo del lenguaje\n??? Coordinaci??n mano-ojo avanzada\n??? Independencia motora"
    
    def get_time_response(self, lead: Dict) -> str:
        """Respuesta sobre tiempo y resultados"""
        name = lead.get("name", "")
        personalized = f"{name}, " if name else ""
        
        return f"""{personalized}Solo necesitas 15-20 minutos al d??a con las t??cnicas que te ense??o. Es tiempo de calidad con tu beb??, no una carga adicional.\n\nCronograma de resultados:\n??? Semana 1-2: Mejor atenci??n visual\n??? Semana 3-4: Respuesta m??s r??pida a est??mulos\n??? Mes 2: Movimientos m??s coordinados\n??? Mes 3: Lenguaje y motricidad avanzada\n\nCada beb?? es diferente, pero con constancia ver??s cambios incre??bles."""
    
    def get_method_response(self, lead: Dict) -> str:
        """Respuesta sobre el m??todo"""
        return f"""Mi m??todo combina neurociencia del desarrollo con t??cnicas pr??cticas que he perfeccionado en 8 a??os de experiencia.\n\nEs basado en:\n??? Estudios de neurodesarrollo infantil\n??? T??cnicas de estimulaci??n temprana validadas\n??? Mi experiencia con +500 familias\n??? Adaptaci??n personalizada a cada beb??\n\nNo es magia, es ciencia aplicada con amor. Te ense??o paso a paso, sin complicaciones."""
    
    def get_safety_response(self, lead: Dict) -> str:
        """Respuesta sobre seguridad"""
        return f"""Absolutamente seguro. Todas las t??cnicas que ense??o son recomendadas por pediatras y terapeutas del desarrollo.\n\nCaracter??sticas de seguridad:\n??? Ejercicios suaves y adaptativos\n??? Respetan el ritmo natural del beb??\n??? Fortalecen el v??nculo madre-hijo\n??? Validadas por profesionales de la salud\n??? Garant??a de satisfacci??n de 30 d??as\n\nAdem??s, te doy acceso al grupo VIP donde puedes preguntar cualquier duda. Tu beb?? est?? en las mejores manos."""
    
    def get_urgency_response(self, lead: Dict) -> str:
        """Respuesta para leads urgentes"""
        return f"??Perfecto! Cada d??a cuenta en el desarrollo de tu beb??. Te env??o el link de pago ahora mismo y confirmas cuando est?? listo. ??Te parece bien? Tambi??n puedo reservar tu lugar mientras decides."
    
    def get_results_response(self, lead: Dict, age_months: int) -> str:
        """Respuesta sobre resultados y testimonios"""
        return f"""Te comparto lo que han visto otras mam??s con beb??s de {age_months} meses:\n\nTestimonios recientes:\n??? 'Mi beb?? de 4 meses ahora sigue objetos perfectamente' - Ana M.\n??? 'A los 2 meses not?? que respond??a m??s r??pido a mi voz' - Laura P.\n??? 'Mi beb?? de 6 meses gatea coordinadamente' - Mar??a G.\n\nResultados t??picos:\n??? Atenci??n visual mejorada en 2 semanas\n??? Respuesta auditiva m??s r??pida\n??? Motricidad m??s coordinada\n??? Lenguaje temprano\n\nLa constancia es clave. ??Te gustar??a ver m??s casos de ??xito?"""
    
    def get_objection_response(self, lead: Dict, message: str) -> str:
        """Respuesta a objeciones"""
        message_lower = message.lower()
        
        if "caro" in message_lower or "dinero" in message_lower:
            return f"""Entiendo tu preocupaci??n. Piensa que es una inversi??n en el futuro de tu beb?? que te durar?? a??os.\n\nOpciones que tengo para ti:\n??? Plan de 3 pagos sin intereses\n??? Descuento del 10% por pago ??nico\n??? Garant??a de satisfacci??n de 30 d??as\n\nPor $1,997 est??s adquiriendo herramientas que usar??s durante los primeros 3 a??os cruciales de tu beb??. ??Te gustar??a conocer el plan de pagos?"""
            
        elif "tiempo" in message_lower or "no alcanzo" in message_lower:
            return f"""S?? que como mam?? tu tiempo es oro. Por eso dise???? t??cnicas que puedes hacer en 15-20 minutos diarios, integradas en tu rutina normal:\n\n??? Durante el ba??o\n??? Mientras amamantas\n??? En el cambio de pa??al\n??? Durante el juego\n\nEs tiempo de calidad con tu beb??, no una tarea extra. ??Te gustar??a ver c??mo otras mam??s lo integran?"""
            
        else:
            return f"""Entiendo tu preocupaci??n. Perm??teme explicarte mejor el valor de lo que ofrezco:\n\nNo es solo una clase, es:\n??? Conocimiento que usar??s por a??os\n??? T??cnicas que fortalecen el v??nculo con tu beb??\n??? Acceso a mi experiencia de 8 a??os\n??? Grupo de apoyo con otras mam??s\n??? Garant??a de satisfacci??n\n\n??Qu?? parte te preocupa m??s? Estoy aqu?? para aclarar todas tus dudas."""
    
    def get_confirmation_response(self, lead: Dict) -> str:
        """Respuesta para confirmaci??n de compra"""
        name = lead.get("name", "")
        personalized = f"{name}, " if name else ""
        
        return f"""{personalized}??Excelente decisi??n! Estoy emocionada de acompa??arte en esta etapa tan especial con tu beb??.\n\nTe env??o el link de pago por mensaje. Una vez que confirmes, recibir??s:\n??? Acceso inmediato al grupo VIP\n??? Material preparatorio\n??? Link para la masterclass\n??? Mi acompa??amiento personal\n\nConfirmas cuando est?? listo y te doy acceso inmediato. ??Te parece bien?"""
    
    def get_generic_response(self, lead: Dict, message: str) -> str:
        """Respuesta gen??rica pero personalizada"""
        name = lead.get("name", "")
        personalized = f"{name}, " if name else ""
        
        return f"""{personalized}Gracias por tu mensaje. Para darte la mejor informaci??n, ??podr??as decirme cu??ntos meses tiene tu beb???\n\nAs?? puedo compartirte t??cnicas espec??ficas para su edad y etapa de desarrollo.\n\nTambi??n puedo enviarte informaci??n general sobre nuestros programas si lo prefieres. ??Qu?? te gustar??a saber primero?"""
    
    def needs_escalation(self, message: str, lead: Dict) -> bool:
        """Determina si necesita escalaci??n a Cyn"""
        message_lower = message.lower()
        
        # Razones para escalar
        escalation_triggers = [
            "emergencia", "urgente", "emergency", "911",
            "m??dico", "doctor", "pediatra", "enfermo", "enfermedad",
            "no responde", "no se mueve", "convulsi??n", "fiebre alta",
            "depresi??n", "sad", "deprimida", "no puedo m??s",
            "quiero hablar con cyn", "hablar con alguien", "llamada",
            "reembolso", "devoluci??n", "no funciona", "estafa",
            "demanda", "abogado", "legal", "demandar"
        ]
        
        for trigger in escalation_triggers:
            if trigger in message_lower:
                return True
        
        # Si el score es muy alto y es objeci??n compleja
        if lead.get("score", 0) >= 90 and ("objeci??n" in self.detect_intent(message)["intents"]):
            return True
        
        return False
    
    def log_interaction(self, phone: str, message: str, response: Dict, context: Dict):
        """Registra la interacci??n en BD"""
        cursor = self.db_connection.cursor()
        
        cursor.execute("""
            INSERT INTO ek_lead_events (lead_id, event_type, payload)
            VALUES (
                (SELECT lead_id FROM ek_leads WHERE phone_normalized = %s ORDER BY created_at DESC LIMIT 1),
                'ai_interaction',
                %s
            );
        """, (phone, json.dumps({
            "direction": "inbound",
            "message": message,
            "response": response["text"],
            "intent": context["intent"],
            "confidence": response.get("confidence", 0),
            "needs_escalation": response.get("needs_escalation", False),
            "timestamp": datetime.now().isoformat()
        })))
        
        self.db_connection.commit()
    
    def close(self):
        """Cierra conexiones"""
        if self.db_connection:
            self.db_connection.close()

# Funci??n principal para Windmill
def main(phone: str, message: str) -> Dict[str, Any]:
    """
    Procesa mensaje de WhatsApp con AI de Cyn
    
    Args:
        phone: N??mero de tel??fono del lead (formato E.164)
        message: Mensaje recibido
    """
    agent = EinsteinKidsAIAgent()
    try:
        response = agent.generate_response(message, phone)
        
        # Si necesita escalaci??n, notificar a Cyn
        if response.get("needs_escalation"):
            # Aqu?? ir??a la notificaci??n a Cyn
            print(f"ESCALACI??N NECESARIA - Lead: {phone}")
            print(f"Raz??n: {response.get('escalation_reason', 'general')}")
        
        return {
            "success": True,
            "response": response["text"],
            "suggested_actions": response["suggested_actions"],
            "needs_escalation": response.get("needs_escalation", False),
            "confidence": response.get("confidence", 0)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "fallback_response": "Gracias por tu mensaje. Cynthia te responder?? personalmente en breve."
        }
    finally:
        agent.close()
