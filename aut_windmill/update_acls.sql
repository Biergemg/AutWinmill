UPDATE folder SET extra_perms = '{"Admins": "Writer"}'::jsonb WHERE workspace_id = 'cliente-x-prod' AND name IN ('ops', 'restricted');
UPDATE folder SET extra_perms = '{"Admins": "Writer", "Developers": "Writer"}'::jsonb WHERE workspace_id = 'cliente-x-prod' AND name IN ('core', 'flows', 'shared', 'templates');
UPDATE folder SET extra_perms = '{"Admins": "Writer", "Developers": "Writer", "Operators": "Runnable", "Auditors": "Reader"}'::jsonb WHERE workspace_id = 'cliente-x-prod' AND name = 'apps';
