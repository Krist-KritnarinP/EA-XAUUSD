# -*- coding: utf-8 -*-
import os

scratch = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
src = os.path.join(scratch, "gold_ai_quant_v641.py")
dst = os.path.join(scratch, "gold_ai_quant_v642.py")

with open(src, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("v6.4.1 HYBRID APEX QUANT ENGINE", "v6.4.2 INSTITUTIONAL APEX QUANT ENGINE")
text = text.replace("v6.4.1 Hybrid Apex", "v6.4.2 Institutional Apex")
text = text.replace("v6.4.1", "v6.4.2")
text = text.replace("ai_sentinel_v641.json", "ai_sentinel_v642.json")
text = text.replace("ai_agent_v641_runtime.log", "ai_agent_v642_runtime.log")

with open(dst, "w", encoding="utf-8") as f:
    f.write(text)

bat_file = os.path.join(scratch, "run_agent_v642.bat")
bat_content = """@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
reg add HKCU\\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1
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
"""

with open(bat_file, "w", encoding="utf-8") as f:
    f.write(bat_content)

print("SUCCESS: gold_ai_quant_v642.py and run_agent_v642.bat generated cleanly!")
