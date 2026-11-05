import os

for path in [
    r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Master_v3_5.mq4",
    r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v3_5.mq4"
]:
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()

    old_s1 = 'if(StringFind(content, ""stand_down": true") >= 0)'
    new_s1 = 'if(StringFind(content, "stand_down\\": true") >= 0 || StringFind(content, "stand_down\\":true") >= 0)'
    
    old_s2 = 'int pos = StringFind(content, ""ai_risk_multiplier":");'
    new_s2 = 'int pos = StringFind(content, "ai_risk_multiplier\\":");'

    if old_s1 in c:
        c = c.replace(old_s1, new_s1)
        print(f"Replaced s1 in {os.path.basename(path)}")
    else:
        print(f"s1 not found in {os.path.basename(path)}")

    if old_s2 in c:
        c = c.replace(old_s2, new_s2)
        print(f"Replaced s2 in {os.path.basename(path)}")
    else:
        print(f"s2 not found in {os.path.basename(path)}")

    with open(path, "w", encoding="utf-8") as f:
        f.write(c)

print("Update completed.")
