# -*- coding: utf-8 -*-
"""
Examine the exact price movement after each of the 18 losing BUY trades in Year-End 2025:
Does expanding SL save them, or does it make losses bigger?
"""
import struct
import os
import json
from datetime import datetime

hst_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst"

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\forensic_trades.json", "r") as f:
    trades = json.load(f)

# Filter year-end losing BUY trades
ye_losses = [t for t in trades if t["open_time"][:4] == "2025" and t["open_time"][5:7] in ["10", "11", "12"] and t["pnl"] <= 0 and t["type"] == "BUY"]

# Read M15 bars from HST
# MT4 HST format for build 509+:
# Header: 148 bytes
# Bar: int64 time (8), double open (8), double high (8), double low (8), double close (8), int64 volume (8), int32 spread (4), int64 real_vol (8) = 60 bytes per bar
bars = []
with open(hst_path, "rb") as f:
    header = f.read(148)
    while True:
        buf = f.read(60)
        if len(buf) < 60: break
        t_sec, o, h, l, c, vol, sp, rvol = struct.unpack("<QddddQiQ", buf)
        dt_str = datetime.utcfromtimestamp(t_sec).strftime("%Y.%m.%d %H:%M")
        bars.append({"time": dt_str, "ts": t_sec, "open": o, "high": h, "low": l, "close": c})

bar_map = {b["time"]: idx for idx, b in enumerate(bars)}
print(f"Total M15 bars in HST: {len(bars)}")

print("\n=== SL EXPANSION FORENSIC SIMULATION ===")
# For each losing BUY trade, check:
# 1. Actual SL distance ($)
# 2. Maximum Drawdown after entry (Lowest low reached within next 24 hours / 96 bars)
# 3. Maximum Potential Profit (Highest high reached within next 24 hours / 96 bars)
# 4. If SL had been doubled (2x) or tripled (3x), would it have hit TP first or hit 2x/3x SL?

saved_by_2x = 0
worse_with_2x = 0
saved_by_3x = 0
worse_with_3x = 0

for t in ye_losses:
    t_time = t["open_time"]
    entry = t["open_price"]
    actual_sl = t["sl"]
    actual_sl_dist = t["sl_dist"]
    actual_tp = t["tp"]
    actual_tp_dist = abs(t["tp"] - entry)
    
    # Find matching bar
    idx = -1
    for i, b in enumerate(bars):
        if b["time"] >= t_time:
            idx = i
            break
            
    if idx == -1:
        print(f"Ticket #{t['ticket']} time {t_time} not found in HST")
        continue

    # Look ahead 96 bars (24 hours)
    lookahead = bars[idx: min(len(bars), idx + 96)]
    min_low = min(b["low"] for b in lookahead)
    max_high = max(b["high"] for b in lookahead)
    
    max_adverse_drop = entry - min_low
    max_favorable_rally = max_high - entry
    
    # Check 2x SL ($)
    sl_2x = entry - (actual_sl_dist * 2.0)
    sl_3x = entry - (actual_sl_dist * 3.0)
    
    # Did price hit TP before hitting 2x SL?
    hit_tp_first_2x = False
    hit_sl_first_2x = False
    for b in lookahead:
        if b["high"] >= actual_tp:
            hit_tp_first_2x = True
            break
        if b["low"] <= sl_2x:
            hit_sl_first_2x = True
            break

    # Did price hit TP before hitting 3x SL?
    hit_tp_first_3x = False
    hit_sl_first_3x = False
    for b in lookahead:
        if b["high"] >= actual_tp:
            hit_tp_first_3x = True
            break
        if b["low"] <= sl_3x:
            hit_sl_first_3x = True
            break

    status_2x = "SAVED (Hit TP)" if hit_tp_first_2x else ("STILL HIT SL (-2x LOSS)" if hit_sl_first_2x else "FLAT")
    status_3x = "SAVED (Hit TP)" if hit_tp_first_3x else ("STILL HIT SL (-3x LOSS)" if hit_sl_first_3x else "FLAT")
    
    if hit_tp_first_2x: saved_by_2x += 1
    elif hit_sl_first_2x: worse_with_2x += 1
    
    if hit_tp_first_3x: saved_by_3x += 1
    elif hit_sl_first_3x: worse_with_3x += 1

    print(f"Ticket #{t['ticket']:2d} ({t['engine']:11s}) | Entry={entry:.2f} | Orig SL Dist=${actual_sl_dist:.2f} | Max Drop=${max_adverse_drop:.2f} | Max Rally=${max_favorable_rally:.2f}")
    print(f"   --> 2x SL (${actual_sl_dist*2:.2f}): {status_2x} | 3x SL (${actual_sl_dist*3:.2f}): {status_3x}")

print("\n=== FINAL VERDICT ON INCREASING SL ===")
print(f"If SL is DOUBLED (2x SL): Saved trades = {saved_by_2x}/{len(ye_losses)}, Lost MORE money (2x SL hit) = {worse_with_2x}/{len(ye_losses)}")
print(f"If SL is TRIPLED (3x SL): Saved trades = {saved_by_3x}/{len(ye_losses)}, Lost MORE money (3x SL hit) = {worse_with_3x}/{len(ye_losses)}")
