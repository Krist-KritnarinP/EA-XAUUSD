# -*- coding: utf-8 -*-
"""
Build Script for GoldSniper v6.2.3 x3 (Pure London 2.5x + Judas Scalp 2.0x Engine)
Requirements:
1. Technical Asian Scalper REMOVED / DISABLED completely
2. Technical New York Reversal REMOVED / DISABLED completely
3. London Sniper Runner Lot MULTIPLIED by 2.5x (LondonSniperLotMultiplier = 2.50)
4. Sweep Fade (Judas Liquidity Scalp) Lot MULTIPLIED by 2.0x (SweepFadeFixedLot = 0.04)
5. Retain proven Super Bull Ribbon, Frankfurt Trap Shield, and Smart Runner Trailing
6. Target names: GoldSniper_Tester_v6_2_3_x3 and GoldSniper_Bridge_v6_2_3_x3
"""

import os
import shutil
import subprocess
import time
import re

experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
scratch_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
metaeditor  = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"

def build_v623x3(source_filename, output_filename):
    source_path = os.path.join(experts_dir, f"{source_filename}.mq4")
    with open(source_path, "r", encoding="latin1") as f:
        code = f.read()

    # 1. Update Title and Property Version
    code = code.replace("Gold Sniper v6.4.1 Super Bull Alignment Engine", "Gold Sniper v6.2.3 x3 Pure London & Judas Engine")
    code = code.replace("Gold Sniper v6.4.1 Super Bull Alignment Bridge", "Gold Sniper v6.2.3 x3 Pure London & Judas Bridge")
    code = code.replace("Gold Sniper v6.3.8-BetaB High-Octane Apex Engine", "Gold Sniper v6.2.3 x3 Pure London & Judas Engine")
    code = code.replace("Gold Sniper v6.3.8-BetaB Bridge", "Gold Sniper v6.2.3 x3 Pure London & Judas Bridge")
    code = re.sub(r'#property version\s+"[\d\.]+"', '#property version   "6.23"', code)

    # 2. Update Master Header
    code = re.sub(
        r'input string\s+Header_Master\s+=\s+".*?";',
        'input string          Header_Master           = "=== MASTER V6.2.3 X3 (PURE LONDON 2.5X + JUDAS SCALP 2.0X) ===";',
        code
    )

    # 3. Add Engine Toggles and Multipliers
    custom_inputs = """//--- 0. ENGINE SELECTION & SCALING CONFIGURATION (v6.2.3 x3)
input string          Header_EngineConfig     = "=== V6.2.3 X3 ENGINE SELECTOR & LOT MULTIPLIERS ===";
input bool            EnableAsianEngine       = false;          // Disable Asian Scalper Completely
input bool            EnableNewYorkEngine     = false;          // Disable New York Reversal Completely
input bool            EnableLondonSniper      = true;           // Active: London Sniper Runner
input double          LondonLotMultiplier     = 2.50;           // London Sniper Lot Multiplier (2.5x Scaling)
input bool            EnableJudasSweepFade    = true;           // Active: Sweep Fade (Judas Liquidity Scalp)
input double          JudasLotMultiplier      = 2.00;           // Sweep Fade Lot Multiplier (2.0x Scaling)
"""
    if "Header_EngineConfig" not in code:
        code = code.replace('input ENUM_FLIP_MODE  OperatingMode', custom_inputs + '\ninput ENUM_FLIP_MODE  OperatingMode')

    # 4. Update Sweep Fade fixed lot to 0.04 (2x from 0.02)
    code = re.sub(r'input double\s+SweepFadeFixedLot\s+=\s+[\d\.]+;', 'input double          SweepFadeFixedLot       = 0.04;           // Judas Scalp Fixed Lot (2.0x Boosted from 0.02 to 0.04)', code)

    # 5. Apply London Lot Multiplier in London Sniper OrderSend
    # Find London Sniper CalculateLotSize:
    # double lot = CalculateLotSize(SniperRiskPercent, dynamicSniperSL);
    london_lot_replacement = """                  double lot = CalculateLotSize(SniperRiskPercent, dynamicSniperSL);
                  lot = NormalizeDouble(lot * LondonLotMultiplier, 2);
                  double minLot = MarketInfo(Symbol(), MODE_MINLOT);
                  double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);
                  if(lot < minLot) lot = minLot;
                  if(lot > maxLot) lot = maxLot;"""
    code = re.sub(r'double lot = CalculateLotSize\(SniperRiskPercent,\s*dynamicSniperSL\);', london_lot_replacement, code)

    # 6. Apply Sweep Fade Lot Multiplier if needed
    code = code.replace(
        'double sweepLot = SweepFadeFixedLot;',
        'double sweepLot = NormalizeDouble(SweepFadeFixedLot * (JudasLotMultiplier / 2.0), 2); // 0.04 lots'
    )

    # 7. Completely disable allowScalper and allowNY inside RunDualModeStrategy()
    code = code.replace('allowScalper = true;', 'if(EnableAsianEngine) allowScalper = true; else allowScalper = false;')
    code = code.replace('allowNY = true;', 'if(EnableNewYorkEngine) allowNY = true; else allowNY = false;')
    code = code.replace('allowNY     = (timeDec', 'allowNY     = EnableNewYorkEngine && (timeDec')

    # Also make sure Engine A and Engine C blocks are guarded
    code = code.replace('if(allowScalper)', 'if(EnableAsianEngine && allowScalper)')
    code = code.replace('if(allowNY)', 'if(EnableNewYorkEngine && allowNY)')

    # 8. Sentinel File and Magic Numbers
    code = code.replace('ai_sentinel_v641.json', 'ai_sentinel_v623x3.json')
    code = code.replace('ai_sentinel_v640.json', 'ai_sentinel_v623x3.json')
    code = code.replace('ai_sentinel.json', 'ai_sentinel_v623x3.json')
    code = code.replace('"version": "6.4.1-HybridApex"', '"version": "6.2.3-x3-PureLondonJudas"')
    code = code.replace('v6.4.1-HybridApex', 'v6.2.3-x3')
    code = code.replace('v6.4.1', 'v6.2.3-x3')
    code = code.replace('GS641HA_', 'GS623X3_')
    code = code.replace('888650', '888710')
    code = code.replace('888651', '888711')
    code = code.replace('888652', '888712')
    code = code.replace('888653', '888713')

    out_mq4 = os.path.join(experts_dir, f"{output_filename}.mq4")
    with open(out_mq4, "w", encoding="latin1") as f:
        f.write(code)
    shutil.copy2(out_mq4, os.path.join(scratch_dir, f"{output_filename}.mq4"))
    print(f"Generated: {out_mq4}")

files_to_build = [
    ("GoldSniper_Tester_v6_4_1_apex_quant", "GoldSniper_Tester_v6_2_3_x3"),
    ("GoldSniper_Bridge_v6_4_1_apex_quant", "GoldSniper_Bridge_v6_2_3_x3")
]

for src, dst in files_to_build:
    build_v623x3(src, dst)

print("\n--- Compiling v6.2.3 x3 with MetaEditor ---")
all_success = True
for src, name in files_to_build:
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
            except Exception:
                pass
    
    print(f"\nLog content for {name}:")
    print(log_content.strip() if log_content else "[No log file written or empty]")
    
    if os.path.exists(ex4_file):
        sz = os.path.getsize(ex4_file)
        print(f"SUCCESS: {ex4_file} built successfully! Size: {sz} bytes")
        shutil.copy2(ex4_file, os.path.join(scratch_dir, f"{name}.ex4"))
    else:
        print(f"ERROR: {ex4_file} NOT found!")
        all_success = False

print(f"\n=======================================================")
if all_success:
    print("ALL v6.2.3 x3 EXPERTS BUILT AND COMPILED WITH ZERO ERRORS!")
else:
    print("WARNING: Some files failed compilation!")
