import os

base_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702"
for root, dirs, files in os.walk(base_dir):
    for fn in files:
        if fn.endswith(".mq4"):
            p = os.path.join(root, fn)
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if "open_orders" in content:
                    print("Found open_orders in:", p)
            except:
                pass
