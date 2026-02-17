# Data Dictionary

## Tabla: events
- id BIGSERIAL PK
- event_id TEXT
- trace_id TEXT
- payload JSONB
- status TEXT
- reason TEXT
- created_at TIMESTAMPTZ
- updated_at TIMESTAMPTZ

## Vista: events_masked
- payload con PII enmascarada por mask_payload

## Tabla: audit_log
- actor TEXT
- action TEXT
- details JSONB
- ts TIMESTAMPTZ
