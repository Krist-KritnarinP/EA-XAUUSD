import json
from collections import defaultdict

with open('v633_7year_parsed_trades.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get('trades', [])

print(f"Total trades loaded: {len(trades)}")

hourly_engine = defaultdict(lambda: defaultdict(list))

for t in trades:
    eng = t.get('engine', 'Unknown')
    open_time = t.get('open_time', '')
    hour = open_time.split(' ')[1].split(':')[0] if ' ' in open_time else '??'
    hourly_engine[eng][hour].append(t)

for eng, hours in hourly_engine.items():
    print(f"\n======================================")
    print(f"--- Engine: {eng} ---")
    print(f"======================================")
    for h in sorted(hours.keys()):
        trs = hours[h]
        wins = [x for x in trs if x.get('profit_usd', 0) > 0]
        losses = [x for x in trs if x.get('profit_usd', 0) <= 0]
        pnl = sum(x.get('profit_usd', 0) for x in trs)
        wr = len(wins) / len(trs) * 100 if trs else 0
        tot_win = sum(x.get('profit_usd', 0) for x in wins)
        tot_loss = sum(x.get('profit_usd', 0) for x in losses)
        avg_w = tot_win / len(wins) if wins else 0
        avg_l = tot_loss / len(losses) if losses else 0
        print(f"Hour {h}: Count {len(trs):3d} | W: {len(wins):2d} | L: {len(losses):2d} | WR: {wr:5.1f}% | Net: ${pnl:8.2f} | AvgW: ${avg_w:6.2f} | AvgL: ${avg_l:6.2f}")
