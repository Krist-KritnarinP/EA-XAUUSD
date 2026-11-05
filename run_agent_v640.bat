@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1
title Gold Sniper AI Quant v6.4.0 Apex Quant Engine - (Papers 1-4)
:loop
echo ======================================================================
echo   Starting Gold Sniper AI Quant Engine (v6.4.0 Apex Quant)...
echo   [Paper 4] Pure-Python Lloyd K-Means (k=3) Admissibility Gate
echo   [Paper 1] Intermarket Lead-Lag Engine (Silver XAGUSD + USDJPY)
echo   [Paper 2] Dynamic Spread-Penalty Utility Sizer
echo   [Paper 3] Sliding ATR Exit Framework + Friday Sunset Cut
echo   [Target]  ai_sentinel_v640.json (Zero conflict with v6.3.8)
echo ======================================================================
python -u "%~dp0gold_ai_quant_v640.py"
echo [!] Agent exited or restarted. Respawning in 2 seconds...
timeout /t 2 >nul
goto loop
