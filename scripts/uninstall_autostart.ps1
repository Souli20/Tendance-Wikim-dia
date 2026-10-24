$ErrorActionPreference = 'Stop'
$TaskName = 'WikimediaPulse-Start'
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -eq $task) { Write-Host "Aucune tâche '$TaskName' n’est enregistrée."; exit 0 }
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
Write-Host 'Démarrage automatique désactivé. Les conteneurs en cours ne sont pas arrêtés.'
