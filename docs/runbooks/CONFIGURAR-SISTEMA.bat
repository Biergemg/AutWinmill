@echo off
echo CONFIGURACION RAPIDA DEL SISTEMA DE CONTROL DE PAGOS
echo =====================================================
echo.

echo 1. Verificando contenedores activos...
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo 2. Creando usuario admin en sistema base (puerto 8000)...
if "%WM_ADMIN_EMAIL%"=="" (
  echo ERROR: Debes definir WM_ADMIN_EMAIL y WM_ADMIN_PASSWORD en tu entorno local.
  goto end
)
if "%WM_ADMIN_PASSWORD%"=="" (
  echo ERROR: Debes definir WM_ADMIN_EMAIL y WM_ADMIN_PASSWORD en tu entorno local.
  goto end
)
docker exec windmill_dev_main windmill user create --email %WM_ADMIN_EMAIL% --password %WM_ADMIN_PASSWORD% --superadmin || echo Usuario ya existe o error

echo.
echo 3. Creando usuario en sistema cliente (puerto 8001)...
if "%CLIENT_ADMIN_EMAIL%"=="" (
  echo AVISO: CLIENT_ADMIN_EMAIL/CLIENT_ADMIN_PASSWORD no definidos. Se omite cliente.
) else (
  if "%CLIENT_ADMIN_PASSWORD%"=="" (
    echo AVISO: CLIENT_ADMIN_EMAIL/CLIENT_ADMIN_PASSWORD no definidos. Se omite cliente.
  ) else (
    docker exec cyn_einstein_kids_windmill windmill user create --email %CLIENT_ADMIN_EMAIL% --password %CLIENT_ADMIN_PASSWORD% --superadmin || echo Cliente con error o ya existe
  )
)

echo.
echo 4. Verificando acceso a sistemas...
echo    Sistema Base (8000): http://localhost:8000
echo    Sistema Cliente (8001): http://localhost:8001
echo    Dashboard Control (8501): http://localhost:8501
echo.
echo Configuracion completada.

:end
pause
