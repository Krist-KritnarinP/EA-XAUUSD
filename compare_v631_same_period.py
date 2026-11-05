import re
import json

# Let's extract v6.3.1 trades from 2025.06.01 to 2026.10.09 across 20261012.log and 20261013.log
log_files = [
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261012.log',
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\tester\logs\20261013.log'
]

v631_trades = {}
open_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_1 GOLD,M15: open #(\d+) (buy|sell) ([\d\.]+) GOLD at ([\d\.]+) sl: ([\d\.]+) tp: ([\d\.]+)')
engine_pattern = re.compile(r'\[(NEW YORK REVERSAL|SNIPER RUNNER|ASIAN SQUEEZE).*?\]\s+Ticket:\s+#(\d+)')
sunset_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+GoldSniper_Tester_v6_3_1 GOLD,M15: close #(\d+).*?at price ([\d\.]+)')
sl_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: stop loss #(\d+) at ([\d\.]+) \(([\d\.]+) / ([\d\.]+)\)')
tp_pattern = re.compile(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2})\s+Tester: take profit #(\d+) at ([\d\.]+) \(([\d\.]+) / ([\d\.]+)\)')

for lf in log_files:
    with open(lf, 'r', encoding='cp1252', errors='ignore') as f:
        for line in f:
            if 'GoldSniper_Tester_v6_3_1' not in line and 'Tester:' not in line:
                continue
            
            m_op = open_pattern.search(line)
            if m_op:
                time_str, ticket, side, lots, price, sl, tp = m_op.groups()
                if time_str >= '2025.06.01' and time_str <= '2026.10.10':
                    t = int(ticket)
                    v631_trades[t] = {
                        'ticket': t,
                        'open_time': time_str,
                        'side': side.upper(),
                        'lots': float(lots),
                        'open_price': float(price),
                        'sl': float(sl),
                        'tp': float(tp),
                        'engine': 'UNKNOWN'
                    }
                continue
            
            m_eng = engine_pattern.search(line)
            if m_eng:
                eng, ticket = m_eng.groups()
                t = int(ticket)
                if t in v631_trades:
                    v631_trades[t]['engine'] = eng
                continue
            
            m_sl = sl_pattern.search(line)
            if m_sl:
                time_str, ticket, sl_price, bid, ask = m_sl.groups()
                t = int(ticket)
                if t in v631_trades:
                    v631_trades[t]['close_time'] = time_str
                    side = v631_trades[t]['side']
                    v631_trades[t]['close_price'] = float(bid) if side == 'BUY' else float(ask)
                    v631_trades[t]['close_reason'] = 'STOP_LOSS'
                continue
            
            m_tp = tp_pattern.search(line)
            if m_tp:
                time_str, ticket, tp_price, bid, ask = m_tp.groups()
                t = int(ticket)
                if t in v631_trades:
                    v631_trades[t]['close_time'] = time_str
                    side = v631_trades[t]['side']
                    v631_trades[t]['close_price'] = float(bid) if side == 'BUY' else float(ask)
                    v631_trades[t]['close_reason'] = 'TAKE_PROFIT'
                continue
            
            m_sun = sunset_pattern.search(line)
            if m_sun:
                time_str, ticket, price = m_sun.groups()
                t = int(ticket)
                if t in v631_trades:
                    v631_trades[t]['close_time'] = time_str
                    v631_trades[t]['close_price'] = float(price)
                    v631_trades[t]['close_reason'] = 'SUNSET_EXIT'
                continue

# Calculate v6.3.1 performance
v631_total_pnl = 0.0
v631_engine_stats = {
    'SNIPER RUNNER': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0},
    'NEW YORK REVERSAL': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0},
    'ASIAN SQUEEZE': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0},
    'UNKNOWN': {'count': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
}

for t in v631_trades.values():
    side = t['side']
    op = t['open_price']
    cp = t.get('close_price', op)
    diff = (cp - op) if side == 'BUY' else (op - cp)
    pnl = diff * t['lots'] * 100.0
    t['pnl'] = pnl
    v631_total_pnl += pnl
    eng = t['engine']
    if eng not in v631_engine_stats: eng = 'UNKNOWN'
    st = v631_engine_stats[eng]
    st['count'] += 1
    st['pnl'] += pnl
    if pnl > 0: st['wins'] += 1
    else: st['losses'] += 1

print("="*70)
print(f"V6.3.1 BENCHMARK (Exact same period: 2025.06 - 2026.10):")
print(f"Total Trades: {len(v631_trades)}")
print(f"Total PnL: ${v631_total_pnl:,.2f}")
print("="*70)
for eng, st in v631_engine_stats.items():
    if st['count'] == 0: continue
    wr = (st['wins'] / st['count']) * 100.0 if st['count'] > 0 else 0.0
    print(f"Engine: {eng:22s} | Trades: {st['count']:3d} | Win: {st['wins']:2d} | Loss: {st['losses']:2d} | WR: {wr:5.1f}% | Net PnL: ${st['pnl']:+9.2f}")
