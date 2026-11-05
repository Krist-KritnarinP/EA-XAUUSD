# -*- coding: utf-8 -*-
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

# Calculate M15 EMAs
def calc_ema(values, period):
    ema = []
    multiplier = 2.0 / (period + 1.0)
    # Start with SMA
    sma = sum(values[:period]) / period
    ema.append(sma)
    for val in values[period:]:
        ema.append((val - ema[-1]) * multiplier + ema[-1])
    return [None]*(period-1) + ema

closes = [b["close"] for b in bars]
ema21 = calc_ema(closes, 21)
ema50 = calc_ema(closes, 50)
ema200 = calc_ema(closes, 200)

test_dates = ["2026.10.08 09:00", "2026.10.21 17:15", "2026.10.22 08:45", "2026.10.27 10:00"]
for td in test_dates:
    for i, b in enumerate(bars):
        if b["time"].strftime("%Y.%m.%d %H:%M") == td:
            c = b["close"]
            e21 = ema21[i]
            e50 = ema50[i]
            e200 = ema200[i]
            is_super_bear = (c < e21) and (e21 < e50) and (e50 < e200)
            print(f"Bar {td}: Close={c:.2f}, EMA21={e21:.2f}, EMA50={e50:.2f}, EMA200={e200:.2f} | Super Bear M15? {is_super_bear}")
