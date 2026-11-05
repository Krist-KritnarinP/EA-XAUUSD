# -*- coding: utf-8 -*-
import struct
from datetime import datetime

hst_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst"

bars = []
with open(hst_path, "rb") as f:
    header = f.read(148)
    while True:
        buf = f.read(60)
        if len(buf) < 60: break
        t_sec, o, h, l, c, vol, sp, rvol = struct.unpack("<QddddQiQ", buf)
        dt_str = datetime.utcfromtimestamp(t_sec).strftime("%Y.%m.%d %H:%M")
        if "2026.10.19" <= dt_str <= "2026.10.28":
            bars.append({"time": dt_str, "open": o, "high": h, "low": l, "close": c})

print(f"Bars found in 2026.10.19 - 2026.10.28: {len(bars)}")
if bars:
    print(f"Start: {bars[0]['time']} Open={bars[0]['open']}")
    print(f"End:   {bars[-1]['time']} Close={bars[-1]['close']}")
    min_l = min(b["low"] for b in bars)
    max_h = max(b["high"] for b in bars)
    print(f"Min Low={min_l}, Max High={max_h}")

# Inspect the entries of tickets #104 to #108:
# 105: 2026.10.21 17:20 SELL @ 4127.82 SL=4137.13
# 106: 2026.10.22 08:50 SELL @ 4074.70 SL=4086.02
# 107: 2026.10.22 11:20 SELL @ 4083.37 SL=4098.68
# 108: 2026.10.27 10:15 SELL @ 3996.46 SL=4006.25

for b in bars:
    if "17:15" in b["time"] or "08:45" in b["time"] or "10:15" in b["time"]:
        print(f"{b['time']} | O={b['open']:.2f} H={b['high']:.2f} L={b['low']:.2f} C={b['close']:.2f}")
