import re
from datetime import datetime
from collections import defaultdict

log_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261012.log'
with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

v631_lines = lines[1998:]

trades = {}
open_re = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_1\s+\w+,\w+:\s+open\s+#(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+([\d\.]+)\s+sl:\s+([\d\.]+)\s+tp:\s+([\d\.]+)')
signal_re = re.compile(r'\[(SNIPER RUNNER|ASIAN SQUEEZE|NEW YORK REVERSAL|CASH FLOW SCALPER)\s+(BUY|SELL)[^\]]*\]\s+Ticket:\s+#(\d+)')
tester_close_re = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+Tester:\s+(stop loss|take profit)\s+#(\d+)\s+at\s+([\d\.]+)')
ea_close_re = re.compile(r'(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_1\s+\w+,\w+:\s+close\s+#(\d+)\s+(buy|sell)\s+([\d\.]+)\s+\w+\s+at\s+[\d\.]+\s+sl:\s+[\d\.]+\s+tp:\s+[\d\.]+\s+at\s+price\s+([\d\.]+)')

for line in v631_lines:
    m_open = open_re.search(line)
    if m_open:
        t_time, ticket, t_type, lot, price, sl, tp = m_open.groups()
        ticket = int(ticket)
        trades[ticket] = {
            'ticket': ticket,
            'open_time': t_time,
            'type': t_type.upper(),
            'lot': float(lot),
            'open_price': float(price),
            'sl': float(sl),
            'tp': float(tp),
            'engine': 'Unknown',
            'modifications': [],
            'close_time': None,
            'close_price': None,
            'close_reason': None
        }
    
    m_sig = signal_re.search(line)
    if m_sig:
        eng, side, ticket = m_sig.groups()
        ticket = int(ticket)
        if ticket in trades:
            if 'SNIPER' in eng:
                trades[ticket]['engine'] = 'London Sniper'
            elif 'ASIAN' in eng or 'SCALPER' in eng:
                trades[ticket]['engine'] = 'Asian Sweeper'
            elif 'NEW YORK' in eng:
                trades[ticket]['engine'] = 'New York Reversal'

    m_tclose = tester_close_re.search(line)
    if m_tclose:
        c_time, reason, ticket, c_price = m_tclose.groups()
        ticket = int(ticket)
        if ticket in trades:
            trades[ticket]['close_time'] = c_time
            trades[ticket]['close_price'] = float(c_price)
            trades[ticket]['close_reason'] = reason.upper()

    m_eclose = ea_close_re.search(line)
    if m_eclose:
        c_time, ticket, c_side, c_lot, c_price = m_eclose.groups()
        ticket = int(ticket)
        if ticket in trades:
            trades[ticket]['close_time'] = c_time
            trades[ticket]['close_price'] = float(c_price)
            if not trades[ticket]['close_reason']:
                trades[ticket]['close_reason'] = 'EA CLOSE'

    for tag in ['SCALPER AUTO-CLOSE', 'SUNSET EXIT', 'SCALPER BE', 'RATCHET STAGE 1', 'RATCHET STAGE 2']:
        if tag in line:
            m_t = re.search(r'#(\d+)', line)
            if m_t:
                tk = int(m_t.group(1))
                if tk in trades:
                    trades[tk]['modifications'].append(tag)
                    if 'AUTO-CLOSE' in tag or 'SUNSET' in tag:
                        trades[tk]['close_reason'] = tag

# Calculate PnL
for tk, d in trades.items():
    if d['close_price'] is not None:
        if d['type'] == 'BUY':
            d['pnl'] = round((d['close_price'] - d['open_price']) * d['lot'] * 100, 2)
        else:
            d['pnl'] = round((d['open_price'] - d['close_price']) * d['lot'] * 100, 2)
    else:
        d['pnl'] = 0.0

print("=== MONTHLY BREAKDOWN (ALL) ===")
months = sorted(list(set(d['open_time'][:7] for d in trades.values())))
for m in months:
    m_trades = [d for d in trades.values() if d['open_time'].startswith(m)]
    m_wins = [d for d in m_trades if d['pnl'] > 0]
    m_loss = [d for d in m_trades if d['pnl'] < 0]
    m_pnl = sum(d['pnl'] for d in m_trades)
    m_wr = round(len(m_wins)/len(m_trades)*100, 1)
    m_gp = sum(d['pnl'] for d in m_wins)
    m_gl = abs(sum(d['pnl'] for d in m_loss))
    m_pf = round(m_gp/m_gl, 2) if m_gl > 0 else (999.0 if m_gp > 0 else 0)
    print(f"{m} | Trades: {len(m_trades):2d} | Wins: {len(m_wins):2d} ({m_wr:4.1f}%) | PnL: ${m_pnl:8.2f} | PF: {m_pf:5.2f}")

print("\n=== DAY OF WEEK BREAKDOWN ===")
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
day_trades = defaultdict(list)
for d in trades.values():
    dt = datetime.strptime(d['open_time'][:10], '%Y.%m.%d')
    day_trades[days[dt.weekday()]].append(d)

for day in days:
    dt_list = day_trades[day]
    d_wins = [d for d in dt_list if d['pnl'] > 0]
    d_pnl = sum(d['pnl'] for d in dt_list)
    d_wr = round(len(d_wins)/len(dt_list)*100, 1) if dt_list else 0
    print(f"{day:9s} | Trades: {len(dt_list):2d} | Wins: {len(d_wins):2d} ({d_wr:4.1f}%) | PnL: ${d_pnl:8.2f}")

print("\n=== DETAILED 2026 TRADES ===")
t_2026 = [d for d in trades.values() if d['open_time'].startswith('2026')]
cum_pnl = 0.0
for d in t_2026:
    cum_pnl += d['pnl']
    res = 'WIN' if d['pnl'] > 0 else 'LOSS'
    mods = ','.join(d['modifications']) if d['modifications'] else '-'
    print(f"#{d['ticket']:3d} | {d['open_time'][:16]} | {d['engine']:16s} | {d['type']:4s} | Lot: {d['lot']:4.2f} | In: {d['open_price']:7.2f} | Out: {d['close_price']:7.2f} | PnL: ${d['pnl']:7.2f} ({res:4s}) | Cum: ${cum_pnl:7.2f} | {d['close_reason']:15s} | {mods}")

print("\n=== ASIAN SWEEPER FORENSICS IN v6.3.1 ===")
asian_trades = [d for d in trades.values() if d['engine'] == 'Asian Sweeper']
tp_hits = [d for d in asian_trades if d['close_reason'] == 'TAKE PROFIT']
sl_hits = [d for d in asian_trades if d['close_reason'] == 'STOP LOSS' and 'SCALPER BE' not in d['modifications']]
be_hits = [d for d in asian_trades if 'SCALPER BE' in d['modifications']]
auto_closes = [d for d in asian_trades if 'SCALPER AUTO-CLOSE' in d['modifications']]
print(f"Total Asian Trades: {len(asian_trades)}")
print(f"Hit Full TP ($5.00): {len(tp_hits)} ({round(len(tp_hits)/len(asian_trades)*100,1)}%)")
print(f"Hit Full SL ($6.00): {len(sl_hits)} ({round(len(sl_hits)/len(asian_trades)*100,1)}%)")
print(f"Activated BE Lock (+3.00 USD -> +0.50 SL): {len(be_hits)} ({round(len(be_hits)/len(asian_trades)*100,1)}%)")
print(f"Auto-Closed at 07:45: {len(auto_closes)} ({round(len(auto_closes)/len(asian_trades)*100,1)}%)")

