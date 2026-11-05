import os

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Logs\20261031.log"
if os.path.exists(log_path):
    with open(log_path, "rb") as f:
        data = f.read()
    # Try utf-16le then cp1252
    try:
        text = data.decode("utf-16le")
    except:
        text = data.decode("latin1", errors="ignore")
    lines = text.strip().split("\n")
    print(f"Total lines: {len(lines)}")
    for l in lines[-30:]:
        print(l.strip())
