import json

path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_v2_5_detailed_trades.json"
trades = json.load(open(path, "r", encoding="utf-8"))

for t in trades[:5]:
    print(t['ticket'], t.keys())
    if 'modifications' in t:
        print("mods:", t['modifications'])

t19 = next((t for t in trades if t['ticket'] == 19), None)
if t19:
    print("Ticket 19:", t19)
