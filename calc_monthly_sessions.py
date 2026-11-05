import re, json, struct, os
from datetime import datetime
from collections import defaultdict

# -------------------------------------------------------------
# 1. Parse Beta B (124 trades)
# -------------------------------------------------------------
betab_file = r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\run_betab_exact.txt'
with open(betab_file, 'r', encoding='utf-8') as f:
    text = f.read()

opens = {}
for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_8_beta_b GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)', text):
    t_str, ticket, cmd, lots, open_p, sl, tp = m.groups()
    ticket = int(ticket)
    opens[ticket] = {
        'ticket': ticket,
        'open_time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'),
        'type': cmd.upper(),
        'lots': float(lots),
        'open_price': float(open_p),
        'init_sl': float(sl),
        'init_tp': float(tp)
    }

closes = {}
for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: (stop loss|take profit) #(\d+) at ([\d\.]+)', text):
    t_str, kind, ticket, close_p = m.groups()
    closes[int(ticket)] = {'time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'), 'price': float(close_p), 'reason': 'TP' if kind == 'take profit' else 'SL'}

for m in re.finditer(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_8_beta_b GOLD,M15: close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+) at price ([\d\.]+)', text):
    t_str, ticket, cmd, lots, open_p, sl, tp, close_p = m.groups()
    closes[int(ticket)] = {'time': datetime.strptime(t_str, '%Y.%m.%d %H:%M:%S'), 'price': float(close_p), 'reason': 'MANUAL'}

betab_trades = []
for t, op in sorted(opens.items()):
    if t in closes:
        cl = closes[t]
        pts = (cl['price'] - op['open_price']) if op['type'] == 'BUY' else (op['open_price'] - cl['price'])
        pnl = pts * op['lots'] * 100
        hr = op['open_time'].hour
        if hr < 8:
            session = "Asian"
        elif hr < 15:
            session = "London"
        else:
            session = "New York"
        
        betab_trades.append({
            'ticket': t,
            'open_time': op['open_time'],
            'month': op['open_time'].strftime('%Y-%m'),
            'session': session,
            'profit': pnl,
            'is_win': pnl > 0
        })

print(f"Beta B total trades: {len(betab_trades)}")

# -------------------------------------------------------------
# 2. Parse 6.2.3 x3 (71 trades)
# -------------------------------------------------------------
with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\v623x3_official_forensic.json', 'r') as f:
    v623_raw = json.load(f)

v623_trades = []
for tr in v623_raw:
    dt = datetime.strptime(tr['open_time'], '%Y.%m.%d %H:%M')
    hr = dt.hour
    if hr < 8:
        session = "Asian"
    elif hr < 15:
        session = "London"
    else:
        session = "New York"
    
    pnl = tr['profit']
    v623_trades.append({
        'ticket': tr['ticket'],
        'open_time': dt,
        'month': dt.strftime('%Y-%m'),
        'session': session,
        'profit': pnl,
        'is_win': pnl > 0
    })

print(f"6.2.3 x3 total trades: {len(v623_trades)}")

# -------------------------------------------------------------
# 3. Parse POI v2.5 (128 trades)
# -------------------------------------------------------------
with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_v2_5_detailed_trades.json', 'r') as f:
    poi_raw = json.load(f)

poi_trades = []
for tr in poi_raw:
    dt = datetime.strptime(tr['open_time'], '%Y.%m.%d %H:%M:%S')
    hr = dt.hour
    if hr < 8:
        session = "Asian"
    elif hr < 15:
        session = "London"
    else:
        session = "New York"
    
    pnl = tr['profit_usd']
    poi_trades.append({
        'ticket': tr['ticket'],
        'open_time': dt,
        'month': dt.strftime('%Y-%m'),
        'session': session,
        'profit': pnl,
        'is_win': pnl > 0
    })

print(f"POI v2.5 total trades: {len(poi_trades)}")

# -------------------------------------------------------------
# Helper aggregation function
# -------------------------------------------------------------
def aggregate_model(trades_list):
    monthly_data = defaultdict(lambda: {
        'all': {'trades': 0, 'wins': 0, 'pnl': 0.0},
        'Asian': {'trades': 0, 'wins': 0, 'pnl': 0.0},
        'London': {'trades': 0, 'wins': 0, 'pnl': 0.0},
        'New York': {'trades': 0, 'wins': 0, 'pnl': 0.0}
    })
    
    for tr in trades_list:
        m = tr['month']
        s = tr['session']
        
        monthly_data[m]['all']['trades'] += 1
        if tr['is_win']: monthly_data[m]['all']['wins'] += 1
        monthly_data[m]['all']['pnl'] += tr['profit']
        
        monthly_data[m][s]['trades'] += 1
        if tr['is_win']: monthly_data[m][s]['wins'] += 1
        monthly_data[m][s]['pnl'] += tr['profit']
        
    return monthly_data

agg_betab = aggregate_model(betab_trades)
agg_v623 = aggregate_model(v623_trades)
agg_poi = aggregate_model(poi_trades)

months = sorted(list(set(list(agg_betab.keys()) + list(agg_v623.keys()) + list(agg_poi.keys()))))

result = {
    'months': months,
    'betab': agg_betab,
    'v623': agg_v623,
    'poi': agg_poi
}

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\comparison_monthly_session.json', 'w') as f:
    json.dump(result, f, indent=2)

print("\nSaved comparison_monthly_session.json successfully!")
