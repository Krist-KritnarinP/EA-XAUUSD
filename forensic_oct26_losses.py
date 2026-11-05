# -*- coding: utf-8 -*-
import os
import struct
from datetime import datetime

hst_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst"

def read_hst(path):
    bars = []
    with open(path, "rb") as f:
        header = f.read(148)
        while True:
            data = f.read(60)
            if len(data) < 60:
                break
            time_sec, open_p, high_p, low_p, close_p, vol, spread, real_vol = struct.unpack("<Qddddqiq", data)
            bars.append({
                "time": datetime.utcfromtimestamp(time_sec),
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close_p
            })
    return bars

bars = read_hst(hst_path)
print(f"Loaded {len(bars)} M15 bars")

bar_dict = {b["time"].strftime("%Y.%m.%d %H:%M"): b for b in bars}

# Let's inspect the 4 losing trades in Oct 2026:
# Ticket #127: 2026.10.08 09:15 SELL Open: 4116.72 SL: 4125.04
# Ticket #129: 2026.10.21 17:20 SELL Open: 4127.82 SL: 4137.13
# Ticket #130: 2026.10.22 08:50 SELL Open: 4074.70 SL: 4086.02
# Ticket #134: 2026.10.27 10:15 SELL Open: 3996.46 SL: 4006.25

test_times = [
    ("Ticket #127", "2026.10.08 09:15", 4116.72, 4125.04),
    ("Ticket #129", "2026.10.21 17:15", 4127.82, 4137.13),
    ("Ticket #130", "2026.10.22 08:45", 4074.70, 4086.02),
    ("Ticket #134", "2026.10.27 10:15", 3996.46, 4006.25),
]

for name, t_str, entry, sl in test_times:
    print(f"\n--- {name} at {t_str} (Entry: {entry}, SL: {sl}) ---")
    # Find bar index
    found_idx = -1
    for i, b in enumerate(bars):
        if b["time"].strftime("%Y.%m.%d %H:%M") == t_str:
            found_idx = i
            break
    if found_idx == -1:
        print(f"Bar not found for {t_str}")
        continue
    
    # Print 3 bars before and 8 bars after
    print("Prior 3 bars:")
    for b in bars[found_idx-3:found_idx]:
        print(f"  {b['time'].strftime('%Y.%m.%d %H:%M')} | O: {b['open']:.2f} H: {b['high']:.2f} L: {b['low']:.2f} C: {b['close']:.2f}")
    
    b_curr = bars[found_idx]
    print(f"Signal bar: {b_curr['time'].strftime('%Y.%m.%d %H:%M')} | O: {b_curr['open']:.2f} H: {b_curr['high']:.2f} L: {b_curr['low']:.2f} C: {b_curr['close']:.2f}")
    
    print("Next 8 bars:")
    for b in bars[found_idx+1:found_idx+9]:
        print(f"  {b['time'].strftime('%Y.%m.%d %H:%M')} | O: {b['open']:.2f} H: {b['high']:.2f} L: {b['low']:.2f} C: {b['close']:.2f}")
