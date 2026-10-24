[CmdletBinding()]
param([switch]$Build, [switch]$OpenDashboard)
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI introuvable. Installe/démarre Docker Desktop.' }
Write-Host 'Attente du moteur Docker (maximum 3 minutes)...'
$ready = $false
for ($i = 0; $i -lt 36; $i++) {
  & docker info *> $null
  if ($LASTEXITCODE -eq 0) { $ready = $true; break }
  Start-Sleep -Seconds 5
}
if (-not $ready) { throw 'Le moteur Docker ne répond pas. Démarre Docker Desktop et réessaie.' }
& docker compose config -q
if ($LASTEXITCODE -ne 0) { throw 'docker-compose.yml est invalide.' }
if ($Build) { & docker compose up -d --build } else { & docker compose up -d }
if ($LASTEXITCODE -ne 0) { throw 'Échec du démarrage Docker Compose.' }
Write-Host ''
& docker compose ps
Write-Host "`nDashboard : http://localhost:8502"
Write-Host 'UI Spark (si active) : http://localhost:4041'
if ($OpenDashboard) {
  Write-Host 'Attente de la réponse du dashboard...'
  $ok = $false
  for ($i = 0; $i -lt 30; $i++) {
    try {
      $r = Invoke-WebRequest -Uri 'http://localhost:8502' -UseBasicParsing -TimeoutSec 2
      if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { $ok = $true; break }
    } catch { Start-Sleep -Seconds 2 }
  }
  if (-not $ok) { Write-Warning 'Le dashboard ne répond pas encore; le navigateur va quand même s’ouvrir.' }
  Start-Process 'http://localhost:8502'
}
