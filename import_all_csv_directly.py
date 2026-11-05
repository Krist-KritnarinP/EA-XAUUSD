import struct, os, time, subprocess, datetime

terminal_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702"
history_dir = os.path.join(terminal_dir, r"history\XMGlobal-Real 46")
tester_history_dir = os.path.join(terminal_dir, r"tester\history")
terminal_exe = r"C:\Program Files (x86)\MetaTrader 4\terminal.exe"

csv_15 = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GOLD15_MT4_IMPORT.csv"
csv_60 = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GOLD60_MT4_IMPORT.csv"

def stop_terminal():
    print("[1/4] Stopping MT4 terminal...")
    subprocess.run(["powershell", "-Command", "Stop-Process -Name terminal -Force -ErrorAction SilentlyContinue"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    print("MT4 stopped.")

def clean_fxt():
    print("[2/4] Cleaning tester FXT cache...")
    if os.path.exists(tester_history_dir):
        for fname in os.listdir(tester_history_dir):
            if fname.lower().endswith(".fxt"):
                fpath = os.path.join(tester_history_dir, fname)
                try:
                    os.chmod(fpath, 0o777)
                    os.remove(fpath)
                    print(f"   Removed: {fname}")
                except Exception as e:
                    pass

def create_hst_header(symbol, period, digits=2):
    header = bytearray(148)
    struct.pack_into('<I', header, 0, 401)
    copyright_str = "(C)opyright 2003, MetaQuotes Software Corp.".encode('latin1')
    header[4:4+len(copyright_str)] = copyright_str
    sym_bytes = symbol.encode('latin1')
    header[68:68+len(sym_bytes)] = sym_bytes
    struct.pack_into('<I', header, 80, period)
    struct.pack_into('<I', header, 84, digits)
    return bytes(header)

def pack_bar(t, o, h, l, c, vol, spread=53):
    return struct.pack('<qddddqiq', int(t), float(o), float(h), float(l), float(c), int(vol), int(spread), 0)

def convert_csv_to_hst(csv_path, symbol, period, out_hst_path):
    print(f"Converting {csv_path} to {out_hst_path}...")
    bars = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split(',')
            if len(parts) < 7: continue
            d_str = parts[0] + ' ' + parts[1]
            try:
                dt = datetime.datetime.strptime(d_str, '%Y.%m.%d %H:%M')
                t = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())
                o = float(parts[2])
                h = float(parts[3])
                l = float(parts[4])
                c = float(parts[5])
                v = int(float(parts[6]))
                bars[t] = (t, o, h, l, c, v)
            except Exception:
                pass
                
    # Also check existing HST to merge any newer bars (e.g. October 2026)
    if os.path.exists(out_hst_path):
        try:
            with open(out_hst_path, 'rb') as f_exist:
                f_exist.read(148)
                added = 0
                while True:
                    d = f_exist.read(60)
                    if len(d) < 60: break
                    t, o, h, l, c, vol, spread, rvol = struct.unpack('<qddddqiq', d)
                    if t not in bars:
                        bars[t] = (t, o, h, l, c, vol)
                        added += 1
                if added > 0:
                    print(f"   Preserved {added} newer bars from existing HST!")
        except Exception:
            pass

    sorted_t = sorted(bars.keys())
    print(f"   Total bars to write: {len(sorted_t):,}")
    print(f"   Range: {datetime.datetime.utcfromtimestamp(sorted_t[0])} -> {datetime.datetime.utcfromtimestamp(sorted_t[-1])}")
    
    out_bytes = bytearray(create_hst_header(symbol, period, 2))
    for t in sorted_t:
        t_val, o, h, l, c, v = bars[t]
        out_bytes.extend(pack_bar(t_val, o, h, l, c, v, 53))
        
    with open(out_hst_path, 'wb') as f_out:
        f_out.write(out_bytes)
    print(f"   Successfully written {out_hst_path} ({len(out_bytes):,} bytes)!")

def restart_terminal():
    print("[4/4] Starting MT4 terminal...")
    subprocess.Popen([terminal_exe])
    time.sleep(3)
    print("MT4 restarted.")

if __name__ == "__main__":
    stop_terminal()
    clean_fxt()
    print("[3/4] Writing pure authentic CSV datasets directly into HST database...")
    convert_csv_to_hst(csv_15, "GOLD", 15, os.path.join(history_dir, "GOLD15.hst"))
    convert_csv_to_hst(csv_60, "GOLD", 60, os.path.join(history_dir, "GOLD60.hst"))
    restart_terminal()
    print("\nDONE! All historical data is 100% written directly into MT4!")
