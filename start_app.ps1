# Script para levantar ECOS de forma unificada (Backend y Frontend)

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " INICIANDO ECOS (Early Control System)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Asegurarse de que el frontend tenga los modulos
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "`n[Frontend] Instalando dependencias (esto solo pasa una vez)..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

# 2. Iniciar el Backend (FastAPI) en segundo plano
Write-Host "`n[Backend] Iniciando servidor de API en puerto 8000..." -ForegroundColor Green
$pythonCmd = if (Get-Command "py" -ErrorAction SilentlyContinue) { "py" } else { "python" }
Start-Process "cmd.exe" -ArgumentList "/k $pythonCmd -m fastapi dev backend/app/main.py --port 8000"

# 3. Iniciar el Frontend (Next.js) en segundo plano
Write-Host "`n[Frontend] Iniciando interfaz de usuario en puerto 3000..." -ForegroundColor Green
Set-Location frontend
Start-Process "cmd.exe" -ArgumentList "/k npm run dev"
Set-Location ..

Write-Host "`n¡Todo listo!" -ForegroundColor Magenta
Write-Host "Abriendo el navegador en http://localhost:3000..." -ForegroundColor Magenta

# 4. Abrir el navegador (dar tiempo a que Next.js levante)
Start-Sleep -Seconds 5
Start-Process "http://localhost:3000"

Write-Host "`nNota: Se han abierto dos ventanas minimizadas para los servidores."
Write-Host "Para detener la aplicacion, simplemente cierra esas dos ventanas negras.`n"
