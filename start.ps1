<#
.SYNOPSIS
    Ethical Online Exam Proctoring POC - Startup Script
.DESCRIPTION
    1. Creates the .venv virtual environment if it is missing.
    2. Installs requirements.txt whenever it changed since the last install (or imports fail).
    3. Ensures .env contains UIPATH_API_KEY and SECRET_KEY (never overwrites existing values).
    4. Seeds the demo database when it is missing/empty, or when -Seed is passed.
    5. Optionally runs the test suite (-Test), then boots the Flask server.
.PARAMETER Port
    Port to run the application on (Default: 5000, or $env:PORT if set)
.PARAMETER Seed
    Force re-seeding of database with demo data
.PARAMETER Test
    Run the pytest suite before starting; abort startup if it fails
.PARAMETER SkipInstall
    Skip the dependency check/install step
#>
param(
    [int]$Port = $(if ($env:PORT) { [int]$env:PORT } else { 5000 }),
    [switch]$Seed,
    [switch]$Test,
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Write-Step($msg)  { Write-Host "[*] $msg" -ForegroundColor Yellow }
function Write-Ok($msg)    { Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Fail($msg)  { Write-Host "[ERROR] $msg" -ForegroundColor Red }

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Ethical Online Exam Proctoring POC - Startup Script   " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Virtual environment detection / setup
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Step "Virtual environment not found at .venv. Creating one..."
    $BasePython = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } elseif (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { $null }
    if (-not $BasePython) {
        Write-Fail "Python was not found in PATH. Install Python 3.12+ and retry."
        exit 1
    }
    & $BasePython -m venv .venv
    if (-not (Test-Path $VenvPython)) {
        Write-Fail "Failed to create virtual environment."
        exit 1
    }
    Write-Ok "Virtual environment created."
}

# 2. Dependencies: reinstall when requirements.txt is newer than the last install stamp
if (-not $SkipInstall) {
    $Requirements = Join-Path $ScriptDir "requirements.txt"
    $Stamp = Join-Path $ScriptDir ".venv\.requirements-installed"
    $needsInstall = (-not (Test-Path $Stamp)) -or ((Get-Item $Requirements).LastWriteTime -gt (Get-Item $Stamp).LastWriteTime)
    if (-not $needsInstall) {
        & $VenvPython -c "import flask, flask_sqlalchemy, cv2, numpy" 2>$null
        $needsInstall = ($LASTEXITCODE -ne 0)
    }
    if ($needsInstall) {
        Write-Step "Installing dependencies from requirements.txt..."
        & $VenvPython -m pip install --disable-pip-version-check -r $Requirements
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Dependency installation failed."
            exit 1
        }
        Set-Content -Path $Stamp -Value (Get-Date -Format o)
        Write-Ok "Dependencies installed."
    } else {
        Write-Ok "Dependencies up to date."
    }
}

# 3. .env: add missing keys only. The UiPath key must match uipath\ExamProctoring\Data\config.json.
$EnvFile = Join-Path $ScriptDir ".env"
$existing = @{}
if (Test-Path $EnvFile) {
    foreach ($line in Get-Content $EnvFile) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') { $existing[$Matches[1]] = $true }
    }
}
$UiPathConfig = Join-Path $ScriptDir "uipath\ExamProctoring\Data\config.json"
$UiPathKey = "poc-uipath-local-key"
if (Test-Path $UiPathConfig) {
    try { $UiPathKey = (Get-Content $UiPathConfig -Raw | ConvertFrom-Json).ApiKey } catch { }
}
$defaults = [ordered]@{
    UIPATH_API_KEY = $UiPathKey
    SECRET_KEY     = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
}
$added = @()
foreach ($key in $defaults.Keys) {
    if (-not $existing.ContainsKey($key)) {
        Add-Content -Path $EnvFile -Value "$key=$($defaults[$key])"
        $added += $key
    }
}
if ($added.Count) { Write-Ok "Added to .env: $($added -join ', ')" } else { Write-Ok ".env configuration present." }

# 4. Database initialization / seed
$DbPath = Join-Path $ScriptDir "instance\exam.db"
if ($Seed -or (-not (Test-Path $DbPath)) -or ((Get-Item $DbPath).Length -eq 0)) {
    Write-Step "Initializing and seeding demo exam database..."
    & $VenvPython seed.py
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Database seeding failed."
        exit 1
    }
    Write-Ok "Database seeded."
}

# 5. Optional test run
if ($Test) {
    Write-Step "Running test suite..."
    & $VenvPython -m pytest -q tests
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Tests failed; not starting the server."
        exit 1
    }
    Write-Ok "All tests passed."
}

# 6. Port availability
$inUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($inUse) {
    $owner = (Get-Process -Id $inUse[0].OwningProcess -ErrorAction SilentlyContinue).ProcessName
    Write-Fail "Port $Port is already in use (process: $owner). Stop it or pass -Port <other>."
    exit 1
}

# 7. Launch Application
$env:PORT = $Port.ToString()
Write-Host ""
Write-Ok "Environment ready. Starting application..."
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host " - Student Portal:   http://127.0.0.1:$Port/student" -ForegroundColor Cyan
Write-Host " - Faculty Portal:   http://127.0.0.1:$Port/faculty" -ForegroundColor Cyan
Write-Host " - API Health:       http://127.0.0.1:$Port/api/health" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host "Press Ctrl+C to terminate the server.`n" -ForegroundColor DarkGray

& $VenvPython run.py
