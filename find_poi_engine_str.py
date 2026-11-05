import os

for root_dir in [r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4", r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"]:
    for r, d, files in os.walk(root_dir):
        for f in files:
            if f.endswith((".mq4", ".py", ".json", ".mqh")):
                p = os.path.join(r, f)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as file:
                        txt = file.read()
                    if '"engine": "POI_v2.5"' in txt or 'POI_v2.5' in txt:
                        print("Found POI_v2.5 in:", p)
                except:
                    pass
