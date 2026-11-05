import re
from collections import defaultdict

log_path = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261020.log'
with open(log_path, 'r', encoding='latin1') as f:
    text = f.read()

lines = text.splitlines()

orders = {}
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_6 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+)')
re_engine = re.compile(r'Ticket: #(\d+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+.*close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+GOLD at [\d\.]+ sl: [\d\.]+ tp: [\d\.]+ at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')
re_partial_close = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_6 GOLD,M15: close #(\d+)\s+(buy|sell)\s+([\d\.]+)\s+GOLD.*at price ([\d\.]+)')

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
            'reason': 'Unknown',
            'pnl': 0.0
        }
    if 'GoldSniper_Tester_v6_3_6 GOLD,M15: [' in line:
        m_t = re_engine.search(line)
        if m_t:
            ticket = int(m_t.group(1))
            if ticket in orders:
                if 'SNIPER RUNNER' in line:
                    orders[ticket]['engine'] = 'London Sniper'
                elif 'NEW YORK' in line:
                    orders[ticket]['engine'] = 'New York Institutional'
                elif 'ASIAN SMC' in line or 'ASIAN SQUEEZE' in line:
                    orders[ticket]['engine'] = 'Asian Scalper (SMC EQ)'
                elif 'SWEEP FADE' in line or 'BOX SWEEP' in line:
                    orders[ticket]['engine'] = 'Sweep Fade'

    m_c = re_close.search(line)
    if m_c:
        c_time, ticket, _, c_lots, c_price = m_c.groups()
        ticket = int(ticket)
        if ticket in orders and orders[ticket]['close_time'] is None:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['reason'] = 'Manual / Sunset / AutoClose'

    m_sl = re_sl.search(line)
    if m_sl:
        c_time, ticket, c_price = m_sl.groups()
        ticket = int(ticket)
        if ticket in orders and orders[ticket]['close_time'] is None:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['reason'] = 'Stop Loss'

    m_tp = re_tp.search(line)
    if m_tp:
        c_time, ticket, c_price = m_tp.groups()
        ticket = int(ticket)
        if ticket in orders and orders[ticket]['close_time'] is None:
            orders[ticket]['close_time'] = c_time
            orders[ticket]['close_price'] = float(c_price)
            orders[ticket]['reason'] = 'Take Profit'

# Calculate PnL for closed orders
closed_orders = [o for o in orders.values() if o['close_time'] is not None]
for o in closed_orders:
    pts = (o['close_price'] - o['open_price']) if o['type'] == 'BUY' else (o['open_price'] - o['close_price'])
    o['pnl'] = pts * o['lots'] * 100.0

print(f"Total Opened Orders: {len(orders)}, Closed: {len(closed_orders)}")
total_pnl = sum(o['pnl'] for o in closed_orders)
wins = [o for o in closed_orders if o['pnl'] > 0]
losses = [o for o in closed_orders if o['pnl'] <= 0]
gp = sum(o['pnl'] for o in wins)
gl = abs(sum(o['pnl'] for o in losses))
pf = (gp / gl) if gl > 0 else 999.0
print(f"Calculated Net PnL: ${total_pnl:.2f} | WinRate: {len(wins)/len(closed_orders)*100:.1f}% | PF: {pf:.2f}")

print("\n=== BREAKDOWN BY ENGINE ===")
by_engine = defaultdict(list)
for o in closed_orders:
    by_engine[o['engine']].append(o)

for eng, ords in by_engine.items():
    pnl = sum(x['pnl'] for x in ords)
    w = [x for x in ords if x['pnl'] > 0]
    l = [x for x in ords if x['pnl'] <= 0]
    g_p = sum(x['pnl'] for x in w)
    g_l = abs(sum(x['pnl'] for x in l))
    p_f = (g_p / g_l) if g_l > 0 else 999.0
    print(f"{eng:25s}: Trades={len(ords):3d} | WinRate={len(w)/len(ords)*100:5.1f}% | PnL=${pnl:8.2f} | PF={p_f:5.2f}")
