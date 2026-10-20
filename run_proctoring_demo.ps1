<#
.SYNOPSIS
    Ethical RPA Exam Proctoring - Master Execution & Demonstration Launcher
.DESCRIPTION
    1. Validates the local Python environment and database.
    2. Starts the Flask backend web server on http://127.0.0.1:5000.
    3. Executes the UiPath RPA workflow (Main.xaml) in the requested execution mode.
    4. Opens the project in UiPath Studio Desktop for visual inspection.
    5. Opens the Faculty Oversight Dashboard and Student Workspace in your default browser.
.PARAMETER Mode
    Execution mode: FULL_DEMO (default), ENVIRONMENT_CHECK, PROCESS_INCIDENTS, GENERATE_REPORT, IMPORT_STUDENTS.
.PARAMETER OpenStudio
    Whether to launch UiPath Studio Desktop (default: true).
.PARAMETER OpenBrowser
    Whether to open web browser portals (default: true).
#>

param(
    [string]$Mode = "FULL_DEMO",
    [switch]$NoStudio,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Continue"
$ProjectRoot = $PSScriptRoot
$UiPathDir = Join-Path $ProjectRoot "uipath\ExamProctoring"
$ProjectJson = Join-Path $UiPathDir "project.json"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  ETHICAL RPA ONLINE EXAM PROCTORING - SYSTEM LAUNCHER & DEMO" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot"
Write-Host "UiPath Dir:   $UiPathDir"
Write-Host "Mode:         $Mode"
Write-Host ""

# 1. Verify Python & Dependencies
if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Python virtual environment not found at .venv\Scripts\python.exe" -ForegroundColor Red
    exit 1
}

# 2. Seed Database
Write-Host "[1/5] Ensuring Database is seeded..." -ForegroundColor Yellow
& $VenvPython (Join-Path $ProjectRoot "seed.py")

# 3. Start Flask Backend Server in a new window
Write-Host "[2/5] Starting Flask Backend Server (http://127.0.0.1:5000)..." -ForegroundColor Yellow
$ServerJob = Start-Process -FilePath $VenvPython -ArgumentList "run.py" -WorkingDirectory $ProjectRoot -PassThru

# Wait for server health
$healthy = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 600
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health" -Headers @{ "X-API-Key" = "poc-uipath-local-key" } -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($resp -and ($resp.status -eq "HEALTHY" -or $resp.status -eq "healthy")) {
            $healthy = $true
            break
        }
    } catch { }
}

if ($healthy) {
    Write-Host "      [OK] Flask Backend is online and healthy!" -ForegroundColor Green
} else {
    Write-Host "      [WARN] Backend taking longer to respond. Proceeding..." -ForegroundColor Yellow
}

# 4. Open UiPath Studio Desktop
if (-not $NoStudio) {
    Write-Host "[3/5] Opening Project in UiPath Studio Desktop..." -ForegroundColor Yellow
    $StudioExe = "C:\Users\srava\AppData\Local\Programs\UiPathPlatform\Studio\26.0.204-cloud.25537\UiPath.Studio.exe"
    if (-not (Test-Path $StudioExe)) {
        $found = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs" -Recurse -Filter "UiPath.Studio.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $StudioExe = $found.FullName }
    }

    if (Test-Path $StudioExe) {
        Write-Host "      Launching: $StudioExe" -ForegroundColor Gray
        Start-Process -FilePath $StudioExe -ArgumentList "`"$ProjectJson`""
        Write-Host "      [OK] UiPath Studio launched with project.json." -ForegroundColor Green
    } else {
        Write-Host "      [INFO] Opening project.json with default application..." -ForegroundColor Gray
        Invoke-Item $ProjectJson
    }
}

# 5. Open Web Portals in Default Browser
if (-not $NoBrowser) {
    Write-Host "[4/5] Opening Faculty Dashboard and Student Portals..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    Start-Process "http://127.0.0.1:5000/faculty"
    Start-Sleep -Milliseconds 500
    Start-Process "http://127.0.0.1:5000/student"
}

# 6. Execute UiPath RPA Workflow
Write-Host "[5/5] Executing UiPath RPA Robot (Mode: $Mode)..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------------------" -ForegroundColor Gray
& uip rpa run --file-path "Main.xaml" --input-arguments "in_ExecutionMode=$Mode" --project-dir $UiPathDir
Write-Host "----------------------------------------------------------------------" -ForegroundColor Gray

# 7. Display Deliverables Summary
$OutputDir = Join-Path $UiPathDir "Output"
if (Test-Path $OutputDir) {
    $reports = Get-ChildItem -Path $OutputDir -Filter "Exam_*.csv" | Sort-Object LastWriteTime -Descending
    if ($reports) {
        $latest = $reports[0]
        Write-Host ""
        Write-Host "======================================================================" -ForegroundColor Green
        Write-Host "  RPA PROCTOR AUDIT REPORT GENERATED" -ForegroundColor Green
        Write-Host "======================================================================" -ForegroundColor Green
        Write-Host "Report File: $($latest.FullName)"
        Write-Host ""
        Get-Content $latest.FullName | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }
    }
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  DEMONSTRATION RUN COMPLETE!" -ForegroundColor Green
Write-Host "  - Flask Backend is running at http://127.0.0.1:5000" -ForegroundColor White
Write-Host "  - Faculty Dashboard:         http://127.0.0.1:5000/faculty" -ForegroundColor White
Write-Host "  - Student Portal:            http://127.0.0.1:5000/student" -ForegroundColor White
Write-Host "  - UiPath Studio is opened with Main.xaml visual canvas" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
