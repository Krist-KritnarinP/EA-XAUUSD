file_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\gold_ai_agent.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# Update NY Session in Heartbeat
old_ny_heartbeat = '''    elif h >= 15 and (h < 17 or (h == 17 and m <= 30)):
        session_name = "🗽 New York Confirmed Reversal"
        session_hours = "15:00 - 17:30 (MT4) | 19:00 - 21:30 น. (ไทย)"'''

new_ny_heartbeat = '''    elif h >= 16 and (h < 18 or (h == 18 and m <= 30)):
        session_name = "🗽 New York Institutional Trend-Rider"
        session_hours = "16:00 - 18:30 (MT4) | 20:00 - 22:30 น. (ไทย)"'''

if old_ny_heartbeat in code:
    code = code.replace(old_ny_heartbeat, new_ny_heartbeat)
    print("1. Updated NY session in heartbeat!")
else:
    print("1. WARNING: old_ny_heartbeat not found")

# Update Version strings
code = code.replace("v6.3.1", "v6.3.2")
code = code.replace("New York Confirmed Reversal", "New York Institutional Trend-Rider")
code = code.replace("New York Reversal", "New York Trend-Rider")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Saved updated gold_ai_agent.py")
