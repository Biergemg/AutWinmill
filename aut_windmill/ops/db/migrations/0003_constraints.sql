ALTER TABLE events
  ADD CONSTRAINT events_event_id_uniq UNIQUE (event_id);

CREATE INDEX IF NOT EXISTS events_trace_id_idx ON events(trace_id);
CREATE INDEX IF NOT EXISTS events_status_idx ON events(status);

ALTER TABLE events
  ADD CONSTRAINT events_status_chk
  CHECK (status IN ('received','validated','queued','processed','failed','dlq'));

ALTER TABLE workflows
  ADD CONSTRAINT workflows_status_chk
  CHECK (status IN ('created','validated','planned','executing','pending_approval','completed','failed','cancelled'));
