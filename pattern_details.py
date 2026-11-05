import json
from collections import defaultdict
from datetime import datetime

with open('v633_7year_parsed_trades.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get('trades', [])

# 1. By Direction (BUY vs SELL)
print("=== DIRECTION ANALYSIS (BUY vs SELL) ===")
dir_engine = defaultdict(lambda: defaultdict(list))
for t in trades:
    eng = t.get('engine', 'Unknown')
    side = t.get('side', 'Unknown')
    dir_engine[eng][side].append(t)

for eng, sides in dir_engine.items():
    print(f"\nEngine: {eng}")
    for side, trs in sides.items():
        wins = [x for x in trs if x.get('profit_usd', 0) > 0]
        losses = [x for x in trs if x.get('profit_usd', 0) <= 0]
        pnl = sum(x.get('profit_usd', 0) for x in trs)
        wr = len(wins) / len(trs) * 100 if trs else 0
        tot_win = sum(x.get('profit_usd', 0) for x in wins)
        tot_loss = sum(x.get('profit_usd', 0) for x in losses)
        avg_w = tot_win / len(wins) if wins else 0
        avg_l = tot_loss / len(losses) if losses else 0
        print(f"  {side:4s}: Count {len(trs):3d} | W: {len(wins):2d} | L: {len(losses):2d} | WR: {wr:5.1f}% | Net: ${pnl:8.2f} | AvgW: ${avg_w:6.2f} | AvgL: ${avg_l:6.2f}")

# 2. Day of Week
print("\n=== DAY OF WEEK ANALYSIS ===")
dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
dow_engine = defaultdict(lambda: defaultdict(list))
for t in trades:
    eng = t.get('engine', 'Unknown')
    ot = t.get('open_time', '')
    dt = datetime.strptime(ot, "%Y.%m.%d %H:%M:%S")
    dow = dow_names[dt.weekday()]
    dow_engine[eng][dow].append(t)

for eng, dows in dow_engine.items():
    print(f"\nEngine: {eng}")
    for d in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
        trs = dows.get(d, [])
        wins = [x for x in trs if x.get('profit_usd', 0) > 0]
        pnl = sum(x.get('profit_usd', 0) for x in trs)
        wr = len(wins) / len(trs) * 100 if trs else 0
        print(f"  {d}: Count {len(trs):3d} | WR: {wr:5.1f}% | Net: ${pnl:8.2f}")

# 3. Close Type
print("\n=== CLOSE TYPE ANALYSIS ===")
ct_engine = defaultdict(lambda: defaultdict(list))
for t in trades:
    eng = t.get('engine', 'Unknown')
    ct = t.get('close_type', 'Unknown')
    ct_engine[eng][ct].append(t)

for eng, cts in ct_engine.items():
    print(f"\nEngine: {eng}")
    for ct, trs in cts.items():
        pnl = sum(x.get('profit_usd', 0) for x in trs)
        print(f"  CloseType {ct:6s}: Count {len(trs):3d} | Net: ${pnl:8.2f}")

# 4. Gold Price Regimes (<1800, 1800-2100, 2100-2500, >2500)
print("\n=== GOLD PRICE REGIMES ===")
def get_regime(price):
    if price < 1800: return "< $1800 (2020 Early)"
    elif price < 2100: return "$1800 - $2100 (2020-2023)"
    elif price < 2500: return "$2100 - $2500 (Early 2024)"
    else: return "> $2500 (2024-2026 Macro Rally)"

regime_engine = defaultdict(lambda: defaultdict(list))
for t in trades:
    eng = t.get('engine', 'Unknown')
    p = t.get('open_price', 0)
    reg = get_regime(p)
    regime_engine[eng][reg].append(t)

for eng, regs in regime_engine.items():
    print(f"\nEngine: {eng}")
    for reg in sorted(regs.keys()):
        trs = regs[reg]
        wins = [x for x in trs if x.get('profit_usd', 0) > 0]
        pnl = sum(x.get('profit_usd', 0) for x in trs)
        wr = len(wins) / len(trs) * 100 if trs else 0
        print(f"  {reg:30s}: Count {len(trs):3d} | WR: {wr:5.1f}% | Net: ${pnl:8.2f}")
