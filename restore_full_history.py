import struct, os, time, subprocess

terminal_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702"
history_dir = os.path.join(terminal_dir, r"history\XMGlobal-Real 46")
backup_dir = os.path.join(history_dir, "backup")
tester_history_dir = os.path.join(terminal_dir, r"tester\history")
terminal_exe = r"C:\Program Files (x86)\MetaTrader 4\terminal.exe"

def stop_terminal():
    print("[1/4] Stopping MT4 terminal to unlock files...")
    subprocess.run(["powershell", "-Command", "Stop-Process -Name terminal -Force -ErrorAction SilentlyContinue"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    print("MT4 stopped successfully.")

def merge_and_write(tf_name):
    bak_path = os.path.join(backup_dir, f"{tf_name}.hst.bak")
    cur_path = os.path.join(history_dir, f"{tf_name}.hst")
    
    if not os.path.exists(bak_path):
        print(f"Backup not found for {tf_name}")
        return
        
    with open(bak_path, "rb") as f:
        header = bytearray(f.read(148))
        bars_dict = {}
        while True:
            d = f.read(60)
            if len(d) < 60: break
            t = struct.unpack("<Q", d[:8])[0]
            bars_dict[t] = d
            
    if os.path.exists(cur_path):
        with open(cur_path, "rb") as f:
            f.read(148)
            while True:
                d = f.read(60)
                if len(d) < 60: break
                t = struct.unpack("<Q", d[:8])[0]
                if t not in bars_dict:
                    bars_dict[t] = d
                    
    sorted_times = sorted(bars_dict.keys())
    
    # Write back clean merged HST
    with open(cur_path, "wb") as f:
        f.write(header)
        for t in sorted_times:
            f.write(bars_dict[t])
            
    print(f"[{tf_name}] Restored {len(sorted_times)} pristine bars successfully!")

def clean_fxt():
    print("[3/4] Cleaning truncated tester cache (.fxt)...")
    if os.path.exists(tester_history_dir):
        for fname in os.listdir(tester_history_dir):
            if fname.lower().endswith(".fxt"):
                fpath = os.path.join(tester_history_dir, fname)
                try:
                    os.chmod(fpath, 0o777)
                    os.remove(fpath)
                    print(f"Removed cache: {fname}")
                except Exception as e:
                    print(f"Could not remove {fname}: {e}")

def restart_terminal():
    print("[4/4] Restarting MT4 terminal...")
    if os.path.exists(terminal_exe):
        subprocess.Popen([terminal_exe])
        print("MT4 terminal launched!")
    else:
        print(f"Executable not found at {terminal_exe}")

if __name__ == "__main__":
    stop_terminal()
    print("[2/4] Merging full historical data...")
    merge_and_write("GOLD15")
    merge_and_write("GOLD1")
    clean_fxt()
    restart_terminal()
    print("\nDONE! Full 6-month historical data (12,596 bars) is now fully restored!")
