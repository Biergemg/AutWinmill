INSERT INTO dlq_events (event_id, trace_id, payload, reason)
SELECT event_id, trace_id, payload, COALESCE(reason, 'manual_test')
FROM events
WHERE event_id = 'test-001';
DELETE FROM events WHERE event_id = 'test-001';
SELECT * FROM dlq_events WHERE event_id = 'test-001';
