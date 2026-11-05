//+------------------------------------------------------------------+
//|                                     Pure_ICT_Tester_v1.mq4       |
//|                    Institutional ICT Precision Engine             |
//|                 OrderBlock, OrderFlow, MSS, CHoCH, FVG, OTE       |
//|                 High-Speed Multi-Timeframe 1H & 4H Architecture   |
//+------------------------------------------------------------------+
#property copyright "Pure ICT Institutional Tester"
#property link      "https://innercircletrader.com"
#property version   "1.20"
#property strict

//+------------------------------------------------------------------+
//| INPUT PARAMETERS                                                 |
//+------------------------------------------------------------------+
//--- 0. Multi-Timeframe HTF (1H & 4H) Structure Alignment Gate
input string          s00 = "=== 0. HTF (1H & 4H) TOP-DOWN BIAS ===";
input bool            EnableHTFFilter         = true;           // Require HTF (1H & 4H) Orderflow Alignment
input bool            RequireH4Alignment      = true;           // Require 4H Orderflow Alignment (BOS/Orderflow)
input bool            RequireH1Alignment      = true;           // Require 1H Orderflow Alignment (BOS/Orderflow)
input int             H4_LookbackBars         = 12;             // 4H Structure Lookback (12 bars = 48 hours)
input int             H1_LookbackBars         = 16;             // 1H Structure Lookback (16 bars = 16 hours)

//--- 1. Killzone Session Timing (Server Time GMT+2/3)
input string          s01 = "=== 1. ICT KILLZONES ===";
input bool            EnableLondonKZ          = true;           // London Open Killzone (08:00 - 11:30 Server)
input int             LondonKZ_StartHour      = 8;              // London Killzone Start Hour
input int             LondonKZ_StartMin       = 0;              // London Killzone Start Minute
input int             LondonKZ_EndHour        = 11;             // London Killzone End Hour
input int             LondonKZ_EndMin         = 30;             // London Killzone End Minute

input bool            EnableNYKZ              = true;           // New York Open Killzone (14:30 - 17:30 Server)
input int             NYKZ_StartHour          = 14;             // NY Killzone Start Hour
input int             NYKZ_StartMin           = 30;             // NY Killzone Start Minute
input int             NYKZ_EndHour            = 17;             // NY Killzone End Hour
input int             NYKZ_EndMin             = 30;             // NY Killzone End Minute

//--- 2. Asian Range Liquidity Reference (BSL / SSL)
input string          s02 = "=== 2. ASIAN LIQUIDITY REFERENCE ===";
input int             AsianRange_StartHour    = 0;              // Asian Range Start Hour (00:00)
input int             AsianRange_EndHour      = 7;              // Asian Range End Hour (07:00)
input double          MinSweepPoints          = 100.0;          // Min Liquidity Sweep Depth (10.0 pips / $1.00 Gold)
input double          MaxSweepPoints          = 900.0;          // Max Liquidity Sweep Depth (90.0 pips / $9.00 Gold)

//--- 3. Market Structure Shift (MSS / CHoCH) & Displacement
input string          s03 = "=== 3. MSS & DISPLACEMENT CHECKLIST ===";
input int             StructureLookbackBars   = 15;             // Bars to find Swing High/Low for MSS
input double          MinDisplacementATR      = 0.85;           // Min Displacement Body vs ATR(14) (Balanced Institutional)
input double          MinBodyToRangeRatio     = 0.50;           // Min Candle Body / Total Range Ratio (Displacement Candle)

//--- 4. Fair Value Gap (FVG) & Order Block (OB)
input string          s04 = "=== 4. FVG & ORDER BLOCK VALIDATION ===";
input double          MinFVGPoints            = 80.0;           // Minimum Fair Value Gap Size (8.0 pips / $0.80 Gold)
input bool            RequireUnmitigatedOB    = true;           // Require Order Block to be Fresh (Unmitigated)
input int             MaxSetupHoldingBars     = 16;             // Max Bars (4 Hours) to Wait for FVG Retracement

//--- 5. Premium / Discount Equilibrium (Fibonacci OTE)
input string          s05 = "=== 5. EQUILIBRIUM & OTE FILTER ===";
input bool            EnforceDiscountBuyOnly  = true;           // Strict ICT Law: ONLY Buy in Discount (< 50% Equilibrium)
input bool            EnforcePremiumSellOnly  = true;           // Strict ICT Law: ONLY Sell in Premium (> 50% Equilibrium)

//--- 6. Money Management & Anti-Broker Ban Protections
input string          s06 = "=== 6. RISK & ANTI-BROKER PROTECTION ===";
input double          RiskPercentPerTrade     = 2.0;            // Risk Per Trade (% of Equity)
input double          MaxLotCap               = 0.50;           // INSTITUTIONAL CAP: Maximum Lot Size Allowed
input double          MinLotSize              = 0.01;           // Minimum Lot Size Allowed
input int             MaxSpreadPoints         = 65;             // Max Spread Allowed for Entry (6.5 pips)
input int             MinHoldingSeconds       = 180;            // ANTI-BAN: Minimum Holding Time (3 Minutes - No HFT Flag)
input int             MaxTradesPerSession     = 1;              // Max 1 Trade per Killzone (No Overtrading)
input int             MagicNumber             = 777108;         // Magic Number
input string          TradeComment            = "Pure_ICT_Master";

//--- 7. Target Management (RR & Liquidity Target)
input string          s07 = "=== 7. RR & TARGET MANAGEMENT ===";
input double          MinTargetRR             = 2.0;            // Minimum Risk:Reward Ratio (1:2.0)
input double          SL_BufferPoints         = 100.0;          // SL Buffer beyond OB / Sweep Low (10.0 pips / $1.00)
input bool            EnableBreakeven         = true;           // Move SL to Breakeven at 1:1.5 RR
input double          BreakevenTriggerRR      = 1.5;            // Breakeven Activation RR

//+------------------------------------------------------------------+
//| GLOBAL STATE & SPEED-CACHED VARIABLES                            |
//+------------------------------------------------------------------+
datetime LastAsianCalculationDate = 0;
double   AsianBSL_High            = 0.0;    // Buy-Side Liquidity (Asian High)
double   AsianSSL_Low             = 0.0;    // Sell-Side Liquidity (Asian Low)

// Cached Multi-Timeframe Biases (Computed ONCE per New Bar for ultra-fast speed)
int      Cached_H4_Bias           = 0;
int      Cached_H1_Bias           = 0;

// Checklist Tracking Flags for the Current Killzone
bool     BullishSweepConfirmed    = false;
double   BullishSweepExtremeLow   = 0.0;
datetime BullishSweepTime         = 0;

bool     BearishSweepConfirmed    = false;
double   BearishSweepExtremeHigh  = 0.0;
datetime BearishSweepTime         = 0;

// Setup Structure Definition
struct ICT_Setup {
   bool     isValid;
   int      direction;         // +1 for Buy, -1 for Sell
   double   sweepExtreme;      // Lowest point of sweep or Highest point of sweep
   double   mssLevel;          // Broken structure price
   double   displacementHigh;  // High of displacement leg
   double   displacementLow;   // Low of displacement leg
   double   equilibrium50;     // 50% Fib level
   double   fvgHigh;           // FVG upper boundary
   double   fvgLow;            // FVG lower boundary
   double   obHigh;            // Order Block High
   double   obLow;             // Order Block Low
   double   entryPrice;        // Limit/Market Trigger Price
   double   slPrice;           // Invalidating Stop Loss
   double   tpPrice;           // Objective Take Profit
   datetime setupTime;
   int      armedBarCount;
};

ICT_Setup CurrentSetup;
int       TradesTakenThisSession  = 0;
int       CurrentSessionID        = -1; // 1 = London, 2 = NY
datetime  LastBarTime             = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   ResetSetup();
   Print("====================================================================");
   Print(" ⚡ PURE ICT INSTITUTIONAL MASTER v1.2 INITIALIZED (ULTRA-FAST SPEED)");
   Print(" Symbol: ", Symbol(), " | Digits: ", Digits, " | Point: ", Point);
   Print(" Risk: ", RiskPercentPerTrade, "% | Max Lot Cap: ", MaxLotCap);
   Print(" HTF Gate: 4H Active: ", RequireH4Alignment, " | 1H Active: ", RequireH1Alignment);
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
   Print("Pure ICT Institutional Tester v1.2 Deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Reset Active Setup State                                         |
//+------------------------------------------------------------------+
void ResetSetup()
{
   CurrentSetup.isValid           = false;
   CurrentSetup.direction         = 0;
   CurrentSetup.sweepExtreme      = 0.0;
   CurrentSetup.mssLevel          = 0.0;
   CurrentSetup.displacementHigh  = 0.0;
   CurrentSetup.displacementLow   = 0.0;
   CurrentSetup.equilibrium50     = 0.0;
   CurrentSetup.fvgHigh           = 0.0;
   CurrentSetup.fvgLow            = 0.0;
   CurrentSetup.obHigh            = 0.0;
   CurrentSetup.obLow             = 0.0;
   CurrentSetup.entryPrice        = 0.0;
   CurrentSetup.slPrice           = 0.0;
   CurrentSetup.tpPrice           = 0.0;
   CurrentSetup.setupTime         = 0;
   CurrentSetup.armedBarCount     = 0;
}

//+------------------------------------------------------------------+
//| STEP 0: HTF (1H & 4H) STRUCTURE & ORDERFLOW EVALUATOR            |
//| Returns: +1 for Bullish, -1 for Bearish, 0 for Neutral           |
//+------------------------------------------------------------------+
int GetHTFStructureBias(int tf, int lookbackBars)
{
   double swingHigh1 = -1.0, swingHigh2 = -1.0;
   double swingLow1  = 9999999.0, swingLow2 = 9999999.0;
   int shCount = 0, slCount = 0;
   
   for(int b = 2; b <= lookbackBars; b++)
   {
      double h = iHigh(Symbol(), tf, b);
      double l = iLow(Symbol(), tf, b);
      
      // Swing High: higher than left and right
      if(h > iHigh(Symbol(), tf, b+1) && h > iHigh(Symbol(), tf, b-1))
      {
         if(shCount == 0)      { swingHigh1 = h; shCount++; }
         else if(shCount == 1) { swingHigh2 = h; shCount++; }
      }
      
      // Swing Low: lower than left and right
      if(l < iLow(Symbol(), tf, b+1) && l < iLow(Symbol(), tf, b-1))
      {
         if(slCount == 0)      { swingLow1 = l; slCount++; }
         else if(slCount == 1) { swingLow2 = l; slCount++; }
      }
      
      if(shCount >= 2 && slCount >= 2) break;
   }
   
   double curClose = iClose(Symbol(), tf, 1);
   
   // 1. Bullish Structure / BOS: Price closed above recent Swing High OR Higher Highs + Higher Lows
   if(curClose > swingHigh1 || (swingHigh1 > swingHigh2 && swingLow1 > swingLow2))
      return 1;
      
   // 2. Bearish Structure / BOS: Price closed below recent Swing Low OR Lower Lows + Lower Highs
   if(curClose < swingLow1 || (swingLow1 < swingLow2 && swingHigh1 < swingHigh2))
      return -1;
      
   return 0; // Neutral / Transition
}

//+------------------------------------------------------------------+
//| Calculate Asian Session BSL / SSL Liquidity Reference Pool       |
//+------------------------------------------------------------------+
void UpdateAsianLiquidityRange()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   
   // Create midnight datetime
   datetime midnight = TimeCurrent() - (dt.hour * 3600 + dt.min * 60 + dt.sec);
   
   if(midnight != LastAsianCalculationDate && dt.hour >= AsianRange_EndHour)
   {
      datetime rangeStart = midnight + (AsianRange_StartHour * 3600);
      datetime rangeEnd   = midnight + (AsianRange_EndHour * 3600);
      
      int startBar = iBarShift(Symbol(), Period(), rangeStart, false);
      int endBar   = iBarShift(Symbol(), Period(), rangeEnd, false);
      
      if(startBar >= 0 && endBar >= 0 && startBar >= endBar)
      {
         double highestHigh = -1.0;
         double lowestLow   = 9999999.0;
         
         for(int b = endBar; b <= startBar; b++)
         {
            double h = iHigh(Symbol(), Period(), b);
            double l = iLow(Symbol(), Period(), b);
            if(h > highestHigh) highestHigh = h;
            if(l < lowestLow)   lowestLow   = l;
         }
         
         if(highestHigh > 0.0 && lowestLow < 9999999.0)
         {
            AsianBSL_High            = highestHigh;
            AsianSSL_Low             = lowestLow;
            LastAsianCalculationDate = midnight;
            
            // Reset daily sweep tracking flags
            BullishSweepConfirmed    = false;
            BullishSweepExtremeLow   = 0.0;
            BearishSweepConfirmed    = false;
            BearishSweepExtremeHigh  = 0.0;
            ResetSetup();
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check if Current Time is inside Official ICT Killzones           |
//+------------------------------------------------------------------+
int GetActiveKillzone()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   int currentMinOfDay = dt.hour * 60 + dt.min;
   
   // London Open Killzone (Default: 08:00 - 11:30 Server)
   if(EnableLondonKZ)
   {
      int ldnStart = LondonKZ_StartHour * 60 + LondonKZ_StartMin;
      int ldnEnd   = LondonKZ_EndHour * 60 + LondonKZ_EndMin;
      if(currentMinOfDay >= ldnStart && currentMinOfDay <= ldnEnd)
         return 1; // London KZ
   }
   
   // New York Open Killzone (Default: 14:30 - 17:30 Server)
   if(EnableNYKZ)
   {
      int nyStart = NYKZ_StartHour * 60 + NYKZ_StartMin;
      int nyEnd   = NYKZ_EndHour * 60 + NYKZ_EndMin;
      if(currentMinOfDay >= nyStart && currentMinOfDay <= nyEnd)
         return 2; // New York KZ
   }
   
   return 0; // Outside Killzone
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
//| Trailing Breakeven & Anti-Broker Ban Protection                 |
//+------------------------------------------------------------------+
void ManageOpenTrades()
{
   int ticket, cmd;
   double openPrice, sl, tp;
   datetime openTime;
   
   int posCount = CountOpenPositions(ticket, openPrice, sl, tp, openTime, cmd);
   if(posCount == 0) return;
   
   if(!EnableBreakeven) return;
   
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
            double bePrice = NormalizeDouble(openPrice + (20 * Point), Digits); // +2 pips buffer
            if(sl < openPrice)
            {
               bool res = OrderModify(ticket, openPrice, bePrice, tp, 0, clrGreen);
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
            double bePrice = NormalizeDouble(openPrice - (20 * Point), Digits); // -2 pips buffer
            if(sl > openPrice || sl == 0.0)
            {
               bool res = OrderModify(ticket, openPrice, bePrice, tp, 0, clrRed);
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
      
   // Round to Lot Step
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   if(lotStep <= 0.0) lotStep = 0.01;
   lot = MathFloor(lot / lotStep) * lotStep;
   
   // Hard Constraints (Anti-Broker Ban & Quant Sizing)
   double minBrokerLot = MarketInfo(Symbol(), MODE_MINLOT);
   if(minBrokerLot <= 0.0) minBrokerLot = 0.01;
   if(lot < minBrokerLot) lot = minBrokerLot;
   
   // INSTITUTIONAL CAP: Never blow up from uncontrolled compounding!
   if(lot > MaxLotCap) lot = MaxLotCap;
   
   return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| STEP 1 & 2: SCAN FOR LIQUIDITY SWEEPS (BSL / SSL)                |
//+------------------------------------------------------------------+
void ScanForLiquiditySweeps()
{
   if(AsianBSL_High <= 0.0 || AsianSSL_Low <= 0.0) return;
   
   double curHigh = High[1];
   double curLow  = Low[1];
   double minSweepDist = MinSweepPoints * Point;
   double maxSweepDist = MaxSweepPoints * Point;
   
   // 1. Bullish Setup: Sell-Side Liquidity (SSL) Sweep
   if(!BullishSweepConfirmed)
   {
      if(curLow < AsianSSL_Low)
      {
         double sweepDepth = AsianSSL_Low - curLow;
         if(sweepDepth >= minSweepDist && sweepDepth <= maxSweepDist)
         {
            if(Close[1] > (curLow + (curHigh - curLow) * 0.30))
            {
               BullishSweepConfirmed   = true;
               BullishSweepExtremeLow  = curLow;
               BullishSweepTime        = Time[1];
            }
         }
      }
   }
   
   // 2. Bearish Setup: Buy-Side Liquidity (BSL) Sweep
   if(!BearishSweepConfirmed)
   {
      if(curHigh > AsianBSL_High)
      {
         double sweepDepth = curHigh - AsianBSL_High;
         if(sweepDepth >= minSweepDist && sweepDepth <= maxSweepDist)
         {
            if(Close[1] < (curHigh - (curHigh - curLow) * 0.30))
            {
               BearishSweepConfirmed   = true;
               BearishSweepExtremeHigh = curHigh;
               BearishSweepTime        = Time[1];
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| STEP 3 to 6: COMPLETE ICT INSTITUTIONAL CONFLUENCE SCANNER       |
//+------------------------------------------------------------------+
void EvaluateICTChecklist()
{
   if(CurrentSetup.isValid)
   {
      CurrentSetup.armedBarCount++;
      if(CurrentSetup.armedBarCount > MaxSetupHoldingBars)
      {
         ResetSetup(); // Retracement window expired
      }
      return;
   }
   
   double atr14 = iATR(Symbol(), Period(), 14, 1);
   if(atr14 <= 0.0) atr14 = 2.0;
   
   //------------------------------------------------------------------
   // A. BULLISH ICT CONFLUENCE CHECKLIST (Buy Setup)
   //------------------------------------------------------------------
   if(BullishSweepConfirmed && BullishSweepExtremeLow > 0.0)
   {
      // HTF Gate: For Buy, 4H & 1H must NOT be actively Bearish
      bool htfBuyAllowed = true;
      if(EnableHTFFilter)
      {
         if(RequireH4Alignment && Cached_H4_Bias == -1) htfBuyAllowed = false;
         if(RequireH1Alignment && Cached_H1_Bias == -1) htfBuyAllowed = false;
      }
      
      if(htfBuyAllowed)
      {
         double recentSwingHigh = 0.0;
         for(int b = 3; b <= StructureLookbackBars; b++)
         {
            if(High[b] > High[b+1] && High[b] > High[b-1])
            {
               recentSwingHigh = High[b];
               break;
            }
         }
         
         if(recentSwingHigh > 0.0)
         {
            for(int d = 1; d <= 4; d++)
            {
               double cOpen  = Open[d];
               double cClose = Close[d];
               double cHigh  = High[d];
               double cLow   = Low[d];
               double body   = cClose - cOpen;
               double range  = cHigh - cLow;
               
               if(cClose > recentSwingHigh && body > 0.0 && range > 0.0)
               {
                  if((body / range) >= MinBodyToRangeRatio && body >= (atr14 * MinDisplacementATR))
                  {
                     double fvgLow  = High[d+1];
                     double fvgHigh = Low[d > 1 ? d-1 : 1];
                     double fvgSize = fvgHigh - fvgLow;
                     
                     if(fvgSize >= (MinFVGPoints * Point) || fvgHigh >= fvgLow)
                     {
                        int obBar = -1;
                        for(int ob = d + 1; ob <= d + 5; ob++)
                        {
                           if(Close[ob] < Open[ob]) { obBar = ob; break; }
                        }
                        
                        if(obBar > 0)
                        {
                           double obLow  = Low[obBar];
                           double legHigh = cHigh;
                           double legLow  = BullishSweepExtremeLow;
                           double dealingRange = legHigh - legLow;
                           double equilibrium  = legLow + (dealingRange * 0.50);
                           
                           if(!EnforceDiscountBuyOnly || fvgLow <= equilibrium)
                           {
                              double invalidationSL = MathMin(BullishSweepExtremeLow, obLow) - (SL_BufferPoints * Point);
                              double plannedEntry   = fvgHigh;
                              double riskDistance   = plannedEntry - invalidationSL;
                              double targetTP       = AsianBSL_High;
                              
                              if((targetTP - plannedEntry) < (riskDistance * MinTargetRR))
                                 targetTP = plannedEntry + (riskDistance * MinTargetRR);
                                 
                              if(riskDistance > (80 * Point))
                              {
                                 CurrentSetup.isValid          = true;
                                 CurrentSetup.direction        = 1;
                                 CurrentSetup.sweepExtreme     = BullishSweepExtremeLow;
                                 CurrentSetup.mssLevel         = recentSwingHigh;
                                 CurrentSetup.displacementHigh = legHigh;
                                 CurrentSetup.displacementLow  = legLow;
                                 CurrentSetup.equilibrium50    = equilibrium;
                                 CurrentSetup.fvgHigh          = fvgHigh;
                                 CurrentSetup.fvgLow           = fvgLow;
                                 CurrentSetup.entryPrice       = plannedEntry;
                                 CurrentSetup.slPrice          = NormalizeDouble(invalidationSL, Digits);
                                 CurrentSetup.tpPrice          = NormalizeDouble(targetTP, Digits);
                                 CurrentSetup.setupTime        = TimeCurrent();
                                 CurrentSetup.armedBarCount    = 0;
                                 return;
                              }
                           }
                        }
                     }
                  }
               }
            }
         }
      }
   }
   
   //------------------------------------------------------------------
   // B. BEARISH ICT CONFLUENCE CHECKLIST (Sell Setup)
   //------------------------------------------------------------------
   if(BearishSweepConfirmed && BearishSweepExtremeHigh > 0.0)
   {
      bool htfSellAllowed = true;
      if(EnableHTFFilter)
      {
         if(RequireH4Alignment && Cached_H4_Bias == 1) htfSellAllowed = false;
         if(RequireH1Alignment && Cached_H1_Bias == 1) htfSellAllowed = false;
      }
      
      if(htfSellAllowed)
      {
         double recentSwingLow = 0.0;
         for(int b = 3; b <= StructureLookbackBars; b++)
         {
            if(Low[b] < Low[b+1] && Low[b] < Low[b-1])
            {
               recentSwingLow = Low[b];
               break;
            }
         }
         
         if(recentSwingLow > 0.0)
         {
            for(int d = 1; d <= 4; d++)
            {
               double cOpen  = Open[d];
               double cClose = Close[d];
               double cHigh  = High[d];
               double cLow   = Low[d];
               double body   = cOpen - cClose;
               double range  = cHigh - cLow;
               
               if(cClose < recentSwingLow && body > 0.0 && range > 0.0)
               {
                  if((body / range) >= MinBodyToRangeRatio && body >= (atr14 * MinDisplacementATR))
                  {
                     double fvgHigh = Low[d+1];
                     double fvgLow  = High[d > 1 ? d-1 : 1];
                     double fvgSize = fvgHigh - fvgLow;
                     
                     if(fvgSize >= (MinFVGPoints * Point) || fvgHigh >= fvgLow)
                     {
                        int obBar = -1;
                        for(int ob = d + 1; ob <= d + 5; ob++)
                        {
                           if(Close[ob] > Open[ob]) { obBar = ob; break; }
                        }
                        
                        if(obBar > 0)
                        {
                           double obHigh = High[obBar];
                           double legHigh = BearishSweepExtremeHigh;
                           double legLow  = cLow;
                           double dealingRange = legHigh - legLow;
                           double equilibrium  = legLow + (dealingRange * 0.50);
                           
                           if(!EnforcePremiumSellOnly || fvgHigh >= equilibrium)
                           {
                              double invalidationSL = MathMax(BearishSweepExtremeHigh, obHigh) + (SL_BufferPoints * Point);
                              double plannedEntry   = fvgLow;
                              double riskDistance   = invalidationSL - plannedEntry;
                              double targetTP       = AsianSSL_Low;
                              
                              if((plannedEntry - targetTP) < (riskDistance * MinTargetRR))
                                 targetTP = plannedEntry - (riskDistance * MinTargetRR);
                                 
                              if(riskDistance > (80 * Point))
                              {
                                 CurrentSetup.isValid          = true;
                                 CurrentSetup.direction        = -1;
                                 CurrentSetup.sweepExtreme     = BearishSweepExtremeHigh;
                                 CurrentSetup.mssLevel         = recentSwingLow;
                                 CurrentSetup.displacementHigh = legHigh;
                                 CurrentSetup.displacementLow  = legLow;
                                 CurrentSetup.equilibrium50    = equilibrium;
                                 CurrentSetup.fvgHigh          = fvgHigh;
                                 CurrentSetup.fvgLow           = fvgLow;
                                 CurrentSetup.entryPrice       = plannedEntry;
                                 CurrentSetup.slPrice          = NormalizeDouble(invalidationSL, Digits);
                                 CurrentSetup.tpPrice          = NormalizeDouble(targetTP, Digits);
                                 CurrentSetup.setupTime        = TimeCurrent();
                                 CurrentSetup.armedBarCount    = 0;
                                 return;
                              }
                           }
                        }
                     }
                  }
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| STEP 7: TRIGGER ENTRY ON FVG / OB MITIGATION RETRACEMENT         |
//+------------------------------------------------------------------+
void ExecuteRetracementEntry()
{
   if(!CurrentSetup.isValid) return;
   
   int currentSpread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   if(currentSpread > MaxSpreadPoints) return;
   
   if(TradesTakenThisSession >= MaxTradesPerSession)
   {
      ResetSetup();
      return;
   }
   
   int dummyTicket, dummyCmd;
   double dummyOpen, dummySL, dummyTP;
   datetime dummyTime;
   if(CountOpenPositions(dummyTicket, dummyOpen, dummySL, dummyTP, dummyTime, dummyCmd) > 0)
      return;
      
   // Bullish Mitigation Trigger
   if(CurrentSetup.direction == 1)
   {
      if(Bid < CurrentSetup.sweepExtreme)
      {
         ResetSetup();
         BullishSweepConfirmed = false;
         return;
      }
      
      if(Ask <= CurrentSetup.fvgHigh && Ask >= (CurrentSetup.fvgLow - (50 * Point)))
      {
         double slDist = Ask - CurrentSetup.slPrice;
         if(slDist > (50 * Point))
         {
            double lot = CalculateICTLotSize(slDist);
            int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, 10, CurrentSetup.slPrice, CurrentSetup.tpPrice, TradeComment, MagicNumber, 0, clrBlue);
            if(ticket > 0)
            {
               TradesTakenThisSession++;
               ResetSetup();
               BullishSweepConfirmed = false;
            }
         }
      }
   }
   // Bearish Mitigation Trigger
   else if(CurrentSetup.direction == -1)
   {
      if(Ask > CurrentSetup.sweepExtreme)
      {
         ResetSetup();
         BearishSweepConfirmed = false;
         return;
      }
      
      if(Bid >= CurrentSetup.fvgLow && Bid <= (CurrentSetup.fvgHigh + (50 * Point)))
      {
         double slDist = CurrentSetup.slPrice - Bid;
         if(slDist > (50 * Point))
         {
            double lot = CalculateICTLotSize(slDist);
            int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, 10, CurrentSetup.slPrice, CurrentSetup.tpPrice, TradeComment, MagicNumber, 0, clrRed);
            if(ticket > 0)
            {
               TradesTakenThisSession++;
               ResetSetup();
               BearishSweepConfirmed = false;
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| UPDATE ON-SCREEN ICT HUD DASHBOARD (Skipped in Backtest)         |
//+------------------------------------------------------------------+
void UpdateICTChartHUD(int activeKZ)
{
   if(IsTesting()) return; // Ultra-Fast Strategy Tester Bypass
   
   string kzName = "OUTSIDE KILLZONE";
   if(activeKZ == 1) kzName = "LONDON OPEN KILLZONE (Active)";
   else if(activeKZ == 2) kzName = "NEW YORK OPEN KILLZONE (Active)";
   
   string h4Str = (Cached_H4_Bias == 1) ? "BULLISH (Higher Highs)" : ((Cached_H4_Bias == -1) ? "BEARISH (Lower Lows)" : "NEUTRAL");
   string h1Str = (Cached_H1_Bias == 1) ? "BULLISH (Higher Highs)" : ((Cached_H1_Bias == -1) ? "BEARISH (Lower Lows)" : "NEUTRAL");
   
   string hud = "\n===================================================\n";
   hud += " 🏛️ PURE ICT INSTITUTIONAL MASTER v1.2\n";
   hud += "===================================================\n";
   hud += " [Time & Killzone] : " + kzName + "\n";
   hud += " [HTF 4H Orderflow]: " + h4Str + "\n";
   hud += " [ITF 1H Orderflow]: " + h1Str + "\n";
   hud += StringFormat(" [Asian BSL (High)]: %.2f | [Asian SSL (Low)]: %.2f\n", AsianBSL_High, AsianSSL_Low);
   hud += "---------------------------------------------------\n";
   hud += " ICT 8-STEP INSTITUTIONAL CHECKLIST STATUS:\n";
   hud += " [0] HTF Confluence  : " + (EnableHTFFilter ? "ACTIVE GATE (4H & 1H Alignment Required)" : "DISABLED") + "\n";
   hud += " [1] Liquidity Sweep : " + (BullishSweepConfirmed ? "BULLISH SSL SWEPT" : (BearishSweepConfirmed ? "BEARISH BSL SWEPT" : "Waiting for Sweep...")) + "\n";
   hud += " [2] MSS / CHoCH     : " + (CurrentSetup.isValid ? "CONFIRMED" : "Scanning...") + "\n";
   hud += " [3] Fair Value Gap  : " + (CurrentSetup.isValid ? "VALID" : "Waiting...") + "\n";
   hud += " [4] Order Block     : " + (CurrentSetup.isValid ? "VALID" : "Waiting...") + "\n";
   hud += " [5] EQ / OTE Zone   : " + (CurrentSetup.isValid ? StringFormat("50%% EQ: %.2f (%s)", CurrentSetup.equilibrium50, (CurrentSetup.direction == 1 ? "DISCOUNT" : "PREMIUM")) : "Waiting...") + "\n";
   hud += " [6] Retracement Tap : " + (CurrentSetup.isValid ? StringFormat("ARMED at %.2f", CurrentSetup.entryPrice) : "Idle") + "\n";
   hud += " [7] Risk Target     : " + (CurrentSetup.isValid ? StringFormat("SL: %.2f | TP: %.2f", CurrentSetup.slPrice, CurrentSetup.tpPrice) : "Ready") + "\n";
   hud += "---------------------------------------------------\n";
   hud += StringFormat(" [Equity]: $%.2f | [Risk/Trade]: %.1f%% | [MaxLotCap]: %.2f\n", AccountEquity(), RiskPercentPerTrade, MaxLotCap);
   hud += StringFormat(" [Spread]: %d pts (Max %d) | [Session Trades]: %d/%d\n", (int)MarketInfo(Symbol(), MODE_SPREAD), MaxSpreadPoints, TradesTakenThisSession, MaxTradesPerSession);
   hud += "===================================================\n";
   Comment(hud);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // 1. Manage Active Positions
   ManageOpenTrades();
   
   // 2. Track Session Transitions
   int activeKZ = GetActiveKillzone();
   if(activeKZ != CurrentSessionID)
   {
      CurrentSessionID = activeKZ;
      TradesTakenThisSession = 0;
   }
   
   // 3. Update Asian Liquidity Range Daily
   UpdateAsianLiquidityRange();
   
   // 4. On New Bar: Evaluate Structural Shifts & Sweeps (High-Speed Once Per Bar)
   bool isNewBar = false;
   if(Time[0] != LastBarTime)
   {
      isNewBar = true;
      LastBarTime = Time[0];
      
      // Update HTF Biases ONLY ONCE PER NEW BAR (Ultra-fast performance)
      if(EnableHTFFilter)
      {
         if(RequireH4Alignment) Cached_H4_Bias = GetHTFStructureBias(PERIOD_H4, H4_LookbackBars);
         if(RequireH1Alignment) Cached_H1_Bias = GetHTFStructureBias(PERIOD_H1, H1_LookbackBars);
      }
      
      // Update HUD Display (only when on chart, bypassed in tester)
      UpdateICTChartHUD(activeKZ);
      
      // Scan for sweeps and evaluate checklist if inside Killzone
      if(activeKZ > 0)
      {
         ScanForLiquiditySweeps();
         EvaluateICTChecklist();
      }
   }
   
   // 5. On Every Tick: Monitor Price Retracement into FVG Zone for Execution
   ExecuteRetracementEntry();
}
//+------------------------------------------------------------------+
