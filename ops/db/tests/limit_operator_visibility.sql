-- Limitar visibilidad de Operators en Settings
-- Solo permiten ver runs, ocultar todo lo demás

UPDATE workspace_settings 
SET operator_settings = '{
  "runs": true,
  "groups": false,
  "folders": false,
  "workers": false,
  "triggers": false,
  "resources": false,
  "schedules": false,
  "variables": false,
  "audit_logs": false
}'::jsonb 
WHERE workspace_id = 'admins';

-- Verificar el cambio
SELECT workspace_id, operator_settings 
FROM workspace_settings 
WHERE workspace_id = 'admins';

-- Registrar en audit_log
INSERT INTO audit_log (actor, action, details, ts) 
VALUES ('rbac_admin', 'operator_visibility_limited', '{"workspace": "admins", "visibility": "limited_to_runs_only"}', NOW());