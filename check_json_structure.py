import json

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v623x3_official_forensic.json', 'r') as f:
    d = json.load(f)

print("List len:", len(d))
print("Item 0:", d[0])
print("Item -1:", d[-1])

# Also check poi_v2_5_detailed_trades.json
with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_v2_5_detailed_trades.json', 'r') as f:
    poi = json.load(f)
print("\nPOI type:", type(poi))
if isinstance(poi, list):
    print("POI len:", len(poi))
    print("POI item 0:", poi[0])
elif isinstance(poi, dict):
    print("POI keys:", poi.keys())
