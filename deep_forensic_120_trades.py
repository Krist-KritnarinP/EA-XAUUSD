# -*- coding: utf-8 -*-
import re
import os
import json
from collections import defaultdict
from datetime import datetime

log_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log"

with open(log_path, "r", encoding="latin1") as f:
    raw_lines = f.readlines()

orders = {}
open_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?open #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)")
sl_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: stop loss #(\d+)\s+at\s+([\d\.]+)")
tp_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?Tester: take profit #(\d+)\s+at\s+([\d\.]+)")
close_re = re.compile(r"(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}(?::\d{2})?).*?close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s*([\d\.]+)\s+tp:\s*([\d\.]+)\s+at price\s+([\d\.]+)")
engine_re = re.compile(r"\[(ASIAN SMC|SNIPER RUNNER|SWEEP FADE|v6\.4\.1-HybridApex NY)\s+(BUY|SELL).*?\]\s+Ticket:\s+#(\d+)")
bailout_pnl_re = re.compile(r"Ticket #(\d+).*?cut early at\s+([-\+\$\d\.]+)")
sunset_pnl_re = re.compile(r"Sniper #(\d+)\s+locked profit\s+([-\+\$\d\.]+)")
partial_pnl_re = re.compile(r"Closed 50%.*?Ticket:? #?(\d+).*?([-\+\$\d\.]+) USD")

pnl_hints = {}

def clean_float(s):
    # s could be "-$37.44" or "+$18.41"
    is_neg = "-" in s
    num_str = re.sub(r"[^\d\.]", "", s)
    if not num_str: return 0.0
    val = float(num_str)
    return -val if is_neg else val

for line in raw_lines:
    m_eng = engine_re.search(line)
    if m_eng:
        eng, side, num = m_eng.groups()
        if int(num) not in orders:
            orders[int(num)] = {}
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
            "sl_dist": abs(float(t_price) - float(t_sl)),
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
            # Standard MT4 contract size 100
            diff = (o["close_price"] - o["open_price"]) if o["type"] == "BUY" else (o["open_price"] - o["close_price"])
            o["pnl"] = round(diff * o["lots"] * 100.0, 2)
        trades.append(o)

print(f"Parsed {len(trades)} complete trades")
with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\forensic_trades.json", "w") as f:
    json.dump(trades, f, indent=2)

# Group by Month
by_month = defaultdict(list)
for t in trades:
    m = t["open_time"][:7] # YYYY.MM
    by_month[m].append(t)

print("\n=== MONTHLY BREAKDOWN ===")
for m in sorted(by_month.keys()):
    t_list = by_month[m]
    wins = [t for t in t_list if t["pnl"] > 0]
    losses = [t for t in t_list if t["pnl"] <= 0]
    pnl = sum(t["pnl"] for t in t_list)
    wr = len(wins)/len(t_list)*100 if t_list else 0
    print(f"{m}: Trades={len(t_list):2d} | WinRate={wr:5.1f}% ({len(wins)}W/{len(losses)}L) | PnL=${pnl:+8.2f}")

# Group by Session / Engine
by_eng = defaultdict(list)
for t in trades:
    by_eng[t["engine"]].append(t)

print("\n=== ENGINE BREAKDOWN ===")
for eng, t_list in by_eng.items():
    wins = [t for t in t_list if t["pnl"] > 0]
    losses = [t for t in t_list if t["pnl"] <= 0]
    pnl = sum(t["pnl"] for t in t_list)
    wr = len(wins)/len(t_list)*100 if t_list else 0
    print(f"{eng:25s}: Trades={len(t_list):2d} | WinRate={wr:5.1f}% ({len(wins)}W/{len(losses)}L) | PnL=${pnl:+8.2f}")

# Analyze Year-End (Oct, Nov, Dec 2025)
year_end = [t for t in trades if t["open_time"][:4] == "2025" and t["open_time"][5:7] in ["10", "11", "12"]]
print(f"\n=== YEAR-END 2025 FORENSIC (Oct-Dec 2025) ===")
print(f"Total trades: {len(year_end)}")
ye_wins = [t for t in year_end if t["pnl"] > 0]
ye_losses = [t for t in year_end if t["pnl"] <= 0]
ye_pnl = sum(t["pnl"] for t in year_end)
print(f"Year-End WinRate: {len(ye_wins)/len(year_end)*100:.1f}% ({len(ye_wins)}W/{len(ye_losses)}L) | PnL=${ye_pnl:+.2f}")

ye_buys = [t for t in year_end if t["type"] == "BUY"]
ye_sells = [t for t in year_end if t["type"] == "SELL"]
print(f"BUY trades: {len(ye_buys)} (Wins: {len([t for t in ye_buys if t['pnl']>0])}, Loss: {len([t for t in ye_buys if t['pnl']<=0])}) | PnL=${sum(t['pnl'] for t in ye_buys):+.2f}")
print(f"SELL trades: {len(ye_sells)} (Wins: {len([t for t in ye_sells if t['pnl']>0])}, Loss: {len([t for t in ye_sells if t['pnl']<=0])}) | PnL=${sum(t['pnl'] for t in ye_sells):+.2f}")

# Detail of all year-end losing trades
print("\n--- Year-End Losing Trades Detail ---")
for t in ye_losses:
    print(f"#{t['ticket']:2d} | {t['open_time']} | {t['engine']:15s} | {t['type']} {t['lots']} lots | Entry={t['open_price']} | SL={t['sl']} (Dist=${t['sl_dist']:.2f}) | Close={t['close_price']} ({t['close_reason']}) | PnL=${t['pnl']:+6.2f}")
