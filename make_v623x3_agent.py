# -*- coding: utf-8 -*-
import os

scratch = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
src = os.path.join(scratch, "gold_ai_quant_v641.py")
dst = os.path.join(scratch, "gold_ai_quant_v623x3.py")

with open(src, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("v6.4.1 HYBRID APEX QUANT ENGINE", "v6.2.3 x3 PURE LONDON & JUDAS SCALP ENGINE")
text = text.replace("v6.4.1 Hybrid Apex", "v6.2.3 x3 Pure London & Judas")
text = text.replace("v6.4.1", "v6.2.3-x3")
text = text.replace("ai_sentinel_v641.json", "ai_sentinel_v623x3.json")
text = text.replace("ai_agent_v641_runtime.log", "ai_agent_v623x3_runtime.log")

with open(dst, "w", encoding="utf-8") as f:
    f.write(text)

bat_file = os.path.join(scratch, "run_agent_v623x3.bat")
bat_content = """@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
reg add HKCU\\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1
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
"""

with open(bat_file, "w", encoding="utf-8") as f:
    f.write(bat_content)

print("SUCCESS: gold_ai_quant_v623x3.py and run_agent_v623x3.bat generated cleanly!")
