import json

with open('v633_7year_parsed_trades.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get('trades', [])
asia = [t for t in trades if t.get('engine') == 'Asian_Squeeze']

print(f"Total Asia trades: {len(asia)}")
print(f"Asia Total Net: ${sum(t['profit_usd'] for t in asia):.2f}")

# Look at Asia trade durations (open_time to close_time)
from datetime import datetime

durations_win = []
durations_loss = []
for t in asia:
    t_open = datetime.strptime(t['open_time'], "%Y.%m.%d %H:%M:%S")
    t_close = datetime.strptime(t['close_time'], "%Y.%m.%d %H:%M:%S")
    dur_min = (t_close - t_open).total_seconds() / 60.0
    if t['profit_usd'] > 0:
        durations_win.append(dur_min)
    else:
        durations_loss.append(dur_min)

print(f"Asia Avg Win Duration: {sum(durations_win)/len(durations_win):.1f} mins (Total wins: {len(durations_win)})")
print(f"Asia Avg Loss Duration: {sum(durations_loss)/len(durations_loss):.1f} mins (Total losses: {len(durations_loss)})")

# Check profit by hour in Asia
for h in ['02', '03', '04', '05']:
    h_trades = [t for t in asia if t['open_time'].split(' ')[1].split(':')[0] == h]
    pnl = sum(t['profit_usd'] for t in h_trades)
    wins = [t for t in h_trades if t['profit_usd'] > 0]
    wr = len(wins) / len(h_trades) * 100 if h_trades else 0
    print(f"Asia Hour {h}: {len(h_trades)} trades | WR: {wr:.1f}% | Net: ${pnl:.2f}")
