@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1
title Gold POI Sniper AI Agent v3.5 - XM MT4
:loop
echo ======================================================================
echo   Starting Gold POI Sniper AI Agent Engine (v3.5 Multi-Engine Suite)...
echo   [Core Engine] London Dual-Engine (Sniper + Judas) + NY POI Prime
echo   [AI Shield]   3-Color Macro Calendar + Zero-Duplicate Breaking RSS
echo   [Protector]   Streak Breaker + Structural Bailout Risk Scaler
echo   [Target MT4]  ai_sentinel_poi.json & ai_sentinel.json
echo ======================================================================
python -u "%~dp0gold_ai_agent_poi_v3_5.py"
echo [!] Agent exited or restarted. Respawning in 2 seconds...
timeout /t 2 >nul
goto loop
