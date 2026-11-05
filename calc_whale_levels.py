import struct, glob
from datetime import datetime, timezone

files_d1 = glob.glob('C:/Users/Kritnarin/AppData/Roaming/MetaQuotes/Terminal/**/GOLD1440.hst', recursive=True)
files_h1 = glob.glob('C:/Users/Kritnarin/AppData/Roaming/MetaQuotes/Terminal/**/GOLD60.hst', recursive=True)
files_m15 = glob.glob('C:/Users/Kritnarin/AppData/Roaming/MetaQuotes/Terminal/**/GOLD15.hst', recursive=True)

def read_bars(p, count=50):
    bars = []
    with open(p, 'rb') as f:
        f.read(148)
        while True:
            c = f.read(60)
            if len(c) < 60: break
            t, o, h, l, cl, v, s, r = struct.unpack('<qddddqiq', c)
            bars.append({'t': t, 'o': o, 'h': h, 'l': l, 'c': cl, 'v': v})
    return bars[-count:]

if files_d1:
    d1 = read_bars(files_d1[0], 10)
    print("--- D1 Structure ---")
    for b in d1[-5:]:
        dt = datetime.fromtimestamp(b['t'], tz=timezone.utc).strftime('%Y-%m-%d')
        print(f"{dt}: H={b['h']:.2f}, L={b['l']:.2f}, C={b['c']:.2f}")

if files_h1:
    h1 = read_bars(files_h1[0], 48)
    print("\n--- H1 Key Levels (Last 48 Hours) ---")
    h1_high = max(b['h'] for b in h1)
    h1_low = min(b['l'] for b in h1)
    print(f"48h High: {h1_high:.2f}, 48h Low: {h1_low:.2f}")
    # Recent swing lows / highs
    print("Recent 10 H1 bars:")
    for b in h1[-10:]:
        dt = datetime.fromtimestamp(b['t'], tz=timezone.utc).strftime('%m-%d %H:%M')
        print(f"{dt}: O={b['o']:.2f}, H={b['h']:.2f}, L={b['l']:.2f}, C={b['c']:.2f}")

import json
try:
    with open(r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Files\market_state.json', 'r') as f:
        st = json.load(f)
    print("\n--- Live Market State ---")
    print(f"Bid: {st.get('bid')}, Ask: {st.get('ask')}")
    print(f"Asian High: {st.get('stored_asian_high')}, Asian Low: {st.get('stored_asian_low')}")
    print(f"Bar High: {st.get('bar_high')}, Bar Low: {st.get('bar_low')}")
except Exception as e:
    print(e)
