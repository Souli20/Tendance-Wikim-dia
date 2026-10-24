$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$StartScript = Join-Path $Root 'scripts\start.ps1'
if (-not (Test-Path $StartScript)) { throw "Script introuvable : $StartScript" }
$TaskName = 'WikimediaPulse-Start'
$Args = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $StartScript + '" -OpenDashboard'
$Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $Args -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -AtLogOn
try { $Trigger.Delay = 'PT1M' } catch { Write-Warning 'Délai non disponible sur cette version; démarrage à la connexion.' }
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description 'Démarre Wikimedia Pulse à la connexion et ouvre le dashboard.' -Force | Out-Null
Write-Host "Tâche '$TaskName' créée. Active aussi le lancement de Docker Desktop à la connexion."
Write-Host 'Tester : powershell -ExecutionPolicy Bypass -File scripts\start.ps1 -OpenDashboard'
