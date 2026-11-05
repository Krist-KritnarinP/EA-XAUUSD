import os

base_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702"
for root, dirs, files in os.walk(base_dir):
    for fn in files:
        if fn.endswith((".mq4", ".ex4")):
            p = os.path.join(root, fn)
            try:
                with open(p, "rb") as f:
                    content = f.read()
                if b"asian_high" in content:
                    print("Found 'asian_high' in binary:", p)
            except:
                pass
