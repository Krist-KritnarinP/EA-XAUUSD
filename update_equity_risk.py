files = [
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Tester_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Tester_v2_5.mq4'
]

old_input = 'extern bool     InpUseRiskPercent   = true;   // TRUE: Dynamic Compounding for $1,000/mo growth\n'
new_input = 'extern bool     InpUseRiskPercent   = true;   // TRUE: Dynamic Compounding for $1,000/mo growth\nextern bool     InpRiskOnEquity     = true;   // TRUE: Calculate Risk based on Real-Time EQUITY (Safer)\n'

old_calc = '''   double balance = AccountBalance();
   double effective_risk = InpRiskPercent;
   
   // Apply AI Sentinel Dynamic Risk Multiplier
   if(InpUseAiSentinel)
   {
      effective_risk = InpRiskPercent * g_ai_risk_multiplier;
      if(effective_risk < 0.20) effective_risk = 0.20; // Safety floor 0.2%
   }
   
   double risk_amount = balance * (effective_risk / 100.0);'''

new_calc = '''   double capital = InpRiskOnEquity ? AccountEquity() : AccountBalance();
   if(capital <= 0.0) capital = AccountBalance();
   double effective_risk = InpRiskPercent;
   
   // Apply AI Sentinel Dynamic Risk Multiplier
   if(InpUseAiSentinel)
   {
      effective_risk = InpRiskPercent * g_ai_risk_multiplier;
      if(effective_risk < 0.20) effective_risk = 0.20; // Safety floor 0.2%
   }
   
   double risk_amount = capital * (effective_risk / 100.0);'''

old_hud = 'InpUseRiskPercent ? "ACTIVE (Compound Growth)" : "OFF", InpRiskPercent,'
new_hud = 'InpUseRiskPercent ? (InpRiskOnEquity ? "ACTIVE (Equity-Based)" : "ACTIVE (Balance-Based)") : "OFF", InpRiskPercent,'

for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'InpRiskOnEquity' not in content:
        content = content.replace(old_input, new_input)
    content = content.replace(old_calc, new_calc)
    content = content.replace(old_hud, new_hud)
    
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated equity risk in:', fname)
