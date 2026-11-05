import re
from collections import defaultdict

# 1. PARSE v6.3.5 from 20261016.log
log_path_v635 = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261016.log'
with open(log_path_v635, 'r', encoding='latin1') as f:
    text_v635 = f.read()

idx = text_v635.rfind('2019.01.01 00:00:00  GoldSniper_Tester_v6_3_5_beta inputs:')
if idx == -1: idx = text_v635.find('2019.01.01 00:00:00')
lines_v635 = text_v635[idx:].splitlines()

orders_v635 = {}
re_open_v635 = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_5_beta GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+)')
re_engine = re.compile(r'Ticket: #(\d+)')
re_close_v635 = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+.*close #(\d+).*at price ([\d\.]+)')
re_sl = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+)')
re_tp = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+)')

for line in lines_v635:
    m = re_open_v635.search(line)
    if m:
        t_time, ticket, o_type, lots, o_price = m.groups()
        ticket = int(ticket)
        orders_v635[ticket] = {'open_time': t_time, 'type': o_type.upper(), 'lots': float(lots), 'open_price': float(o_price), 'engine': 'Unknown', 'pnl': 0.0, 'close_time': None}
    if 'GoldSniper_Tester_v6_3_5_beta GOLD,M15: [' in line:
        m_t = re_engine.search(line)
        if m_t:
            ticket = int(m_t.group(1))
            if ticket in orders_v635:
                if 'SNIPER RUNNER' in line: orders_v635[ticket]['engine'] = 'London Sniper'
                elif 'NEW YORK' in line: orders_v635[ticket]['engine'] = 'New York Trend-Rider'
                elif 'ASIAN BOX' in line: orders_v635[ticket]['engine'] = 'Sweep Fade (Asian Box)'
                elif 'SWEEP FADE' in line: orders_v635[ticket]['engine'] = 'Sweep Fade (EMA50 Trap)'
                elif 'ASIAN SQUEEZE' in line: orders_v635[ticket]['engine'] = 'Asian Scalper'

    for reg, reason in [(re_sl, 'SL'), (re_tp, 'TP'), (re_close_v635, 'Close')]:
        mc = reg.search(line)
        if mc:
            t_time, ticket, c_price = mc.groups()[0], int(mc.groups()[1]), float(mc.groups()[2])
            if ticket in orders_v635 and orders_v635[ticket]['close_time'] is None:
                o = orders_v635[ticket]
                o['close_time'] = t_time
                pts = (c_price - o['open_price']) if o['type'] == 'BUY' else (o['open_price'] - c_price)
                o['pnl'] = pts * o['lots'] * 100.0

p_v635 = [o for o in orders_v635.values() if o['close_time'] and '2026.05.08' <= o['open_time'] <= '2026.10.09']

# 2. PARSE v6.3.6 from 20261020.log
log_path_v636 = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261020.log'
with open(log_path_v636, 'r', encoding='latin1') as f:
    text_v636 = f.read()

orders_v636 = {}
re_open_v636 = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_6 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+)')
re_close_v636 = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+.*close #(\d+).*at price ([\d\.]+)')

for line in text_v636.splitlines():
    m = re_open_v636.search(line)
    if m:
        t_time, ticket, o_type, lots, o_price = m.groups()
        ticket = int(ticket)
        orders_v636[ticket] = {'open_time': t_time, 'type': o_type.upper(), 'lots': float(lots), 'open_price': float(o_price), 'engine': 'Unknown', 'pnl': 0.0, 'close_time': None}
    if 'GoldSniper_Tester_v6_3_6 GOLD,M15: [' in line:
        m_t = re_engine.search(line)
        if m_t:
            ticket = int(m_t.group(1))
            if ticket in orders_v636:
                if 'SNIPER RUNNER' in line: orders_v636[ticket]['engine'] = 'London Sniper'
                elif 'NEW YORK' in line: orders_v636[ticket]['engine'] = 'New York Institutional'
                elif 'ASIAN SMC' in line or 'ASIAN SQUEEZE' in line: orders_v636[ticket]['engine'] = 'Asian Scalper (SMC EQ)'
                elif 'SWEEP FADE' in line or 'BOX SWEEP' in line: orders_v636[ticket]['engine'] = 'Sweep Fade'

    for reg, reason in [(re_sl, 'SL'), (re_tp, 'TP'), (re_close_v636, 'Close')]:
        mc = reg.search(line)
        if mc:
            t_time, ticket, c_price = mc.groups()[0], int(mc.groups()[1]), float(mc.groups()[2])
            if ticket in orders_v636 and orders_v636[ticket]['close_time'] is None:
                o = orders_v636[ticket]
                o['close_time'] = t_time
                pts = (c_price - o['open_price']) if o['type'] == 'BUY' else (o['open_price'] - c_price)
                o['pnl'] = pts * o['lots'] * 100.0

p_v636 = [o for o in orders_v636.values() if o['close_time']]

print("==========================================================================")
print(" HEAD-TO-HEAD COMPARISON: v6.3.5-Beta vs v6.3.6 Institutional")
print(" Exact Period: 2026.05.08 - 2026.10.08 (5 Months, 77.15% Quality Data)")
print("==========================================================================")

def stats(ords):
    tot = sum(o['pnl'] for o in ords)
    w = [o for o in ords if o['pnl'] > 0]
    l = [o for o in ords if o['pnl'] <= 0]
    gp = sum(o['pnl'] for o in w)
    gl = abs(sum(o['pnl'] for o in l))
    pf = gp / gl if gl > 0 else 999.0
    wr = len(w) / len(ords) * 100 if ords else 0
    return len(ords), wr, tot, pf, gp, gl

n5, wr5, tot5, pf5, gp5, gl5 = stats(p_v635)
n6, wr6, tot6, pf6, gp6, gl6 = stats(p_v636)

print(f"Overall v6.3.5: Trades={n5:3d} | WinRate={wr5:5.1f}% | Net PnL=+${tot5:8.2f} | PF={pf5:4.2f} | GP=+${gp5:8.2f} | GL=-${gl5:8.2f}")
print(f"Overall v6.3.6: Trades={n6:3d} | WinRate={wr6:5.1f}% | Net PnL=+${tot6:8.2f} | PF={pf6:4.2f} | GP=+${gp6:8.2f} | GL=-${gl5:8.2f}")
print(f"DELTA (v6.3.6 - v6.3.5): Net PnL Delta: +${tot6 - tot5:.2f} | PF Delta: +{pf6 - pf5:.2f}")

print("\n--------------------------------------------------------------------------")
print(" ENGINE-BY-ENGINE BREAKDOWN")
print("--------------------------------------------------------------------------")
engs = ['London Sniper', 'Sweep Fade', 'New York', 'Asian Scalper']
for e in engs:
    trs5 = [o for o in p_v635 if e in o['engine'] or (e == 'Sweep Fade' and 'Sweep Fade' in o['engine']) or (e == 'New York' and 'New York' in o['engine']) or (e == 'Asian Scalper' and 'Asian' in o['engine'])]
    trs6 = [o for o in p_v636 if e in o['engine'] or (e == 'Sweep Fade' and 'Sweep Fade' in o['engine']) or (e == 'New York' and 'New York' in o['engine']) or (e == 'Asian Scalper' and 'Asian' in o['engine'])]
    
    n_5, wr_5, tot_5, pf_5, _, _ = stats(trs5)
    n_6, wr_6, tot_6, pf_6, _, _ = stats(trs6)
    print(f"[{e.upper()}]")
    print(f"  v6.3.5: Trades={n_5:3d} | WinRate={wr_5:5.1f}% | Net PnL=+${tot_5:8.2f} | PF={pf_5:4.2f}")
    print(f"  v6.3.6: Trades={n_6:3d} | WinRate={wr_6:5.1f}% | Net PnL=+${tot_6:8.2f} | PF={pf_6:4.2f}")
    print(f"  Delta : Trades={n_6 - n_5:+3d} | WinRate={wr_6 - wr_5:+5.1f}% | Net PnL=+${tot_6 - tot_5:+8.2f} | PF={pf_6 - pf_5:+4.2f}\n")
