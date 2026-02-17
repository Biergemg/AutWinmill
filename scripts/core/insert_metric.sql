INSERT INTO metrics_events (metric_name, value, labels)
VALUES (:metric_name, :value, COALESCE(:labels::jsonb, '{}'::jsonb));
