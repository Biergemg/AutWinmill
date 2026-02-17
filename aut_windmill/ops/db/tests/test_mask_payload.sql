DO $$
DECLARE
  v_res jsonb;
BEGIN
  SELECT mask_payload('{"email":"a@b.com","phone":"+123","address":"x","name":"y"}'::jsonb) INTO v_res;
  
  IF (v_res->>'email') != '[redacted]' OR (v_res->>'phone') != '[redacted]' THEN
    RAISE EXCEPTION 'Masking failed. Got: %', v_res;
  END IF;
END $$;
