import struct, os
from datetime import datetime

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

# Precalculate daily highs and lows
daily_highs = {}
daily_lows = {}
for b in bars:
    d = b['time'].date()
    if d not in daily_highs or b['high'] > daily_highs[d]: daily_highs[d] = b['high']
    if d not in daily_lows or b['low'] < daily_lows[d]: daily_lows[d] = b['low']

dates_sorted = sorted(list(daily_highs.keys()))

# Precalculate Asian ranges (00:00 - 07:00)
asian_ranges = {}
for b in bars:
    d = b['time'].date()
    if 0 <= b['time'].hour < 7:
        if d not in asian_ranges:
            asian_ranges[d] = {'high': b['high'], 'low': b['low']}
        else:
            if b['high'] > asian_ranges[d]['high']: asian_ranges[d]['high'] = b['high']
            if b['low'] < asian_ranges[d]['low']: asian_ranges[d]['low'] = b['low']

# ATR 14
atrs = [0.0] * len(bars)
for i in range(14, len(bars)):
    tr_sum = 0.0
    for j in range(i-13, i+1):
        tr = max(bars[j]['high'] - bars[j]['low'], abs(bars[j]['high'] - bars[j-1]['close']), abs(bars[j]['low'] - bars[j-1]['close']))
        tr_sum += tr
    atrs[i] = tr_sum / 14.0

# Test combinations:
# 1. be_r: [1.2, 1.3, 1.4, 1.5]
# 2. session filter: all day vs skip pre-london vs high-volume london/ny
# 3. min_atr filter to avoid dead chop
print("Testing POI Sniper V2 Upgrades...")

for be_r in [1.2, 1.3, 1.4, 1.5]:
    for min_atr in [0.0, 1.0, 1.5]:
        for skip_pre_london in [False, True]:
            trades = []
            open_pos = None
            
            for i in range(100, len(bars)):
                b = bars[i]
                if b['time'] < start_dt or b['time'] > end_dt: continue
                
                # Manage open position
                if open_pos is not None:
                    pos = open_pos
                    if pos['type'] == 'BUY':
                        # Early Breakeven Lock at be_r
                        if not pos['is_be'] and b['high'] >= pos['open'] + (pos['open'] - pos['init_sl']) * be_r:
                            pos['sl'] = pos['open'] + 0.30 # BE + spread buffer
                            pos['is_be'] = True
                        if b['low'] <= pos['sl']:
                            pnl = (pos['sl'] - pos['open']) * pos['lots'] * 100.0
                            trades.append({'time': b['time'], 'type': 'BUY', 'pnl': pnl, 'reason': 'BE' if pos['is_be'] else 'SL'})
                            open_pos = None
                        elif b['high'] >= pos['tp']:
                            pnl = (pos['tp'] - pos['open']) * pos['lots'] * 100.0
                            trades.append({'time': b['time'], 'type': 'BUY', 'pnl': pnl, 'reason': 'TP'})
                            open_pos = None
                    elif pos['type'] == 'SELL':
                        if not pos['is_be'] and b['low'] <= pos['open'] - (pos['init_sl'] - pos['open']) * be_r:
                            pos['sl'] = pos['open'] - 0.30
                            pos['is_be'] = True
                        if b['high'] >= pos['sl']:
                            pnl = (pos['open'] - pos['sl']) * pos['lots'] * 100.0
                            trades.append({'time': b['time'], 'type': 'SELL', 'pnl': pnl, 'reason': 'BE' if pos['is_be'] else 'SL'})
                            open_pos = None
                        elif b['low'] <= pos['tp']:
                            pnl = (pos['open'] - pos['tp']) * pos['lots'] * 100.0
                            trades.append({'time': b['time'], 'type': 'SELL', 'pnl': pnl, 'reason': 'TP'})
                            open_pos = None
                
                if open_pos is not None: continue
                
                # Time filter
                t = b['time']
                h = t.hour
                m = h * 60 + t.minute
                if skip_pre_london and h < 9: continue
                if not (8*60 <= m <= 20*60 + 30): continue
                
                # Volatility filter (from 6.2.3 concept)
                if min_atr > 0 and atrs[i] < min_atr: continue
                
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
                        open_pos = {'type': 'SELL', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp, 'lots': 0.10, 'is_be': False}
                        continue
                        
                # BUY Setup
                at_sup = (c1['low'] <= asian_low or c1['low'] <= pdl)
                if at_sup and (c1_lower_wick / c1_rng) >= 0.35 and c1['close'] > c1['open']:
                    sl = c1['low'] - 1.00
                    entry = b['open']
                    sl_dist = entry - sl
                    if 1.50 <= sl_dist <= 4.50:
                        tp = entry + (sl_dist * 3.5)
                        open_pos = {'type': 'BUY', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp, 'lots': 0.10, 'is_be': False}
                        continue
                        
            wins = [x for x in trades if x['pnl'] > 0]
            gross_p = sum(x['pnl'] for x in wins)
            gross_l = abs(sum(x['pnl'] for x in trades if x['pnl'] < 0))
            pf = gross_p / (gross_l if gross_l > 0 else 1.0)
            net = gross_p - gross_l
            wr = len(wins) / len(trades) * 100.0 if trades else 0.0
            
            # Print if PF >= 1.35
            if pf >= 1.35:
                print(f"BE_R: {be_r} | MinATR: {min_atr} | SkipPreLon: {skip_pre_london} -> Trades: {len(trades)} | WinRate: {wr:.1f}% | Net: ${net:.2f} | PF: {pf:.2f}")
