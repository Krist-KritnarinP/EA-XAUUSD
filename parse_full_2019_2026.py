import re
from datetime import datetime
from collections import defaultdict

log_path = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261016.log'
with open(log_path, 'r', encoding='latin1') as f:
    text = f.read()

# Find the start of the 2019 test
idx = text.rfind('2019.01.01 00:00:00  GoldSniper_Tester_v6_3_5_beta inputs:')
if idx == -1:
    idx = text.find('2019.01.01 00:00:00')

print(f"Index of 2019 test: {idx}")
test_text = text[idx:] if idx != -1 else text
lines = test_text.splitlines()

orders = {}
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_5_beta GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+)')
re_engine = re.compile(r'Ticket: #(\d+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_5_beta GOLD,M15: close #(\d+) (buy|sell) [\d\.]+ GOLD at [\d\.]+ sl: [\d\.]+ tp: [\d\.]+ at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')
re_tester_close = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: close #(\d+) at ([\d\.]+)')

for line in lines:
    m = re_open.search(line)
    if m:
        t_time, ticket, o_type, lots, o_price = m.groups()
        ticket = int(ticket)
        orders[ticket] = {
            'ticket': ticket,
            'open_time': t_time,
            'type': o_type.upper(),
            'lots': float(lots),
            'open_price': float(o_price),
            'engine': 'Unknown',
            'close_time': None,
            'close_price': None,
            'close_reason': 'Unknown',
            'pnl': 0.0
        }
    if 'GoldSniper_Tester_v6_3_5_beta GOLD,M15: [' in line:
        m_t = re_engine.search(line)
        if m_t:
            ticket = int(m_t.group(1))
            if ticket in orders:
                if 'SNIPER RUNNER' in line:
                    orders[ticket]['engine'] = 'London Sniper'
                elif 'NEW YORK TREND-RIDER' in line:
                    orders[ticket]['engine'] = 'New York Trend-Rider'
                elif 'ASIAN BOX SWEEP FADE' in line:
                    orders[ticket]['engine'] = 'Sweep Fade (Asian Box)'
                elif 'SWEEP FADE' in line:
                    orders[ticket]['engine'] = 'Sweep Fade (EMA50 Trap)'
                elif 'ASIAN SQUEEZE' in line:
                    orders[ticket]['engine'] = 'Asian Scalper'

    m_c = re_close.search(line)
    if m_c:
        c_time, ticket, _, c_price = m_c.groups()
        ticket = int(ticket)
        if ticket in orders:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['close_reason'] = 'Sunset Exit / Manual'

    m_sl = re_sl.search(line)
    if m_sl:
        c_time, ticket, c_price = m_sl.groups()
        ticket = int(ticket)
        if ticket in orders:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['close_reason'] = 'Stop Loss'

    m_tp = re_tp.search(line)
    if m_tp:
        c_time, ticket, c_price = m_tp.groups()
        ticket = int(ticket)
        if ticket in orders:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['close_reason'] = 'Take Profit'

    m_tc = re_tester_close.search(line)
    if m_tc:
        c_time, ticket, c_price = m_tc.groups()
        ticket = int(ticket)
        if ticket in orders and orders[ticket]['close_price'] is None:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['close_reason'] = 'Tester End Close'

total_pnl = 0.0
gross_profit = 0.0
gross_loss = 0.0

closed_orders = [o for o in orders.values() if o['close_price'] is not None]

for o in closed_orders:
    if o['type'] == 'BUY':
        pnl = (o['close_price'] - o['open_price']) * o['lots'] * 100.0
    else:
        pnl = (o['open_price'] - o['close_price']) * o['lots'] * 100.0
    o['pnl'] = round(pnl, 2)
    total_pnl += o['pnl']
    if o['pnl'] > 0:
        gross_profit += o['pnl']
    else:
        gross_loss += abs(o['pnl'])

pf = (gross_profit / gross_loss) if gross_loss > 0 else 99.0
print(f"Total Orders: {len(orders)}, Closed: {len(closed_orders)}")
print(f"Total Net PnL: ${total_pnl:.2f} (Gross Profit: ${gross_profit:.2f}, Gross Loss: -${gross_loss:.2f}) | PF: {pf:.2f}")

# Breakdown by Engine
eng_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gp': 0.0, 'gl': 0.0})
for o in closed_orders:
    eng = o['engine']
    eng_stats[eng]['trades'] += 1
    eng_stats[eng]['pnl'] += o['pnl']
    if o['pnl'] > 0:
        eng_stats[eng]['wins'] += 1
        eng_stats[eng]['gp'] += o['pnl']
    else:
        eng_stats[eng]['losses'] += 1
        eng_stats[eng]['gl'] += abs(o['pnl'])

print("\n================== FULL 1401 TRADES ENGINE BREAKDOWN ==================")
for eng, s in sorted(eng_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
    wr = (s['wins'] / s['trades'] * 100) if s['trades'] > 0 else 0
    pf_e = (s['gp'] / s['gl']) if s['gl'] > 0 else 99.0
    print(f"{eng:25}: Trades={s['trades']:4}, WinRate={wr:5.1f}%, PnL=${s['pnl']:9.2f}, PF={pf_e:4.2f}, GP=${s['gp']:8.2f}, GL=${s['gl']:8.2f}")

# Yearly breakdown
yearly_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gp': 0.0, 'gl': 0.0})
for o in closed_orders:
    y = o['open_time'][:4]
    yearly_stats[y]['trades'] += 1
    yearly_stats[y]['pnl'] += o['pnl']
    if o['pnl'] > 0:
        yearly_stats[y]['wins'] += 1
        yearly_stats[y]['gp'] += o['pnl']
    else:
        yearly_stats[y]['losses'] += 1
        yearly_stats[y]['gl'] += abs(o['pnl'])

print("\n================== FULL 1401 TRADES YEARLY BREAKDOWN ==================")
for y in sorted(yearly_stats.keys()):
    s = yearly_stats[y]
    wr = (s['wins'] / s['trades'] * 100) if s['trades'] > 0 else 0
    pf_y = (s['gp'] / s['gl']) if s['gl'] > 0 else 99.0
    print(f"Year {y}: Trades={s['trades']:3}, WinRate={wr:5.1f}%, PnL=${s['pnl']:9.2f}, PF={pf_y:4.2f}, GP=${s['gp']:8.2f}, GL=${s['gl']:8.2f}")

# Long vs Short
type_stats = defaultdict(lambda: {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'gp': 0.0, 'gl': 0.0})
for o in closed_orders:
    typ = o['type']
    type_stats[typ]['trades'] += 1
    type_stats[typ]['pnl'] += o['pnl']
    if o['pnl'] > 0:
        type_stats[typ]['wins'] += 1
        type_stats[typ]['gp'] += o['pnl']
    else:
        type_stats[typ]['losses'] += 1
        type_stats[typ]['gl'] += abs(o['pnl'])

print("\n================== BUY VS SELL BREAKDOWN ==================")
for typ in ['BUY', 'SELL']:
    s = type_stats[typ]
    wr = (s['wins'] / s['trades'] * 100) if s['trades'] > 0 else 0
    pf_t = (s['gp'] / s['gl']) if s['gl'] > 0 else 99.0
    print(f"{typ:4}: Trades={s['trades']:4}, WinRate={wr:5.1f}%, PnL=${s['pnl']:9.2f}, PF={pf_t:4.2f}")
