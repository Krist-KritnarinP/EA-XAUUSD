import json

with open('v632_parsed_trades.json', 'r') as f:
    data = json.load(f)

trades = data['trades']

print("="*80)
print("DEEP DIVE: TRADES DURING THE DRAWDOWN PERIOD (2026.05.20 - 2026.07.31)")
print("="*80)

dd_trades = [t for t in trades if ('2026.05.20' <= t['open_time'] <= '2026.07.31') or ('2025.07.01' <= t['open_time'] <= '2025.07.31')]

dd_engine_stats = {'SNIPER RUNNER': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0},
                   'NEW YORK TREND-RIDER': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0},
                   'ASIAN SQUEEZE': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}}

for t in dd_trades:
    eng = t['engine']
    pnl = t['pnl']
    st = dd_engine_stats[eng]
    st['count'] += 1
    st['pnl'] += pnl
    if pnl > 0: st['wins'] += 1
    else: st['losses'] += 1
    
    print(f"Ticket #{t['ticket']:2d} | Time: {t['open_time']} | Engine: {eng:22s} | Side: {t['side']:4s} | Lots: {t['lots']:.2f} | Open: {t['open_price']:.2f} | Close: {t.get('close_price', 0):.2f} | PnL: ${pnl:+8.2f} | Reason: {t.get('close_reason', 'N/A')}")

print("\n" + "="*80)
print("DRAWDOWN PERIOD SUMMARY BY ENGINE:")
for eng, st in dd_engine_stats.items():
    print(f"Engine: {eng:22s} | Trades: {st['count']:2d} | Win: {st['wins']:2d} | Loss: {st['losses']:2d} | Net PnL: ${st['pnl']:+8.2f}")
