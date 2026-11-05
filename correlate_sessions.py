import json
from collections import defaultdict

with open('v633_7year_parsed_trades.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get('trades', [])

# Let's inspect the largest loss streaks or largest consecutive loss clusters
ny_trades = [t for t in trades if t.get('engine') == 'NY_Trend_Rider']
asia_trades = [t for t in trades if t.get('engine') == 'Asian_Squeeze']

print("=== NY WORST 10 LOSS TRADES ===")
worst_ny = sorted(ny_trades, key=lambda x: x.get('profit_usd', 0))[:10]
for t in worst_ny:
    print(f"Ticket {t['ticket']} | Open: {t['open_time']} | Side: {t['side']} | OpenP: {t['open_price']} | SL: {t['initial_sl']} | CloseP: {t['close_price']} | Loss: ${t['profit_usd']:.2f}")

print("\n=== ASIA WORST 10 LOSS TRADES ===")
worst_asia = sorted(asia_trades, key=lambda x: x.get('profit_usd', 0))[:10]
for t in worst_asia:
    print(f"Ticket {t['ticket']} | Open: {t['open_time']} | Side: {t['side']} | OpenP: {t['open_price']} | SL: {t['initial_sl']} | CloseP: {t['close_price']} | Loss: ${t['profit_usd']:.2f}")

# Check NY trades when London already had a huge trade on the same day
trades_by_date = defaultdict(list)
for t in trades:
    d = t['open_time'].split(' ')[0]
    trades_by_date[d].append(t)

same_day_impact = []
for d, d_trades in trades_by_date.items():
    l_tr = [x for x in d_trades if x.get('engine') == 'London_Sniper']
    ny_tr = [x for x in d_trades if x.get('engine') == 'NY_Trend_Rider']
    if l_tr and ny_tr:
        l_pnl = sum(x.get('profit_usd', 0) for x in l_tr)
        ny_pnl = sum(x.get('profit_usd', 0) for x in ny_tr)
        same_day_impact.append((d, l_pnl, ny_pnl, len(l_tr), len(ny_tr)))

print(f"\nDays with both London and NY: {len(same_day_impact)}")
l_win_ny_win = [x for x in same_day_impact if x[1] > 0 and x[2] > 0]
l_win_ny_loss = [x for x in same_day_impact if x[1] > 0 and x[2] <= 0]
l_loss_ny_win = [x for x in same_day_impact if x[1] <= 0 and x[2] > 0]
l_loss_ny_loss = [x for x in same_day_impact if x[1] <= 0 and x[2] <= 0]

print(f"London WIN & NY WIN : {len(l_win_ny_win)} days | NY PnL: ${sum(x[2] for x in l_win_ny_win):.2f}")
print(f"London WIN & NY LOSS: {len(l_win_ny_loss)} days | NY PnL: ${sum(x[2] for x in l_win_ny_loss):.2f}")
print(f"London LOSS & NY WIN: {len(l_loss_ny_win)} days | NY PnL: ${sum(x[2] for x in l_loss_ny_win):.2f}")
print(f"London LOSS & NY LOSS: {len(l_loss_ny_loss)} days | NY PnL: ${sum(x[2] for x in l_loss_ny_loss):.2f}")
