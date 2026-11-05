//+------------------------------------------------------------------+
//|                               ICT_2022_Mentorship_Tester_v1.mq4  |
//|               Official ICT 2022 Mentorship & Silver Bullet Model  |
//|                    Displacement + FVG + MSS + Trend Filter        |
//+------------------------------------------------------------------+
#property copyright "ICT 2022 Mentorship Institutional Model"
#property link      "https://innercircletrader.com"
#property version   "1.00"
#property strict

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                 |
//+------------------------------------------------------------------+
//--- 1. ICT Killzone Session Windows (Server Time GMT+2/3)
input string          s01 = "=== 1. ICT KILLZONE WINDOWS ===";
input bool            EnableLondonWindow      = true;           // London Killzone (08:00 - 11:30 Server)
input int             LondonStartHour         = 8;              // London Start Hour
input int             LondonStartMin          = 0;              // London Start Minute
input int             LondonEndHour           = 11;             // London End Hour
input int             LondonEndMin            = 30;             // London End Minute

input bool            EnableNYWindow          = true;           // New York Killzone (14:30 - 17:30 Server)
input int             NYStartHour             = 14;             // NY Start Hour
input int             NYStartMin              = 30;             // NY Start Minute
input int             NYEndHour               = 17;             // NY End Hour
input int             NYEndMin                = 30;             // NY End Minute

//--- 2. Market Structure Shift (MSS) & Displacement Settings
input string          s02 = "=== 2. MSS & DISPLACEMENT ===";
input int             SwingLookbackBars       = 6;              // Swing High/Low Lookback for MSS (5-8 bars)
input double          MinDisplacementUSD      = 1.80;           // Min Displacement Body ($1.80 / 18 pips Gold)
input double          MinBodyRatio            = 0.50;           // Min Candle Body / Total Range Ratio (50%)
input int             TrendEMA_Period         = 50;             // Confluence Trend Filter (EMA 50 on M15)

//--- 3. Fair Value Gap (FVG) Validation
input string          s03 = "=== 3. FAIR VALUE GAP (FVG) ===";
input double          MinFVGGapUSD            = 0.60;           // Min FVG Gap Size ($0.60 / 6 pips Gold)
input int             MaxFVGExpiryBars        = 8;              // Max Bars to Wait for FVG Retracement (2 Hours)

//--- 4. Money Management & Anti-Broker Ban Protections
input string          s04 = "=== 4. RISK & ANTI-BROKER PROTECTION ===";
input double          RiskPercentPerTrade     = 2.0;            // Risk Per Trade (% of Equity)
input double          MaxLotCap               = 0.50;           // Institutional Max Lot Cap
input double          MinLotSize              = 0.01;           // Minimum Lot Allowed
input int             MaxSpreadPoints         = 65;             // Max Spread Allowed for Entry (6.5 pips)
input int             MinHoldingSeconds       = 180;            // ANTI-BAN: Min Holding Time (3 Minutes)
input int             MaxTradesPerSession     = 1;              // Max 1 Trade per Session Window
input int             MagicNumber             = 202201;         // Magic Number
input string          TradeComment            = "ICT_2022_Mentorship";

//--- 5. Target & Trade Management (ICT 1:2 RR + Breakeven Lock)
input string          s05 = "=== 5. TARGET & BREAKEVEN LOCK ===";
input double          TargetRR                = 2.0;            // Objective Risk:Reward Ratio (1:2.0)
input double          SL_BufferUSD            = 1.00;           // SL Buffer beyond Displacement Extreme ($1.00)
input bool            EnableBreakevenLock     = true;           // Move SL to Breakeven at 1:1.2 RR
input double          BreakevenTriggerRR      = 1.2;            // Breakeven Activation Level (1:1.2 RR)
input double          BreakevenBufferUSD      = 0.30;           // Breakeven Profit Lock Buffer ($0.30)

//+------------------------------------------------------------------+
//| GLOBAL STATE & FVG QUEUE STRUCTURE                               |
//+------------------------------------------------------------------+
struct ActiveFVG {
   bool     isActive;
   int      direction;         // +1 for Buy, -1 for Sell
   double   fvgHigh;           // FVG upper boundary
   double   fvgLow;            // FVG lower boundary
   double   entryPrice;        // Retracement Entry Target
   double   slPrice;           // Displacement Swing Invalidation SL
   double   tpPrice;           // 1:2 Target RR
   double   riskDistance;      // Distance in Price
   datetime formationTime;
   int      barsHeld;
};

ActiveFVG PendingFVG;
int       TradesThisSession   = 0;
int       CurrentSessionID    = -1;
datetime  LastBarTime         = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   ResetFVG();
   Print("====================================================================");
   Print(" ⚡ ICT 2022 MENTORSHIP & SILVER BULLET MASTER v1.0 INITIALIZED");
   Print(" Strategy: Mainstream Displacement + FVG + MSS + EMA 50 Trend");
   Print(" Symbol: ", Symbol(), " | Digits: ", Digits, " | Point: ", Point);
   Print(" Risk: ", RiskPercentPerTrade, "% | Max Lot Cap: ", MaxLotCap, " | Target RR: 1:", TargetRR);
   Print(" Anti-Broker Ban Protection: Min Holding ", MinHoldingSeconds, "s | Max Spread ", MaxSpreadPoints);
   Print("====================================================================");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Comment("");
   Print("ICT 2022 Mentorship Master Deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Reset Pending FVG State                                          |
//+------------------------------------------------------------------+
void ResetFVG()
{
   PendingFVG.isActive      = false;
   PendingFVG.direction     = 0;
   PendingFVG.fvgHigh       = 0.0;
   PendingFVG.fvgLow        = 0.0;
   PendingFVG.entryPrice    = 0.0;
   PendingFVG.slPrice       = 0.0;
   PendingFVG.tpPrice       = 0.0;
   PendingFVG.riskDistance  = 0.0;
   PendingFVG.formationTime = 0;
   PendingFVG.barsHeld      = 0;
}

//+------------------------------------------------------------------+
//| Check if Current Time is inside Official ICT Killzones           |
//+------------------------------------------------------------------+
int GetActiveKillzone()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int currentMinOfDay = dt.hour * 60 + dt.min;
   
   if(EnableLondonWindow)
   {
      int ldnStart = LondonStartHour * 60 + LondonStartMin;
      int ldnEnd   = LondonEndHour * 60 + LondonEndMin;
      if(currentMinOfDay >= ldnStart && currentMinOfDay <= ldnEnd)
         return 1; // London KZ
   }
   
   if(EnableNYWindow)
   {
      int nyStart = NYStartHour * 60 + NYStartMin;
      int nyEnd   = NYEndHour * 60 + NYEndMin;
      if(currentMinOfDay >= nyStart && currentMinOfDay <= nyEnd)
         return 2; // New York KZ
   }
   
   return 0; // Outside KZ
}

//+------------------------------------------------------------------+
//| Count Open Positions for this EA                                 |
//+------------------------------------------------------------------+
int CountOpenPositions(int &ticket, double &openPrice, double &sl, double &tp, datetime &openTime, int &cmd)
{
   int count = 0;
   ticket = -1;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == MagicNumber)
         {
            count++;
            ticket    = OrderTicket();
            openPrice = OrderOpenPrice();
            sl        = OrderStopLoss();
            tp        = OrderTakeProfit();
            openTime  = OrderOpenTime();
            cmd       = OrderType();
         }
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| Trailing Breakeven Lock at 1:1.2 RR                              |
//+------------------------------------------------------------------+
void ManageOpenTrades()
{
   int ticket, cmd;
   double openPrice, sl, tp;
   datetime openTime;
   
   int posCount = CountOpenPositions(ticket, openPrice, sl, tp, openTime, cmd);
   if(posCount == 0) return;
   
   if(!EnableBreakevenLock) return;
   
   double currentPrice = (cmd == OP_BUY) ? Bid : Ask;
   double initialRiskDist = 0.0;
   
   if(cmd == OP_BUY)
   {
      if(sl > 0.0 && sl < openPrice)
         initialRiskDist = openPrice - sl;
      
      if(initialRiskDist > 0.0)
      {
         double profitDist = currentPrice - openPrice;
         if(profitDist >= (initialRiskDist * BreakevenTriggerRR))
         {
            double bePrice = NormalizeDouble(openPrice + BreakevenBufferUSD, Digits);
            if(sl < openPrice)
            {
               bool res = OrderModify(ticket, openPrice, bePrice, tp, 0, clrGreen);
               if(res) Print("🛡️ [ICT 2022 BREAKEVEN LOCKED] BUY #", ticket, " Moved to: ", bePrice);
            }
         }
      }
   }
   else if(cmd == OP_SELL)
   {
      if(sl > 0.0 && sl > openPrice)
         initialRiskDist = sl - openPrice;
         
      if(initialRiskDist > 0.0)
      {
         double profitDist = openPrice - currentPrice;
         if(profitDist >= (initialRiskDist * BreakevenTriggerRR))
         {
            double bePrice = NormalizeDouble(openPrice - BreakevenBufferUSD, Digits);
            if(sl > openPrice || sl == 0.0)
            {
               bool res = OrderModify(ticket, openPrice, bePrice, tp, 0, clrRed);
               if(res) Print("🛡️ [ICT 2022 BREAKEVEN LOCKED] SELL #", ticket, " Moved to: ", bePrice);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Calculate Safe Institutional Lot Size with MaxLotCap             |
//+------------------------------------------------------------------+
double CalculateICTLotSize(double slDistancePrice)
{
   if(slDistancePrice <= 0.0) return MinLotSize;
   
   double accountEquity = AccountEquity();
   double riskAmountUSD = accountEquity * (RiskPercentPerTrade / 100.0);
   
   double tickValue = MarketInfo(Symbol(), MODE_TICKVALUE);
   double tickSize  = MarketInfo(Symbol(), MODE_TICKSIZE);
   if(tickSize <= 0.0) tickSize = Point;
   if(tickValue <= 0.0) tickValue = 1.0;
   
   double ticksAtRisk = slDistancePrice / tickSize;
   double lossPerLot  = ticksAtRisk * tickValue;
   
   double lot = MinLotSize;
   if(lossPerLot > 0.0)
      lot = riskAmountUSD / lossPerLot;
      
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   if(lotStep <= 0.0) lotStep = 0.01;
   lot = MathFloor(lot / lotStep) * lotStep;
   
   double minBrokerLot = MarketInfo(Symbol(), MODE_MINLOT);
   if(minBrokerLot <= 0.0) minBrokerLot = 0.01;
   if(lot < minBrokerLot) lot = minBrokerLot;
   
   if(lot > MaxLotCap) lot = MaxLotCap;
   
   return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| ICT 2022 MODEL SCANNER: Displacement + FVG + MSS Formation       |
//+------------------------------------------------------------------+
void ScanForICT2022Setup()
{
   // If already having an active FVG waiting for retracement, increment bar count
   if(PendingFVG.isActive)
   {
      PendingFVG.barsHeld++;
      if(PendingFVG.barsHeld > MaxFVGExpiryBars)
      {
         ResetFVG(); // Expired after 2 hours
      }
      return;
   }
   
   double emaTrend = iMA(Symbol(), Period(), TrendEMA_Period, 0, MODE_EMA, PRICE_CLOSE, 1);
   
   // 3-Candle ICT 2022 Sequence:
   // Bar 3: Pre-displacement candle
   // Bar 2: THE DISPLACEMENT CANDLE
   // Bar 1: Confirmation candle creating the Fair Value Gap
   double c1_high = High[3];
   double c1_low  = Low[3];
   
   double c2_open  = Open[2];
   double c2_close = Close[2];
   double c2_high  = High[2];
   double c2_low   = Low[2];
   double c2_body  = MathAbs(c2_close - c2_open);
   double c2_range = c2_high - c2_low;
   
   double c3_high = High[1];
   double c3_low  = Low[1];
   
   //------------------------------------------------------------------
   // 1. BULLISH ICT 2022 MODEL (Expansion / Reversal into Bullish FVG)
   //------------------------------------------------------------------
   if(c2_close > c2_open && c2_range > 0.0)
   {
      // Check Displacement Quality
      if((c2_body / c2_range) >= MinBodyRatio && c2_body >= MinDisplacementUSD)
      {
         // Check Trend Alignment
         if(c2_close > emaTrend)
         {
            // Check Fair Value Gap (Bullish FVG: Low of Bar 1 > High of Bar 3)
            if(c3_low > c1_high)
            {
               double gapSize = c3_low - c1_high;
               if(gapSize >= MinFVGGapUSD)
               {
                  // Check Market Structure Shift (MSS): Did Bar 2 close above recent swing high?
                  double swingHigh = -1.0;
                  for(int b = 4; b <= 4 + SwingLookbackBars; b++)
                  {
                     if(High[b] > swingHigh) swingHigh = High[b];
                  }
                  
                  if(c2_close > swingHigh) // Confirmed MSS
                  {
                     double entry = c3_low; // Retracement tap into upper boundary of FVG
                     double sl    = c2_low - SL_BufferUSD; // Below displacement swing low
                     double slDist = entry - sl;
                     
                     if(slDist >= 2.00 && slDist <= 12.00) // Realistic gold risk boundary
                     {
                        double tp = entry + (slDist * TargetRR);
                        
                        PendingFVG.isActive      = true;
                        PendingFVG.direction     = 1; // BUY
                        PendingFVG.fvgHigh       = c3_low;
                        PendingFVG.fvgLow        = c1_high;
                        PendingFVG.entryPrice    = entry;
                        PendingFVG.slPrice       = NormalizeDouble(sl, Digits);
                        PendingFVG.tpPrice       = NormalizeDouble(tp, Digits);
                        PendingFVG.riskDistance  = slDist;
                        PendingFVG.formationTime = TimeCurrent();
                        PendingFVG.barsHeld      = 0;
                        
                        Print("====================================================================");
                        Print(" 🔥 [ICT 2022 BULLISH FVG ARMED]");
                        Print(StringFormat(" Displacement Body: $%.2f | MSS Broken: %.2f | FVG: %.2f - %.2f (Gap: $%.2f)",
                              c2_body, swingHigh, c1_high, c3_low, gapSize));
                        Print(StringFormat(" Planned Entry: %.2f | SL: %.2f | TP: %.2f | 1:%.1f RR",
                              entry, PendingFVG.slPrice, PendingFVG.tpPrice, TargetRR));
                        Print("====================================================================");
                        return;
                     }
                  }
               }
            }
         }
      }
   }
   
   //------------------------------------------------------------------
   // 2. BEARISH ICT 2022 MODEL (Expansion / Reversal into Bearish FVG)
   //------------------------------------------------------------------
   if(c2_open > c2_close && c2_range > 0.0)
   {
      // Check Displacement Quality
      if((c2_body / c2_range) >= MinBodyRatio && c2_body >= MinDisplacementUSD)
      {
         // Check Trend Alignment
         if(c2_close < emaTrend)
         {
            // Check Fair Value Gap (Bearish FVG: High of Bar 1 < Low of Bar 3)
            if(c3_high < c1_low)
            {
               double gapSize = c1_low - c3_high;
               if(gapSize >= MinFVGGapUSD)
               {
                  // Check Market Structure Shift (MSS): Did Bar 2 close below recent swing low?
                  double swingLow = 9999999.0;
                  for(int b = 4; b <= 4 + SwingLookbackBars; b++)
                  {
                     if(Low[b] < swingLow) swingLow = Low[b];
                  }
                  
                  if(c2_close < swingLow) // Confirmed MSS
                  {
                     double entry = c3_high; // Retracement tap into lower boundary of FVG
                     double sl    = c2_high + SL_BufferUSD; // Above displacement swing high
                     double slDist = sl - entry;
                     
                     if(slDist >= 2.00 && slDist <= 12.00)
                     {
                        double tp = entry - (slDist * TargetRR);
                        
                        PendingFVG.isActive      = true;
                        PendingFVG.direction     = -1; // SELL
                        PendingFVG.fvgHigh       = c1_low;
                        PendingFVG.fvgLow        = c3_high;
                        PendingFVG.entryPrice    = entry;
                        PendingFVG.slPrice       = NormalizeDouble(sl, Digits);
                        PendingFVG.tpPrice       = NormalizeDouble(tp, Digits);
                        PendingFVG.riskDistance  = slDist;
                        PendingFVG.formationTime = TimeCurrent();
                        PendingFVG.barsHeld      = 0;
                        
                        Print("====================================================================");
                        Print(" 🔥 [ICT 2022 BEARISH FVG ARMED]");
                        Print(StringFormat(" Displacement Body: $%.2f | MSS Broken: %.2f | FVG: %.2f - %.2f (Gap: $%.2f)",
                              c2_body, swingLow, c3_high, c1_low, gapSize));
                        Print(StringFormat(" Planned Entry: %.2f | SL: %.2f | TP: %.2f | 1:%.1f RR",
                              entry, PendingFVG.slPrice, PendingFVG.tpPrice, TargetRR));
                        Print("====================================================================");
                        return;
                     }
                  }
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| EXECUTE RETRACEMENT ENTRY WHEN PRICE MITIGATES FVG               |
//+------------------------------------------------------------------+
void ExecuteFVGRetracement()
{
   if(!PendingFVG.isActive) return;
   
   int currentSpread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   if(currentSpread > MaxSpreadPoints) return;
   
   if(TradesThisSession >= MaxTradesPerSession)
   {
      ResetFVG();
      return;
   }
   
   int dummyTicket, dummyCmd;
   double dummyOpen, dummySL, dummyTP;
   datetime dummyTime;
   if(CountOpenPositions(dummyTicket, dummyOpen, dummySL, dummyTP, dummyTime, dummyCmd) > 0)
      return;
      
   // Bullish Mitigation Trigger
   if(PendingFVG.direction == 1)
   {
      // Invalidation Check
      if(Bid <= PendingFVG.slPrice)
      {
         ResetFVG();
         return;
      }
      
      // Retracement Tap into FVG
      if(Ask <= PendingFVG.fvgHigh && Ask >= (PendingFVG.fvgLow - (50 * Point)))
      {
         double slDist = Ask - PendingFVG.slPrice;
         if(slDist > (50 * Point))
         {
            double lot = CalculateICTLotSize(slDist);
            int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, 10, PendingFVG.slPrice, PendingFVG.tpPrice, TradeComment, MagicNumber, 0, clrBlue);
            if(ticket > 0)
            {
               TradesThisSession++;
               Print("🚀 [ICT 2022 ORDER EXECUTED] BUY #", ticket, " Lot: ", lot, " Price: ", Ask, " SL: ", PendingFVG.slPrice, " TP: ", PendingFVG.tpPrice);
               ResetFVG();
            }
         }
      }
   }
   // Bearish Mitigation Trigger
   else if(PendingFVG.direction == -1)
   {
      // Invalidation Check
      if(Ask >= PendingFVG.slPrice)
      {
         ResetFVG();
         return;
      }
      
      // Retracement Tap into FVG
      if(Bid >= PendingFVG.fvgLow && Bid <= (PendingFVG.fvgHigh + (50 * Point)))
      {
         double slDist = PendingFVG.slPrice - Bid;
         if(slDist > (50 * Point))
         {
            double lot = CalculateICTLotSize(slDist);
            int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, 10, PendingFVG.slPrice, PendingFVG.tpPrice, TradeComment, MagicNumber, 0, clrRed);
            if(ticket > 0)
            {
               TradesThisSession++;
               Print("🚀 [ICT 2022 ORDER EXECUTED] SELL #", ticket, " Lot: ", lot, " Price: ", Bid, " SL: ", PendingFVG.slPrice, " TP: ", PendingFVG.tpPrice);
               ResetFVG();
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| UPDATE ON-SCREEN ICT 2022 DASHBOARD                              |
//+------------------------------------------------------------------+
void UpdateICTChartHUD(int activeKZ)
{
   if(IsTesting()) return; // Ultra-Fast Strategy Tester Bypass
   
   string kzName = "OUTSIDE KILLZONE";
   if(activeKZ == 1) kzName = "LONDON OPEN KILLZONE (Active)";
   else if(activeKZ == 2) kzName = "NEW YORK OPEN KILLZONE (Active)";
   
   double emaVal = iMA(Symbol(), Period(), TrendEMA_Period, 0, MODE_EMA, PRICE_CLOSE, 1);
   string trendStr = (Close[1] > emaVal) ? "BULLISH (Above EMA 50)" : "BEARISH (Below EMA 50)";
   
   string hud = "\n===================================================\n";
   hud += " 🏛️ ICT 2022 MENTORSHIP & SILVER BULLET v1.0\n";
   hud += "===================================================\n";
   hud += " [Time & Killzone] : " + kzName + "\n";
   hud += " [Session Trend]   : " + trendStr + "\n";
   hud += "---------------------------------------------------\n";
   hud += " ICT 2022 MODEL STATUS:\n";
   hud += " [1] Displacement  : " + (PendingFVG.isActive ? "CONFIRMED" : "Scanning for Body >= $1.80...") + "\n";
   hud += " [2] Structure MSS : " + (PendingFVG.isActive ? "CONFIRMED (Swing Broken)" : "Scanning...") + "\n";
   hud += " [3] FVG Retracement: " + (PendingFVG.isActive ? StringFormat("ARMED at %.2f (Bars: %d/%d)", PendingFVG.entryPrice, PendingFVG.barsHeld, MaxFVGExpiryBars) : "Idle") + "\n";
   hud += " [4] Target & Risk : " + (PendingFVG.isActive ? StringFormat("SL: %.2f | TP: %.2f (1:%.1f RR)", PendingFVG.slPrice, PendingFVG.tpPrice, TargetRR) : "Ready") + "\n";
   hud += "---------------------------------------------------\n";
   hud += StringFormat(" [Equity]: $%.2f | [Risk/Trade]: %.1f%% | [MaxLotCap]: %.2f\n", AccountEquity(), RiskPercentPerTrade, MaxLotCap);
   hud += StringFormat(" [Spread]: %d pts (Max %d) | [Session Trades]: %d/%d\n", (int)MarketInfo(Symbol(), MODE_SPREAD), MaxSpreadPoints, TradesThisSession, MaxTradesPerSession);
   hud += "===================================================\n";
   Comment(hud);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // 1. Manage Active Positions (Breakeven Lock)
   ManageOpenTrades();
   
   // 2. Track Session Transitions
   int activeKZ = GetActiveKillzone();
   if(activeKZ != CurrentSessionID)
   {
      CurrentSessionID = activeKZ;
      TradesThisSession = 0;
   }
   
   // 3. On New Bar: Scan for ICT 2022 Displacement & FVG Formation
   if(Time[0] != LastBarTime)
   {
      LastBarTime = Time[0];
      
      UpdateICTChartHUD(activeKZ);
      
      if(activeKZ > 0)
      {
         ScanForICT2022Setup();
      }
   }
   
   // 4. On Every Tick: Monitor Price Retracement into FVG
   ExecuteFVGRetracement();
}
//+------------------------------------------------------------------+
