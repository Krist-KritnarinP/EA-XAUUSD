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

total_trades = len(trades)
total_pnl = sum(d['pnl'] for d in trades.values())
wins = [d for d in trades.values() if d['pnl'] > 0]
losses = [d for d in trades.values() if d['pnl'] < 0]

gross_profit = sum(d['pnl'] for d in wins)
gross_loss = abs(sum(d['pnl'] for d in losses))
pf = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0
wr = round(len(wins) / total_trades * 100, 1)

print("=== OVERALL SUMMARY v6.3.1 ===")
print(f"Total Trades: {total_trades}")
print(f"Wins: {len(wins)} ({wr}%), Losses: {len(losses)} ({round(len(losses)/total_trades*100,1)}%)")
print(f"Gross Profit: ${gross_profit:.2f}, Gross Loss: ${gross_loss:.2f}")
print(f"Net PnL: ${total_pnl:.2f}")
print(f"Profit Factor: {pf}")

print("\n=== ENGINE BREAKDOWN ===")
for eng in ['London Sniper', 'New York Reversal', 'Asian Sweeper']:
    eng_trades = [d for d in trades.values() if d['engine'] == eng]
    if eng_trades:
        e_wins = [d for d in eng_trades if d['pnl'] > 0]
        e_loss = [d for d in eng_trades if d['pnl'] < 0]
        e_pnl = sum(d['pnl'] for d in eng_trades)
        e_wr = round(len(e_wins)/len(eng_trades)*100, 1)
        e_gp = sum(d['pnl'] for d in e_wins)
        e_gl = abs(sum(d['pnl'] for d in e_loss))
        e_pf = round(e_gp / e_gl, 2) if e_gl > 0 else 0
        print(f"{eng}: {len(eng_trades)} trades | Wins: {len(e_wins)} ({e_wr}%) | PnL: ${e_pnl:.2f} | Gross Win: ${e_gp:.2f} | Gross Loss: ${e_gl:.2f} | PF: {e_pf}")

print("\n=== YEARLY BREAKDOWN ===")
years = sorted(list(set(d['open_time'][:4] for d in trades.values())))
for y in years:
    y_trades = [d for d in trades.values() if d['open_time'].startswith(y)]
    y_wins = [d for d in y_trades if d['pnl'] > 0]
    y_loss = [d for d in y_trades if d['pnl'] < 0]
    y_pnl = sum(d['pnl'] for d in y_trades)
    y_wr = round(len(y_wins)/len(y_trades)*100, 1) if y_trades else 0
    y_gp = sum(d['pnl'] for d in y_wins)
    y_gl = abs(sum(d['pnl'] for d in y_loss))
    y_pf = round(y_gp / y_gl, 2) if y_gl > 0 else 0
    print(f"Year {y}: {len(y_trades)} trades | Wins: {len(y_wins)} ({y_wr}%) | PnL: ${y_pnl:.2f} | PF: {y_pf}")

