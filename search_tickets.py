import os

mql4_logs_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Logs"
for fn in os.listdir(mql4_logs_dir):
    if fn.endswith(".log"):
        p = os.path.join(mql4_logs_dir, fn)
        with open(p, "rb") as f:
            data = f.read()
        try:
            text = data.decode("utf-16le")
        except:
            text = data.decode("latin1", errors="ignore")
        
        for ticket in [63517157, 63518512, 63533196, 63540001]:
            if str(ticket) in text:
                print(f"Found {ticket} in {fn}!")
                for line in text.split("\n"):
                    if str(ticket) in line:
                        print("  ", line.strip())
