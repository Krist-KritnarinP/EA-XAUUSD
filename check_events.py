import sys, os, json
sys.path.append(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4")
from gold_ai_agent import fetch_economic_calendar, parse_event_time_thai
from datetime import datetime, timezone, timedelta

events = fetch_economic_calendar()
print(f"Total events this week: {len(events)}")
for e in events:
    dt = parse_event_time_thai(e.get('date', ''))
    dt_str = dt.strftime('%Y-%m-%d %H:%M') if dt else 'N/A'
    print(f"{dt_str} | {e.get('title')} | Forecast: {e.get('forecast')} | Prev: {e.get('previous')}")
