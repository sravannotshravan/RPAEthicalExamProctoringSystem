@echo off
setlocal
cd /d "%~dp0"
title Ethical Exam Proctoring - UiPath RPA Launcher

echo ======================================================================
echo   ETHICAL RPA ONLINE EXAM PROCTORING - SYSTEM LAUNCHER
echo ======================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_proctoring_demo.ps1" %*

pause
