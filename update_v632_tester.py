import re

file_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Tester_v6_3_2.mq4"

with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Update London order execution to set LondonDirectionToday
old_london_buy = '''               if(isBuySignal)
               {
                  double lot = CalculateLotSize(SniperRiskPercent, SniperSL_USD);
                  double sl  = NormalizeDouble(Ask - SniperSL_USD, Digits);
                  double tp  = NormalizeDouble(Ask + SniperTP_USD, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.1 Sniper BUY", MagicSniper, 0, clrGreen);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     Print("[SNIPER RUNNER BUY v6.3] Ticket: #", ticket, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " TP: ", tp);
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
                     Print("[SNIPER RUNNER SELL v6.3] Ticket: #", ticket, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " TP: ", tp);
                     return;
                  }
               }'''

new_london_buy = '''               if(isBuySignal)
               {
                  double lot = CalculateLotSize(SniperRiskPercent, SniperSL_USD);
                  double sl  = NormalizeDouble(Ask - SniperSL_USD, Digits);
                  double tp  = NormalizeDouble(Ask + SniperTP_USD, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.2 Sniper BUY", MagicSniper, 0, clrGreen);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     LondonDirectionToday = 1;
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
                     Print("[SNIPER RUNNER SELL v6.3.2] Ticket: #", ticket, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " TP: ", tp);
                     return;
                  }
               }'''

if old_london_buy in content:
    content = content.replace(old_london_buy, new_london_buy)
    print("1. Successfully updated London Sniper order placement!")
else:
    print("1. WARNING: old_london_buy not found!")

# 2. Update Engine C
engine_c_pattern = r'   // ====================================================================\r?\n   // 3\. ENGINE C: NEW YORK CONFIRMED REVERSAL ENGINE \(15:00 - 17:30\)\r?\n   // ====================================================================.*?return;\r?\n                  \}\r?\n               \}\r?\n            \}\r?\n         \}\r?\n      \}\r?\n   \}'

new_engine_c = '''   // ====================================================================
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
                     Print("[NEW YORK TREND-RIDER SELL v6.3.2] Ticket: #", ticket, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " (", dynamicSL, " USD) TP: ", tp, " (", dynamicTP, " USD)");
                     return;
                  }
               }
            }
         }
      }
   }'''

match = re.search(engine_c_pattern, content, re.DOTALL)
if match:
    content = content[:match.start()] + new_engine_c + content[match.end():]
    print("2. Successfully updated Engine C to NY Institutional Trend-Rider!")
else:
    print("2. WARNING: Engine C pattern not matched!")

# 3. Update HUD / Dashboard
content = content.replace('activeSession = "NEW YORK CONFIRMED REVERSAL (15:00 - 17:30)";',
                          'activeSession = "NEW YORK TREND-RIDER (16:00 - 18:30)";')
content = content.replace('else if(h >= 15 && (h < 17 || (h == 17 && m <= 30)))',
                          'else if(h >= 16 && (h < 18 || (h == 18 && m <= 30)))')
content = content.replace('🏹 GOLD SNIPER v6.3.1 INSTITUTIONAL APEX (TESTER)',
                          '🏹 GOLD SNIPER v6.3.2 INSTITUTIONAL APEX (TESTER)')
print("3. Successfully updated Dashboard text!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Saved updated file to:", file_path)
