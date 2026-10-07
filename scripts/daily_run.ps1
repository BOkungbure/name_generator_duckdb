<#
.SYNOPSIS
    Daily refresh job for the name_generator_duckdb dbt project.

.DESCRIPTION
    1. Generates 1000 new fake name records (seeds/raw_names.csv).
    2. Re-seeds DuckDB with the fresh CSV.
    3. Runs `dbt build` (run + test) against the DuckDB database.

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
    Invoke-Step -Name "Generate $NameRowCount names" -Exe "python" `
        -ArgumentList @("scripts/generate_names.py", "--rows", "$NameRowCount")

    Invoke-Step -Name "Generate product catalog" -Exe "python" `
        -ArgumentList @("scripts/generate_products.py")

    Invoke-Step -Name "Generate $SalesRowCount sales transactions" -Exe "python" `
        -ArgumentList @("scripts/generate_sales_transactions.py", "--rows", "$SalesRowCount")

    Invoke-Step -Name "dbt seed" -Exe "dbt" `
        -ArgumentList @("seed", "--profiles-dir", ".", "--full-refresh")

    Invoke-Step -Name "dbt build" -Exe "dbt" `
        -ArgumentList @("build", "--profiles-dir", ".")

    Write-Log "===== Daily run completed successfully ====="
    exit 0
}
catch {
    Write-Log "===== Daily run FAILED: $($_.Exception.Message) ====="
    exit 1
}
