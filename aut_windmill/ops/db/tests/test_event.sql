DELETE FROM events WHERE event_id = 'test-001';
INSERT INTO events (event_id, trace_id, payload, status)
VALUES (
  'test-001',
  'trace-001',
  '{"event_type": "user.created", "user_id": 123, "email": "test@example.com", "source": "api"}',
  'received'
)
RETURNING event_id, status;
