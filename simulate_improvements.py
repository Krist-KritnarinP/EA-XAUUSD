import json
from collections import defaultdict

with open('v633_7year_parsed_trades.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

trades = data.get('trades', [])

print("=== BASELINE PERFORMANCE ===")
tot_pnl = sum(t['profit_usd'] for t in trades)
wins = [t for t in trades if t['profit_usd'] > 0]
print(f"Total Trades: {len(trades)} | Win Rate: {len(wins)/len(trades)*100:.1f}% | Net PnL: ${tot_pnl:.2f}")

# Simulation 1: NY Hour 16 ONLY (drop Hour 17 & 18)
sim1_trades = []
for t in trades:
    eng = t.get('engine')
    h = t['open_time'].split(' ')[1].split(':')[0]
    if eng == 'NY_Trend_Rider' and h in ['17', '18']:
        continue # skip
    sim1_trades.append(t)

pnl1 = sum(t['profit_usd'] for t in sim1_trades)
w1 = [t for t in sim1_trades if t['profit_usd'] > 0]
print(f"\n=== SIMULATION 1: NY Hour 16 ONLY ===")
print(f"Trades: {len(sim1_trades)} (dropped {len(trades)-len(sim1_trades)}) | Win Rate: {len(w1)/len(sim1_trades)*100:.1f}% | Net PnL: ${pnl1:.2f} (Delta: +${pnl1 - tot_pnl:.2f})")

# Simulation 2: London Hour 08, 09, 10 ONLY (drop Hour 11) + NY Hour 16 ONLY
sim2_trades = []
for t in trades:
    eng = t.get('engine')
    h = t['open_time'].split(' ')[1].split(':')[0]
    if eng == 'NY_Trend_Rider' and h in ['17', '18']:
        continue
    if eng == 'London_Sniper' and h == '11':
        continue
    sim2_trades.append(t)

pnl2 = sum(t['profit_usd'] for t in sim2_trades)
w2 = [t for t in sim2_trades if t['profit_usd'] > 0]
print(f"\n=== SIMULATION 2: London 08-10 + NY 16 ONLY ===")
print(f"Trades: {len(sim2_trades)} (dropped {len(trades)-len(sim2_trades)}) | Win Rate: {len(w2)/len(sim2_trades)*100:.1f}% | Net PnL: ${pnl2:.2f} (Delta: +${pnl2 - tot_pnl:.2f})")

# Simulation 3: Add London Loss Circuit Breaker on NY
# If London traded on that day and London PnL <= 0, do NOT take NY trade
trades_by_date = defaultdict(list)
for t in trades:
    d = t['open_time'].split(' ')[0]
    trades_by_date[d].append(t)

sim3_trades = []
for d, d_trades in trades_by_date.items():
    # evaluate London first
    l_trades = [t for t in d_trades if t.get('engine') == 'London_Sniper' and t['open_time'].split(' ')[1].split(':')[0] != '11']
    l_loss = (len(l_trades) > 0 and sum(t['profit_usd'] for t in l_trades) <= 0)
    
    for t in d_trades:
        eng = t.get('engine')
        h = t['open_time'].split(' ')[1].split(':')[0]
        if eng == 'London_Sniper':
            if h != '11':
                sim3_trades.append(t)
        elif eng == 'NY_Trend_Rider':
            if h == '16':
                if not l_loss: # if London didn't lose today
                    sim3_trades.append(t)
        elif eng == 'Asian_Squeeze':
            sim3_trades.append(t)

pnl3 = sum(t['profit_usd'] for t in sim3_trades)
w3 = [t for t in sim3_trades if t['profit_usd'] > 0]
print(f"\n=== SIMULATION 3: London 08-10 + NY 16 + Inter-Session Circuit Breaker ===")
print(f"Trades: {len(sim3_trades)} | Win Rate: {len(w3)/len(sim3_trades)*100:.1f}% | Net PnL: ${pnl3:.2f} (Delta: +${pnl3 - tot_pnl:.2f})")
