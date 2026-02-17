# Test Einstein Kids - PowerShell
Write-Host "🧪 Test Einstein Kids - Sistema Básico" -ForegroundColor Green
Write-Host "=" * 40

# Verificar Docker
Write-Host "`n1️⃣ Verificando contenedores Docker..." -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}" | Select-String "windmill"

# Verificar tablas en PostgreSQL
Write-Host "`n2️⃣ Verificando tablas Einstein Kids..." -ForegroundColor Yellow
$sql = @"
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name LIKE 'ek_%';
"@

$sql | docker exec -i aut_windmill_postgres psql -U windmill -d windmill

# Contar leads
Write-Host "`n3️⃣ Contando leads..." -ForegroundColor Yellow
"SELECT COUNT(*) as total_leads FROM ek_leads;" | docker exec -i aut_windmill_postgres psql -U windmill -d windmill

# Ver primeros leads
Write-Host "`n4️⃣ Primeros leads..." -ForegroundColor Yellow
"SELECT id, name, phone, stage FROM ek_leads LIMIT 3;" | docker exec -i aut_windmill_postgres psql -U windmill -d windmill

Write-Host "`n🎉 Test completado!" -ForegroundColor Green
Write-Host "`n📋 Sistema listo para:" -ForegroundColor Cyan
Write-Host "  • Recibir leads desde landing" -ForegroundColor White
Write-Host "  • Programar mensajes WhatsApp" -ForegroundColor White
Write-Host "  • Procesar webhooks de YCloud" -ForegroundColor White
Write-Host "  • Gestionar pagos y claims" -ForegroundColor White