@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1
title Gold Sniper AI Quant v6.4.2 Institutional Apex Quant Engine - (Papers 1-4)
:loop
echo ======================================================================
echo   Starting Gold Sniper AI Quant Engine (v6.4.2 Institutional)...
echo   [Paper 4] Pure-Python Lloyd K-Means (k=3) Admissibility Gate
echo   [Paper 1] Intermarket Lead-Lag Engine (Silver XAGUSD + USDJPY)
echo   [Paper 2] Realistic XM Spread Sizing (55-65 pts Baseline)
echo   [Paper 3] Sliding ATR Exit Framework + Smart Runner Preservation
echo   [Target]  ai_sentinel_v642.json (Zero conflict with older versions)
echo ======================================================================
python -u "%~dp0gold_ai_quant_v642.py"
echo [!] Agent exited or restarted. Respawning in 2 seconds...
timeout /t 2 >nul
goto loop
