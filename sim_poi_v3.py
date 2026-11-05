import json, struct
from datetime import datetime

# Load M15 bars
hst_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst'
bars = []
with open(hst_file, 'rb') as f:
    f.read(148)
    while True:
        data = f.read(60)
        if len(data) < 60: break
        unp = struct.unpack('<QddddQiq', data)
        bars.append({
            'time': datetime.fromtimestamp(unp[0]),
            'open': unp[1],
            'high': unp[2],
            'low': unp[3],
            'close': unp[4]
        })

start_dt = datetime(2025, 10, 1)
end_dt = datetime(2026, 10, 31)

daily_highs = {}
daily_lows = {}
for b in bars:
    d = b['time'].date()
    if d not in daily_highs or b['high'] > daily_highs[d]: daily_highs[d] = b['high']
    if d not in daily_lows or b['low'] < daily_lows[d]: daily_lows[d] = b['low']
dates_sorted = sorted(list(daily_highs.keys()))

asian_ranges = {}
for b in bars:
    d = b['time'].date()
    if 0 <= b['time'].hour < 7:
        if d not in asian_ranges:
            asian_ranges[d] = {'high': b['high'], 'low': b['low']}
        else:
            if b['high'] > asian_ranges[d]['high']: asian_ranges[d]['high'] = b['high']
            if b['low'] < asian_ranges[d]['low']: asian_ranges[d]['low'] = b['low']

atrs = [0.0] * len(bars)
for i in range(14, len(bars)):
    tr_sum = sum(max(bars[j]['high'] - bars[j]['low'], abs(bars[j]['high'] - bars[j-1]['close']), abs(bars[j]['low'] - bars[j-1]['close'])) for j in range(i-13, i+1))
    atrs[i] = tr_sum / 14.0

trades = []
open_pos = None

for i in range(100, len(bars)):
    b = bars[i]
    if b['time'] < start_dt or b['time'] > end_dt: continue
    
    # Manage open position with v3 Dynamic Structural Trailing & Time Decay
    if open_pos is not None:
        pos = open_pos
        c1 = bars[i-1]
        bars_held = i - pos['open_bar_idx']
        hours_held = bars_held * 0.25 # 15 mins per bar
        
        if pos['type'] == 'BUY':
            init_sl_dist = pos['open'] - pos['init_sl']
            current_profit_dist = b['high'] - pos['open']
            
            # Rule 1: Dynamic Structural Trailing once profit reaches >= 1.2R
            if current_profit_dist >= (init_sl_dist * 1.2):
                pos['reached_1_2r'] = True
                # Trail behind recent M15 swing low (c1 low - 0.50 buffer)
                trail_sl = c1['low'] - 0.50
                if trail_sl > pos['sl']:
                    pos['sl'] = trail_sl
                    
            # Rule 2: Time Decay Guard - after 3 hours (12 M15 bars), if in profit, lock BE
            if hours_held >= 3.0 and not pos['time_be_locked']:
                if b['close'] > pos['open'] + 0.30:
                    pos['sl'] = max(pos['sl'], pos['open'] + 0.30)
                    pos['time_be_locked'] = True
                    
            # Check SL or TP hit
            if b['low'] <= pos['sl']:
                pnl = (pos['sl'] - pos['open']) * pos['lots'] * 100.0
                trades.append({'time': b['time'], 'type': 'BUY', 'pnl': pnl, 'lots': pos['lots'], 'reason': 'SL/TRAIL', 'dur': hours_held})
                open_pos = None
            elif b['high'] >= pos['tp']:
                pnl = (pos['tp'] - pos['open']) * pos['lots'] * 100.0
                trades.append({'time': b['time'], 'type': 'BUY', 'pnl': pnl, 'lots': pos['lots'], 'reason': 'TP', 'dur': hours_held})
                open_pos = None
                
        elif pos['type'] == 'SELL':
            init_sl_dist = pos['init_sl'] - pos['open']
            current_profit_dist = pos['open'] - b['low']
            
            if current_profit_dist >= (init_sl_dist * 1.2):
                pos['reached_1_2r'] = True
                trail_sl = c1['high'] + 0.50
                if trail_sl < pos['sl']:
                    pos['sl'] = trail_sl
                    
            if hours_held >= 3.0 and not pos['time_be_locked']:
                if b['close'] < pos['open'] - 0.30:
                    pos['sl'] = min(pos['sl'], pos['open'] - 0.30)
                    pos['time_be_locked'] = True
                    
            if b['high'] >= pos['sl']:
                pnl = (pos['open'] - pos['sl']) * pos['lots'] * 100.0
                trades.append({'time': b['time'], 'type': 'SELL', 'pnl': pnl, 'lots': pos['lots'], 'reason': 'SL/TRAIL', 'dur': hours_held})
                open_pos = None
            elif b['low'] <= pos['tp']:
                pnl = (pos['open'] - pos['tp']) * pos['lots'] * 100.0
                trades.append({'time': b['time'], 'type': 'SELL', 'pnl': pnl, 'lots': pos['lots'], 'reason': 'TP', 'dur': hours_held})
                open_pos = None

    if open_pos is not None: continue
    
    # New York Session filter (15:00 - 20:30)
    t = b['time']
    h = t.hour
    m = t.minute
    if not (15 <= h < 20 or (h == 20 and m <= 30)): continue
    if atrs[i] < 0.80: continue
    
    cur_date = t.date()
    idx_d = dates_sorted.index(cur_date) if cur_date in dates_sorted else -1
    if idx_d <= 0: continue
    prev_date = dates_sorted[idx_d - 1]
    pdh = daily_highs.get(prev_date, 0.0)
    pdl = daily_lows.get(prev_date, 999999.0)
    if cur_date not in asian_ranges: continue
    asian_high = asian_ranges[cur_date]['high']
    asian_low = asian_ranges[cur_date]['low']
    
    c1 = bars[i-1]
    c1_rng = c1['high'] - c1['low']
    if c1_rng <= 0.80: continue
    
    c1_upper_wick = c1['high'] - max(c1['open'], c1['close'])
    c1_lower_wick = min(c1['open'], c1['close']) - c1['low']
    
    # SELL Setup
    at_res = (c1['high'] >= asian_high or c1['high'] >= pdh)
    if at_res and (c1_upper_wick / c1_rng) >= 0.35 and c1['close'] < c1['open']:
        sl = c1['high'] + 1.00
        entry = b['open']
        sl_dist = sl - entry
        if 1.50 <= sl_dist <= 4.50:
            tp = entry - (sl_dist * 3.5)
            open_pos = {
                'type': 'SELL', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp,
                'lots': 0.10, 'open_bar_idx': i, 'reached_1_2r': False, 'time_be_locked': False
            }
            continue
            
    # BUY Setup
    at_sup = (c1['low'] <= asian_low or c1['low'] <= pdl)
    if at_sup and (c1_lower_wick / c1_rng) >= 0.35 and c1['close'] > c1['open']:
        sl = c1['low'] - 1.00
        entry = b['open']
        sl_dist = entry - sl
        if 1.50 <= sl_dist <= 4.50:
            tp = entry + (sl_dist * 3.5)
            open_pos = {
                'type': 'BUY', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp,
                'lots': 0.10, 'open_bar_idx': i, 'reached_1_2r': False, 'time_be_locked': False
            }
            continue

print(f"Total v3 Trades: {len(trades)}")
wins = [t for t in trades if t['pnl'] > 0]
losses = [t for t in trades if t['pnl'] <= 0]
gp = sum(t['pnl'] for t in wins)
gl = abs(sum(t['pnl'] for t in losses))
net = gp - gl
pf = gp / (gl if gl > 0 else 1.0)
wr = len(wins) / len(trades) * 100.0

print(f"Wins: {len(wins)} ({wr:.1f}%) | Losses: {len(losses)}")
print(f"Gross Profit: USD {gp:.2f} | Gross Loss: USD -{gl:.2f}")
print(f"Net Profit (0.10 lot): USD {net:.2f}")
print(f"Profit Factor: {pf:.2f}")

# Now test with Dynamic Compounding 2.5% starting with $2,000!
bal = 2000.0
peak = bal
max_dd = 0.0
max_dd_pct = 0.0

for t in trades:
    # calculate lot with 2.5% risk
    sl_pts = 300 # average
    risk_amt = bal * 0.025
    lot = risk_amt / (sl_pts * 1.0)
    if lot > 2.0: lot = 2.0
    if lot < 0.01: lot = 0.01
    
    p = (t['pnl'] / 0.10) * lot
    bal += p
    if bal > peak: peak = bal
    dd = peak - bal
    dd_pct = (dd / peak) * 100.0
    if dd > max_dd: max_dd = dd
    if dd_pct > max_dd_pct: max_dd_pct = dd_pct

net_compound = bal - 2000.0
print(f"\n=== WITH 2.5% DYNAMIC COMPOUNDING (Start $2,000) ===")
print(f"End Balance: USD {bal:.2f}")
print(f"Total Net Profit: USD {net_compound:.2f}")
print(f"Max Drawdown: USD {max_dd:.2f} ({max_dd_pct:.1f}%)")
