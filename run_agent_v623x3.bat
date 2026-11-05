@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1
title Gold Sniper AI Quant v6.2.3 x3 Pure London & Judas Engine - (Papers 1-4)
:loop
echo ======================================================================
echo   Starting Gold Sniper AI Quant Engine (v6.2.3 x3 Pure London)...
echo   [Config]  Asian Scalper & NY Reversal REMOVED
echo   [Config]  London Sniper Lot x2.5 | Judas Scalp Lot x2.0
echo   [Paper 4] Lloyd K-Means (k=3) Admissibility Gate (Cluster 0)
echo   [Paper 1] Lead-Lag Engine (Silver XAGUSD + USDJPY)
echo   [Target]  ai_sentinel_v623x3.json
echo ======================================================================
python -u "%~dp0gold_ai_quant_v623x3.py"
echo [!] Agent exited or restarted. Respawning in 2 seconds...
timeout /t 2 >nul
goto loop
