# -*- coding: utf-8 -*-
import os
import subprocess
import time

term_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702"
term_exe = r"C:\Program Files (x86)\MetaTrader 4\terminal.exe"

print("1. Closing MT4...")
subprocess.run(["powershell", "-Command", "Stop-Process -Name terminal -Force -ErrorAction SilentlyContinue"])
time.sleep(2)

print("2. Removing artificial files...")
for f in ["GOLD1.hst", "GOLD15.hst"]:
    p = os.path.join(term_dir, "history", "XMGlobal-Real 46", f)
    if os.path.exists(p):
        os.remove(p)
        print("   Removed:", f)

fxt_dir = os.path.join(term_dir, "tester", "history")
if os.path.exists(fxt_dir):
    for f in os.listdir(fxt_dir):
        if f.endswith(".fxt"):
            os.remove(os.path.join(fxt_dir, f))
            print("   Removed FXT:", f)

print("3. Restarting MT4...")
subprocess.run(["powershell", "-Command", f'Start-Process "{term_exe}"'])
time.sleep(3)
print("SUCCESS: MT4 restored cleanly to genuine XM broker state!")
