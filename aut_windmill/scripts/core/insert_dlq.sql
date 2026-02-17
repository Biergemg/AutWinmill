-- Inserta evento en DLQ
-- Variables esperadas:
-- :event_id, :trace_id, :payload_json, :reason

INSERT INTO dlq_events (event_id, trace_id, payload, reason)
VALUES (:event_id, :trace_id, :payload_json::jsonb, :reason);
