import sys, os
sys.path.insert(0, r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4")
import gold_ai_agent as base_agent

try:
    events = base_agent.fetch_economic_calendar()
    print(f"Total events fetched: {len(events)}")
    for ev in events[:15]:
        print(ev)
except Exception as e:
    print(f"Error fetching calendar: {e}")
