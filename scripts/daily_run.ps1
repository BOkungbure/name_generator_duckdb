<#
.SYNOPSIS
    Daily append-and-transform job for the Neon-backed name_generator dbt project.

.DESCRIPTION
    1. Generates 1000 new fake name records (data/incoming/raw_names.csv).
    2. Generates 5000 matching sales transactions.
    3. Appends both batches to Neon using an idempotent batch date.
    4. Refreshes the small static product seed and runs dbt models and tests.

    Intended to be triggered every morning by Windows Task Scheduler
    (see scripts/register_scheduled_task.ps1).

.NOTES
    All output is appended to logs/daily_run.log with a timestamp, and the
    script exits non-zero if any step fails so Task Scheduler marks the
    run as failed.
#>

$ErrorActionPreference = "Stop"

$ProjectDir      = Split-Path -Parent $PSScriptRoot
$LogDir          = Join-Path $ProjectDir "logs"
$LogFile         = Join-Path $LogDir "daily_run.log"
$NameRowCount    = 1000
$SalesRowCount   = 5000
$BatchDate       = Get-Date -Format "yyyy-MM-dd"
$BatchSeed       = [int]($BatchDate -replace "-", "")

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$timestamp  $Message"
    Write-Output $line
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

function Invoke-Step {
    param(
        [string]$Name,
        [string]$Exe,
        [string[]]$ArgumentList
    )
    Write-Log "START  $Name"
    & $Exe @ArgumentList 2>&1 | ForEach-Object { Write-Log "  $_" }
    if ($LASTEXITCODE -ne 0) {
        Write-Log "FAILED $Name (exit code $LASTEXITCODE)"
        throw "$Name failed with exit code $LASTEXITCODE"
    }
    Write-Log "DONE   $Name"
}

Set-Location $ProjectDir

Write-Log "===== Daily run started ====="
try {
    $CondaExe = "C:\ProgramData\anaconda3\Scripts\conda.exe"
    $DbtEnv   = "C:\Users\Babs\.conda\envs\dbt-env"

    Invoke-Step -Name "Generate $NameRowCount names" -Exe $CondaExe `
        -ArgumentList @("run", "--no-capture-output", "--prefix", $DbtEnv, "python", "scripts/generate_names.py", "--rows", "$NameRowCount", "--seed", "$BatchSeed", "--batch-date", "$BatchDate")

    Invoke-Step -Name "Generate $SalesRowCount sales transactions" -Exe $CondaExe `
        -ArgumentList @("run", "--no-capture-output", "--prefix", $DbtEnv, "python", "scripts/generate_sales_transactions.py", "--rows", "$SalesRowCount", "--seed", "$BatchSeed", "--batch-date", "$BatchDate")

    Invoke-Step -Name "Append batch $BatchDate to Neon" -Exe $CondaExe `
        -ArgumentList @("run", "--no-capture-output", "--prefix", $DbtEnv, "python", "scripts/load_to_neon.py", "--batch-date", "$BatchDate")

    Invoke-Step -Name "dbt seed static product catalog" -Exe $CondaExe `
        -ArgumentList @("run", "--no-capture-output", "--prefix", $DbtEnv, "dbt", "seed", "--select", "raw_products", "--profiles-dir", ".")

    Invoke-Step -Name "dbt snapshot product catalog" -Exe $CondaExe `
        -ArgumentList @("run", "--no-capture-output", "--prefix", $DbtEnv, "dbt", "snapshot", "--select", "product_catalog_snapshot", "--profiles-dir", ".")

    Invoke-Step -Name "dbt build" -Exe $CondaExe `
        -ArgumentList @("run", "--no-capture-output", "--prefix", $DbtEnv, "dbt", "build", "--exclude", "resource_type:seed", "--profiles-dir", ".")

    Write-Log "===== Daily run completed successfully ====="
    exit 0
}
catch {
    Write-Log "===== Daily run FAILED: $($_.Exception.Message) ====="
    exit 1
}
