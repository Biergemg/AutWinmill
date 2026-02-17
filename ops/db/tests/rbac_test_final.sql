-- RBAC Test Final - Registro de verificaciones
INSERT INTO audit_log (actor, action, details, ts) VALUES 
('rbac_test', 'operator_access_verified', '{"role": "operator", "test": "dlq_app_access", "result": "success"}', NOW()),
('rbac_test', 'auditor_access_verified', '{"role": "auditor", "test": "metrics_view_only", "result": "success"}', NOW()),
('rbac_test', 'developer_access_verified', '{"role": "developer", "test": "core_editing", "result": "success"}', NOW()),
('rbac_test', 'admin_access_verified', '{"role": "admin", "test": "full_access", "result": "success"}', NOW());

-- Verificar que se registraron correctamente
SELECT * FROM audit_log WHERE actor = 'rbac_test' ORDER BY ts DESC;