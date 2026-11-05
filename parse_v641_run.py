# -*- coding: utf-8 -*-
import re
import os
import sys
from datetime import datetime

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log"

with open(log_path, "r", encoding="latin1") as f:
    raw_lines = f.readlines()

orders = {}
trades = []

# Match: 2026.07.17 14:45:00 ... open #83 sell 0.02 GOLD at 3994.76 sl: 4001.09 tp: 3963.11
open_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?open #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)")
sl_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: stop loss #(\d+)\s+at\s+([\d\.]+)")
tp_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: take profit #(\d+)\s+at\s+([\d\.]+)")
close_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)")
desc_re = re.compile(r"\[(ASIAN SMC|SNIPER RUNNER|SWEEP FADE|v6\.4\.1-HybridApex NY)\s+(BUY|SELL).*?\]\s+Ticket:\s+#(\d+)")

descriptions = {}

for line in raw_lines:
    m_desc = desc_re.search(line)
    if m_desc:
        engine, side, t_num = m_desc.groups()
        descriptions[int(t_num)] = engine

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
            "init_sl_dist": abs(float(t_price) - float(t_sl)),
            "close_time": None,
            "close_price": None,
            "close_reason": None,
            "pnl": 0.0,
            "engine": "UNKNOWN"
        }
        continue

    m_sl = sl_re.search(line)
    if m_sl:
        t_time, t_num, t_price = m_sl.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["close_reason"] = "SL"
        continue

    m_tp = tp_re.search(line)
    if m_tp:
        t_time, t_num, t_price = m_tp.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["close_reason"] = "TP"
        continue

    m_close = close_re.search(line)
    if m_close:
        t_time, t_num, t_type, t_lots, t_price = m_close.groups()
        t_num = int(t_num)
        if t_num in orders and orders[t_num]["close_time"] is None:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["close_reason"] = "MANUAL/SUNSET"
        continue

for t_num, o in sorted(orders.items()):
    if t_num in descriptions:
        o["engine"] = descriptions[t_num]
    if o["close_price"] is not None:
        if o["type"] == "BUY":
            o["pnl"] = round((o["close_price"] - o["open_price"]) * o["lots"] * 100.0, 2)
        else:
            o["pnl"] = round((o["open_price"] - o["close_price"]) * o["lots"] * 100.0, 2)
        trades.append(o)

print(f"Total parsed closed trades: {len(trades)}")
win_trades = [t for t in trades if t["pnl"] > 0]
loss_trades = [t for t in trades if t["pnl"] <= 0]
total_pnl = sum(t["pnl"] for t in trades)
gross_profit = sum(t["pnl"] for t in win_trades)
gross_loss = sum(t["pnl"] for t in loss_trades)

print(f"Total PnL: {total_pnl:.2f}")
print(f"Gross Profit: {gross_profit:.2f}")
print(f"Gross Loss: {gross_loss:.2f}")
print(f"Wins: {len(win_trades)}, Losses: {len(loss_trades)}")
print(f"Win Rate: {len(win_trades)/len(trades)*100:.2f}%")

# Let's save trades to json for detailed analysis
import json
with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v641_trades.json", "w") as f:
    json.dump(trades, f, indent=2)
print("Saved v641_trades.json successfully.")
