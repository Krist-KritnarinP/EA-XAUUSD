import os

files = [
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Tester_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Tester_v2_5.mq4'
]

new_hud_func = '''//+------------------------------------------------------------------+
//| Update Institutional Visual HUD Dashboard                        |
//+------------------------------------------------------------------+
void UpdateHUD()
{
   if(IsTesting()) return; // Fast backtesting bypass
   
   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   double h1Fast = iMA(Symbol(), PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE, 1);
   double h1Slow = iMA(Symbol(), PERIOD_H1, 200, 0, MODE_EMA, PRICE_CLOSE, 1);
   string h1Trend = (h1Fast > h1Slow) ? "BULLISH [GREEN]" : ((h1Fast < h1Slow) ? "BEARISH [RED]" : "NEUTRAL");
   
   datetime now = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(now, dt);
   
   string activeSession = "STANDBY / ACCUMULATION";
   if(InpFocusNewYorkOnly)
   {
      if(dt.hour >= 15 && dt.hour < 18)
         activeSession = "NEW YORK OPEN (15:00 - 18:00 MT4) [HIGH CONVICTION]";
      else if(dt.hour >= 18 && (dt.hour < 20 || (dt.hour == 20 && dt.min <= 30)))
         activeSession = "NEW YORK LATE (18:00 - 20:30 MT4) [TREND RUNNER]";
      else
         activeSession = "STANDBY / OUT OF NY SESSION";
   }
   else
   {
      activeSession = IsTradingTime() ? "FULL DAY RADAR ACTIVE" : "STANDBY / OUT OF WINDOW";
   }
   
   string aiStatus = InpUseAiSentinel ? (g_ai_stand_down ? "ACTIVE [STAND-DOWN NEWS WINDOW]" : "READY [ALL CLEAR]") : "DISABLED";
   string streakStatus = StringFormat("%d Losses (Risk Mult: %.2fx)", g_ai_consec_losses, g_ai_risk_multiplier);
   
   // Count open orders and today's profit
   int openCount = 0;
   double openProfit = 0.0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicNumber)
         {
            openCount++;
            openProfit += OrderProfit() + OrderSwap() + OrderCommission();
         }
      }
   }
   
   double eq = AccountEquity();
   double bal = AccountBalance();
   double effRisk = InpRiskPercent * (InpUseAiSentinel ? g_ai_risk_multiplier : 1.0);
   
   string text = "=======================================================================\\n";
   text += "  ?? GOLD POI SNIPER v2.5 APEX INSTITUTIONAL (XM LIVE)\\n";
   text += "=======================================================================\\n";
   text += StringFormat("  Server Time    : %s\\n", TimeToString(now, TIME_DATE|TIME_SECONDS));
   text += StringFormat("  Current Session: %s\\n", activeSession);
   text += StringFormat("  H1 Macro Bias  : %s\\n", h1Trend);
   text += "  ---------------------------------------------------------------------\\n";
   text += StringFormat("  [POI Resistance] PDH: %.2f | Asian High: %.2f\\n", g_pdh, g_asian_high);
   text += StringFormat("  [POI Support]    PDL: %.2f | Asian Low : %.2f\\n", g_pdl, g_asian_low);
   text += StringFormat("  Current Price  : Ask %.2f | Bid %.2f\\n", Ask, Bid);
   text += "  ---------------------------------------------------------------------\\n";
   text += StringFormat("  AI Sentinel    : %s\\n", aiStatus);
   text += StringFormat("  AI Streak Guard: %s | AI Bias: %s\\n", streakStatus, g_ai_bias);
   text += "  ---------------------------------------------------------------------\\n";
   text += StringFormat("  Equity: $%.2f | Balance: $%.2f\\n", eq, bal);
   text += StringFormat("  Risk Engine    : %s (Eff Risk: %.2f%% | Max Lot: %.2f)\\n", 
                        InpUseRiskPercent ? (InpRiskOnEquity ? "ACTIVE (Equity-Based)" : "ACTIVE (Balance-Based)") : "FIXED",
                        effRisk, InpMaxLotCap);
   text += StringFormat("  Live Spread    : %d pts (Max: %d)\\n", spread, InpMaxSpreadPoints);
   text += StringFormat("  Target RR      : 1:%.1f | Breakeven Lock: %.1fR (+30 pts)\\n", InpTargetRR, InpBreakevenRR);
   text += StringFormat("  Open POI Orders: %d (Floating PnL: $%.2f)\\n", openCount, openProfit);
   text += "=======================================================================\\n";
   
   Comment(text);
}'''

for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        c = f.read()
    
    # 1. Replace UpdateHUD function
    start_hud = c.find('void UpdateHUD()')
    end_hud = c.find('void OnTick()')
    if start_hud >= 0 and end_hud > start_hud:
        c = c[:start_hud] + new_hud_func + '\n\n' + c[end_hud:]
    
    # 2. Add EventSetTimer in OnInit
    if 'EventSetTimer(1);' not in c:
        c = c.replace(
            'CheckAiSentinel();\n   UpdatePOIs();\n   ExportMarketState();\n   UpdateHUD();',
            'EventSetTimer(1);\n   CheckAiSentinel();\n   UpdatePOIs();\n   ExportMarketState();\n   UpdateHUD();'
        )
    
    # 3. Add OnDeinit and OnTimer
    if 'void OnDeinit' not in c:
        deinit_and_timer = '''//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Comment("");
   Print("[POI SNIPER v2.5] Deinitialized cleanly. Reason code: ", reason);
}

//+------------------------------------------------------------------+
//| Expert timer function (Runs every 1s even when market is closed) |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(!IsTesting())
   {
      CheckAiSentinel();
      UpdatePOIs();
      UpdateHUD();
   }
}
'''
        # Insert right before OnTick()
        c = c.replace('void OnTick()', deinit_and_timer + '\nvoid OnTick()')
        
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Upgraded HUD & OnTimer in:', fname)
