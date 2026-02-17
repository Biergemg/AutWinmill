-- Clean previous run
DELETE FROM audit_log WHERE actor='qa' AND action='rbac_test';

SELECT record_platform_action('qa', 'rbac_test', '{"test":true}'::jsonb);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM audit_log WHERE actor='qa' AND action='rbac_test') THEN
    RAISE EXCEPTION 'Audit log entry not found';
  END IF;
END $$;
