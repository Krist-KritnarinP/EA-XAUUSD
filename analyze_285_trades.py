import re
from datetime import datetime
from collections import defaultdict

with open(r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261101.log', 'r', encoding='latin-1') as f:
    lines = f.readlines()

start_idx = 86487
run_lines = lines[start_idx:]

trades = {}
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+.*close #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+) at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester: (?:take profit|stop loss) #(\d+) at ([\d\.]+)')

for l in run_lines:
    mo = re_open.search(l)
    if mo:
        t_time, ticket, t_type, lots, o_price, sl, tp = mo.groups()
        trades[ticket] = {
            'ticket': int(ticket),
            'open_time': t_time,
            'type': t_type.upper(),
            'lots': float(lots),
            'open_price': float(o_price),
            'init_sl': float(sl),
            'init_tp': float(tp),
            'close_time': None,
            'close_price': None,
            'close_reason': None
        }
    mc = re_close.search(l)
    if mc:
        c_time, ticket, t_type, lots, o_price, sl, tp, c_price = mc.groups()
        if ticket in trades:
            trades[ticket]['close_time'] = c_time
            trades[ticket]['close_price'] = float(c_price)
            trades[ticket]['close_reason'] = 'MANUAL_OR_BAILOUT'
    ms = re_sl.search(l)
    if ms:
        s_time, ticket, s_price = ms.groups()
        if ticket in trades:
            trades[ticket]['close_time'] = s_time
            trades[ticket]['close_price'] = float(s_price)
            trades[ticket]['close_reason'] = 'TAKE_PROFIT' if 'take profit' in l.lower() else 'STOP_LOSS'

trade_list = sorted(trades.values(), key=lambda x: x['ticket'])
monthly = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'profit': 0.0, 'lots_sum': 0.0})

for t in trade_list:
    o_dt = datetime.strptime(t['open_time'], '%Y.%m.%d %H:%M:%S')
    m = o_dt.strftime('%Y-%m')
    if t['close_price']:
        diff = (t['close_price'] - t['open_price']) if t['type'] == 'BUY' else (t['open_price'] - t['close_price'])
        profit = round(diff * t['lots'] * 100.0, 2)
    else:
        profit = 0.0
    monthly[m]['trades'] += 1
    monthly[m]['profit'] += profit
    monthly[m]['lots_sum'] += t['lots']
    if profit > 0:
        monthly[m]['wins'] += 1
    else:
        monthly[m]['losses'] += 1

print('=== 285-TRADE RUN MONTHLY BREAKDOWN ===')
cum_profit = 0.0
for m, d in sorted(monthly.items()):
    cum_profit += d['profit']
    wr = (d['wins']/d['trades'])*100 if d['trades'] > 0 else 0
    avg_lot = d['lots_sum']/d['trades'] if d['trades'] > 0 else 0
    print(f"{m}: {d['trades']} trades | Wins: {d['wins']} ({wr:5.1f}%) | Profit: ${d['profit']:>9.2f} | Cum: ${cum_profit:>9.2f} | AvgLot: {avg_lot:.2f}")

print(f'\nTotal Net Profit: ${cum_profit:.2f}')
