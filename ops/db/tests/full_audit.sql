-- Audit Groups
SELECT 'GROUPS' as audit_section, name
FROM group_
WHERE workspace_id = 'cliente-x-prod';

-- Audit Users and Assignments
SELECT 'USER_ASSIGNMENTS' as audit_section, u.username, u.email, g.name as group_name
FROM usr_to_group ug
JOIN usr u ON ug.usr = u.username
JOIN group_ g ON ug.group_ = g.name AND ug.workspace_id = g.workspace_id
WHERE ug.workspace_id = 'cliente-x-prod'
ORDER BY u.username;

-- Audit Folders and Permissions
SELECT 'FOLDER_PERMS' as audit_section, name, extra_perms
FROM folder
WHERE workspace_id = 'cliente-x-prod'
ORDER BY name;
