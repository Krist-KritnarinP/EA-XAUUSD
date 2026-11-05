import struct, os
from datetime import datetime

hst_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46"
path = os.path.join(hst_dir, 'GOLD1440.hst')
bars = []
with open(path, 'rb') as f:
    f.read(148)
    while True:
        data = f.read(60)
        if len(data) < 60: break
        t, o, h, l, c, v, s, r = struct.unpack('<QddddQiq', data)
        bars.append({'t': datetime.utcfromtimestamp(t), 'o': o, 'h': h, 'l': l, 'c': c})

matches = [b for b in bars if b['l'] <= 3900 and b['h'] >= 3700]
print(f"Total D1 bars in 3700-3900 range: {len(matches)}")
for b in matches[-15:]:
    print(f"{b['t'].strftime('%Y-%m-%d')} | Low: {b['l']:.2f} | High: {b['h']:.2f} | Close: {b['c']:.2f}")

# Look at weekly bars around Oct 2025 - 2026
w_path = os.path.join(hst_dir, 'GOLD10080.hst')
w_bars = []
if os.path.exists(w_path):
    with open(w_path, 'rb') as f:
        f.read(148)
        while True:
            data = f.read(60)
            if len(data) < 60: break
            t, o, h, l, c, v, s, r = struct.unpack('<QddddQiq', data)
            w_bars.append({'t': datetime.utcfromtimestamp(t), 'o': o, 'h': h, 'l': l, 'c': c})
    print(f"\nWeekly bars: {len(w_bars)}")
    for b in w_bars[-10:]:
        print(f"Week {b['t'].strftime('%Y-%m-%d')} | Low: {b['l']:.2f} | High: {b['h']:.2f} | Close: {b['c']:.2f}")
