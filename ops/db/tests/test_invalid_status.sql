DO $$
BEGIN
  UPDATE events SET status = 'invalid_status' WHERE event_id = 'test-001';
  IF FOUND THEN
      RAISE EXCEPTION 'Should have failed with constraint violation';
  END IF;
EXCEPTION WHEN check_violation THEN
  NULL; -- Expected
END $$;
