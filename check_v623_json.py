import json

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v623x3_official_forensic.json', 'r') as f:
    d = json.load(f)

print("Keys:", d.keys())
if "trades" in d:
    print("Trades count:", len(d["trades"]))
    print("First trade:", d["trades"][0])
    print("Last trade:", d["trades"][-1])
elif "monthly" in d:
    print("Monthly:", d["monthly"])
