-- Insert a DLQ event
DO $$
BEGIN
  INSERT INTO dlq_events (event_id, trace_id, payload, reason)
  VALUES (
    'test-dlq-001',
    'trace-dlq-001',
    '{"event_type":"user.created","user_id":999,"email":"pii@example.com","source":"api"}',
    'manual_test'
  );

  INSERT INTO events (event_id, trace_id, payload, status, reason, created_at, updated_at)
  SELECT event_id, trace_id, payload, 'received', NULL, NOW(), NOW()
  FROM dlq_events
  WHERE event_id = 'test-dlq-001'
  ON CONFLICT (event_id) DO NOTHING;

  DELETE FROM dlq_events
  WHERE event_id = 'test-dlq-001';
END$$;

-- Verify
SELECT event_id, status FROM events WHERE event_id = 'test-dlq-001';
SELECT event_id FROM dlq_events WHERE event_id = 'test-dlq-001';
SELECT payload->>'email' AS email_masked FROM events_masked WHERE event_id = 'test-dlq-001';
