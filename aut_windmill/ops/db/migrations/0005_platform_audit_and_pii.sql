-- Platform audit helper and PII masking view
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc WHERE proname = 'record_platform_action'
  ) THEN
    CREATE OR REPLACE FUNCTION record_platform_action(
      p_actor TEXT,
      p_action TEXT,
      p_details JSONB DEFAULT '{}'::jsonb
    )
    RETURNS VOID
    LANGUAGE plpgsql
    AS $func$
    DECLARE
      allowed_actions TEXT[] := ARRAY[
        'rbac_change',
        'secret_rotated',
        'service_token_issued',
        'service_token_revoked',
        'feature_flag_changed',
        'rules_version_published',
        'break_glass_used',
        'requeue',
        'rbac_test'
      ];
    BEGIN
      IF p_action IS NULL OR NOT (p_action = ANY (allowed_actions)) THEN
        RAISE EXCEPTION 'Invalid platform action: %', p_action;
      END IF;

      INSERT INTO audit_log (actor, action, trace_id, workflow_id, event_id, details)
      VALUES (p_actor, p_action, NULL, NULL, NULL, COALESCE(p_details, '{}'::jsonb));
    END;
    $func$;
  END IF;
END$$;

-- Masking function for common PII fields in a flat JSON payload
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_proc WHERE proname = 'mask_payload'
  ) THEN
    CREATE OR REPLACE FUNCTION mask_payload(p_payload JSONB)
    RETURNS JSONB
    LANGUAGE sql
    AS $func$
      SELECT
        jsonb_set(
          jsonb_set(
            jsonb_set(
              jsonb_set(
                COALESCE(p_payload, '{}'::jsonb),
                '{email}', '"[redacted]"'::jsonb, true
              ),
              '{phone}', '"[redacted]"'::jsonb, true
            ),
            '{address}', '"[redacted]"'::jsonb, true
          ),
          '{name}', '"[redacted]"'::jsonb, true
        );
    $func$;
  END IF;
END$$;

-- Masked view for events
CREATE OR REPLACE VIEW events_masked AS
SELECT
  id,
  event_id,
  trace_id,
  mask_payload(payload) AS payload,
  status,
  reason,
  created_at,
  updated_at
FROM events;
