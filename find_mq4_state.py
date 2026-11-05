import os

experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
for fn in os.listdir(experts_dir):
    if fn.endswith(".mq4"):
        p = os.path.join(experts_dir, fn)
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            c = f.read()
        if "market_state.json" in c:
            print(f"File {fn} writes/uses market_state.json")
