CREATE TABLE IF NOT EXISTS dlq_events (
  id BIGSERIAL PRIMARY KEY,
  event_id TEXT NOT NULL,
  trace_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  reason TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dlq_trace ON dlq_events(trace_id);
