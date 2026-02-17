UPDATE events
SET status = 'validated',
    updated_at = NOW()
WHERE event_id = 'test-001'
RETURNING event_id, status, updated_at;
