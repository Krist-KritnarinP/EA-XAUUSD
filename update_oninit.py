files = [
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Tester_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Tester_v2_5.mq4'
]

old_init = '''int OnInit()
{
   Print("[POI SNIPER v2.5 INIT] Institutional Gold POI Sniper v2.5 Initialized.");
   PrintFormat("[CONFIG] Dynamic Risk: %s (%.1f%%) | Focus NY: %s | BE RR: %.1fR | Target RR: 1:%.1f | AI Sentinel: %s", 
               InpUseRiskPercent ? "ON" : "OFF", InpRiskPercent, InpFocusNewYorkOnly ? "YES (15:00-20:30)" : "FULL DAY",
               InpBreakevenRR, InpTargetRR, InpUseAiSentinel ? "ENABLED" : "DISABLED");
   return(INIT_SUCCEEDED);
}'''

new_init = '''int OnInit()
{
   Print("[POI SNIPER v2.5 INIT] Institutional Gold POI Sniper v2.5 Initialized.");
   PrintFormat("[CONFIG] Dynamic Risk: %s (%.1f%%) | Focus NY: %s | BE RR: %.1fR | Target RR: 1:%.1f | AI Sentinel: %s", 
               InpUseRiskPercent ? "ON" : "OFF", InpRiskPercent, InpFocusNewYorkOnly ? "YES (15:00-20:30)" : "FULL DAY",
               InpBreakevenRR, InpTargetRR, InpUseAiSentinel ? "ENABLED" : "DISABLED");
   
   CheckAiSentinel();
   UpdatePOIs();
   ExportMarketState();
   UpdateHUD();
   
   return(INIT_SUCCEEDED);
}'''

for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        c = f.read()
    if old_init in c:
        c = c.replace(old_init, new_init)
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(c)
        print('Successfully updated OnInit in:', fname)
    else:
        print('old_init not matched in:', fname)
