import os, re, shutil, subprocess

scratch_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
metaeditor = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"

# 1. Create Master and Tester v3.6
for ea_type in ["Master", "Tester"]:
    src_path = os.path.join(scratch_dir, f"Gold_POI_Sniper_{ea_type}_v3_5.mq4")
    with open(src_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace(f"Gold_POI_Sniper_{ea_type}_v3_5.mq4", f"Gold_POI_Sniper_{ea_type}_v3_6.mq4")
    content = content.replace("v3.5", "v3.6")
    content = content.replace('version   "3.50"', 'version   "3.60"')
    
    dst_v36 = os.path.join(scratch_dir, f"Gold_POI_Sniper_{ea_type}_v3_6.mq4")
    with open(dst_v36, "w", encoding="utf-8") as f:
        f.write(content)
    print("Created:", dst_v36)

# 2. Revert v3.5 files back to pure v3.5
for ea_type in ["Master", "Tester"]:
    v35_path = os.path.join(scratch_dir, f"Gold_POI_Sniper_{ea_type}_v3_5.mq4")
    with open(v35_path, "r", encoding="utf-8") as f:
        text = f.read()
        
    text = text.replace("extern bool     InpEnableHTFShield      = true;   // Enable H1/H4/D1 Support/Resistance Collision Shield\n", "")
    text = text.replace("extern double   InpHTFBufferUSD         = 6.00;   // Min Distance from H1/H4/D1 Support/Resistance ($6.00)\n", "")
    text = text.replace("extern double   InpLondonMaxPenetration = 6.00;   // Max Penetration beyond Asian Box to prevent Exhaustion ($6.00)\n", "")
    text = text.replace("extern double   InpMaxDailyExtensionUSD = 40.00;  // Max Daily Exhaustion Move from Day High/Low ($40.00)\n", "")
    
    # Remove function IsNearHTFSupportOrResistance
    text = re.sub(r'//\+[-]+\+\s+//\|\s+Multi-Timeframe \(H1, H4, D1\) Support & Resistance Shield[\s\S]*?^}\n', '', text, flags=re.M)
    
    old_signals = '''         double dayHigh = iHigh(Symbol(), PERIOD_D1, 0);
         double dayLow  = iLow(Symbol(), PERIOD_D1, 0);
         bool notExhaustedBuy  = (c1_close - dayLow) <= InpMaxDailyExtensionUSD;
         bool notExhaustedSell = (dayHigh - c1_close) <= InpMaxDailyExtensionUSD;
         
         bool isBuySignal  = sniperRvolOk && sniperBodyOk && isBull && notExhaustedBuy &&
                             (c1_close > g_stored_asian_high) && 
                             ((c1_close - g_stored_asian_high) >= InpLondonMinPenetration) && 
                             ((c1_close - g_stored_asian_high) <= InpLondonMaxPenetration) && 
                             (c1_close > c1_open);
                             
         bool isSellSignal = sniperRvolOk && sniperBodyOk && isBear && notExhaustedSell &&
                             (c1_close < g_stored_asian_low) && 
                             ((g_stored_asian_low - c1_close) >= InpLondonMinPenetration) && 
                             ((g_stored_asian_low - c1_close) <= InpLondonMaxPenetration) && 
                             (c1_close < c1_open);'''

    v35_signals = '''         bool isBuySignal  = sniperRvolOk && sniperBodyOk && isBull && 
                             (c1_close > g_stored_asian_high) && 
                             ((c1_close - g_stored_asian_high) >= InpLondonMinPenetration) && 
                             (c1_close > c1_open);
                             
         bool isSellSignal = sniperRvolOk && sniperBodyOk && isBear && 
                             (c1_close < g_stored_asian_low) && 
                             ((g_stored_asian_low - c1_close) >= InpLondonMinPenetration) && 
                             (c1_close < c1_open);'''

    text = text.replace(old_signals, v35_signals)
    text = text.replace("if(isBuySignal && !IsNearHTFSupportOrResistance(OP_BUY, Ask, InpHTFBufferUSD))", "if(isBuySignal)")
    text = text.replace("else if(isSellSignal && !IsNearHTFSupportOrResistance(OP_SELL, Bid, InpHTFBufferUSD))", "else if(isSellSignal)")
    
    with open(v35_path, "w", encoding="utf-8") as f:
        f.write(text)
    print("Reverted to pure v3.5:", v35_path)

# 3. Copy all 4 files to Experts directory and compile all 4
all_eas = [
    "Gold_POI_Sniper_Master_v3_5",
    "Gold_POI_Sniper_Tester_v3_5",
    "Gold_POI_Sniper_Master_v3_6",
    "Gold_POI_Sniper_Tester_v3_6"
]

for ea in all_eas:
    src_mq4 = os.path.join(scratch_dir, f"{ea}.mq4")
    dst_mq4 = os.path.join(experts_dir, f"{ea}.mq4")
    shutil.copy2(src_mq4, dst_mq4)
    
    log_path = os.path.join(scratch_dir, f"compile_{ea}.log")
    cmd = [metaeditor, f"/compile:{dst_mq4}", f"/log:{log_path}"]
    subprocess.run(cmd)
    
    if os.path.exists(log_path):
        with open(log_path, "rb") as f:
            log_txt = f.read().decode("utf-16", errors="ignore").strip()
            print(f"=== {ea} ===")
            print(log_txt)
