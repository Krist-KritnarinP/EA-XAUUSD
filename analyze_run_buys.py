# -*- coding: utf-8 -*-
import re
import os
import json

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log"

with open(log_path, "r", encoding="latin1") as f:
    lines = f.readlines()

last_start_idx = 0
for i, line in enumerate(lines):
    if "GoldSniper_Tester_v6_4_1_apex_quant inputs:" in line:
        last_start_idx = i

print(f"Latest test started at line {last_start_idx} of {len(lines)}")
run_lines = lines[last_start_idx:]

open_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?open #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)")
sl_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: stop loss #(\d+)\s+at\s+([\d\.]+)")
tp_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: take profit #(\d+)\s+at\s+([\d\.]+)")
close_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)\s+at price\s+([\d\.]+)")
engine_re = re.compile(r"\[(ASIAN SMC|SNIPER RUNNER|SWEEP FADE|v6\.\d\.\d.*?NY)\s+(BUY|SELL).*?\]\s+Ticket:\s+#(\d+)")

orders = {}
pnl_hints = {}
bailout_pnl_re = re.compile(r"Ticket #(\d+).*?cut early at\s+([-\+\$\d\.]+)")
sunset_pnl_re = re.compile(r"Sniper #(\d+)\s+locked profit\s+([-\+\$\d\.]+)")

def clean_float(s):
    is_neg = "-" in s
    num_str = re.sub(r"[^\d\.]", "", s)
    if not num_str: return 0.0
    val = float(num_str)
    return -val if is_neg else val

for line in run_lines:
    m_eng = engine_re.search(line)
    if m_eng:
        eng, side, num = m_eng.groups()
        if int(num) not in orders: orders[int(num)] = {}
        orders[int(num)]["engine"] = eng

    m_b = bailout_pnl_re.search(line)
    if m_b:
        num, val = m_b.groups()
        pnl_hints[int(num)] = clean_float(val)

    m_s = sunset_pnl_re.search(line)
    if m_s:
        num, val = m_s.groups()
        pnl_hints[int(num)] = clean_float(val)

    m_open = open_re.search(line)
    if m_open:
        t_time, t_num, t_type, t_lots, t_price, t_sl, t_tp = m_open.groups()
        t_num = int(t_num)
        if t_num not in orders: orders[t_num] = {}
        orders[t_num].update({
            "ticket": t_num,
            "open_time": t_time[:16],
            "type": t_type.upper(),
            "lots": float(t_lots),
            "open_price": float(t_price),
            "sl": float(t_sl),
            "tp": float(t_tp),
            "close_time": None,
            "close_price": None,
            "close_reason": None,
            "pnl": 0.0,
            "engine": orders[t_num].get("engine", "UNKNOWN")
        })

    m_sl = sl_re.search(line)
    if m_sl:
        t_time, t_num, t_price = m_sl.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["close_reason"] = "SL"

    m_tp = tp_re.search(line)
    if m_tp:
        t_time, t_num, t_price = m_tp.groups()
        t_num = int(t_num)
        if t_num in orders:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_price)
            orders[t_num]["close_reason"] = "TP"

    m_c = close_re.search(line)
    if m_c:
        t_time, t_num, t_type, t_lots, t_open, t_sl, t_tp, t_close = m_c.groups()
        t_num = int(t_num)
        if t_num in orders and orders[t_num].get("close_price") is None:
            orders[t_num]["close_time"] = t_time[:16]
            orders[t_num]["close_price"] = float(t_close)
            orders[t_num]["close_reason"] = "MANUAL_CLOSE"

trades = []
for t_num, o in sorted(orders.items()):
    if "open_price" in o and o["close_price"] is not None:
        if t_num in pnl_hints:
            o["pnl"] = pnl_hints[t_num]
        else:
            diff = (o["close_price"] - o["open_price"]) if o["type"] == "BUY" else (o["open_price"] - o["close_price"])
            o["pnl"] = round(diff * o["lots"] * 100.0, 2)
        trades.append(o)

print(f"Total trades parsed: {len(trades)}")
buy_trades = [t for t in trades if t["type"] == "BUY"]
sell_trades = [t for t in trades if t["type"] == "SELL"]
losing_buys = [t for t in buy_trades if t["pnl"] <= 0]
winning_buys = [t for t in buy_trades if t["pnl"] > 0]
losing_sells = [t for t in sell_trades if t["pnl"] <= 0]
winning_sells = [t for t in sell_trades if t["pnl"] > 0]

print(f"\nSELL TRADES: {len(sell_trades)} | Wins={len(winning_sells)} ({len(winning_sells)/len(sell_trades)*100:.1f}%) | Losses={len(losing_sells)} | PnL=${sum(t['pnl'] for t in sell_trades):+.2f}")
print(f"BUY TRADES:  {len(buy_trades)} | Wins={len(winning_buys)} ({len(winning_buys)/len(buy_trades)*100:.1f}%) | Losses={len(losing_buys)} | PnL=${sum(t['pnl'] for t in buy_trades):+.2f}")

print("\n--- LOSING BUY TRADES BY ENGINE ---")
from collections import defaultdict
eng_losing_buys = defaultdict(list)
for t in losing_buys:
    eng_losing_buys[t["engine"]].append(t)

for eng, t_list in eng_losing_buys.items():
    print(f"{eng:25s}: {len(t_list)} losses, total loss = ${sum(t['pnl'] for t in t_list):.2f}")

print("\n--- SAMPLE 15 LOSING BUYS ---")
for t in losing_buys[:15]:
    print(f"Ticket #{t['ticket']:2d} | {t['open_time']} | {t['engine']:15s} | Lots={t['lots']} | Entry={t['open_price']} | SL={t['sl']} | PnL=${t['pnl']:+6.2f}")
