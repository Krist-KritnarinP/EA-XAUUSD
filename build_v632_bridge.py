import re

src_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Bridge_v6_3_1.mq4"
dst_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Bridge_v6_3_2.mq4"

with open(src_path, "r", encoding="utf-8", errors="ignore") as f:
    code = f.read()

# 1. Update NY Inputs
old_inputs = '''//--- 3. NEW YORK CONFIRMED REVERSAL ENGINE (Overhauled Post-Wall Street Open)
input string          Header_NY               = "=== NEW YORK CONFIRMED REVERSAL (15:00-17:30) ===";
input int             NYTradeStartHour        = 15;             // NY Session Start Hour (15:00 - Post NYSE Open)
input int             NYTradeStartMin         = 0;              // NY Session Start Minute
input int             NYTradeEndHour          = 17;             // NY Session End Hour (17:30)
input int             NYTradeEndMin           = 30;             // NY Session End Minute
input double          NY_SL_USD               = 8.00;           // New York Stop Loss USD ($8.00)
input double          NY_TP_USD               = 16.00;          // New York Take Profit USD ($16.00 - RR 2.0:1 High Probability)
input double          NY_RVOL_Multiplier      = 1.15;           // New York RVOL Multiplier (1.15x)
input double          NY_MinADX               = 22.0;           // Min ADX Trend Strength Filter
input int             MagicNY                 = 888633;         // Magic Number New York v6.3.1'''

new_inputs = '''//--- 3. NEW YORK INSTITUTIONAL TREND-RIDER ENGINE (v6.3.2 Wall Street Momentum Wave)
input string          Header_NY               = "=== NEW YORK TREND-RIDER (16:00-18:30) ===";
input int             NYTradeStartHour        = 16;             // NY Session Start Hour (16:00 - Post-News Window)
input int             NYTradeStartMin         = 0;              // NY Session Start Minute
input int             NYTradeEndHour          = 18;             // NY Session End Hour (18:30)
input int             NYTradeEndMin           = 30;             // NY Session End Minute
input double          NY_Min_SL_USD           = 8.00;           // Min Base SL USD ($8.00)
input double          NY_ATR_Multiplier       = 1.50;           // Dynamic ATR SL Multiplier (1.5x M15 ATR)
input double          NY_RR_Ratio             = 2.20;           // Risk/Reward Ratio (2.2:1 Target)
input double          NY_RVOL_Multiplier      = 1.05;           // New York RVOL Multiplier (1.05x)
input double          NY_MinADX               = 18.0;           // Min ADX Trend Strength Filter
input bool            NY_RequireLondonAlign   = true;           // Require alignment with London Trend
input int             MagicNY                 = 888633;         // Magic Number New York v6.3.2'''

assert old_inputs in code, "old_inputs not found"
code = code.replace(old_inputs, new_inputs)

# 2. Add LondonDirectionToday global
old_globals = '''// Stored Asian Pre-Market Range for London Sniper
double   StoredAsianHigh           = 0.0;
double   StoredAsianLow            = 0.0;
datetime StoredAsianDate           = 0;'''

new_globals = '''// Stored Asian Pre-Market Range for London Sniper
double   StoredAsianHigh           = 0.0;
double   StoredAsianLow            = 0.0;
datetime StoredAsianDate           = 0;

// London Session Consensus Tracking for New York Alignment
int      LondonDirectionToday      = 0; // +1 for BUY, -1 for SELL, 0 for None'''

assert old_globals in code, "old_globals not found"
code = code.replace(old_globals, new_globals)

# 3. Reset LondonDirectionToday at midnight
old_reset = '''      StoredAsianHigh        = 0.0;
      StoredAsianLow         = 0.0;
      StoredAsianDate        = 0;
      PartialTPExecuted      = false;'''

new_reset = '''      StoredAsianHigh        = 0.0;
      StoredAsianLow         = 0.0;
      StoredAsianDate        = 0;
      LondonDirectionToday   = 0;
      PartialTPExecuted      = false;'''

assert old_reset in code, "old_reset not found"
code = code.replace(old_reset, new_reset)

# 4. CheckDailyResetAndStats - recover LondonDirectionToday
old_history_loop = '''         if((m == MagicScalper || m == MagicSniper || m == MagicNY) && OrderSymbol() == Symbol())
         {
            if(OrderOpenTime() >= today) todayTradeCount++;
            if(OrderCloseTime() >= today)'''

new_history_loop = '''         if((m == MagicScalper || m == MagicSniper || m == MagicNY) && OrderSymbol() == Symbol())
         {
            if(OrderOpenTime() >= today)
            {
               todayTradeCount++;
               if(m == MagicSniper)
               {
                  if(OrderType() == OP_BUY) LondonDirectionToday = 1;
                  else if(OrderType() == OP_SELL) LondonDirectionToday = -1;
               }
            }
            if(OrderCloseTime() >= today)'''

assert old_history_loop in code, "old_history_loop not found"
code = code.replace(old_history_loop, new_history_loop, 1)

old_open_loop = '''         if((m == MagicScalper || m == MagicSniper || m == MagicNY) && OrderSymbol() == Symbol())
         {
            if(OrderOpenTime() >= today) todayTradeCount++;
            double fp = OrderProfit() + OrderSwap() + OrderCommission();'''

new_open_loop = '''         if((m == MagicScalper || m == MagicSniper || m == MagicNY) && OrderSymbol() == Symbol())
         {
            if(OrderOpenTime() >= today)
            {
               todayTradeCount++;
               if(m == MagicSniper)
               {
                  if(OrderType() == OP_BUY) LondonDirectionToday = 1;
                  else if(OrderType() == OP_SELL) LondonDirectionToday = -1;
               }
            }
            double fp = OrderProfit() + OrderSwap() + OrderCommission();'''

assert old_open_loop in code, "old_open_loop not found"
code = code.replace(old_open_loop, new_open_loop, 1)

# 5. OnInit banner
old_init = '''   Print(" ⚡ GOLD SNIPER v6.3.1 INSTITUTIONAL LIVE XM BRIDGE LOADED");
   Print(" Architecture: ", EnumToString(OperatingMode));
   Print(" Sniper Runner: SL: $", SniperSL_USD, " | TP: $", SniperTP_USD, " (RR 3.5:1) | Risk: ", SniperRiskPercent, "%");
   Print(" NY Cash Flow:  SL: $", NY_SL_USD, " | TP: $", NY_TP_USD, " (RR 2.0:1) | Risk: ", NYRiskPercent, "% (Boosted)");'''

new_init = '''   Print(" ⚡ GOLD SNIPER v6.3.2 INSTITUTIONAL LIVE XM BRIDGE LOADED");
   Print(" Architecture: ", EnumToString(OperatingMode));
   Print(" Sniper Runner: SL: $", SniperSL_USD, " | TP: $", SniperTP_USD, " (RR 3.5:1) | Risk: ", SniperRiskPercent, "%");
   Print(" NY Trend-Rider: Dynamic ATR SL (Min $", NY_Min_SL_USD, ", ", NY_ATR_Multiplier, "x) | TP: RR ", NY_RR_Ratio, ":1 | Risk: ", NYRiskPercent, "%");'''

assert old_init in code, "old_init not found"
code = code.replace(old_init, new_init)

# 6. Position Management for NY (2-Stage Ratchet)
old_pos_ny = '''            // 3. NEW YORK REVERSAL POSITION MANAGEMENT
            if(m == MagicNY)
            {
               double profitUSD = (oType == OP_BUY) ? (Bid - openP) : (openP - Ask);
               if(profitUSD >= 10.00)
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + spreadOffset + 1.00, Digits);
                     if(curSL < targetSL)
                     {
                        bool modRes = OrderModify(ticket, openP, targetSL, curTP, 0, clrBlue);
                     }
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - spreadOffset - 1.00, Digits);
                     if(curSL > targetSL || curSL == 0)
                     {
                        bool modRes = OrderModify(ticket, openP, targetSL, curTP, 0, clrBlue);
                     }
                  }
               }
            }'''

new_pos_ny = '''            // 3. NEW YORK INSTITUTIONAL TREND-RIDER POSITION MANAGEMENT (v6.3.2)
            if(m == MagicNY)
            {
               double profitUSD = (oType == OP_BUY) ? (Bid - openP) : (openP - Ask);
               
               // Invariant initial risk calculation via TakeProfit distance
               double initialRiskUSD = NY_Min_SL_USD;
               if(curTP > 0 && NY_RR_Ratio > 0)
               {
                  initialRiskUSD = NormalizeDouble(MathAbs(curTP - openP) / NY_RR_Ratio, 2);
               }
               if(initialRiskUSD < 4.0) initialRiskUSD = NY_Min_SL_USD;
               
               // Stage 2: Profit Ratchet (+0.75R Lock) when profit reaches 1.50R
               if(profitUSD >= (initialRiskUSD * 1.50))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + (initialRiskUSD * 0.75), Digits);
                     if(curSL < targetSL)
                     {
                        bool modRes = OrderModify(ticket, openP, targetSL, curTP, 0, clrGreen);
                        if(modRes) Print("[NY RATCHET STAGE 2 v6.3.2] NY Buy #", ticket, " SL locked at +0.75R (+", NormalizeDouble(initialRiskUSD * 0.75, 2), " USD)");
                     }
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - (initialRiskUSD * 0.75), Digits);
                     if(curSL > targetSL || curSL == 0)
                     {
                        bool modRes = OrderModify(ticket, openP, targetSL, curTP, 0, clrGreen);
                        if(modRes) Print("[NY RATCHET STAGE 2 v6.3.2] NY Sell #", ticket, " SL locked at +0.75R (+", NormalizeDouble(initialRiskUSD * 0.75, 2), " USD)");
                     }
                  }
               }
               // Stage 1: Breakeven Lock (+0.50 cover) when profit reaches 1.00R
               else if(profitUSD >= initialRiskUSD)
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + spreadOffset + 0.50, Digits);
                     if(curSL < targetSL)
                     {
                        bool modRes = OrderModify(ticket, openP, targetSL, curTP, 0, clrBlue);
                        if(modRes) Print("[NY RATCHET STAGE 1 v6.3.2] NY Buy #", ticket, " SL moved to Breakeven (+0.50 cover)");
                     }
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - spreadOffset - 0.50, Digits);
                     if(curSL > targetSL || curSL == 0)
                     {
                        bool modRes = OrderModify(ticket, openP, targetSL, curTP, 0, clrBlue);
                        if(modRes) Print("[NY RATCHET STAGE 1 v6.3.2] NY Sell #", ticket, " SL moved to Breakeven (+0.50 cover)");
                     }
                  }
               }
            }'''

assert old_pos_ny in code, "old_pos_ny not found"
code = code.replace(old_pos_ny, new_pos_ny)

# 7. ExportMarketState updates
code = code.replace('"version": "6.3.1"', '"version": "6.3.2"')
code = code.replace('json += "  \\"stored_asian_low\\": " + DoubleToString(StoredAsianLow, Digits) + ",\\n";',
                    'json += "  \\"stored_asian_low\\": " + DoubleToString(StoredAsianLow, Digits) + ",\\n";\n   json += "  \\"london_direction\\": " + IntegerToString(LondonDirectionToday) + ",\\n";')

# 8. London order execution - set LondonDirectionToday
old_london_orders = '''               if(isBuySignal)
               {
                  double lot = CalculateLotSize(SniperRiskPercent, SniperSL_USD);
                  double sl  = NormalizeDouble(Ask - SniperSL_USD, Digits);
                  double tp  = NormalizeDouble(Ask + SniperTP_USD, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.1 Sniper BUY", MagicSniper, 0, clrGreen);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     BroadcastSignal("A+", "BUY", Ask, sl, tp, "London Institutional Breakout", "Asian High Penetrated >= $1.50 with RVOL >= 1.4 & H1 Bull Trend");
                     Print("[SNIPER RUNNER BUY v6.3.1] Ticket: #", ticket, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " TP: ", tp);
                     return;
                  }
               }
               else if(isSellSignal)
               {
                  double lot = CalculateLotSize(SniperRiskPercent, SniperSL_USD);
                  double sl  = NormalizeDouble(Bid + SniperSL_USD, Digits);
                  double tp  = NormalizeDouble(Bid - SniperTP_USD, Digits);
                  int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, SlippagePoints, sl, tp, "v6.3.1 Sniper SELL", MagicSniper, 0, clrRed);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     BroadcastSignal("A+", "SELL", Bid, sl, tp, "London Institutional Breakout", "Asian Low Penetrated >= $1.50 with RVOL >= 1.4 & H1 Bear Trend");
                     Print("[SNIPER RUNNER SELL v6.3.1] Ticket: #", ticket, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " TP: ", tp);
                     return;
                  }
               }'''

new_london_orders = '''               if(isBuySignal)
               {
                  double lot = CalculateLotSize(SniperRiskPercent, SniperSL_USD);
                  double sl  = NormalizeDouble(Ask - SniperSL_USD, Digits);
                  double tp  = NormalizeDouble(Ask + SniperTP_USD, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.2 Sniper BUY", MagicSniper, 0, clrGreen);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     LondonDirectionToday = 1;
                     BroadcastSignal("A+", "BUY", Ask, sl, tp, "London Institutional Breakout", "Asian High Penetrated >= $1.50 with RVOL >= 1.4 & H1 Bull Trend");
                     Print("[SNIPER RUNNER BUY v6.3.2] Ticket: #", ticket, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " TP: ", tp);
                     return;
                  }
               }
               else if(isSellSignal)
               {
                  double lot = CalculateLotSize(SniperRiskPercent, SniperSL_USD);
                  double sl  = NormalizeDouble(Bid + SniperSL_USD, Digits);
                  double tp  = NormalizeDouble(Bid - SniperTP_USD, Digits);
                  int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, SlippagePoints, sl, tp, "v6.3.2 Sniper SELL", MagicSniper, 0, clrRed);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     LondonDirectionToday = -1;
                     BroadcastSignal("A+", "SELL", Bid, sl, tp, "London Institutional Breakout", "Asian Low Penetrated >= $1.50 with RVOL >= 1.4 & H1 Bear Trend");
                     Print("[SNIPER RUNNER SELL v6.3.2] Ticket: #", ticket, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " TP: ", tp);
                     return;
                  }
               }'''

assert old_london_orders in code, "old_london_orders not found"
code = code.replace(old_london_orders, new_london_orders)

# 9. Engine C in Bridge
engine_c_pattern = r'   // ====================================================================\r?\n   // 3\. ENGINE C: NEW YORK CONFIRMED REVERSAL ENGINE \(15:00 - 17:30\)\r?\n   // ====================================================================.*?return;\r?\n                  \}\r?\n               \}\r?\n            \}\r?\n         \}\r?\n      \}\r?\n   \}'

new_bridge_engine_c = '''   // ====================================================================
   // 3. ENGINE C: NEW YORK INSTITUTIONAL TREND-RIDER ENGINE (16:00 - 18:30)
   // ====================================================================
   if(allowNY && DailyNYLossCount < MaxNYDailyLosses)
   {
      // 🌟 V6.3 JACKPOT LOCK: If London Sniper already banked >= $100 today, LOCK IN PROFITS & HALT NY!
      if(EnableJackpotLock && DailySniperPnL >= JackpotProfitUSD)
      {
         return; // Jackpot locked! Protect daily winnings!
      }
      
      bool nyActive = false;
      for(int i = 0; i < OrdersTotal(); i++)
      {
         if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
         {
            if((OrderMagicNumber() == MagicNY || OrderMagicNumber() == MagicSniper) && OrderSymbol() == Symbol())
            {
               nyActive = true;
               break;
            }
         }
      }
      
      if(!nyActive)
      {
         // Volume filter & ADX Trend filter for NY Expansion
         double adxVal = iADX(Symbol(), PERIOD_M15, 14, PRICE_CLOSE, MODE_MAIN, 1);
         if(adxVal >= NY_MinADX && CheckRVOL(NY_RVOL_Multiplier))
         {
            // Dynamic ATR Stop Loss & Target Calculation (Adaptive Volatility Sizing)
            double atr15 = iATR(Symbol(), PERIOD_M15, 14, 1);
            double dynamicSL = MathMax(NY_Min_SL_USD, NormalizeDouble(atr15 * NY_ATR_Multiplier, 2));
            double dynamicTP = NormalizeDouble(dynamicSL * NY_RR_Ratio, 2);
            
            // BUY Trend-Rider: H1 Macro Bull + M15 EMAs Bull + London Direction Alignment
            bool buyDirectionOk = isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15);
            if(NY_RequireLondonAlign && LondonDirectionToday < 0) buyDirectionOk = false; // Block counter-trend Sell from London
            
            if(buyDirectionOk)
            {
               // Pullback: Low probed EMA50 and closed back above
               bool testedEMA = (l1 <= ema50_m15 + 1.50) && (c1 > ema50_m15);
               // Institutional Confirmation: Green candle + lower wick rejection (>=30%) OR strong body (>=45%), upper wick <= 35%
               bool isBullRejection = (c1 > o1) && (((lowerWick / range1) >= 0.30) || ((body1 / range1) >= 0.45)) && ((upperWick / range1) <= 0.35);
               
               if(testedEMA && isBullRejection)
               {
                  double lot = CalculateLotSize(NYRiskPercent, dynamicSL);
                  double sl  = NormalizeDouble(Ask - dynamicSL, Digits);
                  double tp  = NormalizeDouble(Ask + dynamicTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.2 NY Buy", MagicNY, 0, clrBlue);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     BroadcastSignal("A+", "BUY", Ask, sl, tp, "New York Institutional Trend-Rider", "Post-News Trend-Riding at EMA50 Pullback with London Consensus Alignment");
                     Print("[NEW YORK TREND-RIDER BUY v6.3.2] Ticket: #", ticket, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " (", dynamicSL, " USD) TP: ", tp, " (", dynamicTP, " USD)");
                     return;
                  }
               }
            }
            // SELL Trend-Rider: H1 Macro Bear + M15 EMAs Bear + London Direction Alignment
            bool sellDirectionOk = isH1Bear && (c1 < ema200_m15) && (ema50_m15 < ema200_m15);
            if(NY_RequireLondonAlign && LondonDirectionToday > 0) sellDirectionOk = false; // Block counter-trend Buy from London
            
            if(sellDirectionOk)
            {
               // Pullback: High probed EMA50 and closed back below
               bool testedEMA = (h1 >= ema50_m15 - 1.50) && (c1 < ema50_m15);
               // Institutional Confirmation: Red candle + upper wick rejection (>=30%) OR strong body (>=45%), lower wick <= 35%
               bool isBearRejection = (c1 < o1) && (((upperWick / range1) >= 0.30) || ((body1 / range1) >= 0.45)) && ((lowerWick / range1) <= 0.35);
               
               if(testedEMA && isBearRejection)
               {
                  double lot = CalculateLotSize(NYRiskPercent, dynamicSL);
                  double sl  = NormalizeDouble(Bid + dynamicSL, Digits);
                  double tp  = NormalizeDouble(Bid - dynamicTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, SlippagePoints, sl, tp, "v6.3.2 NY Sell", MagicNY, 0, clrMagenta);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     BroadcastSignal("A+", "SELL", Bid, sl, tp, "New York Institutional Trend-Rider", "Post-News Trend-Riding at EMA50 Pullback with London Consensus Alignment");
                     Print("[NEW YORK TREND-RIDER SELL v6.3.2] Ticket: #", ticket, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " (", dynamicSL, " USD) TP: ", tp, " (", dynamicTP, " USD)");
                     return;
                  }
               }
            }
         }
      }
   }'''

match = re.search(engine_c_pattern, code, re.DOTALL)
assert match is not None, "engine_c_pattern not found"
code = code[:match.start()] + new_bridge_engine_c + code[match.end():]

# 10. Dashboard & HUD updates
code = code.replace('activeSession = "NEW YORK CONFIRMED REVERSAL (15:00 - 17:30)";',
                    'activeSession = "NEW YORK TREND-RIDER (16:00 - 18:30)";')
code = code.replace('else if(h >= 15 && (h < 17 || (h == 17 && m <= 30)))',
                    'else if(h >= 16 && (h < 18 || (h == 18 && m <= 30)))')
code = code.replace('🏹 GOLD SNIPER v6.3.1 INSTITUTIONAL APEX (XM LIVE)',
                    '🏹 GOLD SNIPER v6.3.2 INSTITUTIONAL APEX (XM LIVE)')

with open(dst_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Successfully created GoldSniper_Bridge_v6_3_2.mq4 at:", dst_path)
