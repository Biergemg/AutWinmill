"""
Pre-procesamiento de mensajes para Einstein Kids AI
Detecta intenci??n, escala si es necesario, y prepara para AI
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List
import psycopg2
import os

class MessagePreprocessor:
    """Pre-procesa mensajes antes de enviar a AI"""
    
    def __init__(self):
        self.db_connection = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('POSTGRES_USER', 'windmill'),
            password=os.getenv('POSTGRES_PASSWORD'),
            database=os.getenv('POSTGRES_DB', 'windmill')
        )
        
        # Palabras clave para escalaci??n inmediata
        self.emergency_keywords = [
            "emergency", "emergencia", "urgente", "urgencia", "911",
            "no respira", "convulsi??n", "fiebre alta", "inconsciente",
            "no reacciona", "crisis", "emergency room", "hospital",
            "muerte", "muerto", "accidente", "grave"
        ]
        
        self.human_request_keywords = [
            "hablar con cyn", "quiero hablar con alguien", "persona real",
            "no eres real", "humano", "cynthia", "cyn", "especialista",
            "experta", "profesional", "llamada", "videollamada"
        ]
        
        self.medical_keywords = [
            "diagnosticar", "tratamiento", "medicina", "p??dale a su pediatra",
            "debe tomar", "medicamento", "enfermedad", "s??ntoma", "doctor",
            "problema m??dico", "condici??n", "tratar", "cura", "receta"
        ]
        
        self.sensitive_keywords = [
            "depresi??n", "suicidio", "abuso", "violencia", "divorcio",
            "problema legal", "demanda", "abogado", "pelea", "golpe",
            "maltrato", "neglect", "abandono"
        ]
    
    def preprocess_message(self, phone: str, message: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-procesa mensaje completo"""
        
        # Normalizar mensaje
        normalized_message = self.normalize_message(message)
        
        # Detectar intenciones
        intent_data = self.detect_intent(normalized_message)
        
        # Detectar si necesita escalaci??n
        escalation_data = self.check_escalation(normalized_message, lead_context)
        
        # An??lisis de sentimiento
        sentiment_data = self.analyze_sentiment(normalized_message)
        
        # Detectar informaci??n ??til
        extracted_info = self.extract_info(normalized_message)
        
        # Decidir ruta
        route = self.decide_route(escalation_data, intent_data, lead_context)
        
        # Preparar contexto completo
        result = {
            "phone": phone,
            "original_message": message,
            "normalized_message": normalized_message,
            "intent": intent_data,
            "escalation": escalation_data,
            "sentiment": sentiment_data,
            "extracted_info": extracted_info,
            "route": route["route"],
            "escalation_reason": route.get("reason"),
            "confidence": route["confidence"],
            "timestamp": datetime.now().isoformat(),
            "interaction_type": self.classify_interaction(intent_data, escalation_data),
            "lead_context": lead_context
        }
        
        # Registrar pre-procesamiento
        self.log_preprocessing(result)
        
        return result
    
    def normalize_message(self, message: str) -> str:
        """Normaliza mensaje para an??lisis"""
        # Convertir a min??sculas
        normalized = message.lower().strip()
        
        # Eliminar acentos
        import unicodedata
        normalized = unicodedata.normalize('NFKD', normalized).encode('ASCII', 'ignore').decode('utf-8')
        
        # Eliminar emojis y caracteres especiales (mantener n??meros y letras)
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Eliminar espacios m??ltiples
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized.strip()
    
    def detect_intent(self, message: str) -> Dict[str, Any]:
        """Detecta intenci??n del mensaje"""
        
        intents = {
            "greeting": ["hola", "buenos", "buenas", "hey", "hello"],
            "farewell": ["adios", "bye", "hasta luego", "nos vemos"],
            "thanks": ["gracias", "thank", "agradecido", "thank you"],
            "price": ["precio", "costo", "valor", "cuanto", "dinero", "precio"],
            "information": ["informacion", "info", "dime", "cuenta", "explica"],
            "question": ["que", "como", "cuando", "donde", "por que", "?"],
            "affirmation": ["si", "claro", "perfecto", "ok", "vale", "adelante"],
            "negation": ["no", "nunca", "jam??s", "negativo"],
            "urgency": ["urgente", "rapido", "ya", "inmediato", "ahora"],
            "complaint": ["problema", "error", "fallo", "malo", "peor"],
            "compliment": ["bueno", "excelente", "perfecto", "me encanta"],
            "comparison": ["comparar", "diferente", "mejor", "peor", "versus"],
            "confirmation": ["confirmar", "confirmo", "listo", "hecho"],
            "payment": ["pagar", "pago", "tarjeta", "transferencia", "comprar"],
            "schedule": ["hora", "fecha", "cuando", "agendar", "programar"],
            "age": ["meses", "a??os", "edad", "bebe", "ni??o", "peque??o"],
            "results": ["resultados", "cambios", "progreso", "mejora"],
            "doubts": ["duda", "dudoso", "inseguro", "no se"],
            "emergency": self.emergency_keywords
        }
        
        detected_intents = []
        intent_scores = {}
        
        for intent, keywords in intents.items():
            score = 0
            for keyword in keywords:
                if keyword in message:
                    score += 1
            
            if score > 0:
                detected_intents.append(intent)
                intent_scores[intent] = score / len(keywords)
        
        # Detectar edad espec??fica
        age_match = re.search(r'(\d+)\s*(mes|a??o)', message)
        age_months = None
        if age_match:
            age = int(age_match.group(1))
            unit = age_match.group(2)
            if 'mes' in unit:
                age_months = age
            elif 'a??o' in unit:
                age_months = age * 12
        
        # Detectar n??meros de tel??fono
        phone_numbers = re.findall(r'\d{10,}', message)
        
        # Detectar emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
        
        # Detectar menciones de dinero
        money_mentions = re.findall(r'\$\d+|\d+\s*(pesos|mxn)', message)
        
        return {
            "primary_intents": detected_intents[:3],  # Top 3
            "intent_scores": intent_scores,
            "age_months": age_months,
            "phone_numbers": phone_numbers,
            "emails": emails,
            "money_mentions": money_mentions,
            "has_question": "?" in message,
            "has_exclamation": "!" in message,
            "message_length": len(message.split()),
            "is_caps_heavy": sum(1 for c in message if c.isupper()) > len(message) * 0.3
        }
    
    def check_escalation(self, message: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica si necesita escalaci??n inmediata"""
        
        escalation_triggers = []
        confidence = 0.0
        
        # 1. Emergencias m??dicas
        for keyword in self.emergency_keywords:
            if keyword in message:
                escalation_triggers.append("emergency_medical")
                confidence += 0.9
                break
        
        # 2. Solicitud expl??cita de humano
        for keyword in self.human_request_keywords:
            if keyword in message:
                escalation_triggers.append("human_requested")
                confidence += 0.8
                break
        
        # 3. Temas m??dicos sensibles
        for keyword in self.medical_keywords:
            if keyword in message:
                escalation_triggers.append("medical_topic")
                confidence += 0.6
                break
        
        # 4. Temas sensibles
        for keyword in self.sensitive_keywords:
            if keyword in message:
                escalation_triggers.append("sensitive_topic")
                confidence += 0.7
                break
        
        # 5. M??ltiples signos de frustraci??n
        frustration_indicators = [
            "no entiendo", "estoy frustrada", "no funciona",
            "me est??s ignorando", "contesta bien", "no me ayudas"
        ]
        
        frustration_count = sum(1 for indicator in frustration_indicators if indicator in message)
        if frustration_count >= 2:
            escalation_triggers.append("high_frustration")
            confidence += 0.6
        
        # 6. Score alto del lead + objeci??n
        if lead_context.get("score", 0) >= 80 and ("objeci??n" in message or "no quiero" in message):
            escalation_triggers.append("high_value_objection")
            confidence += 0.5
        
        # 7. Mensaje muy largo y complejo
        if len(message.split()) > 50:
            escalation_triggers.append("complex_message")
            confidence += 0.3
        
        return {
            "needs_escalation": len(escalation_triggers) > 0,
            "triggers": escalation_triggers,
            "confidence": min(confidence, 1.0),
            "priority": self.calculate_priority(escalation_triggers)
        }
    
    def analyze_sentiment(self, message: str) -> Dict[str, Any]:
        """An??lisis b??sico de sentimiento"""
        
        positive_words = [
            "bueno", "excelente", "perfecto", "me encanta", "genial",
            "maravilloso", "fant??stico", "s??per", "incre??ble", "amazing"
        ]
        
        negative_words = [
            "malo", "terrible", "horrible", "pesimo", "fatal",
            "no me gusta", "odio", "detesto", "frustrante", "dif??cil"
        ]
        
        neutral_words = [
            "normal", "regular", "m??s o menos", "ni fu ni fa", "standard"
        ]
        
        positive_count = sum(1 for word in positive_words if word in message)
        negative_count = sum(1 for word in negative_words if word in message)
        neutral_count = sum(1 for word in neutral_words if word in message)
        
        # Calcular sentimiento
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(positive_count / 3, 1.0)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = min(negative_count / 3, 1.0)
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": score,
            "positive_words": positive_count,
            "negative_words": negative_count,
            "neutral_words": neutral_count
        }
    
    def extract_info(self, message: str) -> Dict[str, Any]:
        """Extrae informaci??n ??til del mensaje"""
        
        info = {
            "baby_age": None,
            "concerns": [],
            "goals": [],
            "timeline": None,
            "budget": None
        }
        
        # Extraer edad del beb??
        age_patterns = [
            r'(\d+)\s*mes(?:es)?',  # 3 meses
            r'(\d+)\s*a??(?:o|os)',   # 1 a??o
            r'mi beb?? tiene (\d+)', # mi beb?? tiene 6
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                age = int(match.group(1))
                if 'mes' in pattern:
                    info["baby_age"] = age
                elif 'a??' in pattern:
                    info["baby_age"] = age * 12
                break
        
        # Detectar preocupaciones
        concern_keywords = [
            "preocupa", "miedo", "temor", "ansiedad", "duda",
            "no s??", "no entiendo", "confundida", "perdida"
        ]
        
        for keyword in concern_keywords:
            if keyword in message:
                info["concerns"].append(keyword)
        
        # Detectar objetivos
        goal_keywords = [
            "quiero", "me gustar??a", "espero", "mi meta", "mi objetivo",
            "busco", "necesito", "deseo"
        ]
        
        for keyword in goal_keywords:
            if keyword in message:
                # Extraer el objetivo completo
                goal_match = re.search(rf'{keyword}[^.!?]*', message, re.IGNORECASE)
                if goal_match:
                    info["goals"].append(goal_match.group(0).strip())
        
        # Detectar l??nea de tiempo
        timeline_patterns = [
            r'(\d+)\s*semana(?:s)?',  # 2 semanas
            r'(\d+)\s*mes(?:es)?',   # 1 mes
            r'(\d+)\s*d??a(?:s)?',    # 7 d??as
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                timeline = int(match.group(1))
                if 'semana' in pattern:
                    info["timeline"] = f"{timeline} semanas"
                elif 'mes' in pattern:
                    info["timeline"] = f"{timeline} meses"
                elif 'd??a' in pattern:
                    info["timeline"] = f"{timeline} d??as"
                break
        
        # Detectar presupuesto
        budget_patterns = [
            r'\$(\d+)',              # $1000
            r'(\d+)\s*(pesos|mxn)', # 1000 pesos
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                budget = int(match.group(1))
                info["budget"] = budget
                break
        
        return info
    
    def decide_route(self, escalation_data: Dict[str, Any], intent_data: Dict[str, Any], lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Decide si va por AI o humano"""
        
        # Si necesita escalaci??n, va directo a humano
        if escalation_data["needs_escalation"]:
            return {
                "route": "human",
                "reason": escalation_data["triggers"][0] if escalation_data["triggers"] else "general_escalation",
                "confidence": escalation_data["confidence"],
                "priority": escalation_data["priority"]
            }
        
        # Si pide expl??citamente humano, va a humano
        if "human_requested" in escalation_data["triggers"]:
            return {
                "route": "human",
                "reason": "explicit_human_request",
                "confidence": 0.9,
                "priority": "high"
            }
        
        # Si es emergencia, va a humano
        if "emergency_medical" in escalation_data["triggers"]:
            return {
                "route": "human",
                "reason": "emergency_medical",
                "confidence": 0.95,
                "priority": "critical"
            }
        
        # Si es un tema m??dico sensible, considerar humano
        if "medical_topic" in escalation_data["triggers"] and escalation_data["confidence"] > 0.7:
            return {
                "route": "human",
                "reason": "sensitive_medical_topic",
                "confidence": escalation_data["confidence"],
                "priority": "medium"
            }
        
        # Si el lead tiene score alto y es objeci??n, considerar humano
        if lead_context.get("score", 0) >= 80 and "high_value_objection" in escalation_data["triggers"]:
            return {
                "route": "human",
                "reason": "high_value_lead_objection",
                "confidence": escalation_data["confidence"],
                "priority": "high"
            }
        
        # Por defecto, va por AI
        return {
            "route": "ai",
            "reason": "suitable_for_ai",
            "confidence": 1.0 - escalation_data["confidence"],  # Invertido
            "priority": "normal"
        }
    
    def calculate_priority(self, triggers: List[str]) -> str:
        """Calcula prioridad de escalaci??n"""
        
        if "emergency_medical" in triggers:
            return "critical"
        elif "high_frustration" in triggers or "human_requested" in triggers:
            return "high"
        elif "high_value_objection" in triggers or "sensitive_topic" in triggers:
            return "medium"
        else:
            return "normal"
    
    def classify_interaction(self, intent_data: Dict[str, Any], escalation_data: Dict[str, Any]) -> str:
        """Clasifica el tipo de interacci??n"""
        
        if escalation_data["needs_escalation"]:
            return "escalation_needed"
        
        if "greeting" in intent_data["primary_intents"]:
            return "greeting"
        elif "price" in intent_data["primary_intents"]:
            return "pricing_inquiry"
        elif "information" in intent_data["primary_intents"]:
            return "information_request"
        elif "question" in intent_data["has_question"]:
            return "question"
        elif "doubts" in intent_data["primary_intents"]:
            return "objection_handling"
        elif "urgency" in intent_data["primary_intents"]:
            return "urgent_request"
        elif "results" in intent_data["primary_intents"]:
            return "results_inquiry"
        else:
            return "general_conversation"
    
    def log_preprocessing(self, result: Dict[str, Any]):
        """Registra el pre-procesamiento"""
        
        cursor = self.db_connection.cursor()
        
        cursor.execute("""
            INSERT INTO ek_lead_events (lead_id, event_type, payload)
            VALUES (
                (SELECT lead_id FROM ek_leads WHERE phone_normalized = %s ORDER BY created_at DESC LIMIT 1),
                'message_preprocessed',
                %s
            );
        """, (result["phone"], json.dumps({
            "direction": "inbound",
            "preprocessing_result": {
                "intent": result["intent"],
                "escalation": result["escalation"],
                "route": result["route"],
                "confidence": result["confidence"],
                "interaction_type": result["interaction_type"]
            },
            "timestamp": result["timestamp"]
        })))
        
        self.db_connection.commit()
    
    def close(self):
        """Cierra conexi??n"""
        if self.db_connection:
            self.db_connection.close()

# Funci??n principal para Windmill
def main(phone: str, message: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pre-procesa mensaje para Einstein Kids AI
    
    Args:
        phone: N??mero de tel??fono del lead
        message: Mensaje recibido
        lead_context: Contexto del lead
    """
    
    preprocessor = MessagePreprocessor()
    
    try:
        result = preprocessor.preprocess_message(phone, message, lead_context)
        
        # Si necesita escalaci??n, notificar
        if result["escalation"]["needs_escalation"]:
            print(f"ESCALACI??N NECESARIA - Lead: {phone}")
            print(f"Raz??n: {result['escalation_reason']}")
            print(f"Prioridad: {result['escalation']['priority']}")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "route": "human",  # Fallback a humano
            "escalation_reason": "preprocessing_error",
            "confidence": 1.0
        }
    finally:
        preprocessor.close()
