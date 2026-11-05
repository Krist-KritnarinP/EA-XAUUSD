import os
import shutil
import subprocess
import time

experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
scratch_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
metaeditor  = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"

source_tester = os.path.join(experts_dir, "GoldSniper_Tester_v6_3_8_beta.mq4")
with open(source_tester, "r", encoding="latin1") as f:
    code = f.read()

# 1. Update Header and Version
code = code.replace("Gold Sniper v6.3.8-Beta Institutional Apex Engine", "Gold Sniper v6.3.8-BetaB High-Octane Apex Engine")
code = code.replace('Header_Master           = "=== MASTER V6.3.8-BETA INSTITUTIONAL APEX (SMC EQ FILTER + FAST BAILOUT) ===";',
                    'Header_Master           = "=== MASTER V6.3.8-BETAB HIGH-OCTANE APEX (ORIGINAL LOT SIZING + SMC SHIELD) ===";')

# 2. Restore Original Lot Size / Risk Percentages (5.0% / 3.5% / 1.0%)
code = code.replace('input double          SniperRiskPercent       = 3.0;            // London Sniper Risk (% of Equity - Balanced 3.0%)',
                    'input double          SniperRiskPercent       = 5.0;            // London Sniper Risk (% of Equity - Original 5.0% Lot Sizing)')
code = code.replace('input double          NYRiskPercent           = 2.0;            // New York Continuation Risk (2.0% Safe Institutional)',
                    'input double          NYRiskPercent           = 3.5;            // New York Continuation Risk (Original 3.5% Lot Sizing)')
code = code.replace('input double          ScalperRiskPercent      = 0.5;            // Asian Scalper Micro-Risk (% of Equity - Safe 0.5%)',
                    'input double          ScalperRiskPercent      = 1.0;            // Asian Scalper Micro-Risk (% of Equity - Original 1.0% Safe)')

# 3. Update Global Variable prefix and Version in strings
code = code.replace('GS638B_', 'GS638BB_')
code = code.replace('v6.3.8-Beta', 'v6.3.8-BetaB')
code = code.replace('"version": "6.3.8-Beta"', '"version": "6.3.8-BetaB"')

# Write files in MT4 Experts & Scratch
files_to_make = [
    ("GoldSniper_Tester_v6_3_8_beta_b", "GoldSniper_Tester_v6_3_8_beta_b"),
    ("GoldSniper_Bridge_v6_3_8_beta_b", "GoldSniper_Bridge_v6_3_8_beta_b")
]

for name, base in files_to_make:
    mq4_path = os.path.join(experts_dir, f"{name}.mq4")
    with open(mq4_path, "w", encoding="latin1") as f:
        f.write(code)
    shutil.copy2(mq4_path, os.path.join(scratch_dir, f"{name}.mq4"))
    print(f"Created: {mq4_path}")

print("\n--- Compiling v6.3.8-BetaB with MetaEditor ---")
for name, base in files_to_make:
    mq4_file = os.path.join(experts_dir, f"{name}.mq4")
    ex4_file = os.path.join(experts_dir, f"{name}.ex4")
    log_file = os.path.join(experts_dir, f"{name}.log")
    
    if os.path.exists(ex4_file): os.remove(ex4_file)
    if os.path.exists(log_file): os.remove(log_file)
    
    cmd = f'"{metaeditor}" /compile:"{mq4_file}" /log:"{log_file}"'
    subprocess.run(cmd, shell=True)
    time.sleep(2)
    
    log_content = ""
    if os.path.exists(log_file):
        for enc in ['utf-16', 'utf-8', 'latin1']:
            try:
                with open(log_file, 'r', encoding=enc) as f:
                    log_content = f.read()
                    break
            except Exception: pass
            
    print(f"\nCompile Log for {name}:")
    print(log_content.strip() if log_content else "[No log written]")
    
    if os.path.exists(ex4_file):
        shutil.copy2(ex4_file, os.path.join(scratch_dir, f"{name}.ex4"))
        print(f"SUCCESS: {ex4_file} built and synced ({os.path.getsize(ex4_file)} bytes)!")
    else:
        print(f"ERROR: {ex4_file} NOT created!")

print("\n--- v6.3.8-BetaB Build & Compilation Completed Successfully! ---")
