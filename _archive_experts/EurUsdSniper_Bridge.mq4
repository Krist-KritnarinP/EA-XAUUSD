//+------------------------------------------------------------------+
//|                                        EurUsdSniper_Bridge.mq4   |
//|                          Copyright 2026, Pure ICT Quant AI Engine |
//|                EURUSD Institutional ICT Pure Execution Engine     |
//|               [Zero-Latency Decoupled Bridge • XM 1:1000 Equity]  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Pure ICT Quant AI Engine"
#property link      "https://github.com/eurusd-sniper-institutional"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input string          Header_Master           = "=== EURUSD PURE ICT MASTER ENGINE ===";
input double          EquityRiskPercent       = 1.5;            // Risk per Trade (% of Account Equity)
input double          MaxSpreadPips           = 1.8;            // Max Allowed Spread in Pips (18 points)
input int             MagicNumber             = 777100;         // Magic Number for EURUSD ICT Orders
input string          OrderCommentTag         = "EURUSD_ICT_Apex";

input string          Header_Bridge           = "=== AI SENTINEL DECOUPLED BRIDGE ===";
input bool            UseAiSentinel           = true;           // Read AI Sentinel JSON Signals
input string          SentinelFileName        = "ai_sentinel_eurusd.json";  // Sentinel File in MQL4/Files
input string          MarketStateFileName     = "market_state_eurusd.json"; // State Export in MQL4/Files
input string          CrossAssetSmtSymbol     = "GBPUSD";       // SMT Correlated Symbol for Divergence
input int             StateExportIntervalSec  = 1;              // Export Frequency (Seconds)

input string          Header_Sessions         = "=== ICT TIME & SESSIONS (UTC / SERVER) ===";
input int             AsianStartHour          = 0;              // Asian Range Start (00:00 UTC)
input int             AsianEndHour            = 6;              // Asian Range End (06:00 UTC)
input int             LondonStartHour         = 7;              // London Killzone Start (07:00 UTC)
input int             LondonEndHour           = 10;             // London Killzone End (10:00 UTC)
input int             NYStartHour             = 12;             // New York Killzone Start (12:00 UTC)
input int             NYEndHour               = 15;             // New York Killzone End (15:00 UTC)

input string          Header_Protection       = "=== RISK & TRADE PROTECTION ===";
input bool            EnableBreakeven         = true;           // Move SL to Breakeven (+0.5 pip) at 1.5R
input double          BE_Trigger_R            = 1.50;           // Breakeven Profit Trigger (R:R)
input bool            EnableDynamicTrail      = true;           // Dynamic Trailing Stop past 2.0R
input double          TrailDistance_R         = 1.25;           // Trailing distance behind price (R:R)
input bool            FridaySunsetCut         = true;           // Close Intraday Trades on Friday 21:00 UTC
input int             FridaySunsetCutHour     = 21;             // Friday Auto-Close Hour (21:00 UTC)

//+------------------------------------------------------------------+
//| Global Internal State                                            |
//+------------------------------------------------------------------+
datetime LastExportTime       = 0;
datetime LastSentinelReadTime = 0;
bool     AiNewsStandDown      = false;
double   AiRiskMultiplier     = 1.0;
string   LastExecutedSignalId = "";

double   StoredAsianHigh      = 0.0;
double   StoredAsianLow       = 0.0;
datetime LastAsianCalcDay     = 0;

//+------------------------------------------------------------------+
//| Helper: Convert Pips to Points                                   |
//+------------------------------------------------------------------+
double PipsToPoints(double pips)
{
   if(Digits == 3 || Digits == 5) return pips * 10.0 * Point;
   return pips * Point;
}

double PointsToPips(double points)
{
   if(Digits == 3 || Digits == 5) return points / (10.0 * Point);
   return points / Point;
}

//+------------------------------------------------------------------+
//| Expert Initialization                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("================================================================================");
   Print(" [EURUSD PURE ICT BRIDGE v1.00] Initialized on ", Symbol(), " Digits: ", Digits);
   Print(" Account Equity: $", DoubleToStr(AccountEquity(), 2), " | Broker Leverage: 1:", AccountLeverage());
   Print(" Target SMT Cross Symbol: ", CrossAssetSmtSymbol);
   Print("================================================================================");
   
   EventSetTimer(1); // 1-second heartbeat
   ExportMarketState(true);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert Deinitialization                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("[EURUSD PURE ICT BRIDGE] Engine Deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Timer Event                                                      |
//+------------------------------------------------------------------+
void OnTimer()
{
   ReadAiSentinel();
   ExportMarketState(false);
}

//+------------------------------------------------------------------+
//| Check & Update Asian Range (00:00 - 06:00 UTC)                   |
//+------------------------------------------------------------------+
void UpdateAsianRange()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Check if new day
   datetime todayStart = StringToTime(TimeToStr(TimeCurrent(), TIME_DATE));
   if(todayStart != LastAsianCalcDay)
   {
      StoredAsianHigh = 0.0;
      StoredAsianLow  = 0.0;
      LastAsianCalcDay = todayStart;
   }
   
   // During Asian session, dynamically find highest and lowest
   if(dt.hour >= AsianStartHour && dt.hour < AsianEndHour)
   {
      int startBar = iBarShift(Symbol(), PERIOD_M15, todayStart + (AsianStartHour * 3600));
      int currentBar = iBarShift(Symbol(), PERIOD_M15, TimeCurrent());
      if(startBar >= currentBar && currentBar >= 0)
      {
         int count = startBar - currentBar + 1;
         int highestIdx = iHighest(Symbol(), PERIOD_M15, MODE_HIGH, count, currentBar);
         int lowestIdx  = iLowest(Symbol(), PERIOD_M15, MODE_LOW, count, currentBar);
         if(highestIdx >= 0 && lowestIdx >= 0)
         {
            StoredAsianHigh = iHigh(Symbol(), PERIOD_M15, highestIdx);
            StoredAsianLow  = iLow(Symbol(), PERIOD_M15, lowestIdx);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Read AI Sentinel JSON from Python                                |
//+------------------------------------------------------------------+
void ReadAiSentinel()
{
   if(!UseAiSentinel) return;
   if(TimeCurrent() - LastSentinelReadTime < 1) return;
   LastSentinelReadTime = TimeCurrent();
   
   if(!FileIsExist(SentinelFileName)) return;
   
   int handle = FileOpen(SentinelFileName, FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE) return;
   
   string content = "";
   while(!FileIsEnding(handle)) content += FileReadString(handle);
   FileClose(handle);
   
   // 1. Parse Stand Down
   if(StringFind(content, "\"stand_down\": true") >= 0)
   {
      if(!AiNewsStandDown)
         Print("[EURUSD ICT SENTINEL] Macro High-Impact News Detected! Stand-Down ENGAGED.");
      AiNewsStandDown = true;
   }
   else
   {
      if(AiNewsStandDown)
         Print("[EURUSD ICT SENTINEL] News window cleared. Stand-Down DISENGAGED.");
      AiNewsStandDown = false;
   }
   
   // 2. Parse AI Risk Multiplier
   int multPos = StringFind(content, "\"ai_risk_multiplier\":");
   if(multPos >= 0)
   {
      string sub = StringSubstr(content, multPos + 22, 4);
      double m = StringToDouble(sub);
      if(m >= 0.0 && m <= 2.0) AiRiskMultiplier = m;
   }
   
   // 3. Parse Trade Signal
   if(!AiNewsStandDown && StringFind(content, "\"is_valid\": true") >= 0)
   {
      ParseAndExecuteSignal(content);
   }
}

//+------------------------------------------------------------------+
//| Parse Signal JSON and Execute Order                              |
//+------------------------------------------------------------------+
void ParseAndExecuteSignal(string json)
{
   // Extract Signal ID
   int idPos = StringFind(json, "\"signal_id\": \"");
   if(idPos < 0) return;
   int idEnd = StringFind(json, "\"", idPos + 14);
   string sigId = StringSubstr(json, idPos + 14, idEnd - (idPos + 14));
   
   if(sigId == "" || sigId == LastExecutedSignalId) return; // Prevent duplicate execution
   
   // Check Spread
   double spreadPips = PointsToPips(MarketInfo(Symbol(), MODE_SPREAD) * Point);
   if(spreadPips > MaxSpreadPips)
   {
      Print("[EURUSD ICT] Trade rejected: Spread ", spreadPips, " pips exceeds max ", MaxSpreadPips);
      return;
   }
   
   // Determine Action
   bool isBuy = (StringFind(json, "\"action\": \"BUY\"") >= 0);
   bool isSell = (StringFind(json, "\"action\": \"SELL\"") >= 0);
   if(!isBuy && !isSell) return;
   
   // Extract Prices
   double entryPrice = 0.0, slPrice = 0.0, tpPrice = 0.0;
   
   int epPos = StringFind(json, "\"entry_price\":");
   if(epPos >= 0) entryPrice = StringToDouble(StringSubstr(json, epPos + 15, 8));
   
   int slPos = StringFind(json, "\"sl_price\":");
   if(slPos >= 0) slPrice = StringToDouble(StringSubstr(json, slPos + 12, 8));
   
   int tpPos = StringFind(json, "\"tp_price\":");
   if(tpPos >= 0) tpPrice = StringToDouble(StringSubstr(json, tpPos + 12, 8));
   
   if(slPrice <= 0 || tpPrice <= 0) return;
   
   // Calculate Stop Loss distance
   double currentPrice = isBuy ? Ask : Bid;
   double slDistancePoints = isBuy ? (currentPrice - slPrice) / Point : (slPrice - currentPrice) / Point;
   if(slDistancePoints <= 0) slDistancePoints = 100; // minimum fallback 10 pips
   
   // Dynamic Lot Calculation based on Account Equity (XM 1:1000)
   double riskMoney = AccountEquity() * (EquityRiskPercent / 100.0) * AiRiskMultiplier;
   double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
   if(tickValue <= 0) tickValue = 1.0;
   
   double calculatedLot = riskMoney / (slDistancePoints * tickValue);
   
   // Lot normalization
   double minLot = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot = MarketInfo(Symbol(), MODE_MAXLOT);
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   
   calculatedLot = MathFloor(calculatedLot / lotStep) * lotStep;
   if(calculatedLot < minLot) calculatedLot = minLot;
   if(calculatedLot > maxLot) calculatedLot = maxLot;
   
   // Execute Market Order
   int cmd = isBuy ? OP_BUY : OP_SELL;
   color clr = isBuy ? clrDodgerBlue : clrCrimson;
   int ticket = OrderSend(Symbol(), cmd, calculatedLot, currentPrice, 3, slPrice, tpPrice, OrderCommentTag, MagicNumber, 0, clr);
   
   if(ticket > 0)
   {
      LastExecutedSignalId = sigId;
      Print("[EURUSD ICT EXECUTION] Ticket #", ticket, " ", (isBuy ? "BUY" : "SELL"), 
            " Lots: ", calculatedLot, " at ", currentPrice, " SL: ", slPrice, " TP: ", tpPrice,
            " Equity Risk: $", DoubleToStr(riskMoney, 2));
      ExportMarketState(true);
   }
   else
   {
      Print("[EURUSD ICT EXECUTION ERROR] OrderSend failed with error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Manage Open Orders: Trailing Stop & Breakeven                    |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != MagicNumber) continue;
      
      double openPrice = OrderOpenPrice();
      double currentSL = OrderStopLoss();
      double currentTP = OrderTakeProfit();
      double initialRisk = MathAbs(openPrice - currentSL);
      if(initialRisk <= 0) continue;
      
      // 1. BUY Position Management
      if(OrderType() == OP_BUY)
      {
         double currentProfitDist = Bid - openPrice;
         double currentR = currentProfitDist / initialRisk;
         
         // Breakeven Lock at 1.5R (+0.5 pip lock)
         if(EnableBreakeven && currentR >= BE_Trigger_R)
         {
            double bePrice = NormalizeDouble(openPrice + PipsToPoints(0.5), Digits);
            if(currentSL < bePrice)
            {
               bool mod = OrderModify(OrderTicket(), openPrice, bePrice, currentTP, 0, clrAqua);
               if(mod) Print("[ICT PROTECTION] Ticket #", OrderTicket(), " moved to Breakeven (+0.5 pip).");
            }
         }
         
         // Dynamic Trailing Stop past 2.0R
         if(EnableDynamicTrail && currentR >= 2.0)
         {
            double trailSL = NormalizeDouble(Bid - (initialRisk * TrailDistance_R), Digits);
            if(trailSL > currentSL && trailSL > openPrice)
            {
               bool mod = OrderModify(OrderTicket(), openPrice, trailSL, currentTP, 0, clrGreen);
            }
         }
      }
      
      // 2. SELL Position Management
      if(OrderType() == OP_SELL)
      {
         double currentProfitDist = openPrice - Ask;
         double currentR = currentProfitDist / initialRisk;
         
         // Breakeven Lock at 1.5R
         if(EnableBreakeven && currentR >= BE_Trigger_R)
         {
            double bePrice = NormalizeDouble(openPrice - PipsToPoints(0.5), Digits);
            if(currentSL > bePrice || currentSL == 0)
            {
               bool mod = OrderModify(OrderTicket(), openPrice, bePrice, currentTP, 0, clrAqua);
               if(mod) Print("[ICT PROTECTION] Ticket #", OrderTicket(), " moved to Breakeven (+0.5 pip).");
            }
         }
         
         // Dynamic Trailing Stop past 2.0R
         if(EnableDynamicTrail && currentR >= 2.0)
         {
            double trailSL = NormalizeDouble(Ask + (initialRisk * TrailDistance_R), Digits);
            if((trailSL < currentSL || currentSL == 0) && trailSL < openPrice)
            {
               bool mod = OrderModify(OrderTicket(), openPrice, trailSL, currentTP, 0, clrGreen);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check Friday Sunset Cut (21:00 UTC)                              |
//+------------------------------------------------------------------+
void CheckFridaySunsetCut()
{
   if(!FridaySunsetCut) return;
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   if(dt.day_of_week == 5 && dt.hour >= FridaySunsetCutHour)
   {
      for(int i = OrdersTotal() - 1; i >= 0; i--)
      {
         if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
         if(OrderSymbol() != Symbol() || OrderMagicNumber() != MagicNumber) continue;
         
         if(OrderType() == OP_BUY)
         {
            bool cls = OrderClose(OrderTicket(), OrderLots(), Bid, 3, clrOrangeRed);
         }
         else if(OrderType() == OP_SELL)
         {
            bool cls = OrderClose(OrderTicket(), OrderLots(), Ask, 3, clrOrangeRed);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Export Market State to JSON for Python AI Agent                  |
//+------------------------------------------------------------------+
void ExportMarketState(bool forceExport)
{
   if(!forceExport && (TimeCurrent() - LastExportTime < StateExportIntervalSec)) return;
   LastExportTime = TimeCurrent();
   
   UpdateAsianRange();
   
   // Cross-Asset SMT Quotes
   double smtBid = 0.0, smtAsk = 0.0;
   if(CrossAssetSmtSymbol != "")
   {
      smtBid = MarketInfo(CrossAssetSmtSymbol, MODE_BID);
      smtAsk = MarketInfo(CrossAssetSmtSymbol, MODE_ASK);
   }
   
   // ATR M15 in Pips
   double atrValue = iATR(Symbol(), PERIOD_M15, 14, 0);
   double atrPips = PointsToPips(atrValue);
   
   string json = "{\n";
   json += "  \"symbol\": \"" + Symbol() + "\",\n";
   json += "  \"server_time\": \"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\",\n";
   json += "  \"bid\": " + DoubleToString(Bid, Digits) + ",\n";
   json += "  \"ask\": " + DoubleToString(Ask, Digits) + ",\n";
   json += "  \"spread_pips\": " + DoubleToString(PointsToPips(MarketInfo(Symbol(), MODE_SPREAD) * Point), 1) + ",\n";
   json += "  \"balance\": " + DoubleToString(AccountBalance(), 2) + ",\n";
   json += "  \"equity\": " + DoubleToString(AccountEquity(), 2) + ",\n";
   json += "  \"free_margin\": " + DoubleToString(AccountFreeMargin(), 2) + ",\n";
   json += "  \"leverage\": " + IntegerToString(AccountLeverage()) + ",\n";
   json += "  \"asian_high\": " + DoubleToString(StoredAsianHigh, Digits) + ",\n";
   json += "  \"asian_low\": " + DoubleToString(StoredAsianLow, Digits) + ",\n";
   json += "  \"atr_m15_pips\": " + DoubleToString(atrPips, 1) + ",\n";
   json += "  \"smt_symbol\": \"" + CrossAssetSmtSymbol + "\",\n";
   json += "  \"smt_bid\": " + DoubleToString(smtBid, Digits) + ",\n";
   json += "  \"smt_ask\": " + DoubleToString(smtAsk, Digits) + ",\n";
   
   // Export Recent 20 M5 Bars for Python Pattern & FVG Detection
   json += "  \"bars_m5\": [\n";
   for(int b = 19; b >= 0; b--)
   {
      json += "    {\"open\": " + DoubleToString(iOpen(Symbol(), PERIOD_M5, b), Digits) + 
              ", \"high\": " + DoubleToString(iHigh(Symbol(), PERIOD_M5, b), Digits) + 
              ", \"low\": " + DoubleToString(iLow(Symbol(), PERIOD_M5, b), Digits) + 
              ", \"close\": " + DoubleToString(iClose(Symbol(), PERIOD_M5, b), Digits) + 
              ", \"time\": \"" + TimeToString(iTime(Symbol(), PERIOD_M5, b), TIME_DATE|TIME_MINUTES) + "\"}";
      if(b > 0) json += ",\n";
      else json += "\n";
   }
   json += "  ],\n";
   
   // Export Recent 10 SMT M5 Bars for Divergence Analysis
   json += "  \"smt_bars\": [\n";
   if(CrossAssetSmtSymbol != "")
   {
      for(int s = 9; s >= 0; s--)
      {
         json += "    {\"open\": " + DoubleToString(iOpen(CrossAssetSmtSymbol, PERIOD_M5, s), Digits) + 
                 ", \"high\": " + DoubleToString(iHigh(CrossAssetSmtSymbol, PERIOD_M5, s), Digits) + 
                 ", \"low\": " + DoubleToString(iLow(CrossAssetSmtSymbol, PERIOD_M5, s), Digits) + 
                 ", \"close\": " + DoubleToString(iClose(CrossAssetSmtSymbol, PERIOD_M5, s), Digits) + "}";
         if(s > 0) json += ",\n";
         else json += "\n";
      }
   }
   json += "  ]\n";
   json += "}\n";
   
   int handle = FileOpen(MarketStateFileName, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, json);
      FileClose(handle);
   }
}

//+------------------------------------------------------------------+
//| Expert Tick Function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   CheckFridaySunsetCut();
   ReadAiSentinel();
   ExportMarketState(false);
   ManageOpenPositions();
}
//+------------------------------------------------------------------+
