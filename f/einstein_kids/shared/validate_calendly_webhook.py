"""
VALIDACIÓN DE WEBHOOKS - Calendly
Valida autenticidad de webhooks entrantes de Calendly
"""

import hmac
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Any

def validate_calendly_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida webhook de Calendly usando firma HMAC
    
    Args:
        webhook_data: Datos del webhook incluyendo headers y payload
        
    Returns:
        Dict con resultado de validación y datos procesados
    """
    
    try:
        # Extraer componentes del webhook
        headers = webhook_data.get('headers', {})
        body = webhook_data.get('body', '')
        
        # Validar firma si está configurada
        signature = headers.get('X-Calendly-Signature', '')
        webhook_secret = os.getenv('CALENDLY_WEBHOOK_SECRET')
        
        if webhook_secret and signature:
            # Calcular firma esperada
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return {
                    'valid': False,
                    'error': 'Firma inválida',
                    'expected': expected_signature[:10] + '...',
                    'received': signature[:10] + '...'
                }
        
        # Parsear el body JSON
        payload = json.loads(body) if isinstance(body, str) else body
        
        # Validar estructura básica
        event = payload.get('event')
        if not event:
            return {
                'valid': False,
                'error': 'No se encontró evento en payload'
            }
        
        # Validar tipos de eventos soportados
        supported_events = [
            'invitee.created',
            'invitee.cancelled', 
            'invitee.no_show'
        ]
        
        if event not in supported_events:
            return {
                'valid': False,
                'error': f'Evento no soportado: {event}',
                'supported_events': supported_events
            }
        
        # Validar payload completo
        validation_result = validate_event_payload(event, payload)
        
        if not validation_result['valid']:
            return validation_result
        
        # Extraer datos relevantes
        processed_data = extract_relevant_data(event, payload)
        
        return {
            'valid': True,
            'event': event,
            'payload': processed_data,
            'timestamp': datetime.now().isoformat(),
            'processed_at': datetime.now().isoformat()
        }
        
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': f'JSON inválido: {str(e)}'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'Error procesando webhook: {str(e)}'
        }

def validate_event_payload(event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Valida estructura del payload según el tipo de evento"""
    
    try:
        # Validar estructura común
        if 'payload' not in payload:
            return {
                'valid': False,
                'error': 'No se encontró payload principal'
            }
        
        event_payload = payload['payload']
        
        # Validaciones específicas por evento
        if event == 'invitee.created':
            return validate_invitee_created(event_payload)
        elif event == 'invitee.cancelled':
            return validate_invitee_cancelled(event_payload)
        elif event == 'invitee.no_show':
            return validate_invitee_no_show(event_payload)
        
        return {
            'valid': False,
            'error': f'Validación no implementada para: {event}'
        }
        
    except KeyError as e:
        return {
            'valid': False,
            'error': f'Campo requerido faltante: {str(e)}'
        }

def validate_invitee_created(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Valida payload de invitee.created"""
    
    # Validar estructura de invitee
    invitee = payload.get('invitee', {})
    required_invitee_fields = ['email', 'name', 'uri']
    
    for field in required_invitee_fields:
        if field not in invitee or not invitee[field]:
            return {
                'valid': False,
                'error': f'Campo invitee requerido faltante: {field}'
            }
    
    # Validar estructura de event
    event = payload.get('event', {})
    required_event_fields = ['uri', 'start_time', 'end_time']
    
    for field in required_event_fields:
        if field not in event or not event[field]:
            return {
                'valid': False,
                'error': f'Campo event requerido faltante: {field}'
            }
    
    # Validar questions_and_answers (opcional pero recomendado)
    questions = invitee.get('questions_and_answers', [])
    if not questions:
        print("Advertencia: No se encontraron preguntas y respuestas")
    
    return {
        'valid': True,
        'message': 'Payload de invitee.created válido'
    }

def validate_invitee_cancelled(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Valida payload de invitee.cancelled"""
    
    # Similar a created pero con estructura diferente
    invitee = payload.get('invitee', {})
    
    if 'email' not in invitee or not invitee['email']:
        return {
            'valid': False,
            'error': 'Email del invitee requerido'
        }
    
    return {
        'valid': True,
        'message': 'Payload de invitee.cancelled válido'
    }

def validate_invitee_no_show(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Valida payload de invitee.no_show"""
    
    invitee = payload.get('invitee', {})
    
    if 'email' not in invitee or not invitee['email']:
        return {
            'valid': False,
            'error': 'Email del invitee requerido'
        }
    
    return {
        'valid': True,
        'message': 'Payload de invitee.no_show válido'
    }

def extract_relevant_data(event: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Extrae datos relevantes del payload"""
    
    event_payload = payload['payload']
    invitee = event_payload.get('invitee', {})
    event_info = event_payload.get('event', {})
    
    # Datos comunes
    data = {
        'event_type': event,
        'timestamp': payload.get('created_at', datetime.now().isoformat()),
        'invitee': {
            'email': invitee.get('email', ''),
            'name': invitee.get('name', ''),
            'first_name': invitee.get('first_name', ''),
            'last_name': invitee.get('last_name', ''),
            'uri': invitee.get('uri', ''),
            'status': invitee.get('status', ''),
            'timezone': invitee.get('timezone', ''),
            'questions_and_answers': invitee.get('questions_and_answers', [])
        },
        'event': {
            'uri': event_info.get('uri', ''),
            'start_time': event_info.get('start_time', ''),
            'end_time': event_info.get('end_time', ''),
            'timezone': event_info.get('timezone', ''),
            'event_type': event_info.get('event_type', ''),
            'location': event_info.get('location', {}),
            'meeting_url': event_info.get('meeting_url', '')
        }
    }
    
    # Extraer información específica de preguntas
    questions = invitee.get('questions_and_answers', [])
    extracted_questions = {}
    
    for qa in questions:
        question = qa.get('question', '').lower()
        answer = qa.get('answer', '')
        
        # Detectar tipo de pregunta
        if any(keyword in question for keyword in ['teléfono', 'phone', 'whatsapp']):
            extracted_questions['phone'] = answer
        elif any(keyword in question for keyword in ['edad', 'age', 'bebé', 'bebe']):
            extracted_questions['baby_age'] = answer
        elif any(keyword in question for keyword in ['nombre', 'name']):
            extracted_questions['name'] = answer
        elif any(keyword in question for keyword in ['interés', 'interest', 'razón', 'reason']):
            extracted_questions['interest_reason'] = answer
    
    data['extracted_data'] = extracted_questions
    
    return data

# Función principal para Windmill
def main(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función principal para validar webhooks de Calendly
    
    Args:
        webhook_data: Datos completos del webhook (headers + body)
        
    Returns:
        Resultado de validación
    """
    return validate_calendly_webhook(webhook_data)