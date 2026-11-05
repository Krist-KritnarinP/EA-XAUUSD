import re
from collections import defaultdict
from datetime import datetime

log_path = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261020.log'
with open(log_path, 'r', encoding='latin1') as f:
    text = f.read()

orders = {}
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_6 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+)')
re_setup = re.compile(r'Ticket: #(\d+)\s+Setup:\s+([^\s]+ [^\s]+ [^\s]+ [^\s]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+.*close #(\d+).*at price ([\d\.]+)')

for line in text.splitlines():
    m = re_open.search(line)
    if m:
        t_time, ticket, o_type, lots, o_price = m.groups()
        ticket = int(ticket)
        orders[ticket] = {'open_time': t_time, 'type': o_type.upper(), 'lots': float(lots), 'open_price': float(o_price), 'engine': 'Unknown', 'setup': 'Unknown', 'pnl': 0.0, 'close_time': None}
    if 'NEW YORK INSTITUTIONAL' in line:
        m_s = re.search(r'Ticket: #(\d+)\s+Setup:\s+(.*?)\s+Lots:', line)
        if m_s:
            t = int(m_s.group(1))
            if t in orders:
                orders[t]['engine'] = 'New York Institutional'
                orders[t]['setup'] = m_s.group(2).strip()

    for reg, reason in [(re_sl, 'SL'), (re_tp, 'TP'), (re_close, 'Close')]:
        mc = reg.search(line)
        if mc:
            t_time, ticket, c_price = mc.groups()[0], int(mc.groups()[1]), float(mc.groups()[2])
            if ticket in orders and orders[ticket]['close_time'] is None:
                o = orders[ticket]
                o['close_time'] = t_time
                o['reason'] = reason
                pts = (c_price - o['open_price']) if o['type'] == 'BUY' else (o['open_price'] - c_price)
                o['pnl'] = pts * o['lots'] * 100.0

ny_trades = [o for o in orders.values() if o['engine'] == 'New York Institutional' and o['close_time']]
print(f"Total NY Trades: {len(ny_trades)}")

print("\n--- NY BY SETUP ---")
by_setup = defaultdict(list)
for t in ny_trades:
    by_setup[t['setup']].append(t)
for s, trs in by_setup.items():
    pnl = sum(x['pnl'] for x in trs)
    wins = len([x for x in trs if x['pnl'] > 0])
    print(f"{s:35s}: Trades={len(trs):2d} | WinRate={wins/len(trs)*100:4.1f}% | PnL=${pnl:7.2f}")

print("\n--- NY BY OPEN HOUR ---")
by_hour = defaultdict(list)
for t in ny_trades:
    h = int(t['open_time'].split(' ')[1].split(':')[0])
    by_hour[h].append(t)
for h in sorted(by_hour.keys()):
    trs = by_hour[h]
    pnl = sum(x['pnl'] for x in trs)
    wins = len([x for x in trs if x['pnl'] > 0])
    print(f"Hour {h:02d}: Trades={len(trs):2d} | WinRate={wins/len(trs)*100:4.1f}% | PnL=${pnl:7.2f}")

print("\n--- NY BY DAY OF WEEK ---")
dow_map = {0:'Mon', 1:'Tue', 2:'Wed', 3:'Thu', 4:'Fri'}
by_dow = defaultdict(list)
for t in ny_trades:
    dt = datetime.strptime(t['open_time'], '%Y.%m.%d %H:%M:%S')
    by_dow[dt.weekday()].append(t)
for d in sorted(by_dow.keys()):
    trs = by_dow[d]
    pnl = sum(x['pnl'] for x in trs)
    wins = len([x for x in trs if x['pnl'] > 0])
    print(f"{dow_map[d]}: Trades={len(trs):2d} | WinRate={wins/len(trs)*100:4.1f}% | PnL=${pnl:7.2f}")
