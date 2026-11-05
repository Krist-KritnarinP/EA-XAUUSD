# -*- coding: utf-8 -*-
import os

agent_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py"
with open(agent_path, "r", encoding="utf-8") as f:
    code = f.read()

old_fetch = """def fetch_economic_calendar():
    \"\"\"Fetches and caches high-impact USD economic events for the current week\"\"\"
    global cached_calendar, cached_calendar_time
    now = time.time()
    # Cache for 2 hours
    if cached_calendar and (now - cached_calendar_time) < 7200:
        return cached_calendar

    try:
        req = urllib.request.Request(CALENDAR_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            usd_high = [e for e in data if e.get("impact") == "High" and e.get("country") == "USD"]
            cached_calendar = usd_high
            cached_calendar_time = now
            return cached_calendar
    except Exception as e:
        safe_print(f"    [Calendar Sync Error] {e}")
        return cached_calendar"""

new_fetch = """CALENDAR_CACHE_PATH = os.path.join(os.path.dirname(__file__), "calendar_cache.json")

def fetch_economic_calendar():
    \"\"\"Fetches and caches high-impact USD economic events with persistent disk fallback\"\"\"
    global cached_calendar, cached_calendar_time
    now = time.time()
    if cached_calendar and (now - cached_calendar_time) < 7200:
        return cached_calendar

    # Try live fetch
    try:
        req = urllib.request.Request(CALENDAR_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            usd_high = [e for e in data if e.get("impact") == "High" and e.get("country") == "USD"]
            if usd_high:
                cached_calendar = usd_high
                cached_calendar_time = now
                with open(CALENDAR_CACHE_PATH, "w", encoding="utf-8") as f:
                    json.dump(cached_calendar, f, indent=2)
                return cached_calendar
    except Exception as e:
        pass

    # Fallback to persistent disk cache
    if os.path.exists(CALENDAR_CACHE_PATH):
        try:
            with open(CALENDAR_CACHE_PATH, "r", encoding="utf-8") as f:
                cached_calendar = json.load(f)
                cached_calendar_time = now
                return cached_calendar
        except Exception:
            pass

    return cached_calendar"""

code = code.replace(old_fetch, new_fetch)
with open(agent_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Updated fetch_economic_calendar with disk cache fallback!")
