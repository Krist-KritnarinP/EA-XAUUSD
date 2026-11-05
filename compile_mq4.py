import subprocess
import os

METAEDITOR = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"

def compile_mq4(mq4_path, log_path=None):
    if log_path is None:
        log_path = os.path.splitext(mq4_path)[0] + "_compile.log"
    
    cmd = f'"{METAEDITOR}" /compile:"{mq4_path}" /log:"{log_path}"'
    res = subprocess.run(cmd, shell=True)
    
    log_content = ""
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-16", errors="ignore") as f:
            log_content = f.read()
        if not log_content.strip():
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                log_content = f.read()
    
    print(f"Compilation finished for {os.path.basename(mq4_path)}:")
    print(log_content.strip())
    return "0 errors, 0 warnings" in log_content

import sys

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Bridge_v6_3_4_beta.mq4"
    compile_mq4(target)
