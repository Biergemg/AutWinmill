import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Ajustar path para importar src
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from windmill_automation.validators.base import _validate_object
from windmill_automation.validators.registry import get_schema_path
from windmill_automation.validators.jsonschema_validator import validate_payload

# --- Tests para Registry ---

def test_registry_known_event():
    # Asume que registry.json tiene "order_created"
    path = get_schema_path("order_created")
    assert path is not None
    assert "order_created.schema.json" in path

def test_registry_unknown_event():
    path = get_schema_path("evento_inexistente_12345")
    assert path is None

# --- Tests para Validator (Casos borde) ---

def test_validate_payload_unknown_event():
    payload = {"event_name": "unknown_event"}
    result = validate_payload(payload)
    assert result["valid"] is False
    assert "Evento no registrado" in result["errors"][0]

def test_validate_payload_invalid_json_structure():
    # Payload que rompe schemas
    payload = {"event_name": "order_created"} # Faltan campos requeridos
    # Esto debería ser detectado por jsonschema o el fallback
    result = validate_payload(payload)
    assert result["valid"] is False

# --- Tests para Fallback / Validación Manual (_validate_object) ---

@pytest.mark.parametrize("value,expected_type,valid", [
    ("texto", "string", True),
    (123, "string", False),
    (123, "number", True),
    (123.45, "number", True),
    ("123", "number", False),
    (True, "boolean", True),
    ("True", "boolean", False),
    ([1, 2], "array", True),
    ({"a": 1}, "object", True),
])
def test_manual_type_checking(value, expected_type, valid):
    # Test indirecto a traves de un schema simple
    schema = {
        "properties": {
            "field": {"type": expected_type}
        }
    }
    data = {"field": value}
    ok, errors = _validate_object(schema, data)
    assert ok is valid

def test_manual_validation_required_field():
    schema = {"required": ["field1"]}
    data = {"field2": "exists"}
    ok, errors = _validate_object(schema, data)
    assert ok is False
    assert "field1: faltante" in errors[0]

def test_manual_validation_nested():
    schema = {
        "properties": {
            "parent": {
                "type": "object",
                "properties": {
                    "child": {"type": "string"}
                }
            }
        }
    }
    data = {"parent": {"child": 123}} # Error de tipo
    ok, errors = _validate_object(schema, data)
    assert ok is False
    assert "parent.child: tipo inválido" in errors[0]

# --- Test de Simulación de Fallback ---

def test_fallback_when_jsonschema_missing():
    # Simular que jsonschema no está instalado lanzando ImportError
    with patch.dict(sys.modules, {'jsonschema': None}):
        # Mockear _validate_jsonschema para que lance excepcion y active fallback
        with patch('windmill_automation.validators.jsonschema_validator._validate_jsonschema') as mock_val:
            # Configurar el mock para retornar la señal de error de importacion
            mock_val.return_value = (False, ["jsonschema_no_disponible"])
            
            # Usar un payload simple
            with open("contracts/examples/order_created.valid.json", "r", encoding="utf-8") as f:
                payload = json.load(f)
            
            # Ejecutar validación
            result = validate_payload(payload)
            
            # Debería usar _validate_object (que funciona ok para el payload valido)
            assert result["valid"] is True
            # Verificar error si fuera invalido
            payload_bad = payload.copy()
            del payload_bad["event_id"]
            result_bad = validate_payload(payload_bad)
            assert result_bad["valid"] is False
