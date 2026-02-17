-- Re-encola evento desde DLQ hacia events con estado 'queued'
-- Variables esperadas:
-- :dlq_id

WITH moved AS (
  DELETE FROM dlq_events
  WHERE id = :dlq_id
  RETURNING event_id, trace_id, payload
)
INSERT INTO events (event_id, trace_id, payload, status, reason)
SELECT event_id, trace_id, payload, 'queued', 'requeued_from_dlq'
FROM moved;
