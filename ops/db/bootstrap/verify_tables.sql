-- Verificar tablas Einstein Kids
SELECT '=== TABLAS EINSTEIN KIDS ===' as info;

-- Verificar si existe ek_leads
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ek_leads') 
        THEN '✅ ek_leads EXISTE' 
        ELSE '❌ ek_leads NO EXISTE' 
    END as status;

-- Contar registros
SELECT 'Leads en ek_leads: ' || COUNT(*) as count FROM ek_leads;

-- Mostrar primeros 2 leads
SELECT 'Primeros leads:' as info;
SELECT id, name, phone, stage FROM ek_leads LIMIT 2;

-- Verificar ek_jobs
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ek_jobs') 
        THEN '✅ ek_jobs EXISTE' 
        ELSE '❌ ek_jobs NO EXISTE' 
    END as status;

SELECT 'Trabajos en ek_jobs: ' || COUNT(*) as count FROM ek_jobs;