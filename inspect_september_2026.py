# -*- coding: utf-8 -*-
import json
import struct
from datetime import datetime

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v623x3_official_forensic.json", "r", encoding="utf-8") as f:
    trades = json.load(f)

sep_trades = [t for t in trades if t["close_time"] and t["close_time"].startswith("2026.09")]

print(f"Total trades in September 2026: {len(sep_trades)}")
print(f"{'Ticket':<7} | {'Open Time':<16} | {'Close Time':<16} | {'Type':<4} | {'Lots':<5} | {'Open P':<8} | {'Close P':<8} | {'Pts':<6} | {'Profit USD':<12} | {'Exit':<18}")
print("-" * 110)

cum_pnl = 0.0
for t in sep_trades:
    cum_pnl += t["profit"]
    pts = (t["close_price"] - t["open_price"]) if t["type"] == "BUY" else (t["open_price"] - t["close_price"])
    print(f"#{t['ticket']:<6} | {t['open_time']:<16} | {t['close_time']:<16} | {t['type']:<4} | {t['lots']:<5.2f} | {t['open_price']:<8.2f} | {t['close_price']:<8.2f} | {pts:+6.2f} | ${t['profit']:+10.2f} | {t['exit_reason']:<18}")

print("-" * 110)
print(f"Total September 2026 Profit: ${cum_pnl:,.2f}")
