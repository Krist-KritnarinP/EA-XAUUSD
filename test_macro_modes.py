import struct
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

daily = {}
for b in bars:
    d = b['time'].date()
    if d not in daily:
        daily[d] = {'open': b['open'], 'high': b['high'], 'low': b['low'], 'close': b['close']}
    else:
        if b['high'] > daily[d]['high']: daily[d]['high'] = b['high']
        if b['low'] < daily[d]['low']: daily[d]['low'] = b['low']
        daily[d]['close'] = b['close']
dates_sorted = sorted(list(daily.keys()))

daily_atr = {}
for idx in range(14, len(dates_sorted)):
    cur_d = dates_sorted[idx]
    tr_sum = sum(max(daily[dates_sorted[j]]['high'] - daily[dates_sorted[j]]['low'], abs(daily[dates_sorted[j]]['high'] - daily[dates_sorted[j-1]]['close']), abs(daily[dates_sorted[j]]['low'] - daily[dates_sorted[j-1]]['close'])) for j in range(idx-13, idx+1))
    daily_atr[cur_d] = tr_sum / 14.0

asian_ranges = {}
for b in bars:
    d = b['time'].date()
    if 0 <= b['time'].hour < 7:
        if d not in asian_ranges:
            asian_ranges[d] = {'high': b['high'], 'low': b['low']}
        else:
            if b['high'] > asian_ranges[d]['high']: asian_ranges[d]['high'] = b['high']
            if b['low'] < asian_ranges[d]['low']: asian_ranges[d]['low'] = b['low']

closes = [b['close'] for b in bars]
ema800 = [closes[0]] * len(closes)
k = 2.0 / (800 + 1)
for idx in range(1, len(closes)):
    ema800[idx] = closes[idx] * k + ema800[idx-1] * (1 - k)

atrs = [0.0] * len(bars)
for i in range(14, len(bars)):
    tr_sum = sum(max(bars[j]['high'] - bars[j]['low'], abs(bars[j]['high'] - bars[j-1]['close']), abs(bars[j]['low'] - bars[j-1]['close'])) for j in range(i-13, i+1))
    atrs[i] = tr_sum / 14.0

for mode in ['NONE', 'D1_DUMP_AND_H4', 'D1_DUMP_ONLY']:
    trades = []
    open_pos = None

    for i in range(100, len(bars)):
        b = bars[i]
        if b['time'] < start_dt or b['time'] > end_dt: continue
        
        # Position management
        if open_pos is not None:
            pos = open_pos
            bars_held = i - pos['open_bar_idx']
            hours_held = bars_held * 0.25
            
            if pos['type'] == 'BUY':
                init_sl_dist = pos['open'] - pos['init_sl']
                cur_profit = b['high'] - pos['open']
                if not pos['is_be'] and cur_profit >= (init_sl_dist * 1.8):
                    pos['sl'] = pos['open'] + 0.30
                    pos['is_be'] = True
                if b['low'] <= pos['sl']:
                    trades.append({'time': b['time'], 'pnl': (pos['sl'] - pos['open']) * pos['lots'] * 100.0})
                    open_pos = None
                elif b['high'] >= pos['tp']:
                    trades.append({'time': b['time'], 'pnl': (pos['tp'] - pos['open']) * pos['lots'] * 100.0})
                    open_pos = None
            elif pos['type'] == 'SELL':
                init_sl_dist = pos['init_sl'] - pos['open']
                cur_profit = pos['open'] - b['low']
                if not pos['is_be'] and cur_profit >= (init_sl_dist * 1.8):
                    pos['sl'] = pos['open'] - 0.30
                    pos['is_be'] = True
                if b['high'] >= pos['sl']:
                    trades.append({'time': b['time'], 'pnl': (pos['open'] - pos['sl']) * pos['lots'] * 100.0})
                    open_pos = None
                elif b['low'] <= pos['tp']:
                    trades.append({'time': b['time'], 'pnl': (pos['open'] - pos['tp']) * pos['lots'] * 100.0})
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
        pdh = daily[prev_date]['high']
        pdl = daily[prev_date]['low']
        prev_open = daily[prev_date]['open']
        prev_close = daily[prev_date]['close']
        prev_rng = pdh - pdl
        d1_atr = daily_atr.get(cur_date, 60.0)
        h4_ema = ema800[i]
        
        is_d1_dump = (prev_close < prev_open) and (prev_rng >= d1_atr * 1.0)
        is_below_h4 = (b['close'] < h4_ema)
        
        block_buy = False
        if mode == 'D1_DUMP_AND_H4' and is_d1_dump and is_below_h4: block_buy = True
        elif mode == 'D1_DUMP_ONLY' and is_d1_dump: block_buy = True

        if cur_date not in asian_ranges: continue
        asian_high = asian_ranges[cur_date]['high']
        asian_low = asian_ranges[cur_date]['low']
        
        c1 = bars[i-1]
        c1_rng = c1['high'] - c1['low']
        if c1_rng <= 0.80: continue
        
        c1_upper_wick = c1['high'] - max(c1['open'], c1['close'])
        c1_lower_wick = min(c1['open'], c1['close']) - c1['low']
        
        # SELL
        at_res = (c1['high'] >= asian_high or c1['high'] >= pdh)
        if at_res and (c1_upper_wick / c1_rng) >= 0.35 and c1['close'] < c1['open']:
            sl = c1['high'] + 1.00
            entry = b['open']
            sl_dist = sl - entry
            if 1.50 <= sl_dist <= 4.50:
                tp = entry - (sl_dist * 3.5)
                open_pos = {'type': 'SELL', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp, 'lots': 0.10, 'open_bar_idx': i, 'is_be': False}
                continue
                
        # BUY
        at_sup = (c1['low'] <= asian_low or c1['low'] <= pdl)
        if at_sup and (c1_lower_wick / c1_rng) >= 0.35 and c1['close'] > c1['open'] and not block_buy:
            sl = c1['low'] - 1.00
            entry = b['open']
            sl_dist = entry - sl
            if 1.50 <= sl_dist <= 4.50:
                tp = entry + (sl_dist * 3.5)
                open_pos = {'type': 'BUY', 'open': entry, 'sl': sl, 'init_sl': sl, 'tp': tp, 'lots': 0.10, 'open_bar_idx': i, 'is_be': False}
                continue

    wins = [x for x in trades if x['pnl'] > 0]
    losses = [x for x in trades if x['pnl'] <= 0]
    gp = sum(x['pnl'] for x in wins)
    gl = abs(sum(x['pnl'] for x in losses))
    pf = gp / (gl if gl > 0 else 1.0)
    net = gp - gl
    wr = len(wins) / len(trades) * 100.0 if trades else 0.0
    
    # Oct 2026 stats
    oct26_trades = [x for x in trades if x['time'].year == 2026 and x['time'].month == 10]
    oct26_wins = [x for x in oct26_trades if x['pnl'] > 0]
    oct26_pnl = sum(x['pnl'] for x in oct26_trades)
    
    print(f"Mode: {mode:16s} -> All Trades: {len(trades)} | WinRate: {wr:.1f}% | Net: ${net:.2f} | PF: {pf:.2f} || Oct26: {len(oct26_trades)} trades, {len(oct26_wins)} wins, PnL: ${oct26_pnl:.2f}")
