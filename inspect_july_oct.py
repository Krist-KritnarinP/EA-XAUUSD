# -*- coding: utf-8 -*-
import json

with open(r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v642_all_trades.json", "r", encoding="utf-8") as f:
    trades = json.load(f)

for month in ["2026.07", "2026.10"]:
    print(f"\n=== TRADES IN {month} ===")
    m_trades = [t for t in trades if (t["close_time"] and t["close_time"][:7] == month) or (not t["close_time"] and t["open_time"][:7] == month)]
    for t in m_trades:
        print(f"Ticket #{t['ticket']}: {t['open_time']} -> {t.get('close_time')} | {t['type']} {t['lots']} lots | Open: {t['open_price']} | SL: {t['sl']} | PnL: ${t['profit']:+.2f} ({t.get('exit_reason')})")
