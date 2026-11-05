//+------------------------------------------------------------------+
//|                                        EurUsdSniper_Tester.mq4   |
//|                          Copyright 2026, Pure ICT Quant AI Engine |
//|          EURUSD Institutional Pure ICT Strategy Tester Engine     |
//|         [Full Native MQL4 ICT Logic • Backtest & Live Ready]      |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Pure ICT Quant AI Engine"
#property link      "https://github.com/eurusd-sniper-institutional"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input string          Header_Master           = "=== EURUSD PURE ICT STRATEGY TESTER ===";
input double          EquityRiskPercent       = 1.5;            // Risk per Trade (% of Account Equity)
input double          MaxSpreadPips           = 5.0;            // Max Allowed Spread (Pips - 5.0 for Tester)
input int             MagicNumber             = 777200;         // Magic Number
input string          OrderCommentTag         = "EURUSD_ICT_Tester";

input string          Header_Sessions         = "=== ICT TIME & SESSIONS (UTC / SERVER) ===";
input int             AsianStartHour          = 0;              // Asian Range Start (00:00 UTC)
input int             AsianEndHour            = 6;              // Asian Range End (06:00 UTC)
input int             LondonStartHour         = 7;              // London Killzone Start (07:00 UTC)
input int             LondonEndHour           = 11;             // London Killzone End (11:00 UTC)
input int             NYStartHour             = 12;             // New York Killzone Start (12:00 UTC)
input int             NYEndHour               = 16;             // New York Killzone End (16:00 UTC)

input string          Header_ICT_Rules        = "=== PURE ICT PATTERN RULES ===";
input double          MinSweepPips            = 3.5;            // Minimum Penetration beyond Liquidity (Pips)
input double          MinBodyRatio            = 0.55;           // Minimum Candle Body Ratio (55% Displacement)
input double          MinRR_Ratio             = 2.50;           // Minimum Risk/Reward Ratio (1:2.5 Target)
input double          StopLossBufferPips      = 2.5;            // Stop Loss Buffer beyond Sweep Wick (Pips)
input double          MinStopLossPips         = 8.0;            // Minimum Stop Loss (Pips)
input double          MaxStopLossPips         = 25.0;           // Maximum Stop Loss (Pips)

input string          Header_Protection       = "=== RISK & TRADE PROTECTION ===";
input bool            EnableBreakeven         = true;           // Move SL to Breakeven (+0.5 pip) at 1.5R
input double          BE_Trigger_R            = 1.50;           // Breakeven Profit Trigger (R:R)
input bool            EnableDynamicTrail      = true;           // Dynamic Trailing Stop past 2.0R
input double          TrailDistance_R         = 1.25;           // Trailing distance behind price (R:R)
input bool            FridaySunsetCut         = true;           // Close Intraday Trades on Friday 21:00 UTC
input int             FridaySunsetCutHour     = 21;             // Friday Auto-Close Hour (21:00 UTC)

//+------------------------------------------------------------------+
//| Global Internal Variables                                        |
//+------------------------------------------------------------------+
datetime LastBarTime           = 0;
datetime LastAsianDay          = 0;
double   AsianHigh             = 0.0;
double   AsianLow              = 0.0;
bool     AsianCalibrated       = false;

bool     LondonSweptLow        = false;
bool     LondonSweptHigh       = false;
double   SweepExtremePrice     = 0.0;
datetime SweepTime             = 0;

int      DailyTradesCount      = 0;
datetime CurrentTradingDay     = 0;

//+------------------------------------------------------------------+
//| Helpers: Pips & Points                                           |
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
   Print(" [EURUSD PURE ICT TESTER v1.00] Initialized on ", Symbol(), " Period: ", Period());
   Print(" Account Equity: $", DoubleToStr(AccountEquity(), 2), " | Broker Leverage: 1:", AccountLeverage());
   Print(" Equity Risk: ", EquityRiskPercent, "% | Min Sweep: ", MinSweepPips, " pips | Min RR: 1:", MinRR_Ratio);
   Print("================================================================================");
   
   LastBarTime = 0;
   LastAsianDay = 0;
   AsianHigh = 0.0;
   AsianLow = 0.0;
   AsianCalibrated = false;
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert Deinitialization                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("[EURUSD PURE ICT TESTER] Deinitialized. Total Session Trades: ", DailyTradesCount);
}

//+------------------------------------------------------------------+
//| Calculate Asian Range (00:00 - 06:00 UTC)                        |
//+------------------------------------------------------------------+
void CalculateAsianRange()
{
   datetime currentServerTime = TimeCurrent();
   datetime todayMidnight = StringToTime(TimeToStr(currentServerTime, TIME_DATE));
   
   if(todayMidnight != LastAsianDay)
   {
      LastAsianDay = todayMidnight;
      AsianHigh = 0.0;
      AsianLow = 0.0;
      AsianCalibrated = false;
      LondonSweptLow = false;
      LondonSweptHigh = false;
      DailyTradesCount = 0;
   }
   
   MqlDateTime dt;
   TimeToStruct(currentServerTime, dt);
   
   // If during Asian Session, continually track highs and lows
   if(dt.hour >= AsianStartHour && dt.hour < AsianEndHour)
   {
      double h = iHigh(Symbol(), PERIOD_M5, 1);
      double l = iLow(Symbol(), PERIOD_M5, 1);
      if(AsianHigh == 0.0 || h > AsianHigh) AsianHigh = h;
      if(AsianLow == 0.0 || l < AsianLow) AsianLow = l;
   }
   else if(dt.hour >= AsianEndHour && !AsianCalibrated)
   {
      // Finalize Asian Range after 06:00
      datetime asianStart = todayMidnight + (AsianStartHour * 3600);
      datetime asianEnd   = todayMidnight + (AsianEndHour * 3600);
      
      int startIdx = iBarShift(Symbol(), PERIOD_M15, asianStart);
      int endIdx   = iBarShift(Symbol(), PERIOD_M15, asianEnd);
      
      if(startIdx >= endIdx && endIdx >= 0)
      {
         int count = startIdx - endIdx + 1;
         int hiIdx = iHighest(Symbol(), PERIOD_M15, MODE_HIGH, count, endIdx);
         int loIdx = iLowest(Symbol(), PERIOD_M15, MODE_LOW, count, endIdx);
         if(hiIdx >= 0 && loIdx >= 0)
         {
            AsianHigh = iHigh(Symbol(), PERIOD_M15, hiIdx);
            AsianLow  = iLow(Symbol(), PERIOD_M15, loIdx);
            AsianCalibrated = true;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check Liquidity Sweep of Asian Range                             |
//+------------------------------------------------------------------+
void CheckLiquiditySweeps()
{
   if(AsianHigh <= 0.0 || AsianLow <= 0.0) return;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Sweep checks active during London Open & NY Killzones
   bool inKillzone = (dt.hour >= LondonStartHour && dt.hour < LondonEndHour) ||
                     (dt.hour >= NYStartHour && dt.hour < NYEndHour);
   if(!inKillzone) return;
   
   double barHigh = iHigh(Symbol(), PERIOD_M5, 1);
   double barLow  = iLow(Symbol(), PERIOD_M5, 1);
   double barClose = iClose(Symbol(), PERIOD_M5, 1);
   
   double minSweepDist = PipsToPoints(MinSweepPips);
   
   // 1. Sell-Side Liquidity (SSL) Sweep below Asian Low
   if(!LondonSweptLow && barLow <= (AsianLow - minSweepDist))
   {
      // Must reject back up (Close above low with lower wick)
      if(barClose > barLow)
      {
         LondonSweptLow = true;
         SweepExtremePrice = barLow;
         SweepTime = TimeCurrent();
         Print("[ICT SWEEP DETECTED] Sell-Side Liquidity Swept! Low: ", barLow, " AsianLow: ", AsianLow);
      }
   }
   
   // 2. Buy-Side Liquidity (BSL) Sweep above Asian High
   if(!LondonSweptHigh && barHigh >= (AsianHigh + minSweepDist))
   {
      if(barClose < barHigh)
      {
         LondonSweptHigh = true;
         SweepExtremePrice = barHigh;
         SweepTime = TimeCurrent();
         Print("[ICT SWEEP DETECTED] Buy-Side Liquidity Swept! High: ", barHigh, " AsianHigh: ", AsianHigh);
      }
   }
}

//+------------------------------------------------------------------+
//| Detect Displacement & Fair Value Gap (FVG) on M5                 |
//+------------------------------------------------------------------+
void CheckIctTradeSetups()
{
   if(!LondonSweptLow && !LondonSweptHigh) return;
   if(DailyTradesCount >= 3) return; // Max 3 trades per day
   
   // Check active open orders
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
            return; // Only 1 active ICT trade at a time
      }
   }
   
   // Check Spread
   double spreadPips = PointsToPips(MarketInfo(Symbol(), MODE_SPREAD) * Point);
   if(spreadPips > MaxSpreadPips) return;
   
   // Recent 3 candles for FVG:
   // Candle 1: bar 3, Candle 2 (Displacement): bar 2, Candle 3: bar 1
   double c1_high = iHigh(Symbol(), PERIOD_M5, 3);
   double c1_low  = iLow(Symbol(), PERIOD_M5, 3);
   
   double c2_open = iOpen(Symbol(), PERIOD_M5, 2);
   double c2_high = iHigh(Symbol(), PERIOD_M5, 2);
   double c2_low  = iLow(Symbol(), PERIOD_M5, 2);
   double c2_close = iClose(Symbol(), PERIOD_M5, 2);
   
   double c3_high = iHigh(Symbol(), PERIOD_M5, 1);
   double c3_low  = iLow(Symbol(), PERIOD_M5, 1);
   
   // Displacement quality check on Candle 2
   double c2_range = c2_high - c2_low;
   if(c2_range <= 0) return;
   double c2_body = MathAbs(c2_close - c2_open);
   double bodyRatio = c2_body / c2_range;
   if(bodyRatio < MinBodyRatio) return;
   
   // -------------------------------------------------------------
   // CASE A: BULLISH ICT SETUP (Swept Low -> Bullish FVG -> BUY)
   // -------------------------------------------------------------
   if(LondonSweptLow && c2_close > c2_open)
   {
      // Bullish FVG (BISI): Candle 3 Low > Candle 1 High
      if(c3_low > c1_high)
      {
         double gapPips = PointsToPips(c3_low - c1_high);
         if(gapPips >= 1.0)
         {
            double fvgCE = (c3_low + c1_high) / 2.0; // Consequent Encroachment (50%)
            double currentBid = Bid;
            
            // Retracement into FVG zone (price touches or enters the gap)
            if(currentBid <= c3_low && currentBid >= c1_high - PipsToPoints(2.0))
            {
               double entryPrice = Ask;
               double slPrice = NormalizeDouble(SweepExtremePrice - PipsToPoints(StopLossBufferPips), Digits);
               double slPips = PointsToPips(entryPrice - slPrice);
               
               if(slPips >= MinStopLossPips && slPips <= MaxStopLossPips)
               {
                  // Target opposing Asian High or 1:2.5+ RR
                  double targetPips = PointsToPips(AsianHigh - entryPrice);
                  double minTargetPips = slPips * MinRR_Ratio;
                  double tpPrice = 0.0;
                  
                  if(targetPips >= minTargetPips)
                     tpPrice = NormalizeDouble(AsianHigh, Digits);
                  else
                     tpPrice = NormalizeDouble(entryPrice + PipsToPoints(minTargetPips), Digits);
                  
                  ExecuteOrder(OP_BUY, entryPrice, slPrice, tpPrice, slPips);
                  LondonSweptLow = false; // Reset setup
               }
            }
         }
      }
   }
   
   // -------------------------------------------------------------
   // CASE B: BEARISH ICT SETUP (Swept High -> Bearish FVG -> SELL)
   // -------------------------------------------------------------
   if(LondonSweptHigh && c2_close < c2_open)
   {
      // Bearish FVG (SIBI): Candle 1 Low > Candle 3 High
      if(c1_low > c3_high)
      {
         double gapPips = PointsToPips(c1_low - c3_high);
         if(gapPips >= 1.0)
         {
            double fvgCE = (c1_low + c3_high) / 2.0; // Consequent Encroachment (50%)
            double currentAsk = Ask;
            
            // Retracement into FVG zone
            if(currentAsk >= c3_high && currentAsk <= c1_low + PipsToPoints(2.0))
            {
               double entryPrice = Bid;
               double slPrice = NormalizeDouble(SweepExtremePrice + PipsToPoints(StopLossBufferPips), Digits);
               double slPips = PointsToPips(slPrice - entryPrice);
               
               if(slPips >= MinStopLossPips && slPips <= MaxStopLossPips)
               {
                  double targetPips = PointsToPips(entryPrice - AsianLow);
                  double minTargetPips = slPips * MinRR_Ratio;
                  double tpPrice = 0.0;
                  
                  if(targetPips >= minTargetPips)
                     tpPrice = NormalizeDouble(AsianLow, Digits);
                  else
                     tpPrice = NormalizeDouble(entryPrice - PipsToPoints(minTargetPips), Digits);
                  
                  ExecuteOrder(OP_SELL, entryPrice, slPrice, tpPrice, slPips);
                  LondonSweptHigh = false; // Reset setup
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Execute Order with Dynamic Equity Risk Calculation (XM 1:1000)   |
//+------------------------------------------------------------------+
void ExecuteOrder(int cmd, double entryPrice, double slPrice, double tpPrice, double slPips)
{
   double riskMoney = AccountEquity() * (EquityRiskPercent / 100.0);
   double slDistancePoints = MathAbs(entryPrice - slPrice) / Point;
   double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
   if(tickValue <= 0) tickValue = 1.0;
   
   double calculatedLot = riskMoney / (slDistancePoints * tickValue);
   
   // Normalization
   double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   
   calculatedLot = MathFloor(calculatedLot / lotStep) * lotStep;
   if(calculatedLot < minLot) calculatedLot = minLot;
   if(calculatedLot > maxLot) calculatedLot = maxLot;
   
   color clr = (cmd == OP_BUY) ? clrDodgerBlue : clrCrimson;
   int ticket = OrderSend(Symbol(), cmd, calculatedLot, entryPrice, 3, slPrice, tpPrice, OrderCommentTag, MagicNumber, 0, clr);
   
   if(ticket > 0)
   {
      DailyTradesCount++;
      Print("[ICT EXECUTION] Ticket #", ticket, " ", (cmd == OP_BUY ? "BUY" : "SELL"),
            " Lots: ", calculatedLot, " at ", entryPrice, " SL: ", slPrice, " (", slPips, " pips) TP: ", tpPrice);
   }
   else
   {
      Print("[ICT EXECUTION ERROR] OrderSend failed with error code: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Manage Open Orders: Breakeven & Dynamic Trailing                 |
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
      
      // BUY Trade
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
      
      // SELL Trade
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
//| Check Friday Sunset Cut                                          |
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
//| Expert Tick Function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   CheckFridaySunsetCut();
   CalculateAsianRange();
   CheckLiquiditySweeps();
   
   // Execute pattern check on new bar (M5 / M15)
   datetime currentBarTime = iTime(Symbol(), PERIOD_M5, 0);
   if(currentBarTime != LastBarTime)
   {
      LastBarTime = currentBarTime;
      CheckIctTradeSetups();
   }
   
   ManageOpenPositions();
}
//+------------------------------------------------------------------+
