import struct
import math
from datetime import datetime, date
from collections import defaultdict

hst_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst'
with open(hst_file, 'rb') as f:
    f.read(148)
    bars = []
    while True:
        data = f.read(60)
        if len(data) < 60: break
        unp = struct.unpack('<QddddQiq', data)
        bars.append({
            'time': datetime.fromtimestamp(unp[0]),
            'open': unp[1],
            'high': unp[2],
            'low': unp[3],
            'close': unp[4],
            'vol': unp[5]
        })

start_dt = datetime(2025, 10, 1)
end_dt = datetime(2026, 11, 1)

# Precalculate daily PDH, PDL
daily_bars = defaultdict(list)
for b in bars:
    daily_bars[b['time'].date()].append(b)

sorted_dates = sorted(list(daily_bars.keys()))
pdh_map = {}
pdl_map = {}
for i in range(1, len(sorted_dates)):
    prev_d = sorted_dates[i-1]
    curr_d = sorted_dates[i]
    prev_bars = daily_bars[prev_d]
    pdh_map[curr_d] = max(b['high'] for b in prev_bars)
    pdl_map[curr_d] = min(b['low'] for b in prev_bars)

# Precalculate Asian Range (00:00 - 07:00) for POI
asian_poi_map = {}
# Precalculate Asian Pre-market Box (04:00 - 08:00) for London Dual-Engine
asian_london_map = {}

for d, d_bars in daily_bars.items():
    poi_bars = [b for b in d_bars if 0 <= b['time'].hour < 7]
    if poi_bars:
        asian_poi_map[d] = {
            'high': max(b['high'] for b in poi_bars),
            'low': min(b['low'] for b in poi_bars)
        }
    lon_bars = [b for b in d_bars if 4 <= b['time'].hour < 8]
    if len(lon_bars) >= 6:
        asian_london_map[d] = {
            'high': max(b['high'] for b in lon_bars),
            'low': min(b['low'] for b in lon_bars)
        }

# Precalculate Indicators: M15 EMA50, EMA200, ATR14, RVOL SMA20
closes = [b['close'] for b in bars]
n = len(bars)

# EMAs
def calc_ema(period):
    res = [closes[0]] * n
    k = 2.0 / (period + 1)
    for i in range(1, n):
        res[i] = closes[i] * k + res[i-1] * (1 - k)
    return res

ema50_m15 = calc_ema(50)
ema200_m15 = calc_ema(200)

# ATR 14
atr14 = [0.0] * n
for i in range(1, n):
    tr = max(bars[i]['high'] - bars[i]['low'],
             abs(bars[i]['high'] - bars[i-1]['close']),
             abs(bars[i]['low'] - bars[i-1]['close']))
    if i == 1:
        atr14[i] = tr
    elif i <= 14:
        atr14[i] = (atr14[i-1] * (i-1) + tr) / i
    else:
        atr14[i] = (atr14[i-1] * 13 + tr) / 14

# H1 Resampling for H1 Trend (EMA50 and EMA200 on H1)
# 4 M15 bars = 1 H1 bar
h1_bars = []
curr_h1 = None
for b in bars:
    h_time = b['time'].replace(minute=0, second=0)
    if curr_h1 is None or curr_h1['time'] != h_time:
        if curr_h1 is not None:
            h1_bars.append(curr_h1)
        curr_h1 = {'time': h_time, 'open': b['open'], 'high': b['high'], 'low': b['low'], 'close': b['close']}
    else:
        curr_h1['high'] = max(curr_h1['high'], b['high'])
        curr_h1['low'] = min(curr_h1['low'], b['low'])
        curr_h1['close'] = b['close']
if curr_h1: h1_bars.append(curr_h1)

h1_closes = [b['close'] for b in h1_bars]
h1_ema50 = [h1_closes[0]] * len(h1_closes)
h1_ema200 = [h1_closes[0]] * len(h1_closes)
k50 = 2.0 / 51.0
k200 = 2.0 / 201.0
for i in range(1, len(h1_closes)):
    h1_ema50[i] = h1_closes[i] * k50 + h1_ema50[i-1] * (1 - k50)
    h1_ema200[i] = h1_closes[i] * k200 + h1_ema200[i-1] * (1 - k200)

h1_map = {}
for i, hb in enumerate(h1_bars):
    h1_map[hb['time']] = {'close': hb['close'], 'ema50': h1_ema50[i], 'ema200': h1_ema200[i]}

def get_h1_trend(t):
    h_prev = t.replace(minute=0, second=0)
    # Get previous closed H1 bar
    # If t is at 08:15, previous closed H1 bar is 07:00
    from datetime import timedelta
    prev_h = h_prev - timedelta(hours=1)
    if prev_h in h1_map:
        info = h1_map[prev_h]
        bull = (info['close'] > info['ema200']) and (info['ema50'] > info['ema200'])
        bear = (info['close'] < info['ema200']) and (info['ema50'] < info['ema200'])
        return bull, bear
    return False, False

# RVOL SMA20
volumes = [b['vol'] for b in bars]
def check_rvol(idx, threshold):
    if idx < 22: return True
    sum_v = sum(volumes[idx-20:idx])
    avg_v = sum_v / 20.0
    if avg_v <= 0: return True
    return volumes[idx] >= (avg_v * threshold)

print("Starting simulation for Gold POI Sniper v3.5 across 13 months...")

initial_deposit = 2000.0
balance = initial_deposit
equity = initial_deposit
peak_equity = initial_deposit
max_dd = 0.0

open_orders = [] # list of active positions
closed_trades = []

lot_step = 0.01
min_lot = 0.01
max_lot = 2.00

def calc_lot_compound(equity_val, risk_pct, sl_dist):
    if sl_dist <= 0.50: sl_dist = 3.50
    risk_usd = equity_val * (risk_pct / 100.0)
    contract_size = 100.0
    raw_lot = risk_usd / (sl_dist * contract_size)
    l = math.floor(raw_lot / lot_step) * lot_step
    l = max(min_lot, min(max_lot, l))
    return l

for i in range(250, n):
    b0 = bars[i]
    t0 = b0['time']
    if t0 < start_dt or t0 > end_dt:
        continue
    
    b1 = bars[i-1] # previous bar
    d = t0.date()
    
    # 1. Manage Active Positions at Tick/Bar Level
    active_remaining = []
    for pos in open_orders:
        engine = pos['engine']
        cmd = pos['type']
        o_price = pos['open_price']
        sl = pos['sl']
        tp = pos['tp']
        lots = pos['lots']
        init_risk = pos['init_risk']
        
        # Check high / low of bar b0
        closed = False
        
        # BUY MANAGEMENT
        if cmd == 'BUY':
            profit_high = b0['high'] - o_price
            profit_curr = b0['close'] - o_price
            
            # Leg 1: London Sniper Ratchet
            if engine == 'London Sniper':
                if not pos['ratchet_stage2'] and profit_high >= (init_risk * 2.50):
                    pos['sl'] = max(pos['sl'], o_price + (init_risk * 1.25))
                    pos['ratchet_stage2'] = True
                elif not pos['ratchet_stage1'] and profit_high >= (init_risk * 1.75):
                    pos['sl'] = max(pos['sl'], o_price + 0.50)
                    pos['ratchet_stage1'] = True
                # Sunset exit at 13:00
                if t0.hour >= 13 and profit_curr >= (init_risk * 1.25):
                    pnl = (b0['close'] - o_price) * lots * 100.0
                    closed_trades.append({'time': t0, 'engine': engine, 'type': cmd, 'lots': lots, 'pnl': pnl, 'reason': 'SUNSET_EXIT'})
                    balance += pnl
                    equity = balance
                    closed = True
            
            # Leg 2: Judas Sweep Fade Ratchet & Partial TP
            elif engine == 'Judas Sweep Fade':
                # 2-Tier Partial TP at +1.5R
                if not pos['partial_done'] and profit_high >= (init_risk * 1.50):
                    close_lot = math.floor((lots * 0.50) / lot_step) * lot_step
                    if close_lot >= min_lot and (lots - close_lot) >= min_lot:
                        part_pnl = (o_price + init_risk * 1.50 - o_price) * close_lot * 100.0
                        closed_trades.append({'time': t0, 'engine': engine, 'type': cmd, 'lots': close_lot, 'pnl': part_pnl, 'reason': 'PARTIAL_TP_1.5R'})
                        balance += part_pnl
                        equity = balance
                        pos['lots'] -= close_lot
                        pos['sl'] = max(pos['sl'], o_price + 0.30)
                        pos['partial_done'] = True
                # Stage 3 trail
                if profit_high >= (init_risk * 3.50):
                    trail_sl = b0['high'] - (init_risk * 1.50)
                    lock_sl  = o_price + (init_risk * 2.50)
                    pos['sl'] = max(pos['sl'], max(lock_sl, trail_sl))
                elif profit_high >= (init_risk * 2.50):
                    pos['sl'] = max(pos['sl'], o_price + (init_risk * 1.25))
            
            # Leg 3: NY POI Sniper Breakeven
            elif engine == 'POI NY Sniper':
                if not pos['be_done'] and profit_high >= (init_risk * 1.80):
                    pos['sl'] = max(pos['sl'], o_price + 0.30)
                    pos['be_done'] = True
            
            if not closed:
                # Check hit SL
                if b0['low'] <= pos['sl']:
                    pnl = (pos['sl'] - o_price) * pos['lots'] * 100.0
                    reason = 'BE_LOCK' if pos['sl'] >= o_price else 'STOP_LOSS'
                    closed_trades.append({'time': t0, 'engine': engine, 'type': cmd, 'lots': pos['lots'], 'pnl': pnl, 'reason': reason})
                    balance += pnl
                    equity = balance
                    closed = True
                # Check hit TP
                elif b0['high'] >= tp:
                    pnl = (tp - o_price) * pos['lots'] * 100.0
                    closed_trades.append({'time': t0, 'engine': engine, 'type': cmd, 'lots': pos['lots'], 'pnl': pnl, 'reason': 'TAKE_PROFIT'})
                    balance += pnl
                    equity = balance
                    closed = True
        
        # SELL MANAGEMENT
        elif cmd == 'SELL':
            profit_high = o_price - b0['low']
            profit_curr = o_price - b0['close']
            
            # Leg 1: London Sniper Ratchet
            if engine == 'London Sniper':
                if not pos['ratchet_stage2'] and profit_high >= (init_risk * 2.50):
                    pos['sl'] = min(pos['sl'], o_price - (init_risk * 1.25))
                    pos['ratchet_stage2'] = True
                elif not pos['ratchet_stage1'] and profit_high >= (init_risk * 1.75):
                    pos['sl'] = min(pos['sl'], o_price - 0.50)
                    pos['ratchet_stage1'] = True
                if t0.hour >= 13 and profit_curr >= (init_risk * 1.25):
                    pnl = (o_price - b0['close']) * lots * 100.0
                    closed_trades.append({'time': t0, 'engine': engine, 'type': cmd, 'lots': lots, 'pnl': pnl, 'reason': 'SUNSET_EXIT'})
                    balance += pnl
                    equity = balance
                    closed = True
            
            # Leg 2: Judas Sweep Fade
            elif engine == 'Judas Sweep Fade':
                if not pos['partial_done'] and profit_high >= (init_risk * 1.50):
                    close_lot = math.floor((lots * 0.50) / lot_step) * lot_step
                    if close_lot >= min_lot and (lots - close_lot) >= min_lot:
                        part_pnl = (o_price - (o_price - init_risk * 1.50)) * close_lot * 100.0
                        closed_trades.append({'time': t0, 'engine': engine, 'type': cmd, 'lots': close_lot, 'pnl': part_pnl, 'reason': 'PARTIAL_TP_1.5R'})
                        balance += part_pnl
                        equity = balance
                        pos['lots'] -= close_lot
                        pos['sl'] = min(pos['sl'], o_price - 0.30)
                        pos['partial_done'] = True
                if profit_high >= (init_risk * 3.50):
                    trail_sl = b0['low'] + (init_risk * 1.50)
                    lock_sl  = o_price - (init_risk * 2.50)
                    pos['sl'] = min(pos['sl'], min(lock_sl, trail_sl))
                elif profit_high >= (init_risk * 2.50):
                    pos['sl'] = min(pos['sl'], o_price - (init_risk * 1.25))
            
            # Leg 3: NY POI Sniper
            elif engine == 'POI NY Sniper':
                if not pos['be_done'] and profit_high >= (init_risk * 1.80):
                    pos['sl'] = min(pos['sl'], o_price - 0.30)
                    pos['be_done'] = True
            
            if not closed:
                if b0['high'] >= pos['sl']:
                    pnl = (o_price - pos['sl']) * pos['lots'] * 100.0
                    reason = 'BE_LOCK' if pos['sl'] <= o_price else 'STOP_LOSS'
                    closed_trades.append({'time': t0, 'engine': engine, 'type': cmd, 'lots': pos['lots'], 'pnl': pnl, 'reason': reason})
                    balance += pnl
                    equity = balance
                    closed = True
                elif b0['low'] <= tp:
                    pnl = (o_price - tp) * pos['lots'] * 100.0
                    closed_trades.append({'time': t0, 'engine': engine, 'type': cmd, 'lots': pos['lots'], 'pnl': pnl, 'reason': 'TAKE_PROFIT'})
                    balance += pnl
                    equity = balance
                    closed = True
        
        if not closed:
            active_remaining.append(pos)
    
    open_orders = active_remaining
    
    # Calculate drawdown
    if equity > peak_equity: peak_equity = equity
    dd = (peak_equity - equity) / peak_equity * 100.0
    if dd > max_dd: max_dd = dd
    
    # 2. Check Bar 1 for New Trade Entries
    c1_h = b1['high']
    c1_l = b1['low']
    c1_o = b1['open']
    c1_c = b1['close']
    c1_range = c1_h - c1_l
    if c1_range < 0.80: continue
    
    c1_upper_wick = c1_h - max(c1_o, c1_c)
    c1_lower_wick = min(c1_o, c1_c) - c1_l
    c1_body = abs(c1_c - c1_o)
    
    cur_atr = atr14[i-1]
    if cur_atr < 0.80: continue
    
    min_of_day = t0.hour * 60 + t0.minute
    
    # H1 Trend
    is_h1_bull, is_h1_bear = get_h1_trend(t0)
    
    # Check Active Orders count by engine
    lon_active = any(p['engine'] == 'London Sniper' for p in open_orders)
    sw_active  = any(p['engine'] == 'Judas Sweep Fade' for p in open_orders)
    poi_active = any(p['engine'] == 'POI NY Sniper' for p in open_orders)
    
    # ---------------------------------------------------------
    # LEG 2: JUDAS SWEEP FADE (08:00 - 11:30)
    # ---------------------------------------------------------
    if not sw_active and 480 <= min_of_day <= 690:
        if d in asian_london_map:
            ash = asian_london_map[d]['high']
            asl = asian_london_map[d]['low']
            
            # Bearish Judas Sweep of Asian High
            if c1_h >= (ash + 2.50) and c1_c < ash and c1_c < c1_o and (c1_upper_wick / c1_range) >= 0.40:
                if not is_h1_bull:
                    entry = b0['open']
                    sl = c1_h + 2.50
                    sl_dist = sl - entry
                    if 2.00 <= sl_dist <= 12.00:
                        tp = entry - (sl_dist * 5.0)
                        lot = 0.02
                        open_orders.append({
                            'engine': 'Judas Sweep Fade', 'type': 'SELL', 'open_price': entry,
                            'sl': sl, 'tp': tp, 'lots': lot, 'init_risk': sl_dist,
                            'partial_done': False, 'open_time': t0
                        })
            # Bullish Judas Sweep of Asian Low
            elif c1_l <= (asl - 2.50) and c1_c > asl and c1_c > c1_o and (c1_lower_wick / c1_range) >= 0.40:
                if not is_h1_bear:
                    entry = b0['open']
                    sl = c1_l - 2.50
                    sl_dist = entry - sl
                    if 2.00 <= sl_dist <= 12.00:
                        tp = entry + (sl_dist * 5.0)
                        lot = 0.02
                        open_orders.append({
                            'engine': 'Judas Sweep Fade', 'type': 'BUY', 'open_price': entry,
                            'sl': sl, 'tp': tp, 'lots': lot, 'init_risk': sl_dist,
                            'partial_done': False, 'open_time': t0
                        })
    
    # ---------------------------------------------------------
    # LEG 1: LONDON SNIPER (08:00 - 11:30)
    # ---------------------------------------------------------
    if not lon_active and 480 <= min_of_day <= 690:
        if d in asian_london_map:
            ash = asian_london_map[d]['high']
            asl = asian_london_map[d]['low']
            
            rvol_mult = 1.40 if (t0.hour == 8 and t0.minute == 45) else 1.10
            rvol_ok = check_rvol(i-1, rvol_mult)
            body_ok = not (t0.hour == 8 and (c1_body / c1_range) < 0.60)
            
            wick_buy_ok = (c1_upper_wick / c1_range) <= 0.40
            wick_sell_ok = (c1_lower_wick / c1_range) <= 0.40
            
            is_bull = is_h1_bull and (c1_c > ema200_m15[i-1]) and (ema50_m15[i-1] > ema200_m15[i-1]) and wick_buy_ok
            is_bear = is_h1_bear and (c1_c < ema200_m15[i-1]) and (ema50_m15[i-1] < ema200_m15[i-1]) and wick_sell_ok
            
            # BUY Breakout
            if rvol_ok and body_ok and is_bull and c1_c > ash and (c1_c - ash) >= 2.00 and c1_c > c1_o:
                dyn_sl = max(6.50, round(cur_atr * 1.60, 2))
                dyn_tp = round(dyn_sl * 3.50, 2)
                entry = b0['open']
                sl = entry - dyn_sl
                tp = entry + dyn_tp
                lot = calc_lot_compound(equity, 5.0, dyn_sl)
                open_orders.append({
                    'engine': 'London Sniper', 'type': 'BUY', 'open_price': entry,
                    'sl': sl, 'tp': tp, 'lots': lot, 'init_risk': dyn_sl,
                    'ratchet_stage1': False, 'ratchet_stage2': False, 'open_time': t0
                })
            # SELL Breakdown
            elif rvol_ok and body_ok and is_bear and c1_c < asl and (asl - c1_c) >= 2.00 and c1_c < c1_o:
                dyn_sl = max(6.50, round(cur_atr * 1.60, 2))
                dyn_tp = round(dyn_sl * 3.50, 2)
                entry = b0['open']
                sl = entry + dyn_sl
                tp = entry - dyn_tp
                lot = calc_lot_compound(equity, 5.0, dyn_sl)
                open_orders.append({
                    'engine': 'London Sniper', 'type': 'SELL', 'open_price': entry,
                    'sl': sl, 'tp': tp, 'lots': lot, 'init_risk': dyn_sl,
                    'ratchet_stage1': False, 'ratchet_stage2': False, 'open_time': t0
                })
    
    # ---------------------------------------------------------
    # LEG 3: NEW YORK POI SNIPER (15:00 - 20:30)
    # ---------------------------------------------------------
    if not poi_active and 900 <= min_of_day <= 1230:
        pdh = pdh_map.get(d, 0.0)
        pdl = pdl_map.get(d, 0.0)
        ash_poi = asian_poi_map.get(d, {}).get('high', 0.0)
        asl_poi = asian_poi_map.get(d, {}).get('low', 999999.0)
        
        # SELL Setup: Resistance Sweep & Rejection
        at_res = (c1_h >= ash_poi or c1_h >= pdh)
        if at_res and (c1_upper_wick / c1_range) >= 0.35 and c1_c < c1_o:
            entry = b0['open']
            sl = c1_h + 1.00
            sl_dist = sl - entry
            if 1.50 <= sl_dist <= 4.50:
                tp = entry - (sl_dist * 3.50)
                lot = calc_lot_compound(equity, 2.5, sl_dist)
                open_orders.append({
                    'engine': 'POI NY Sniper', 'type': 'SELL', 'open_price': entry,
                    'sl': sl, 'tp': tp, 'lots': lot, 'init_risk': sl_dist,
                    'be_done': False, 'open_time': t0
                })
        
        # BUY Setup: Support Sweep & Rejection
        at_sup = (c1_l <= asl_poi or c1_l <= pdl)
        if at_sup and (c1_lower_wick / c1_range) >= 0.35 and c1_c > c1_o:
            entry = b0['open']
            sl = c1_l - 1.00
            sl_dist = entry - sl
            if 1.50 <= sl_dist <= 4.50:
                tp = entry + (sl_dist * 3.50)
                lot = calc_lot_compound(equity, 2.5, sl_dist)
                open_orders.append({
                    'engine': 'POI NY Sniper', 'type': 'BUY', 'open_price': entry,
                    'sl': sl, 'tp': tp, 'lots': lot, 'init_risk': sl_dist,
                    'be_done': False, 'open_time': t0
                })

print("\nSimulation Complete!")
print(f"Total Trades: {len(closed_trades)}")

# Engine Breakdown
by_engine = defaultdict(list)
for tr in closed_trades:
    by_engine[tr['engine']].append(tr)

print("\n--- RESULTS BY ENGINE ---")
for eng, trs in by_engine.items():
    wins = [t for t in trs if t['pnl'] > 0]
    losses = [t for t in trs if t['pnl'] < 0]
    total_pnl = sum(t['pnl'] for t in trs)
    gross_win = sum(t['pnl'] for t in wins)
    gross_loss = abs(sum(t['pnl'] for t in losses))
    pf = (gross_win / gross_loss) if gross_loss > 0 else 999.0
    wr = (len(wins) / len(trs) * 100.0) if trs else 0.0
    print(f"[{eng}] Trades: {len(trs)} | Wins: {len(wins)} ({wr:.1f}%) | Net PnL: ${total_pnl:,.2f} | PF: {pf:.2f}")

# Overall Summary
wins_all = [t for t in closed_trades if t['pnl'] > 0]
loss_all = [t for t in closed_trades if t['pnl'] < 0]
total_net = sum(t['pnl'] for t in closed_trades)
gross_w = sum(t['pnl'] for t in wins_all)
gross_l = abs(sum(t['pnl'] for t in loss_all))
pf_all = (gross_w / gross_l) if gross_l > 0 else 999.0
wr_all = (len(wins_all) / len(closed_trades) * 100.0) if closed_trades else 0.0

print(f"\n==========================================")
print(f"  GOLD POI SNIPER v3.5 OVERALL PERFORMANCE")
print(f"==========================================")
print(f"Initial Deposit: ${initial_deposit:,.2f}")
print(f"Final Balance  : ${balance:,.2f}")
print(f"Net Profit     : +${total_net:,.2f} ({(total_net/initial_deposit)*100:.1f}%)")
print(f"Profit Factor  : {pf_all:.2f}")
print(f"Win Rate       : {wr_all:.1f}% ({len(wins_all)} wins / {len(loss_all)} losses)")
print(f"Max Drawdown   : {max_dd:.2f}%")
print(f"==========================================")

# Monthly Breakdown
monthly = defaultdict(list)
for t in closed_trades:
    ym = t['time'].strftime('%Y-%m')
    monthly[ym].append(t)

print("\n--- MONTHLY BREAKDOWN ---")
for ym in sorted(monthly.keys()):
    m_trs = monthly[ym]
    m_wins = [t for t in m_trs if t['pnl'] > 0]
    m_pnl = sum(t['pnl'] for t in m_trs)
    m_wr = (len(m_wins) / len(m_trs) * 100.0) if m_trs else 0.0
    print(f"{ym} | Trades: {len(m_trs):2d} | Win Rate: {m_wr:5.1f}% | Net PnL: ${m_pnl:+9.2f}")
