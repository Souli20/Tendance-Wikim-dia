$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI introuvable. Démarre Docker Desktop.' }
& docker compose stop
if ($LASTEXITCODE -ne 0) { throw 'Échec de l’arrêt Docker Compose.' }
Write-Host 'Conteneurs arrêtés. Les volumes et les données sont conservés.'
Write-Host 'Redémarrer : powershell -ExecutionPolicy Bypass -File scripts\start.ps1'
