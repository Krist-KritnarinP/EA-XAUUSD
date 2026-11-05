import struct
import os
from datetime import datetime

hst_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\history\XMGlobal-Real 46"

for tf_name, fn in [('MN1', 'GOLD43200.hst'), ('W1', 'GOLD10080.hst'), ('D1', 'GOLD1440.hst'), ('H4', 'GOLD240.hst'), ('H1', 'GOLD60.hst'), ('M15', 'GOLD15.hst')]:
    path = os.path.join(hst_dir, fn)
    if not os.path.exists(path):
        print(f"{tf_name}: not found")
        continue
    with open(path, 'rb') as f:
        header = f.read(148)
        bars = []
        while True:
            data = f.read(60)
            if len(data) < 60:
                break
            t, o, h, l, c, v, s, r = struct.unpack('<QddddQiq', data)
            bars.append((datetime.utcfromtimestamp(t), o, h, l, c, v, s))
        print(f"=== {tf_name} (Total: {len(bars)}) ===")
        for b in bars[-8:]:
            print(f"{b[0].strftime('%Y-%m-%d %H:%M')} | O: {b[1]:.2f} | H: {b[2]:.2f} | L: {b[3]:.2f} | C: {b[4]:.2f} | Spread: {b[6]}")
