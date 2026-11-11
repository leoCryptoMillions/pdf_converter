@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start.ps1" %*
set "appExit=%ERRORLEVEL%"
if not "%appExit%"=="0" pause
exit /b %appExit%
