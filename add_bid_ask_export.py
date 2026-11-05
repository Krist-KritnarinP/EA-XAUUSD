files = [
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Tester_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Tester_v2_5.mq4'
]

old_export_head = '''   string json = "{\\n";
   json += "  \\"symbol\\": \\"" + Symbol() + "\\",\\n";
   json += "  \\"server_time\\": \\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\\",\\n";
   json += "  \\"balance\\": " + DoubleToString(AccountBalance(), 2) + ",\\n";
   json += "  \\"equity\\": " + DoubleToString(AccountEquity(), 2) + ",\\n";'''

new_export_head = '''   string json = "{\\n";
   json += "  \\"symbol\\": \\"" + Symbol() + "\\",\\n";
   json += "  \\"server_time\\": \\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\\",\\n";
   json += "  \\"bid\\": " + DoubleToString(Bid, Digits) + ",\\n";
   json += "  \\"ask\\": " + DoubleToString(Ask, Digits) + ",\\n";
   json += "  \\"balance\\": " + DoubleToString(AccountBalance(), 2) + ",\\n";
   json += "  \\"equity\\": " + DoubleToString(AccountEquity(), 2) + ",\\n";'''

for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        c = f.read()
    if old_export_head in c:
        c = c.replace(old_export_head, new_export_head)
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(c)
        print('Added bid/ask to market_state in:', fname)
    else:
        print('old_export_head not matched in:', fname)
