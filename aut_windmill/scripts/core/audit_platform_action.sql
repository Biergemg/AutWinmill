SELECT record_platform_action(:actor, :action, COALESCE(:details::jsonb, '{}'::jsonb));
