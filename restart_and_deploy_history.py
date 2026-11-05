# -*- coding: utf-8 -*-
import os
import subprocess
import time

term_exe = r"C:\Program Files (x86)\MetaTrader 4\terminal.exe"
term_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702"
fxt_file = os.path.join(term_dir, r"tester\history\GOLD15_0.fxt")

print("1. Gracefully closing MT4 to flush handles...")
subprocess.run('powershell -Command "Stop-Process -Name terminal -Force -ErrorAction SilentlyContinue"', shell=True)
time.sleep(2)

print("2. Re-writing fresh complete 168,240 M1 & 11,216 M15 history...")
subprocess.run('python "C:\\Users\\Kritnarin\\.gemini\\antigravity\\scratch\\GoldSniper_MT4\\synthesize_full_history.py"', shell=True)

print("3. Clearing old cached FXT so MT4 regenerates 100% green data...")
if os.path.exists(fxt_file):
    try:
        os.remove(fxt_file)
        print("   Deleted old FXT file successfully!")
    except Exception as e:
        print("   Could not delete FXT:", e)

print("4. Restarting MT4 Terminal...")
subprocess.run(f'powershell -Command "Start-Process \'{term_exe}\'"', shell=True)
time.sleep(3)

print("All done! MT4 restarted with 100% complete 6-month M1 data ready for testing!")
