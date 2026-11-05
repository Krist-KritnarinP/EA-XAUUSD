import glob
import os
import struct
from datetime import datetime

pattern = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\*\GOLD1440.hst"
matches = glob.glob(pattern)

print("Found files:", matches)
for p in matches:
    mtime = datetime.fromtimestamp(os.path.getmtime(p))
    with open(p, "rb") as f:
        f.seek(148)
        data = f.read()
    total_bars = len(data) // 60
    # read last bar
    if total_bars > 0:
        last_chunk = data[(total_bars - 1) * 60 : total_bars * 60]
        time_sec, o, h, l, c, vol, spread, real_vol = struct.unpack("<qddddqiq", last_chunk)
        last_dt = datetime.utcfromtimestamp(time_sec)
        print(f"File: {p}")
        print(f"  Total Bars: {total_bars}")
        print(f"  Last Modified on Disk: {mtime}")
        print(f"  Latest Candle Date: {last_dt} | Close: ${c:.2f}")
