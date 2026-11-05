import os
import sys
import json
import struct
from datetime import datetime

sys.path.insert(0, r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4")
import gold_ai_agent as base

cfg = base.load_config()
mt4_dir = cfg.get("mt4_files_dir")
ms_file = os.path.join(mt4_dir, "market_state.json")
with open(ms_file, "r", encoding="utf-8") as f:
    state = json.load(f)

bid = float(state.get("bid", 0.0))
qd = base.compute_5_sciences_quant(mt4_dir, "GOLD", state, bid)
print("=== 5 SCIENCES QUANT ===")
print(json.dumps(qd, indent=2, ensure_ascii=True))

hist_base = os.path.abspath(os.path.join(mt4_dir, "..", "..", "history"))
for root, dirs, files in os.walk(hist_base):
    for f in files:
        if "GOLD" in f.upper() and f.endswith(".hst"):
            p = os.path.join(root, f)
            if f.upper() in ["GOLD15.HST", "GOLD60.HST", "GOLD1440.HST"]:
                with open(p, "rb") as fp:
                    fp.seek(148)
                    data = fp.read()
                rec_sz = 60
                n_bars = len(data) // rec_sz
                print(f"\n--- Last 10 bars of {f} (total {n_bars}) ---")
                for i in range(max(0, n_bars - 10), n_bars):
                    chunk = data[i*60:(i+1)*60]
                    t, o, h, l, c, v, sp, rv = struct.unpack("<qddddqiq", chunk)
                    dt_str = datetime.utcfromtimestamp(t).strftime("%Y-%m-%d %H:%M")
                    print(f"  [{dt_str}] O:{o:.2f} H:{h:.2f} L:{l:.2f} C:{c:.2f} V:{v}")
