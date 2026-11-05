import os

log_file = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\ai_agent_runtime.log"
with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if "63533196" in line or "63540001" in line:
            print(line.strip().encode('ascii', errors='replace').decode('ascii'))
