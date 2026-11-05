# -*- coding: utf-8 -*-
import re
import os
import json
from collections import defaultdict

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log"

with open(log_path, "r", encoding="latin1") as f:
    raw_lines = f.readlines()

# Find last run start
last_start_idx = 0
for i, line in enumerate(raw_lines):
    if "GoldSniper_Tester_v6_4_2_apex_quant inputs:" in line:
        last_start_idx = i

print(f"v6.4.2 run started at line {last_start_idx} of {len(raw_lines)}")
run_lines = raw_lines[last_start_idx:]

open_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?open #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)")
sl_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: stop loss #(\d+)\s+at\s+([\d\.]+)")
tp_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: take profit #(\d+)\s+at\s+([\d\.]+)")
close_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)")

orders = {}
trades = []

for line in run_lines:
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
            "profit": 0.0
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

for t_num, ord_info in orders.items():
    if ord_info["close_price"] is not None:
        if ord_info["type"] == "BUY":
            pts = ord_info["close_price"] - ord_info["open_price"]
        else:
            pts = ord_info["open_price"] - ord_info["close_price"]
        profit = pts * ord_info["lots"] * 100.0 # 1 lot = 100 oz
        ord_info["profit"] = round(profit, 2)
        trades.append(ord_info)

trades.sort(key=lambda x: x["ticket"])
print(f"Parsed {len(trades)} trades successfully!")

monthly = defaultdict(lambda: {"trades": 0, "wins": 0, "losses": 0, "gross_win": 0.0, "gross_loss": 0.0, "net": 0.0, "buys": 0, "sells": 0})
for t in trades:
    m = t["close_time"][:7] if t["close_time"] else t["open_time"][:7]
    monthly[m]["trades"] += 1
    monthly[m]["net"] += t["profit"]
    if t["type"] == "BUY":
        monthly[m]["buys"] += 1
    else:
        monthly[m]["sells"] += 1
    if t["profit"] > 0:
        monthly[m]["wins"] += 1
        monthly[m]["gross_win"] += t["profit"]
    else:
        monthly[m]["losses"] += 1
        monthly[m]["gross_loss"] += t["profit"]

print("\n" + "="*85)
print(f"{'Month':<10} | {'Trades':<6} | {'Win %':<8} | {'Buys/Sells':<12} | {'Gross Win':<12} | {'Gross Loss':<12} | {'Net Profit':<12}")
print("="*85)
total_net = 0.0
total_gw = 0.0
total_gl = 0.0
for m in sorted(monthly.keys()):
    st = monthly[m]
    wr = (st["wins"] / st["trades"] * 100) if st["trades"] > 0 else 0
    total_net += st["net"]
    total_gw += st["gross_win"]
    total_gl += st["gross_loss"]
    print(f"{m:<10} | {st['trades']:<6} | {wr:6.1f}% | {st['buys']}B / {st['sells']}S | +${st['gross_win']:10.2f} | -${abs(st['gross_loss']):10.2f} | ${st['net']:+10.2f}")

print("="*85)
print(f"Total: Net ${total_net:,.2f} | Gross Win: +${total_gw:,.2f} | Gross Loss: -${abs(total_gl):,.2f}")

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v642_all_trades.json", "w", encoding="utf-8") as f:
    json.dump(trades, f, indent=2)
