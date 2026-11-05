import json, struct
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

for swing_bars in [3, 4, 5]:
    for swing_buf in [0.80, 1.00, 1.50]:
        trades = []
        open_pos = None

        for i in range(100, len(bars)):
            b = bars[i]
            if b['time'] < start_dt or b['time'] > end_dt: continue
            
            if open_pos is not None:
                pos = open_pos
                bars_held = i - pos['open_bar_idx']
                hours_held = bars_held * 0.25
                
                if pos['type'] == 'BUY':
                    init_sl_dist = pos['open'] - pos['init_sl']
                    cur_profit = b['high'] - pos['open']
                    
                    # Dynamic Structural Trail after +1.2R
                    if cur_profit >= (init_sl_dist * 1.2):
                        swing_low = min(bars[j]['low'] for j in range(i-swing_bars, i))
                        trail_sl = swing_low - swing_buf
                        if trail_sl > pos['sl']:
                            pos['sl'] = trail_sl
                            
                    # Time Decay after 3 hours
                    if hours_held >= 3.0 and not pos['time_be_locked']:
                        if b['close'] > pos['open'] + 0.30:
                            pos['sl'] = max(pos['sl'], pos['open'] + 0.30)
                            pos['time_be_locked'] = True
                            
                    if b['low'] <= pos['sl']:
                        pnl = (pos['sl'] - pos['open']) * pos['lots'] * 100.0
                        trades.append({'pnl': pnl})
                        open_pos = None
                    elif b['high'] >= pos['tp']:
                        pnl = (pos['tp'] - pos['open']) * pos['lots'] * 100.0
                        trades.append({'pnl': pnl})
                        open_pos = None
                        
                elif pos['type'] == 'SELL':
                    init_sl_dist = pos['init_sl'] - pos['open']
                    cur_profit = pos['open'] - b['low']
                    
                    if cur_profit >= (init_sl_dist * 1.2):
                        swing_high = max(bars[j]['high'] for j in range(i-swing_bars, i))
                        trail_sl = swing_high + swing_buf
                        if trail_sl < pos['sl']:
                            pos['sl'] = trail_sl
                            
                    if hours_held >= 3.0 and not pos['time_be_locked']:
                        if b['close'] < pos['open'] - 0.30:
                            pos['sl'] = min(pos['sl'], pos['open'] - 0.30)
                            pos['time_be_locked'] = True
                            
                    if b['high'] >= pos['sl']:
                        pnl = (pos['open'] - pos['sl']) * pos['lots'] * 100.0
                        trades.append({'pnl': pnl})
                        open_pos = None
                    elif b['low'] <= pos['tp']:
                        pnl = (pos['open'] - pos['tp']) * pos['lots'] * 100.0
                        trades.append({'pnl': pnl})
                        open_pos = None

            if open_pos is not None: continue
            
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
            
            at_res = (c1['high'] >= asian_high or c1['high'] >= pdh)
            if at_res and (c1_upper_wick / c1_rng) >= 0.35 and c1['close'] < c1['open']:
                sl = c1['high'] + 1.00
                entry = b['open']
                sl_dist = sl - entry
                if 1.50 <= sl_dist <= 4.50:
                    tp = entry - (sl_dist * 3.5)
                    open_pos = {
                        'type': 'SELL', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp,
                        'lots': 0.10, 'open_bar_idx': i, 'time_be_locked': False
                    }
                    continue
                    
            at_sup = (c1['low'] <= asian_low or c1['low'] <= pdl)
            if at_sup and (c1_lower_wick / c1_rng) >= 0.35 and c1['close'] > c1['open']:
                sl = c1['low'] - 1.00
                entry = b['open']
                sl_dist = entry - sl
                if 1.50 <= sl_dist <= 4.50:
                    tp = entry + (sl_dist * 3.5)
                    open_pos = {
                        'type': 'BUY', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp,
                        'lots': 0.10, 'open_bar_idx': i, 'time_be_locked': False
                    }
                    continue

        wins = [x for x in trades if x['pnl'] > 0]
        losses = [x for x in trades if x['pnl'] <= 0]
        gp = sum(x['pnl'] for x in wins)
        gl = abs(sum(x['pnl'] for x in losses))
        pf = gp / (gl if gl > 0 else 1.0)
        net = gp - gl
        wr = len(wins) / len(trades) * 100.0 if trades else 0.0
        
        # Test Compound
        bal = 2000.0
        peak = bal
        max_dd_pct = 0.0
        for t in trades:
            risk_amt = bal * 0.025
            lot = risk_amt / (300.0 * 1.0)
            if lot > 2.0: lot = 2.0
            p = (t['pnl'] / 0.10) * lot
            bal += p
            if bal > peak: peak = bal
            dd = peak - bal
            dd_pct = (dd / peak) * 100.0
            if dd_pct > max_dd_pct: max_dd_pct = dd_pct
            
        print(f"SwingBars: {swing_bars} | Buf: ${swing_buf:.2f} -> Trades: {len(trades)} | WinRate: {wr:.1f}% | Net: ${bal-2000:.2f} | PF: {pf:.2f} | DD: {max_dd_pct:.1f}%")
