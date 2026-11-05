import sys, os, json
sys.path.append(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4")
from gold_ai_agent import fetch_economic_calendar

events = fetch_economic_calendar()
for e in events[:3]:
    print(e)
