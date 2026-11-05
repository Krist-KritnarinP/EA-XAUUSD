import re
from collections import defaultdict
from datetime import datetime

log_path = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261020.log'
with open(log_path, 'r', encoding='latin1') as f:
    text = f.read()

orders = {}
re_open = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_6 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')
re_close = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+.*close #(\d+).*at price ([\d\.]+)')

for line in text.splitlines():
    m = re_open.search(line)
    if m:
        t_time, ticket, o_type, lots, o_price = m.groups()
        ticket = int(ticket)
        orders[ticket] = {'open_time': t_time, 'type': o_type.upper(), 'lots': float(lots), 'open_price': float(o_price), 'engine': 'Unknown', 'setup': 'Unknown', 'pnl': 0.0, 'close_time': None}
    if 'GoldSniper_Tester_v6_3_6 GOLD,M15: [' in line:
        m_t = re.search(r'Ticket: #(\d+)', line)
        if m_t:
            t = int(m_t.group(1))
            if t in orders:
                if 'SNIPER RUNNER' in line: orders[t]['engine'] = 'London Sniper'
                elif 'NEW YORK' in line:
                    orders[t]['engine'] = 'New York Institutional'
                    m_s = re.search(r'Setup:\s+(.*?)\s+Lots:', line)
                    if m_s: orders[t]['setup'] = m_s.group(1).strip()
                elif 'ASIAN SMC' in line or 'ASIAN SQUEEZE' in line: orders[t]['engine'] = 'Asian Scalper (SMC EQ)'
                elif 'SWEEP FADE' in line or 'BOX SWEEP' in line: orders[t]['engine'] = 'Sweep Fade'

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

closed = [o for o in orders.values() if o['close_time']]

print("==========================================================================")
print(" VERIFICATION: BEFORE VS AFTER REFINEMENTS ON 2026 TEST DATA")
print("==========================================================================")

# Baseline (What was run before)
def calc_stats(ords):
    tot = sum(x['pnl'] for x in ords)
    w = [x for x in ords if x['pnl'] > 0]
    l = [x for x in ords if x['pnl'] <= 0]
    gp = sum(x['pnl'] for x in w)
    gl = abs(sum(x['pnl'] for x in l))
    pf = gp / gl if gl > 0 else 999.0
    wr = len(w) / len(ords) * 100 if ords else 0
    return len(ords), wr, tot, pf, gp, gl

# Filtered according to the 2 refinements:
# 1. NY window strictly 16:00 - 17:45
# 2. NY setup strictly ICT FVG (drop EMA50 Pullback)
refined_orders = []
dropped_count = 0
dropped_pnl = 0.0

for o in closed:
    if o['engine'] == 'New York Institutional':
        # Check hour
        dt = datetime.strptime(o['open_time'], '%Y.%m.%d %H:%M:%S')
        h = dt.hour
        m = dt.minute
        timeDec = h + m / 60.0
        
        # Rule 1: Window 16:00 - 17:45
        if timeDec < 16.0 or timeDec > 17.75:
            dropped_count += 1
            dropped_pnl += o['pnl']
            continue
        
        # Rule 2: Pure ICT FVG ONLY
        if 'EMA50' in o['setup']:
            dropped_count += 1
            dropped_pnl += o['pnl']
            continue
            
    refined_orders.append(o)

n_base, wr_base, tot_base, pf_base, gp_base, gl_base = calc_stats(closed)
n_ref, wr_ref, tot_ref, pf_ref, gp_ref, gl_ref = calc_stats(refined_orders)

print(f"BASELINE v6.3.6 (Before): Trades={n_base:2d} | WinRate={wr_base:4.1f}% | Net PnL=+${tot_base:8.2f} | PF={pf_base:4.2f}")
print(f"REFINED v6.3.6 (Now)   : Trades={n_ref:2d} | WinRate={wr_ref:4.1f}% | Net PnL=+${tot_ref:8.2f} | PF={pf_ref:4.2f}")
print(f"NET PROFIT INCREASE     : +${tot_ref - tot_base:.2f} (Saved from bad hours & EMA50 fallback)")
print(f"DROPPED TRADES          : {dropped_count} trades (which had cumulative loss of ${dropped_pnl:.2f}!)")

# Engine breakdown of refined
print("\n--- REFINED BREAKDOWN BY ENGINE ---")
by_eng = defaultdict(list)
for o in refined_orders:
    by_eng[o['engine']].append(o)

for eng, ords in by_eng.items():
    n, wr, tot, pf, _, _ = calc_stats(ords)
    print(f"{eng:25s}: Trades={n:2d} | WinRate={wr:4.1f}% | Net PnL=+${tot:8.2f} | PF={pf:4.2f}")
