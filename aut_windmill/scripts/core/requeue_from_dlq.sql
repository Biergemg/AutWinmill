WITH moved AS (
  INSERT INTO events (event_id, trace_id, payload, status, reason, created_at, updated_at)
  SELECT event_id, trace_id, payload, 'received', NULL, NOW(), NOW()
  FROM dlq_events
  WHERE event_id = :event_id
  ON CONFLICT (event_id) DO NOTHING
  RETURNING event_id
)
DELETE FROM dlq_events
WHERE event_id IN (SELECT event_id FROM moved);
