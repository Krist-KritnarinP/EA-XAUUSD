# -*- coding: utf-8 -*-
import os

def add_hud(file_path, is_bridge):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    tag = "XM LIVE" if is_bridge else "TESTER"
    
    sentinel_var = """   string sentinelStatus = StandDownActive ? "ACTIVE [STAND-DOWN NEWS WINDOW]" : "READY [ALL CLEAR]";\n""" if is_bridge else ""
    sentinel_line = """                 " AI Macro Sentinel: " + sentinelStatus + "\\n" +\n""" if is_bridge else ""

    hud_code = f"""
//+------------------------------------------------------------------+
//| On-Chart Status HUD Dashboard                                    |
//+------------------------------------------------------------------+
void UpdateChartDashboard()
{{
   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   double h1Fast = iMA(Symbol(), PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE, 1);
   double h1Slow = iMA(Symbol(), PERIOD_H1, 200, 0, MODE_EMA, PRICE_CLOSE, 1);
   string h1Trend = (h1Fast > h1Slow) ? "BULLISH [GREEN]" : ((h1Fast < h1Slow) ? "BEARISH [RED]" : "NEUTRAL");
   
   datetime now = TimeCurrent();
   int h = TimeHour(now);
   int m = TimeMinute(now);
   
   string activeSession = "STAND-BY / ACCUMULATION";
   if(h >= 2 && (h < 6 || (h == 2 && m >= 30)))
      activeSession = "ASIAN SQUEEZE SWEEPER (02:30 - 06:00)";
   else if(h >= 8 && (h < 11 || (h == 11 && m <= 30)))
      activeSession = "LONDON INSTITUTIONAL SNIPER (08:00 - 11:30)";
   else if(h >= 15 && (h < 17 || (h == 17 && m <= 30)))
      activeSession = "NEW YORK CONFIRMED REVERSAL (15:00 - 17:30)";
      
{sentinel_var}   string jackpotStatus = (EnableJackpotLock && DailySniperPnL >= JackpotProfitUSD) ? "LOCKED (+$" + DoubleToString(DailySniperPnL, 2) + " BANKED - NY HALTED)" : "READY";

   string text = "========================================================\\n" +
                 "  🏹 GOLD SNIPER v6.3.1 INSTITUTIONAL APEX ({tag})\\n" +
                 "========================================================\\n" +
                 " Server Time: " + TimeToStr(now, TIME_DATE|TIME_SECONDS) + "\\n" +
                 " Current Session: " + activeSession + "\\n" +
                 " H1 Macro Bias: " + h1Trend + "\\n" +
{sentinel_line}                 " Jackpot Lock: " + jackpotStatus + "\\n" +
                 "--------------------------------------------------------\\n" +
                 " Equity: $" + DoubleToString(AccountEquity(), 2) + " | Balance: $" + DoubleToString(AccountBalance(), 2) + "\\n" +
                 " Today PnL: $" + DoubleToString(DailyPnL, 2) + " (" + DoubleToString(DailyPnLPct, 2) + "%)\\n" +
                 " Sniper PnL: $" + DoubleToString(DailySniperPnL, 2) + "\\n" +
                 " Daily Trades: " + IntegerToString(DailyTotalTrades) + "\\n" +
                 " Live Spread: " + IntegerToString(spread) + " pts (Max: " + IntegerToString(MaxSpreadPoints) + ")\\n" +
                 " Open Orders: " + IntegerToString(OrdersTotal()) + "\\n" +
                 "========================================================";
   Comment(text);
}}
"""
    if 'UpdateChartDashboard()' not in code:
        code = code.replace("void OnTick()", hud_code + "\nvoid OnTick()")
        code = code.replace("return(INIT_SUCCEEDED);", "UpdateChartDashboard();\n   return(INIT_SUCCEEDED);")
        # in OnDeinit
        code = code.replace("Print(\"[GoldSniper", "Comment(\"\");\n   Print(\"[GoldSniper")
        # in OnTick
        last_brace = code.rfind("}")
        if last_brace != -1:
            code = code[:last_brace] + "   UpdateChartDashboard();\n}\n"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"Added HUD to {file_path}")

b_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\GoldSniper_Bridge_v6_3_1.mq4"
t_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\GoldSniper_Tester_v6_3_1.mq4"
add_hud(b_path, True)
add_hud(t_path, False)
