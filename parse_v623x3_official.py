# -*- coding: utf-8 -*-
import re
import os
import json
from collections import defaultdict

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log"

with open(log_path, "r", encoding="latin1") as f:
    raw_lines = f.readlines()[10147:]

open_re = re.compile(r"open #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)")
sl_re = re.compile(r"Tester: stop loss #(\d+)\s+at\s+([\d\.]+)")
tp_re = re.compile(r"Tester: take profit #(\d+)\s+at\s+([\d\.]+)")
close_re = re.compile(r"close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+.*?at price\s+([\d\.]+)")

orders = {}
trades = []

for line in raw_lines:
    m_open = open_re.search(line)
    if m_open:
        t_num, t_type, t_lots, t_price, t_sl, t_tp = m_open.groups()
        t_num = int(t_num)
        t_time = line[line.find("202"):line.find("202")+16]
        orders[t_num] = {
            "ticket": t_num, "open_time": t_time, "type": t_type.upper(),
            "lots": float(t_lots), "open_price": float(t_price),
            "sl": float(t_sl), "tp": float(t_tp),
            "close_time": None, "close_price": None, "profit": 0.0
        }

    m_sl = sl_re.search(line)
    if m_sl:
        t_num, t_price = m_sl.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["close_time"] = line[line.find("202"):line.find("202")+16]

    m_tp = tp_re.search(line)
    if m_tp:
        t_num, t_price = m_tp.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["close_time"] = line[line.find("202"):line.find("202")+16]

    m_close = close_re.search(line)
    if m_close:
        t_num, t_type, t_lots, t_price = m_close.groups()
        t_num = int(t_num)
        if t_num in orders and orders[t_num]["close_time"] is None:
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["close_time"] = line[line.find("202"):line.find("202")+16]

for t_num, o in sorted(orders.items()):
    if o["close_price"] is not None:
        pts = (o["close_price"] - o["open_price"]) if o["type"] == "BUY" else (o["open_price"] - o["close_price"])
        o["profit"] = round(pts * o["lots"] * 100.0, 2)
        trades.append(o)

print(f"Total v6.2.3 x3 trades: {len(trades)}")
print(f"Total Net: ${sum(t['profit'] for t in trades):,.2f}")

monthly = defaultdict(lambda: {"count": 0, "wins": 0, "net": 0.0})
for t in trades:
    m = t["close_time"][:7] if t["close_time"] else t["open_time"][:7]
    monthly[m]["count"] += 1
    monthly[m]["net"] += t["profit"]
    if t["profit"] > 0: monthly[m]["wins"] += 1

print("\nMonthly Breakdown v6.2.3 x3 Actual Run:")
for m in sorted(monthly.keys()):
    st = monthly[m]
    print(f"{m} | Trades: {st['count']:2d} | Wins: {st['wins']:2d} ({st['wins']/st['count']*100:4.1f}%) | Net: ${st['net']:+10.2f}")
