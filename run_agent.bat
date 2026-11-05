@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1
title Gold Sniper AI Agent v6.3.8-Beta - XM MT4
:loop
echo ======================================================================
echo   Starting Gold Sniper AI Agent Engine (v6.3.8-Beta Institutional)...
echo   [News Engine] 3-Color Calendar (Red/Orange/Yellow) + 2-Stage RSS
echo   [Protection]  QuickEdit click-to-freeze disabled.
echo   [Persistence] agent_runtime_state.json active.
echo ======================================================================
python -u "%~dp0gold_ai_agent.py"
echo [!] Agent exited or restarted. Respawning in 2 seconds...
timeout /t 2 >nul
goto loop
