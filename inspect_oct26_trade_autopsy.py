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

bar_map = {b['time']: b for b in bars}
bar_times = [b['time'] for b in bars]

# Inspect the 9 losses in October 2026
trades_to_inspect = [
    {'ticket': 117, 'time': datetime(2026, 10, 2, 19, 45), 'type': 'BUY', 'open': 4137.81, 'sl': 4132.94, 'tp': 4154.85},
    {'ticket': 118, 'time': datetime(2026, 10, 6, 19, 15), 'type': 'SELL', 'open': 4162.57, 'sl': 4166.73, 'tp': 4147.01},
    {'ticket': 119, 'time': datetime(2026, 10, 7, 15, 0), 'type': 'BUY', 'open': 4121.97, 'sl': 4118.28, 'tp': 4134.88},
    {'ticket': 120, 'time': datetime(2026, 10, 9, 18, 0), 'type': 'SELL', 'open': 4182.38, 'sl': 4185.48, 'tp': 4171.53},
    {'ticket': 121, 'time': datetime(2026, 10, 9, 18, 45), 'type': 'SELL', 'open': 4188.41, 'sl': 4193.18, 'tp': 4171.71},
    {'ticket': 122, 'time': datetime(2026, 10, 12, 18, 20), 'type': 'BUY', 'open': 4165.95, 'sl': 4161.95, 'tp': 4179.95},
    {'ticket': 123, 'time': datetime(2026, 10, 19, 17, 45), 'type': 'BUY', 'open': 4146.97, 'sl': 4143.03, 'tp': 4160.76},
    {'ticket': 124, 'time': datetime(2026, 10, 19, 18, 20), 'type': 'BUY', 'open': 4147.09, 'sl': 4143.15, 'tp': 4160.88},
    {'ticket': 125, 'time': datetime(2026, 10, 21, 19, 20), 'type': 'SELL', 'open': 4130.34, 'sl': 4134.03, 'tp': 4117.42},
    {'ticket': 126, 'time': datetime(2026, 10, 23, 19, 15), 'type': 'BUY', 'open': 4004.92, 'sl': 4000.39, 'tp': 4020.77},
    {'ticket': 128, 'time': datetime(2026, 10, 27, 19, 5), 'type': 'SELL', 'open': 4058.86, 'sl': 4063.31, 'tp': 4045.54}
]

print("=== INSPECTING POST-SL PRICE ACTION (DID IT GO TO TP?) ===")
for t in trades_to_inspect:
    t_open = t['time']
    # find next 30 bars (7.5 hours)
    sub_bars = [b for b in bars if b['time'] >= t_open][:35]
    if not sub_bars: continue
    
    sl_hit_bar = None
    tp_eventually_hit = False
    
    for idx, b in enumerate(sub_bars):
        if t['type'] == 'BUY':
            if sl_hit_bar is None and b['low'] <= t['sl']:
                sl_hit_bar = idx
            if sl_hit_bar is not None and b['high'] >= t['tp']:
                tp_eventually_hit = True
                break
        else:
            if sl_hit_bar is None and b['high'] >= t['sl']:
                sl_hit_bar = idx
            if sl_hit_bar is not None and b['low'] <= t['tp']:
                tp_eventually_hit = True
                break
                
    post_sl_result = "YES! Went to TP after taking SL!" if tp_eventually_hit else "No, pure continuation against trade"
    print(f"Ticket #{t['ticket']} | {t['type']} @ {t['open']} | SL hit at bar {sl_hit_bar} | {post_sl_result}")
