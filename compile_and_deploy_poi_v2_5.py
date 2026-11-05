import subprocess
import os
import shutil

metaeditor = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"
mt4_experts = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
scratch_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"

files = [
    "Gold_POI_Sniper_Master_v2_5.mq4",
    "Gold_POI_Sniper_Tester_v2_5.mq4"
]

for fn in files:
    src_mq4 = os.path.join(scratch_dir, fn)
    log_path = os.path.join(scratch_dir, f"compile_{fn}.log")
    cmd = [metaeditor, f"/compile:{src_mq4}", f"/log:{log_path}"]
    subprocess.run(cmd, timeout=30)
    
    log_content = ""
    if os.path.exists(log_path):
        with open(log_path, "rb") as f:
            log_content = f.read().decode("utf-16le", errors="ignore")
    
    status = "OK"
    for line in log_content.splitlines():
        if "error" in line.lower() or "warning" in line.lower():
            print(f"[{fn}] {line.strip()}")
            
    ex4_src = src_mq4.replace(".mq4", ".ex4")
    if os.path.exists(ex4_src):
        ex4_dst = os.path.join(mt4_experts, os.path.basename(ex4_src))
        shutil.copy2(ex4_src, ex4_dst)
        mq4_dst = os.path.join(mt4_experts, fn)
        shutil.copy2(src_mq4, mq4_dst)
        print(f"DEPLOYED SUCCESS: {fn} -> {ex4_dst}")
    else:
        print(f"FAILED TO COMPILE: {fn}")
