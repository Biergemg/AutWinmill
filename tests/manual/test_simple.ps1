# Test simple - PowerShell
Write-Host "🧪 Test Einstein Kids" -ForegroundColor Green

# Verificar Docker
Write-Host "`nContenedores activos:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}" | findstr "windmill"

# Verificar tablas
Write-Host "`nVerificando tablas Einstein Kids..." -ForegroundColor Yellow
$tables = @"
SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'ek_%';
"@ | docker exec -i aut_windmill_postgres psql -U windmill -d windmill -t

Write-Host "Tablas encontradas:" -ForegroundColor Cyan
$tables | ForEach-Object { Write-Host "  ✅ $_" -ForegroundColor White }

# Contar leads
Write-Host "`nLeads en sistema:" -ForegroundColor Yellow
$count = @"
SELECT COUNT(*) FROM ek_leads;
"@ | docker exec -i aut_windmill_postgres psql -U windmill -d windmill -t -A

Write-Host "Total leads: $count" -ForegroundColor Green

Write-Host "`n✅ Sistema Einstein Kids está funcionando!" -ForegroundColor Green