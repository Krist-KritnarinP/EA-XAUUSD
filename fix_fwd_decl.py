import os
import shutil

base_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
mt4_experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"

for fname in ["Gold_POI_Sniper_Master_v3_5.mq4", "Gold_POI_Sniper_Tester_v3_5.mq4"]:
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        code = f.read()

    code = code.replace("void ExportMarketState();", "void ExportMarketState(bool force = false);")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(code)
    shutil.copy2(fpath, os.path.join(mt4_experts_dir, fname))
    print(f"[OK] Updated forward declaration in {fname}")
