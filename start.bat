@echo off
setlocal
cd /d "%~dp0"
title Ethical Exam Proctoring POC

REM Delegates to start.ps1 so both launchers share one setup path.
REM Usage: start.bat [-Port 5000] [-Seed] [-Test] [-SkipInstall]
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*

pause
