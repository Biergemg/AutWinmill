# ADR-0001: jsonschema vs pydantic

## Contexto
Se requiere validar payloads de eventos contra contratos con alto rendimiento y compatibilidad.

## Decisión
Se utiliza jsonschema (Draft 2020-12) como validador principal con fallback interno y pydantic para modelos opcionales de tipado.

## Consecuencias
- Validación estándar interoperable con múltiples herramientas.
- Fallback interno garantiza funcionamiento sin dependencia estricta.
- Tipado adicional con pydantic para componentes que lo requieran.
