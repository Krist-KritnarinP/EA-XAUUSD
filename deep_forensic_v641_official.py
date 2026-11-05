# -*- coding: utf-8 -*-
import re
import os
import json
import struct
from datetime import datetime
from collections import defaultdict

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log"
hst_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst"

with open(log_path, "r", encoding="latin1") as f:
    raw_lines = f.readlines()

# Run starts at line 5117 and ends at 6653
run_lines = raw_lines[5117:6654]
print(f"Loaded {len(run_lines)} lines for official v6.4.1 run")

open_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?open #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)")
sl_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: stop loss #(\d+)\s+at\s+([\d\.]+)")
tp_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: take profit #(\d+)\s+at\s+([\d\.]+)")
close_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)")
desc_re = re.compile(r"\[(ASIAN SMC|SNIPER RUNNER|SWEEP FADE|NEW YORK INSTITUTIONAL|v6\.4\.1-HybridApex NY)\s+(BUY|SELL).*?\]\s+Ticket:\s+#(\d+)")

orders = {}
descriptions = {}

for line in run_lines:
    m_desc = desc_re.search(line)
    if m_desc:
        engine, side, t_num = m_desc.groups()
        t_num = int(t_num)
        if "ASIAN" in engine:
            descriptions[t_num] = "Asian Scalp"
        elif "SNIPER" in engine:
            descriptions[t_num] = "London Sniper"
        elif "NEW YORK" in engine or "NY" in engine:
            descriptions[t_num] = "New York Reversal"
        elif "SWEEP" in engine:
            descriptions[t_num] = "Sweep Fade"
        else:
            descriptions[t_num] = engine

    m_open = open_re.search(line)
    if m_open:
        t_time, t_num, t_type, t_lots, t_price, t_sl, t_tp = m_open.groups()
        t_num = int(t_num)
        orders[t_num] = {
            "ticket": t_num,
            "open_time": t_time[:16],
            "type": t_type.upper(),
            "lots": float(t_lots),
            "open_price": float(t_price),
            "sl": float(t_sl),
            "tp": float(t_tp),
            "close_time": None,
            "close_price": None,
            "exit_reason": "UNKNOWN",
            "profit": 0.0,
            "engine": "London Sniper" # default
        }

    m_sl = sl_re.search(line)
    if m_sl:
        t_time, t_num, t_price = m_sl.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["exit_reason"] = "SL"

    m_tp = tp_re.search(line)
    if m_tp:
        t_time, t_num, t_price = m_tp.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["exit_reason"] = "TP"

    m_close = close_re.search(line)
    if m_close:
        t_time, t_num, t_type, t_lots, t_price = m_close.groups()
        t_num = int(t_num)
        if t_num in orders and orders[t_num]["close_time"] is None:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["exit_reason"] = "MANUAL_OR_FRIDAY"

for t_num, eng in descriptions.items():
    if t_num in orders:
        orders[t_num]["engine"] = eng

trades = []
for t_num, ord_info in orders.items():
    if ord_info["close_price"] is not None:
        if ord_info["type"] == "BUY":
            pts = ord_info["close_price"] - ord_info["open_price"]
        else:
            pts = ord_info["open_price"] - ord_info["close_price"]
        profit = pts * ord_info["lots"] * 100.0
        ord_info["profit"] = round(profit, 2)
        trades.append(ord_info)

trades.sort(key=lambda x: x["ticket"])
print(f"Total trades parsed: {len(trades)}")
net_pnl = sum(t["profit"] for t in trades)
gross_win = sum(t["profit"] for t in trades if t["profit"] > 0)
gross_loss = sum(t["profit"] for t in trades if t["profit"] < 0)
print(f"Verification: Net PnL = ${net_pnl:,.2f} | Gross Win = ${gross_win:,.2f} | Gross Loss = ${gross_loss:,.2f}")

# Load M15 bars
bars = []
with open(hst_path, "rb") as f:
    f.read(148)
    while True:
        data = f.read(60)
        if len(data) < 60: break
        t_sec, op, hp, lp, cp, vol, sp, rvol = struct.unpack("<Qddddqiq", data)
        bars.append({
            "time": datetime.utcfromtimestamp(t_sec),
            "open": op, "high": hp, "low": lp, "close": cp
        })

print(f"Loaded {len(bars)} M15 bars from HST")
bar_map = {b["time"].strftime("%Y.%m.%d %H:%M"): i for i, b in enumerate(bars)}

# Compute Holding Hours, MAE, MFE for every trade
for t in trades:
    ot = t["open_time"]
    ct = t["close_time"]
    dt_open = datetime.strptime(ot, "%Y.%m.%d %H:%M")
    dt_close = datetime.strptime(ct, "%Y.%m.%d %H:%M") if ct else dt_open
    duration_hrs = (dt_close - dt_open).total_seconds() / 3600.0
    t["holding_hours"] = round(duration_hrs, 2)

    # MAE & MFE from bars
    idx_start = bar_map.get(ot)
    idx_end = bar_map.get(ct)
    if idx_start is not None and idx_end is not None:
        sub_bars = bars[idx_start:idx_end+1]
        if sub_bars:
            if t["type"] == "BUY":
                highest = max(b["high"] for b in sub_bars)
                lowest = min(b["low"] for b in sub_bars)
                t["mfe_usd"] = round(highest - t["open_price"], 2)
                t["mae_usd"] = round(t["open_price"] - lowest, 2)
            else:
                highest = max(b["high"] for b in sub_bars)
                lowest = min(b["low"] for b in sub_bars)
                t["mfe_usd"] = round(t["open_price"] - lowest, 2)
                t["mae_usd"] = round(highest - t["open_price"], 2)
    else:
        t["mfe_usd"] = 0.0
        t["mae_usd"] = 0.0

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v641_official_forensic.json", "w", encoding="utf-8") as f:
    json.dump(trades, f, indent=2)

print("Saved v641_official_forensic.json successfully!")
