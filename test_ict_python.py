import struct
from datetime import datetime

hst_file = r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46\GOLD15.hst'
with open(hst_file, 'rb') as f:
    header = f.read(148)
    bars = []
    while True:
        data = f.read(60)
        if len(data) < 60: break
        unp = struct.unpack('<QddddQiq', data)
        dt = datetime.fromtimestamp(unp[0])
        bars.append({
            'time': dt,
            'open': unp[1],
            'low': unp[2],
            'high': unp[3],
            'close': unp[4]
        })

# Let's inspect each day between 2025-10-01 and 2025-11-15
# We simulate Asian Range (00:00 - 07:00), Sweep, and then EvaluateICTChecklist
for idx in range(100, len(bars)):
    cur_bar = bars[idx]
    if not (datetime(2025, 10, 1) <= cur_bar['time'] <= datetime(2025, 11, 15)):
        continue
    
    # Check if inside London KZ (08:00 - 11:30) or NY KZ (14:30 - 17:30)
    t = cur_bar['time']
    m = t.hour * 60 + t.minute
    in_london = (8*60 <= m <= 11*60 + 30)
    in_ny = (14*60 + 30 <= m <= 17*60 + 30)
    if not (in_london or in_ny):
        continue
        
    # Asian Range (00:00 to 07:00 of same day)
    asian_bars = [b for b in bars[idx-40:idx] if b['time'].date() == t.date() and 0 <= b['time'].hour < 7]
    if not asian_bars:
        continue
    asian_high = max(b['high'] for b in asian_bars)
    asian_low = min(b['low'] for b in asian_bars)
    
    prev = bars[idx-1]
    if prev['high'] > asian_high:
        print(f"High {prev['high']:.2f} > Asian {asian_high:.2f}")
    
    # Bearish Sweep: prev['high'] > asian_high
    if prev['high'] > asian_high:
        depth = prev['high'] - asian_high
        if 1.0 <= depth <= 9.0: # 100 to 900 points
            # Rejection wick: Close[1] < curHigh - (curHigh - curLow)*0.30
            rng = prev['high'] - prev['low']
            if rng > 0 and prev['close'] < (prev['high'] - rng * 0.30):
                # SWEEP CONFIRMED!
                # Now check MSS
                # In EA: for b = 3 to 15: find Swing Low
                recent_swing_low = None
                for b in range(3, 16):
                    cand = bars[idx-b]
                    c_left = bars[idx-b-1]
                    c_right = bars[idx-b+1]
                    if cand['low'] < c_left['low'] and cand['low'] < c_right['low']:
                        recent_swing_low = cand['low']
                        break
                
                # Check displacement
                disp_found = False
                atr = 4.0 # approximate
                for d in range(1, 5):
                    cand = bars[idx-d]
                    c_body = cand['open'] - cand['close']
                    c_range = cand['high'] - cand['low']
                    if recent_swing_low and cand['close'] < recent_swing_low:
                        if c_range > 0 and (c_body / c_range) >= 0.50 and c_body >= (atr * 0.85):
                            disp_found = True
                            print(f"{t} BEARISH DISPLACEMENT FOUND! Close={cand['close']} < SwingLow={recent_swing_low}, Body={c_body:.2f}")
                            break
                print(f"[{t}] SWEEP DETECTED! High={prev['high']:.2f} > AsianHigh={asian_high:.2f} (Depth={depth:.2f})")
                print(f"   Recent Swing Low: {recent_swing_low}")
                for d in range(1, 5):
                    cand = bars[idx-d]
                    c_body = cand['open'] - cand['close']
                    c_range = cand['high'] - cand['low']
                    print(f"   Bar d={d} ({cand['time'].strftime('%H:%M')}): Close={cand['close']:.2f}, Body={c_body:.2f}, Range={c_range:.2f}")
                    if recent_swing_low and cand['close'] < recent_swing_low:
                        print(f"      -> Broke structure! Body/Range={c_body/c_range:.2f}, Body={c_body:.2f} vs ATR={atr*0.85:.2f}")
