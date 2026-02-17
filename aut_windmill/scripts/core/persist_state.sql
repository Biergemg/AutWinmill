-- Inserta evento validado y crea workflow asociado
-- Variables esperadas:
-- :event_id, :trace_id, :payload_json, :workflow_id

BEGIN;

INSERT INTO events (event_id, trace_id, payload, status)
VALUES (:event_id, :trace_id, :payload_json::jsonb, 'validated');

INSERT INTO workflows (workflow_id, trace_id, event_id, status)
VALUES (:workflow_id, :trace_id, :event_id, 'validated');

COMMIT;
