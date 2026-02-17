INSERT INTO audit_log (actor, action, trace_id, workflow_id, event_id, details)
VALUES (:actor, :action, :trace_id, :workflow_id, :event_id, COALESCE(:details::jsonb, '{}'::jsonb));
