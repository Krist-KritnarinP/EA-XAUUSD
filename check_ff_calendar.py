import os
import sys
import json

sys.path.insert(0, r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4")
import gold_ai_agent as base

cal = base.fetch_economic_calendar()
print(f"Total USD events in ForexFactory calendar: {len(cal)}")
for ev in cal:
    dt_th = base.parse_event_time_thai(ev.get("date", ""))
    dt_str = dt_th.strftime("%a %Y-%m-%d %H:%M") if dt_th else ev.get("date", "")
    print(f"  [{ev.get('impact')}] {dt_str} | {ev.get('title')} (Forecast: {ev.get('forecast')}, Prev: {ev.get('previous')})")

rt_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\agent_poi_runtime_state.json"
if os.path.exists(rt_path):
    with open(rt_path, "r", encoding="utf-8") as f:
        print("\n=== POI AGENT RUNTIME STATE ===")
        print(f.read())
