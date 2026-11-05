import json, struct
from datetime import datetime, timedelta
from collections import defaultdict

# 1. Load parsed trades
with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_sniper_parsed_trades.json', 'r') as f:
    trades = json.load(f)

print(f"Loaded {len(trades)} trades.")

# 2. Load GOLD15.hst for exact bar-by-bar price action during each trade
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

bar_map = {b['time']: b for b in bars}
bar_times = [b['time'] for b in bars]

print(f"Loaded {len(bars)} M15 bars from history.")

# Enrich each trade with duration, MAE, MFE, session, and month
for t in trades:
    t_open = datetime.strptime(t['open_time'], '%Y.%m.%d %H:%M:%S')
    t_close = datetime.strptime(t['close_time'], '%Y.%m.%d %H:%M:%S')
    duration_hrs = (t_close - t_open).total_seconds() / 3600.0
    t['duration_hrs'] = duration_hrs
    t['month_str'] = t_open.strftime('%Y-%m')
    
    # Session breakdown based on server open time
    # 08:00 - 09:00: Late Asian / Pre-London
    # 09:00 - 14:59: London Session
    # 15:00 - 20:30: New York Session
    h = t_open.hour
    if 8 <= h < 9:
        t['session'] = 'Late Asian / Pre-London'
    elif 9 <= h < 15:
        t['session'] = 'London Session'
    elif 15 <= h <= 20:
        t['session'] = 'New York Session'
    else:
        t['session'] = 'Off Session'
        
    # Find all bars between open and close to measure MAE and MFE
    trade_bars = [b for b in bars if t_open <= b['time'] <= t_close]
    if not trade_bars:
        trade_bars = [{'high': t['open_price'], 'low': t['open_price'], 'open': t['open_price'], 'close': t['open_price']}]
        
    init_sl = t['trigger_info']['sl_calc'] if t['trigger_info'] else (t['open_price'] - 3.0 if t['type']=='BUY' else t['open_price'] + 3.0)
    sl_dist = abs(t['open_price'] - init_sl)
    
    if t['type'] == 'BUY':
        lowest_during = min(b['low'] for b in trade_bars)
        highest_during = max(b['high'] for b in trade_bars)
        mae_dist = t['open_price'] - lowest_during # max adverse (drawdown in price)
        mfe_dist = highest_during - t['open_price'] # max favorable (floating profit)
        dist_to_sl_min = lowest_during - init_sl
    else: # SELL
        lowest_during = min(b['low'] for b in trade_bars)
        highest_during = max(b['high'] for b in trade_bars)
        mae_dist = highest_during - t['open_price']
        mfe_dist = t['open_price'] - lowest_during
        dist_to_sl_min = init_sl - highest_during
        
    t['mae_pts'] = round(mae_dist * 100.0, 1)
    t['mfe_pts'] = round(mfe_dist * 100.0, 1)
    t['dist_to_sl_min_pts'] = round(dist_to_sl_min * 100.0, 1)
    t['mfe_r'] = round(mfe_dist / (sl_dist if sl_dist > 0 else 1.0), 2)

# --- 1. MONTHLY BREAKDOWN ---
monthly = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'be': 0, 'pnl': 0.0, 'sessions': defaultdict(lambda: {'total': 0, 'wins': 0})})
for t in trades:
    m = t['month_str']
    monthly[m]['total'] += 1
    monthly[m]['pnl'] += t['pnl']
    if t['pnl'] > 0:
        monthly[m]['wins'] += 1
    elif t['close_reason'] == 'BE':
        monthly[m]['be'] += 1
    else:
        monthly[m]['losses'] += 1
    s = t['session']
    monthly[m]['sessions'][s]['total'] += 1
    if t['pnl'] > 0:
        monthly[m]['sessions'][s]['wins'] += 1

# --- 2. SESSION OVERALL BREAKDOWN ---
sessions_overall = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0})
for t in trades:
    s = t['session']
    sessions_overall[s]['total'] += 1
    sessions_overall[s]['pnl'] += t['pnl']
    if t['pnl'] > 0:
        sessions_overall[s]['wins'] += 1
    else:
        sessions_overall[s]['losses'] += 1

# --- 3. WINNING TRADES DEEP FORENSICS ---
win_trades = [t for t in trades if t['pnl'] > 0]
win_durations = [t['duration_hrs'] for t in win_trades]
avg_win_duration = sum(win_durations) / len(win_durations) if win_durations else 0.0
win_dist_to_sl = [t['dist_to_sl_min_pts'] for t in win_trades]
avg_dist_to_sl = sum(win_dist_to_sl) / len(win_dist_to_sl) if win_dist_to_sl else 0.0
# เข้าแล้วบวกเลย (drawdown <= spread ~ 50 pts)
zero_drawdown_wins = [t for t in win_trades if t['mae_pts'] <= 55.0]

# --- 4. LOSING TRADES DEEP FORENSICS ---
loss_trades = [t for t in trades if t['pnl'] <= 0]
# How many were profit first before reversing?
profit_first_1r = [t for t in loss_trades if t['mfe_r'] >= 1.0]
profit_first_1_5r = [t for t in loss_trades if t['mfe_r'] >= 1.5]
pure_wrong_direction = [t for t in loss_trades if t['mfe_r'] < 0.5]

# --- 5. STREAKS ANALYSIS (CONSECUTIVE WINS & LOSSES) ---
max_win_streak = 0
max_loss_streak = 0
cur_win_streak = 0
cur_loss_streak = 0
cur_win_amt = 0.0
cur_loss_amt = 0.0
max_win_amt = 0.0
max_loss_amt = 0.0
streaks_records = []

for t in trades:
    if t['pnl'] > 0:
        cur_win_streak += 1
        cur_win_amt += t['pnl']
        if cur_loss_streak > 0:
            streaks_records.append(('LOSS', cur_loss_streak, cur_loss_amt))
            cur_loss_streak = 0
            cur_loss_amt = 0.0
        if cur_win_streak > max_win_streak:
            max_win_streak = cur_win_streak
            max_win_amt = cur_win_amt
    else:
        cur_loss_streak += 1
        cur_loss_amt += abs(t['pnl'])
        if cur_win_streak > 0:
            streaks_records.append(('WIN', cur_win_streak, cur_win_amt))
            cur_win_streak = 0
            cur_win_amt = 0.0
        if cur_loss_streak > max_loss_streak:
            max_loss_streak = cur_loss_streak
            max_loss_amt = cur_loss_amt

if cur_win_streak > 0: streaks_records.append(('WIN', cur_win_streak, cur_win_amt))
if cur_loss_streak > 0: streaks_records.append(('LOSS', cur_loss_streak, cur_loss_amt))

# Output all structured findings
summary = {
    'monthly': dict(monthly),
    'sessions_overall': dict(sessions_overall),
    'win_stats': {
        'total_wins': len(win_trades),
        'avg_duration_hrs': round(avg_win_duration, 2),
        'min_duration_hrs': round(min(win_durations), 2) if win_durations else 0,
        'max_duration_hrs': round(max(win_durations), 2) if win_durations else 0,
        'avg_clearance_to_sl_pts': round(avg_dist_to_sl, 1),
        'zero_drawdown_wins_count': len(zero_drawdown_wins),
        'zero_drawdown_wins_pct': round(len(zero_drawdown_wins)/len(win_trades)*100, 1) if win_trades else 0
    },
    'loss_stats': {
        'total_losses': len(loss_trades),
        'pure_fakeout_wrong_way': len(pure_wrong_direction),
        'pure_fakeout_pct': round(len(pure_wrong_direction)/len(loss_trades)*100, 1) if loss_trades else 0,
        'profit_then_reversed_1r': len(profit_first_1r),
        'profit_then_reversed_1_5r': len(profit_first_1_5r),
    },
    'streaks': {
        'max_consecutive_wins': max_win_streak,
        'max_win_streak_profit': round(max_win_amt, 2),
        'max_consecutive_losses': max_loss_streak,
        'max_loss_streak_loss': round(max_loss_amt, 2)
    }
}

with open(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\poi_sniper_deep_audit.json', 'w') as f:
    json.dump(summary, f, indent=2)

print("Forensics completed successfully.")
