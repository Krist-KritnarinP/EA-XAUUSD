import subprocess
import os
import time
import shutil

metaeditor = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"
experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
scratch_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"

files = [
    "GoldSniper_Tester_v6_3_7_beta",
    "GoldSniper_Bridge_v6_3_7_beta"
]

for name in files:
    mq4_file = os.path.join(experts_dir, f"{name}.mq4")
    ex4_file = os.path.join(experts_dir, f"{name}.ex4")
    log_file = os.path.join(experts_dir, f"{name}.log")
    
    # Remove old ex4 to be 100% sure new one is built
    if os.path.exists(ex4_file):
        os.remove(ex4_file)
    if os.path.exists(log_file):
        os.remove(log_file)
        
    cmd = f'"{metaeditor}" /compile:"{mq4_file}" /log:"{log_file}"'
    print(f"Compiling: {name}...")
    res = subprocess.run(cmd, shell=True)
    time.sleep(2)
    
    # Check log
    log_content = ""
    if os.path.exists(log_file):
        for enc in ['utf-16', 'utf-8', 'latin1']:
            try:
                with open(log_file, 'r', encoding=enc) as f:
                    log_content = f.read()
                    break
            except Exception:
                pass
    
    print(f"Log content for {name}:")
    print(log_content.strip() if log_content else "[No log file written or empty]")
    
    if os.path.exists(ex4_file):
        sz = os.path.getsize(ex4_file)
        mtime = time.ctime(os.path.getmtime(ex4_file))
        print(f"SUCCESS: {ex4_file} built successfully! Size: {sz} bytes, mtime: {mtime}")
        
        # Copy to scratch dir as well
        shutil.copy2(mq4_file, os.path.join(scratch_dir, f"{name}.mq4"))
        shutil.copy2(ex4_file, os.path.join(scratch_dir, f"{name}.ex4"))
        print(f"Synced to scratch directory: {scratch_dir}")
    else:
        print(f"ERROR: {ex4_file} NOT found!")

print("\n--- Finished Compilation Script ---")
