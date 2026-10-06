<#
.SYNOPSIS
    Registers (or re-registers) the Windows Task Scheduler job that runs
    daily_run.ps1 every morning.

.DESCRIPTION
    Windows has no native cron daemon, so Task Scheduler is used as the
    equivalent. Run this script ONCE (as the user who should own the task)
    to create the scheduled task. Re-run it any time to update the trigger
    time or script path.

.PARAMETER Time
    Local time to run every day, 24h "HH:mm" format. Default 07:00.

.PARAMETER TaskName
    Name of the scheduled task. Default "NameGeneratorDbtDailyRun".

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\register_scheduled_task.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\register_scheduled_task.ps1 -Time 06:30
#>

param(
    [string]$Time = "07:00",
    [string]$TaskName = "NameGeneratorDbtDailyRun"
)

$ProjectDir = Split-Path -Parent $PSScriptRoot
$ScriptPath = Join-Path $ProjectDir "scripts\daily_run.ps1"

if (-not (Test-Path $ScriptPath)) {
    throw "Could not find daily_run.ps1 at $ScriptPath"
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory $ProjectDir

$Trigger = New-ScheduledTaskTrigger -Daily -At $Time

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Generates 1000 fake names and runs dbt build for name_generator_duckdb every morning." `
    -Force

Write-Output "Scheduled task '$TaskName' registered to run daily at $Time."
Write-Output "View it with:   Get-ScheduledTask -TaskName '$TaskName'"
Write-Output "Run it now with: Start-ScheduledTask -TaskName '$TaskName'"
Write-Output "Remove it with:  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
