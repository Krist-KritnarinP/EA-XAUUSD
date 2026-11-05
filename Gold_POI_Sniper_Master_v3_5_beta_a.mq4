//+------------------------------------------------------------------+
//|                                    Gold_POI_Sniper_Master_v3_5_beta_a.mq4 |
//|        Institutional POI Sniper v3.5 beta a (Dual-Engine + Role-Reversal + ATR SL) |
//|                                  Copyright 2026, Institutional AI|
//+------------------------------------------------------------------+
#property copyright "Institutional AI"
#property link      "https://antigravity.ai"
#property version   "3.51"
#property strict

//--- 1. GLOBAL RISK & COMPOUNDING ---
extern string   SEP_RISK                = "=== DYNAMIC RISK & COMPOUNDING ===";
extern bool     InpUseRiskPercent       = true;   // TRUE: Dynamic Compounding for High Growth
extern double   InpRiskPercent          = 2.5;    // Risk % per trade for NY POI Sniper (2.0% - 3.0%)
extern double   InpLondonRiskPercent    = 5.0;    // Risk % per trade for London Sniper Runner (5.0% Apex)
extern double   InpSweepFadeFixedLot    = 0.02;   // Disciplined Fixed Lot for Judas Sweep Fade (0.02 Lot)
extern double   InpFixedLot             = 0.10;   // Fallback lot if UseRiskPercent is false
extern double   InpMaxLotCap            = 2.00;   // Maximum lot ceiling for broker compliance

//--- 2. MASTER ENGINE MATRIX ---
extern string   SEP_ENGINES             = "=== MASTER DUAL-ENGINE MATRIX ===";
extern bool     InpEnableLondonSniper   = true;   // Leg 1: London Trend Breakout Runner (08:00-11:30)
extern bool     InpEnableJudasSweepFade = true;   // Leg 2: Judas Trap Stop-Hunt Fade (08:00-11:30)
extern bool     InpEnableNewYorkPOI     = true;   // Leg 3: New York Institutional POI Sniper (15:00-20:30)

//--- 3. LEG 1: LONDON SNIPER RUNNER (TREND BREAKOUT) ---
extern string   SEP_LONDON_SNIPER       = "=== LEG 1: LONDON SNIPER (TREND BREAKOUT) ===";
extern int      InpLondonStartHour      = 8;      // London Trade Start Hour (08:00 Server)
extern int      InpLondonStartMin       = 0;
extern int      InpLondonEndHour        = 11;     // London Trade End Hour (11:30 Server)
extern int      InpLondonEndMin         = 30;
extern double   InpLondonMinPenetration = 2.00;   // Min Penetration beyond Asian Box ($2.00 Judas Shield)
extern double   InpLondonMaxPenetration = 6.00;   // Max Penetration beyond Asian Box to prevent Exhaustion (.00)
extern double   InpMaxDailyExtensionUSD = 40.00;  // Max Daily Exhaustion Move from Day High/Low (.00)
extern double   InpLondonMinBodyRatio   = 0.60;   // Min Candle Body Ratio (60%)
extern double   InpLondonRVOL_Mult      = 1.10;   // RVOL Multiplier (1.10x SMA20)
extern bool     InpFilterPreOpenTrap0845= true;   // Require 1.4x RVOL at 08:45 Pre-Open Trap
extern double   InpLondonMinSL_USD      = 6.50;   // Min Base SL USD ($6.50 Dynamic Floor)
extern double   InpLondonATR_Mult       = 1.60;   // Dynamic ATR SL Multiplier (1.6x M15 ATR)
extern double   InpLondonTargetRR       = 3.50;   // London Risk/Reward Ratio (1:3.50 Runner Target)
extern bool     InpEnableLondonRatchet  = true;   // Dynamic Ratchet Trailing (BE @ 1.75R, +1.25R @ 2.5R)
extern bool     InpUseSunsetExit        = true;   // Sunset Handover Exit at 13:00 Server Time
extern int      InpSunsetHour           = 13;     // Sunset Exit Hour (13:00)
extern double   InpSunsetProfitLock     = 1.25;   // Sunset Profit Lock Ratio (1.25R)
extern int      InpMagicLondonSniper    = 778832; // Magic Number London Sniper

//--- 4. LEG 2: JUDAS SWEEP FADE (CONTRARIAN TRAP HUNTER) ---
extern string   SEP_SWEEP_FADE          = "=== LEG 2: JUDAS SWEEP FADE (CONTRARIAN TRAP HUNTER) ===";
extern int      InpSweepKillzoneStartH  = 8;      // London Killzone Window Start (08:00 Server)
extern int      InpSweepKillzoneEndH    = 11;     // London Killzone Window End Hour (11:30 Server)
extern int      InpSweepKillzoneEndM    = 30;     // London Killzone Window End Minute
extern double   InpSweepBufferUSD       = 2.50;   // Stop Buffer beyond extreme sweep wick ($2.50)
extern double   InpSweepMinWickRatio    = 0.40;   // Min Rejection Wick Ratio (>= 40% Pinbar)
extern double   InpSweepTargetRR        = 5.00;   // Asymmetric R:R Runner Multiplier (1:5.00)
extern bool     InpEnableSweepPartialTP = true;   // 2-Tier Partial TP: Close 50% at +1.50R, remainder to BE
extern double   InpSweepPartialRatio    = 1.50;   // Partial TP Trigger (+1.50R)
extern bool     InpEnableSweepDynamicTr = true;   // Progressive Ratchet: +2.5R->+1.25R, +3.5R->+2.5R & Trail
extern double   InpSweepTrailDistance_R = 1.50;   // Dynamic Trail Distance behind peak (1.50R)
extern bool     InpEnableSweepH1Align   = true;   // Sweep Fade Trend Filter (Don't fade into strong macro trend)
extern int      InpMagicSweepFade       = 778834; // Magic Number Judas Sweep Fade

//--- 5. LEG 3: NEW YORK INSTITUTIONAL POI SNIPER ---
extern string   SEP_NY_POI              = "=== LEG 3: NEW YORK POI SNIPER PRIME ===";
extern int      InpNYStartHour          = 15;     // NY Session Start Hour (15:00 Server)
extern int      InpNYStartMin           = 0;
extern int      InpNYEndHour            = 20;     // NY Session End Hour (20:30 Server)
extern int      InpNYEndMin             = 30;
extern double   InpNYTargetRR           = 3.5;    // Target R:R (Asymmetrical 1:3.5)
extern double   InpNYBreakevenRR        = 1.8;    // Breakeven Lock at +1.8R (+30 pts)
extern double   InpNYMinSLPoints        = 150.0;  // Min SL distance in points ($1.50)
extern double   InpNYMaxSLPoints        = 450.0;  // Base Min-Max SL distance in points ($4.50)
extern bool     InpEnableDynamicMaxSL   = true;   // Dynamic ATR Max SL Scaling at $4,100 Gold
extern double   InpNYATR_Mult           = 1.80;   // Dynamic ATR Multiplier for Max SL (1.8x M15 ATR)
extern double   InpNYAbsMaxSL_USD       = 12.00;  // Absolute Max SL Ceiling USD ($12.00)
extern bool     InpEnableRoleReversal   = true;   // Enable PDH/PDL Role-Reversal Retest Engine
extern double   InpRoleReversalBufferUSD= 12.00;  // FVG Retest zone buffer around PDH/PDL ($12.00)
extern bool     InpEnableLondonFixShield= true;   // London 4 PM Fix Blackout Shield (17:25 - 18:05 Server)
extern int      InpFixStartHour         = 17;     // Fix Blackout Start Hour (17:25 Server / 22:25 Thai)
extern int      InpFixStartMin          = 25;
extern int      InpFixEndHour           = 18;     // Fix Blackout End Hour (18:05 Server / 23:05 Thai)
extern int      InpFixEndMin            = 5;
extern double   InpNYWickThreshold      = 0.35;   // Rejection wick threshold (35% of bar)
extern double   InpNYBufferPoints       = 100.0;  // Buffer beyond wick extreme ($1.00)
extern bool     InpNYStructuralExit     = true;   // Early bailout when M15 structure breaks in profit
extern int      InpMagicPOISniper       = 778899; // Magic Number POI Sniper

//--- 6. VOLATILITY, FILTERS & BROKER SAFETY ---
extern string   SEP_SAFETY              = "=== VOLATILITY, FILTERS & BROKER SAFETY ===";
extern int      InpAsianPreStartHour    = 4;      // Asian Box Reference Start (04:00 Server)
extern int      InpAsianPreEndHour      = 8;      // Asian Box Reference End (08:00 Server)
extern double   InpMinATRPoints         = 80.0;   // Minimum M15 ATR(14) in points ($0.80) to avoid dead chop
extern int      InpMaxSpreadPoints      = 65;     // Max allowable spread (points)
extern int      InpMinHoldingSec        = 180;    // Anti-Broker Ban: Min holding time (sec)
extern int      InpSlippage             = 30;
extern int      InpEMAFastPeriod        = 50;     // Trend Fast EMA
extern int      InpEMASlowPeriod        = 200;    // Trend Slow EMA

//--- 7. AI SENTINEL BRIDGE ---
extern string   SEP_AI_SENTINEL         = "=== AI SENTINEL & NEWS GUARD BRIDGE ===";
extern bool     InpEnableMacroNewsShield = true;   // Stand-Down during High-Impact News / Macro Events
extern bool     InpEnableStreakBreaker   = true;   // Auto-scale risk via AI Streak Breaker multiplier

bool     g_ai_stand_down = false;
double   g_ai_risk_multiplier = 1.0;
datetime g_last_sentinel_read = 0;

//--- GLOBAL VARIABLES ---
datetime g_last_bar_time = 0;
double   g_pdh = 0.0;
double   g_pdl = 0.0;
double   g_asian_high = 0.0;
double   g_asian_low = 0.0;

// Stored Asian Pre-Market Box for London Session (04:00 - 08:00)
double   g_stored_asian_high = 0.0;
double   g_stored_asian_low  = 0.0;
datetime g_stored_asian_date = 0;

// Order Risk Tracking Cache (Memory + GlobalVariables)
#define MAX_TRACKED_TICKETS 500
int      g_TrackedTickets[MAX_TRACKED_TICKETS];
double   g_TrackedInitRisk[MAX_TRACKED_TICKETS];
int      g_TrackedCount = 0;

// Forward Declarations
void ReadAISentinel();
void UpdatePOIs();
void UpdateLondonAsianBox();
void ExportMarketState(bool force = false);
void UpdateHUD();
void ManagePOIBreakeven();
void ManageLondonRatchet();
void ManageSweepFadeRatchet();
void CheckStructuralExit();
bool CheckRVOL(double threshold);
void SetOrderInitRisk(int ticket, double riskUSD);
double GetOrderInitRisk(int ticket, double openP, double curSL, double fallbackUSD);
bool SafeModifySL(int ticket, double openP, double curSL, double targetSL, double curTP, int oType, double minStepUSD, color modColor);
bool SafeCloseOrder(int ticket, double lots, double closePrice, int slippage, color closeColor);
double CalculateLotsCompound(double riskPercent, double slUSD);

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+

int OnInit()
{
   Print("[POI SNIPER v3.5 beta a INIT] Initializing Institutional Gold POI Sniper v3.5...");
   if(!IsTesting())
   {
      EventSetTimer(1); // 1-second live telemetry timer
   }
   UpdatePOIs();
   UpdateLondonAsianBox();
   ExportMarketState();
   UpdateHUD();
   
   PrintFormat("[POI SNIPER v3.5 beta a INIT] Initialized successfully. London Sniper: %s | Judas Sweep Fade: %s | NY POI: %s",
               InpEnableLondonSniper ? "ON" : "OFF",
               InpEnableJudasSweepFade ? "ON" : "OFF",
               InpEnableNewYorkPOI ? "ON" : "OFF");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(!IsTesting())
   {
      EventKillTimer();
      Comment("");
   }
}

//+------------------------------------------------------------------+
//| Expert timer function (Live telemetry every 1 sec)               |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(!IsTesting())
   {
      ReadAISentinel();
      UpdatePOIs();
      UpdateLondonAsianBox();
      ExportMarketState();
      UpdateHUD();
   }
}

//+------------------------------------------------------------------+
//| Update POIs (PDH, PDL, Asian Range 00:00-07:00)                  |
//+------------------------------------------------------------------+
void UpdatePOIs()
{
   datetime cur_time = TimeCurrent();
   if(cur_time <= 0) return;
   
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   
   // PDH and PDL from D1 bar 1
   g_pdh = iHigh(Symbol(), PERIOD_D1, 1);
   g_pdl = iLow(Symbol(), PERIOD_D1, 1);
   
   // Asian Range calculation (00:00 to 07:00 server time today)
   datetime today_start = cur_time - (cur_time % 86400);
   int shift_start = iBarShift(Symbol(), PERIOD_M15, today_start);
   if(shift_start < 0) return;
   if(shift_start > 500) shift_start = 500;
   
   double a_high = 0.0;
   double a_low = 999999.0;
   bool found_asian = false;
   
   for(int s = shift_start; s >= 0; s--)
   {
      datetime bar_t = iTime(Symbol(), PERIOD_M15, s);
      if(bar_t <= 0) continue;
      MqlDateTime b_dt;
      TimeToStruct(bar_t, b_dt);
      
      if(b_dt.day == dt.day && b_dt.hour >= 0 && b_dt.hour < 7)
      {
         found_asian = true;
         double h = iHigh(Symbol(), PERIOD_M15, s);
         double l = iLow(Symbol(), PERIOD_M15, s);
         if(h > a_high) a_high = h;
         if(l < a_low)  a_low = l;
      }
      else if(b_dt.day != dt.day || b_dt.hour >= 7)
      {
         if(found_asian) break;
      }
   }
   
   if(found_asian)
   {
      g_asian_high = a_high;
      g_asian_low = a_low;
   }
}

//+------------------------------------------------------------------+
//| Update London Asian Pre-Market Box (04:00 - 08:00)               |
//+------------------------------------------------------------------+
void UpdateLondonAsianBox()
{
   datetime cur_time = TimeCurrent();
   if(cur_time <= 0) return;
   
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   datetime midnight = cur_time - (cur_time % 86400);
   
   if(dt.hour >= InpAsianPreEndHour && (g_stored_asian_date != midnight || g_stored_asian_high <= 0.0))
   {
      datetime preStart = midnight + (InpAsianPreStartHour * 3600);
      datetime preEnd   = midnight + (InpAsianPreEndHour * 3600);
      double preHigh = -1.0;
      double preLow  = 999999.0;
      int preBarCount = 0;
      
      for(int b = 1; b < 60; b++)
      {
         datetime barTime = iTime(Symbol(), PERIOD_M15, b);
         if(barTime < preStart) break;
         if(barTime >= preStart && barTime < preEnd)
         {
            double bh = iHigh(Symbol(), PERIOD_M15, b);
            double bl = iLow(Symbol(), PERIOD_M15, b);
            if(bh > preHigh) preHigh = bh;
            if(bl < preLow)  preLow  = bl;
            preBarCount++;
         }
      }
      
      if(preBarCount >= 6 && preHigh > 0 && preLow < 999999.0)
      {
         g_stored_asian_high = preHigh;
         g_stored_asian_low  = preLow;
         g_stored_asian_date = midnight;
      }
   }
}

//+------------------------------------------------------------------+
//| Set & Cache Order Initial Risk                                   |
//+------------------------------------------------------------------+
void SetOrderInitRisk(int ticket, double riskUSD)
{
   if(ticket <= 0 || riskUSD <= 0.0) return;
   for(int i = 0; i < g_TrackedCount; i++)
   {
      if(g_TrackedTickets[i] == ticket)
      {
         g_TrackedInitRisk[i] = riskUSD;
         return;
      }
   }
   if(g_TrackedCount < MAX_TRACKED_TICKETS)
   {
      g_TrackedTickets[g_TrackedCount] = ticket;
      g_TrackedInitRisk[g_TrackedCount] = riskUSD;
      g_TrackedCount++;
   }
   if(!IsTesting())
   {
      GlobalVariableSet("POI35_Risk_" + IntegerToString(ticket), riskUSD);
   }
}

//+------------------------------------------------------------------+
//| Get Order Initial Risk (USD distance per 1 lot)                  |
//+------------------------------------------------------------------+
double GetOrderInitRisk(int ticket, double openP, double curSL, double fallbackUSD)
{
   if(!IsTesting())
   {
      string gv = "POI35_Risk_" + IntegerToString(ticket);
      if(GlobalVariableCheck(gv))
      {
         double v = GlobalVariableGet(gv);
         if(v >= 1.0 && v <= 50.0) return v;
      }
   }
   for(int i = 0; i < g_TrackedCount; i++)
   {
      if(g_TrackedTickets[i] == ticket) return g_TrackedInitRisk[i];
   }
   if(curSL > 0.0)
   {
      double d = MathAbs(openP - curSL);
      if(d >= 1.0) return d;
   }
   return fallbackUSD;
}

//+------------------------------------------------------------------+
//| Safe SL Modification                                             |
//+------------------------------------------------------------------+
#define MAX_MOD_COOLDOWN_TICKETS 300
static int      s_lastModTicket[MAX_MOD_COOLDOWN_TICKETS];
static datetime s_lastModTime[MAX_MOD_COOLDOWN_TICKETS];
static int      s_lastModCount = 0;

//+------------------------------------------------------------------+
//| Anti-Broker Ban Safe SL Modification (10s Cooldown + Anti-Spam)   |
//+------------------------------------------------------------------+
bool SafeModifySL(int ticket, double openP, double curSL, double targetSL, double curTP, int oType, double minStepUSD, color modColor)
{
   if(!IsTesting() && (!IsTradeAllowed() || IsTradeContextBusy())) return false;
   
   // Anti-Broker Ban Time-Cooldown: Min 10s between modifications on the same ticket!
   if(!IsTesting())
   {
      datetime nowT = TimeCurrent();
      for(int k = 0; k < s_lastModCount; k++)
      {
         if(s_lastModTicket[k] == ticket)
         {
            if((nowT - s_lastModTime[k]) < 10) return false; // Throttled! Zero broker server flood
            break;
         }
      }
   }
   
   targetSL = NormalizeDouble(targetSL, Digits);
   curSL    = NormalizeDouble(curSL, Digits);
   if(MathAbs(targetSL - curSL) < minStepUSD) return false;
   
   double stopLevel = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
   if(stopLevel <= 0.0) stopLevel = 30.0 * Point;
   
   if(oType == OP_BUY)
   {
      if(Bid - targetSL < stopLevel) return false;
      if(curSL > 0.0 && targetSL <= curSL) return false;
   }
   else if(oType == OP_SELL)
   {
      if(targetSL - Ask < stopLevel) return false;
      if(curSL > 0.0 && targetSL >= curSL) return false;
   }
   
   bool res = OrderModify(ticket, openP, targetSL, curTP, 0, modColor);
   if(res && !IsTesting())
   {
      datetime nowT = TimeCurrent();
      bool found = false;
      for(int k = 0; k < s_lastModCount; k++)
      {
         if(s_lastModTicket[k] == ticket)
         {
            s_lastModTime[k] = nowT;
            found = true;
            break;
         }
      }
      if(!found && s_lastModCount < MAX_MOD_COOLDOWN_TICKETS)
      {
         s_lastModTicket[s_lastModCount] = ticket;
         s_lastModTime[s_lastModCount]   = nowT;
         s_lastModCount++;
      }
      ExportMarketState();
   }
   return res;
}

//+------------------------------------------------------------------+
//| Safe Order Close                                                 |
//+------------------------------------------------------------------+
bool SafeCloseOrder(int ticket, double lots, double closePrice, int slippage, color closeColor)
{
   if(!IsTesting() && (!IsTradeAllowed() || IsTradeContextBusy())) return false;
   bool res = OrderClose(ticket, lots, closePrice, slippage, closeColor);
   if(res && !IsTesting()) ExportMarketState();
   return res;
}

//+------------------------------------------------------------------+
//| Check RVOL against SMA20                                         |
//+------------------------------------------------------------------+
bool CheckRVOL(double threshold)
{
   long vol1 = iVolume(Symbol(), PERIOD_M15, 1);
   long sumVol = 0;
   int period = 20;
   for(int i = 2; i <= period + 1; i++)
   {
      sumVol += iVolume(Symbol(), PERIOD_M15, i);
   }
   double avgVol = (double)sumVol / period;
   if(avgVol <= 0) return true;
   return ((double)vol1 >= (avgVol * threshold));
}

//+------------------------------------------------------------------+
//| Calculate Lot Size Compound                                      |
//+------------------------------------------------------------------+
double CalculateLotsCompound(double riskPercent, double slUSD)
{
   if(!InpUseRiskPercent)
   {
      double lot = InpFixedLot;
      if(lot > InpMaxLotCap) lot = InpMaxLotCap;
      return lot;
   }
   
   if(slUSD <= 0.50) slUSD = 3.50;
   double effectiveRisk = riskPercent;
   if(InpEnableStreakBreaker && g_ai_risk_multiplier > 0.05 && g_ai_risk_multiplier <= 2.0)
   {
      effectiveRisk = riskPercent * g_ai_risk_multiplier;
   }
   double riskAmount = AccountEquity() * (effectiveRisk / 100.0);
   double contractSize = MarketInfo(Symbol(), MODE_LOTSIZE);
   if(contractSize <= 0) contractSize = 100.0;
   
   double rawLots = riskAmount / (slUSD * contractSize);
   double step    = MarketInfo(Symbol(), MODE_LOTSTEP);
   double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
   if(step <= 0)  step = 0.01;
   
   double calcLots = MathFloor(rawLots / step) * step;
   if(calcLots < minLot) calcLots = minLot;
   if(calcLots > maxLot) calcLots = maxLot;
   if(calcLots > InpMaxLotCap) calcLots = InpMaxLotCap;
   
   return calcLots;
}

//+------------------------------------------------------------------+
//| Count Open Positions by Magic                                    |
//+------------------------------------------------------------------+
int CountOpenByMagic(int magic)
{
   int count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == magic)
         {
            count++;
         }
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| Manage Breakeven for POI Sniper (1.8R Lock +30 pts)              |
//+------------------------------------------------------------------+
void ManagePOIBreakeven()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicPOISniper)
         {
            int ticket     = OrderTicket();
            double open_pr = OrderOpenPrice();
            double sl_pr   = OrderStopLoss();
            int cmd        = OrderType();
            
            // Use cached initial risk so if user drags SL wider manually, bot still locks BE at original +1.8R!
            double init_risk_usd = GetOrderInitRisk(ticket, open_pr, sl_pr, InpNYMinSLPoints * Point);
            if(cmd == OP_BUY)
            {
               if(sl_pr >= open_pr) continue;
               
               if((Bid - open_pr) >= (init_risk_usd * InpNYBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr + (30.0 * Point), Digits);
                  SafeModifySL(ticket, open_pr, sl_pr, new_sl, OrderTakeProfit(), cmd, 0.10, clrBlue);
               }
            }
            else if(cmd == OP_SELL)
            {
               if(sl_pr <= open_pr && sl_pr > 0.0) continue;
               
               if((open_pr - Ask) >= (init_risk_usd * InpNYBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr - (30.0 * Point), Digits);
                  SafeModifySL(ticket, open_pr, sl_pr, new_sl, OrderTakeProfit(), cmd, 0.10, clrRed);
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Manage Dynamic Ratchet Trailing for London Sniper                |
//+------------------------------------------------------------------+
void ManageLondonRatchet()
{
   if(!InpEnableLondonSniper) return;
   
   datetime cur_time = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicLondonSniper)
         {
            int ticket     = OrderTicket();
            int oType      = OrderType();
            double openP   = OrderOpenPrice();
            double curSL   = OrderStopLoss();
            double curTP   = OrderTakeProfit();
            double lots    = OrderLots();
            double profitUSD = (oType == OP_BUY) ? (Bid - openP) : (openP - Ask);
            double riskUSD = GetOrderInitRisk(ticket, openP, curSL, InpLondonMinSL_USD);
            
            // A. DYNAMIC RATCHET TRAILING (DISCRETE 2-STAGE - ZERO SPREAD JITTER)
            if(InpEnableLondonRatchet)
            {
               // Stage 2: Profit >= 2.50R -> Lock in +1.25R Guaranteed Profit (Fires EXACTLY ONCE)
               if(profitUSD >= (riskUSD * 2.50))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + (riskUSD * 1.25), Digits);
                     if(curSL < targetSL - 0.10)
                        SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - (riskUSD * 1.25), Digits);
                     if(curSL > targetSL + 0.10 || curSL == 0.0)
                        SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
                  }
               }
               // Stage 1: Profit >= 1.75R -> Move SL to Risk-Free Breakeven (Fixed +$0.50 USD Cover - Fires EXACTLY ONCE)
               else if(profitUSD >= (riskUSD * 1.75))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + 0.50, Digits);
                     if(curSL < openP + 0.30) // Only fire ONCE when SL is still below breakeven!
                        SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrBlue);
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - 0.50, Digits);
                     if(curSL > openP - 0.30 || curSL == 0.0) // Only fire ONCE when SL is still above breakeven!
                        SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrBlue);
                  }
               }
            }
            
            // B. SUNSET EXIT (13:00 Server Time)
            if(InpUseSunsetExit && dt.hour >= InpSunsetHour)
            {
               if(profitUSD >= (riskUSD * InpSunsetProfitLock))
               {
                  double cPrice = (oType == OP_BUY) ? Bid : Ask;
                  SafeCloseOrder(ticket, lots, cPrice, InpSlippage, clrGold);
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Manage Judas Sweep Fade Trailing & Partial TP                    |
//+------------------------------------------------------------------+
void ManageSweepFadeRatchet()
{
   if(!InpEnableJudasSweepFade) return;
   
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicSweepFade)
         {
            int ticket     = OrderTicket();
            int oType      = OrderType();
            double openP   = OrderOpenPrice();
            double curSL   = OrderStopLoss();
            double curTP   = OrderTakeProfit();
            double lots    = OrderLots();
            double profitUSD = (oType == OP_BUY) ? (Bid - openP) : (openP - Ask);
            double sweepRiskUSD = GetOrderInitRisk(ticket, openP, curSL, InpSweepBufferUSD);
            
            // 2-TIER PARTIAL TAKE PROFIT (+1.5R Lock 50%, Run remaining 50% to 5.0R)
            if(InpEnableSweepPartialTP && profitUSD >= (sweepRiskUSD * InpSweepPartialRatio))
            {
               string gvKey = "POI35_SwPart_" + IntegerToString(ticket);
               bool alreadyPartClosed = false;
               if(!IsTesting() && GlobalVariableCheck(gvKey)) alreadyPartClosed = true;
               
               if(!alreadyPartClosed)
               {
                  double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                  double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                  if(lotStep <= 0) lotStep = 0.01;
                  double closeLot = MathFloor((lots * 0.50) / lotStep) * lotStep;
                  
                  if(closeLot >= minLot && (lots - closeLot) >= minLot)
                  {
                     double cPrice = (oType == OP_BUY) ? Bid : Ask;
                     if(SafeCloseOrder(ticket, closeLot, cPrice, InpSlippage, clrGold))
                     {
                        if(!IsTesting()) GlobalVariableSet(gvKey, 1.0);
                        PrintFormat("[SWEEP FADE 2-TIER] Closed 50%% (%.2f lots) at +1.5R (+%.2f USD). Moving remaining lot to BE!", closeLot, profitUSD);
                        
                        int childTicket = -1;
                        for(int k = OrdersTotal() - 1; k >= 0; k--)
                        {
                           if(OrderSelect(k, SELECT_BY_POS, MODE_TRADES))
                           {
                              if(OrderMagicNumber() == InpMagicSweepFade && OrderSymbol() == Symbol() && OrderType() == oType)
                              {
                                 childTicket = OrderTicket();
                                 break;
                              }
                           }
                        }
                        if(childTicket > 0 && OrderSelect(childTicket, SELECT_BY_TICKET))
                        {
                           if(!IsTesting()) GlobalVariableSet("POI35_SwPart_" + IntegerToString(childTicket), 1.0);
                           SetOrderInitRisk(childTicket, sweepRiskUSD);
                           double beSL = (oType == OP_BUY) ? 
                              NormalizeDouble(OrderOpenPrice() + 0.50, Digits) :
                              NormalizeDouble(OrderOpenPrice() - 0.50, Digits);
                           SafeModifySL(childTicket, OrderOpenPrice(), OrderStopLoss(), beSL, OrderTakeProfit(), oType, 0.10, clrBlue);
                        }
                        continue;
                     }
                  }
               }
            }
            
            // Progressive Ratchet: Stage 3 (Profit >= 3.50R -> Lock +2.50R) (Fires EXACTLY ONCE)
            if(InpEnableSweepDynamicTr && profitUSD >= (sweepRiskUSD * 3.50))
            {
               if(oType == OP_BUY)
               {
                  double targetSL = NormalizeDouble(openP + (sweepRiskUSD * 2.50), Digits);
                  if(curSL < targetSL - 0.10)
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
               }
               else if(oType == OP_SELL)
               {
                  double targetSL = NormalizeDouble(openP - (sweepRiskUSD * 2.50), Digits);
                  if(curSL > targetSL + 0.10 || curSL == 0.0)
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
               }
            }
            // Stage 2: Profit >= 2.50R -> Lock in +1.25R Guaranteed Profit (Fires EXACTLY ONCE)
            else if(InpEnableSweepDynamicTr && profitUSD >= (sweepRiskUSD * 2.50))
            {
               if(oType == OP_BUY)
               {
                  double targetSL = NormalizeDouble(openP + (sweepRiskUSD * 1.25), Digits);
                  if(curSL < targetSL - 0.10)
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
               }
               else if(oType == OP_SELL)
               {
                  double targetSL = NormalizeDouble(openP - (sweepRiskUSD * 1.25), Digits);
                  if(curSL > targetSL + 0.10 || curSL == 0.0)
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check Structural Exit for NY POI positions                       |
//+------------------------------------------------------------------+
void CheckStructuralExit()
{
   if(!InpNYStructuralExit) return;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicPOISniper)
         {
            int cmd = OrderType();
            double open_pr = OrderOpenPrice();
            datetime open_t = OrderOpenTime();
            
            if((TimeCurrent() - open_t) < InpMinHoldingSec) continue;
            
            double c1_high  = iHigh(Symbol(), PERIOD_M15, 1);
            double c1_low   = iLow(Symbol(), PERIOD_M15, 1);
            double c1_open  = iOpen(Symbol(), PERIOD_M15, 1);
            double c1_close = iClose(Symbol(), PERIOD_M15, 1);
            double c1_range = c1_high - c1_low;
            if(c1_range < 50.0 * Point) continue;
            
            if(cmd == OP_BUY)
            {
               double upper_wick = c1_high - MathMax(c1_open, c1_close);
               if(Bid > (open_pr + 60.0 * Point))
               {
                  if((upper_wick / c1_range) >= 0.45 && c1_close < c1_open)
                  {
                     SafeCloseOrder(OrderTicket(), OrderLots(), Bid, InpSlippage, clrOrange);
                  }
               }
            }
            else if(cmd == OP_SELL)
            {
               double lower_wick = MathMin(c1_open, c1_close) - c1_low;
               if(Ask < (open_pr - 60.0 * Point))
               {
                  if((lower_wick / c1_range) >= 0.45 && c1_close > c1_open)
                  {
                     SafeCloseOrder(OrderTicket(), OrderLots(), Ask, InpSlippage, clrOrange);
                  }
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Read AI Sentinel State (Macro News Stand-Down & Risk Multiplier) |
//+------------------------------------------------------------------+
void ReadAISentinel()
{
   if(IsTesting()) return;
   static datetime lastRead = 0;
   if(TimeCurrent() == lastRead) return;
   lastRead = TimeCurrent();
   
   string targetFile = "ai_sentinel_poi.json";
   if(!FileIsExist(targetFile)) targetFile = "ai_sentinel.json";
   if(!FileIsExist(targetFile)) return;
   
   int handle = FileOpen(targetFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE) return;
   string content = "";
   while(!FileIsEnding(handle)) content += FileReadString(handle);
   FileClose(handle);
   
   if(StringLen(content) < 10) return;
   
   // 1. Parse News Stand-Down
   if(StringFind(content, "stand_down\": true") >= 0 || StringFind(content, "stand_down\":true") >= 0)
   {
      if(!g_ai_stand_down)
         Print("[AI SENTINEL v3.5] High-Impact Macro News / Geopolitical Shock active! Stand-Down engaged.");
      g_ai_stand_down = true;
   }
   else
   {
      if(g_ai_stand_down)
         Print("[AI SENTINEL v3.5] News Stand-Down cleared. Normal trading resumed.");
      g_ai_stand_down = false;
   }
   
   // 2. Parse AI Risk Multiplier
   int pos = StringFind(content, "ai_risk_multiplier");
   if(pos >= 0)
   {
      int colon = StringFind(content, ":", pos);
      int start = (colon >= 0) ? (colon + 1) : (pos + 21);
      string numStr = "";
      for(int i = start; i < start + 12 && i < StringLen(content); i++)
      {
         ushort ch = StringGetCharacter(content, i);
         if((ch >= '0' && ch <= '9') || ch == '.')
            numStr += CharToString((uchar)ch);
         else if(StringLen(numStr) > 0)
            break;
      }
      double parsedMult = StringToDouble(numStr);
      if(parsedMult >= 0.05 && parsedMult <= 2.0)
         g_ai_risk_multiplier = parsedMult;
   }
}

//+------------------------------------------------------------------+
//| Export Real-Time Market State for Python AI Sentinel             |
//+------------------------------------------------------------------+
void ExportMarketState(bool force = false)
{
   if(IsTesting()) return;
   static datetime s_lastExport = 0;
   if(!force && TimeCurrent() == s_lastExport) return;
   s_lastExport = TimeCurrent();
   
   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   double cur_bid = MarketInfo(Symbol(), MODE_BID);
   double cur_ask = MarketInfo(Symbol(), MODE_ASK);
   if(cur_bid <= 0.0) cur_bid = Bid;
   if(cur_ask <= 0.0) cur_ask = Ask;
   
   string openOrdersJson = "[";
   int openCount = 0;
   
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol())
         {
            int m = OrderMagicNumber();
            string eng = "User Manual";
            if(m == InpMagicPOISniper)         eng = "POI NY Sniper";
            else if(m == InpMagicLondonSniper) eng = "London Sniper";
            else if(m == InpMagicSweepFade)    eng = "Judas Sweep Fade";
            
            if(openCount > 0) openOrdersJson += ", ";
            openOrdersJson += "{\"ticket\": " + IntegerToString(OrderTicket()) + 
                              ", \"magic\": " + IntegerToString(m) +
                              ", \"engine\": \"" + eng + "\"" +
                              ", \"type\": " + IntegerToString(OrderType()) +
                              ", \"lots\": " + DoubleToString(OrderLots(), 2) +
                              ", \"open_price\": " + DoubleToString(OrderOpenPrice(), Digits) +
                              ", \"sl\": " + DoubleToString(OrderStopLoss(), Digits) +
                              ", \"tp\": " + DoubleToString(OrderTakeProfit(), Digits) +
                              ", \"profit\": " + DoubleToString(OrderProfit() + OrderSwap() + OrderCommission(), 2) + "}";
            openCount++;
         }
      }
   }
   openOrdersJson += "]";
   
   // Export today's closed orders
   datetime todayStart = iTime(Symbol(), PERIOD_D1, 0);
   string closedOrdersJson = "[";
   int closedCount = 0;
   
   for(int h = OrdersHistoryTotal() - 1; h >= 0 && closedCount < 30; h--)
   {
      if(OrderSelect(h, SELECT_BY_POS, MODE_HISTORY))
      {
         if(OrderSymbol() == Symbol())
         {
            int m = OrderMagicNumber();
            string eng = "User Manual";
            if(m == InpMagicPOISniper)         eng = "POI NY Sniper";
            else if(m == InpMagicLondonSniper) eng = "London Sniper";
            else if(m == InpMagicSweepFade)    eng = "Judas Sweep Fade";
            
            if(OrderCloseTime() >= todayStart || closedCount < 10)
            {
               if(closedCount > 0) closedOrdersJson += ", ";
               closedOrdersJson += "{\"ticket\": " + IntegerToString(OrderTicket()) + 
                                   ", \"magic\": " + IntegerToString(m) +
                                   ", \"engine\": \"" + eng + "\"" +
                                   ", \"type\": " + IntegerToString(OrderType()) +
                                   ", \"lots\": " + DoubleToString(OrderLots(), 2) +
                                   ", \"open_price\": " + DoubleToString(OrderOpenPrice(), Digits) +
                                   ", \"close_price\": " + DoubleToString(OrderClosePrice(), Digits) +
                                   ", \"profit\": " + DoubleToString(OrderProfit() + OrderSwap() + OrderCommission(), 2) +
                                   ", \"close_time\": \"" + TimeToString(OrderCloseTime(), TIME_DATE|TIME_SECONDS) + "\"}";
               closedCount++;
            }
         }
      }
   }
   closedOrdersJson += "]";
   
   string json = "{\n";
   json += "  \"symbol\": \"" + Symbol() + "\",\n";
   json += "  \"server_time\": \"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\",\n";
   json += "  \"bid\": " + DoubleToString(cur_bid, Digits) + ",\n";
   json += "  \"ask\": " + DoubleToString(cur_ask, Digits) + ",\n";
   json += "  \"balance\": " + DoubleToString(AccountBalance(), 2) + ",\n";
   json += "  \"equity\": " + DoubleToString(AccountEquity(), 2) + ",\n";
   json += "  \"spread\": " + IntegerToString(spread) + ",\n";
   json += "  \"pdh\": " + DoubleToString(g_pdh, Digits) + ",\n";
   json += "  \"pdl\": " + DoubleToString(g_pdl, Digits) + ",\n";
   json += "  \"asian_high\": " + DoubleToString(g_asian_high, Digits) + ",\n";
   json += "  \"asian_low\": " + DoubleToString(g_asian_low, Digits) + ",\n";
   json += "  \"stored_asian_high\": " + DoubleToString(g_stored_asian_high, Digits) + ",\n";
   json += "  \"stored_asian_low\": " + DoubleToString(g_stored_asian_low, Digits) + ",\n";
   json += "  \"open_orders\": " + openOrdersJson + ",\n";
   json += "  \"recent_closed_orders\": " + closedOrdersJson + "\n";
   json += "}\n";
   
   int hFile = FileOpen("market_state.json", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(hFile != INVALID_HANDLE)
   {
      FileWriteString(hFile, json);
      FileClose(hFile);
   }
}

//+------------------------------------------------------------------+
//| Update Institutional HUD                                         |
//+------------------------------------------------------------------+
void UpdateHUD()
{
   if(IsTesting()) return;
   
   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   int poiCount = 0, londonCount = 0, sweepCount = 0, manualCount = 0;
   double poiPnl = 0.0, londonPnl = 0.0, sweepPnl = 0.0, manualPnl = 0.0;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol())
         {
            double p = OrderProfit() + OrderSwap() + OrderCommission();
            int m = OrderMagicNumber();
            if(m == InpMagicPOISniper)         { poiCount++;    poiPnl += p; }
            else if(m == InpMagicLondonSniper) { londonCount++; londonPnl += p; }
            else if(m == InpMagicSweepFade)    { sweepCount++;  sweepPnl += p; }
            else                               { manualCount++; manualPnl += p; }
         }
      }
   }
   
   datetime cur_time = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   int minOfDay = dt.hour * 60 + dt.min;
   
   bool inLondon = (minOfDay >= InpLondonStartHour*60+InpLondonStartMin && minOfDay <= InpLondonEndHour*60+InpLondonEndMin);
   bool inNY     = (minOfDay >= InpNYStartHour*60+InpNYStartMin && minOfDay <= InpNYEndHour*60+InpNYEndMin);
   
   string txt = "\n  === GOLD POI SNIPER v3.5 beta a (ROLE-REVERSAL + DYNAMIC ATR) ===\n";
   txt += "  ------------------------------------------------------------\n";
   txt += StringFormat("  Server Time    : %s\n", TimeToString(cur_time, TIME_DATE|TIME_SECONDS));
   txt += StringFormat("  London Engine  : [%s] (08:00-11:30) | State: %s\n", 
                       InpEnableLondonSniper ? "ON" : "OFF", inLondon ? "ACTIVE" : "STANDBY");
   txt += StringFormat("  Judas SweepFade: [%s] (08:00-11:30) | State: %s\n", 
                       InpEnableJudasSweepFade ? "ON" : "OFF", inLondon ? "ACTIVE" : "STANDBY");
   txt += StringFormat("  New York POI   : [%s] (15:00-20:30) | State: %s\n", 
                       InpEnableNewYorkPOI ? "ON" : "OFF", inNY ? "ACTIVE" : "STANDBY");
   txt += "  ------------------------------------------------------------\n";
   txt += StringFormat("  Asian Box (04-08): High: %.2f | Low: %.2f\n", g_stored_asian_high, g_stored_asian_low);
   txt += StringFormat("  Macro POI Levels : PDH: %.2f | PDL: %.2f\n", g_pdh, g_pdl);
   txt += StringFormat("  Market Price     : Ask %.2f | Bid %.2f | Spread: %d pts\n", Ask, Bid, spread);
   txt += "  ------------------------------------------------------------\n";
   txt += StringFormat("  Open London Sniper: %d ไม้ (Floating PnL: $%.2f)\n", londonCount, londonPnl);
   txt += StringFormat("  Open Sweep Fade   : %d ไม้ (Floating PnL: $%.2f)\n", sweepCount, sweepPnl);
   txt += StringFormat("  Open NY POI Sniper: %d ไม้ (Floating PnL: $%.2f)\n", poiCount, poiPnl);
   txt += StringFormat("  Open User Manual  : %d ไม้ (Floating PnL: $%.2f)\n", manualCount, manualPnl);
   txt += "  ------------------------------------------------------------\n";
   txt += StringFormat("  Account Equity   : $%.2f | Balance: $%.2f\n", AccountEquity(), AccountBalance());
   txt += StringFormat("  AI Sentinel Bridge: [%s | Risk Mult: %.2fx]\n", 
                       g_ai_stand_down ? "STAND-DOWN 🔴" : "ACTIVE 🟢", g_ai_risk_multiplier);
   txt += "  ============================================================\n";
   Comment(txt);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   ReadAISentinel();
   // 1. Tick-level Management
   ManagePOIBreakeven();
   ManageLondonRatchet();
   ManageSweepFadeRatchet();
   ExportMarketState();
   
   // 2. Bar Close Synchronizer (M15 Bar Transition)
   datetime cur_bar_time = iTime(Symbol(), PERIOD_M15, 0);
   if(cur_bar_time == g_last_bar_time)
   {
      return;
   }
   g_last_bar_time = cur_bar_time;
   
   CheckStructuralExit();
   UpdatePOIs();
   UpdateLondonAsianBox();
   UpdateHUD();
   
   // Volatility & Spread Filters
   double cur_atr = iATR(Symbol(), PERIOD_M15, 14, 0);
   if(cur_atr < (InpMinATRPoints * Point)) return;
   
   int cur_spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   if(cur_spread > InpMaxSpreadPoints) return;
   
   // Bar 1 Analysis
   double c1_high  = iHigh(Symbol(), PERIOD_M15, 1);
   double c1_low   = iLow(Symbol(), PERIOD_M15, 1);
   double c1_open  = iOpen(Symbol(), PERIOD_M15, 1);
   double c1_close = iClose(Symbol(), PERIOD_M15, 1);
   double c1_range = c1_high - c1_low;
   if(c1_range < (80.0 * Point)) return;
   
   double c1_upper_wick = c1_high - MathMax(c1_open, c1_close);
   double c1_lower_wick = MathMin(c1_open, c1_close) - c1_low;
   double c1_body       = MathAbs(c1_close - c1_open);
   
   // Trend EMAs
   double ema50_h1   = iMA(Symbol(), PERIOD_H1, InpEMAFastPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   double ema200_h1  = iMA(Symbol(), PERIOD_H1, InpEMASlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   double c1_h1      = iClose(Symbol(), PERIOD_H1, 1);
   bool isH1Bull     = (c1_h1 > ema200_h1) && (ema50_h1 > ema200_h1);
   bool isH1Bear     = (c1_h1 < ema200_h1) && (ema50_h1 < ema200_h1);
   
   double ema50_m15  = iMA(Symbol(), PERIOD_M15, InpEMAFastPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   double ema200_m15 = iMA(Symbol(), PERIOD_M15, InpEMASlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   
   datetime cur_time = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   int minOfDay = dt.hour * 60 + dt.min;
   
   // ====================================================================
   // ENGINE A: LEG 2 - JUDAS SWEEP FADE (08:00 - 11:30 Server Time)
   //    - Evaluated FIRST because it detects stop-hunt sweeps & false breaks
   // ====================================================================
   bool inSweepWindow = (minOfDay >= InpSweepKillzoneStartH * 60 && minOfDay <= (InpSweepKillzoneEndH * 60 + InpSweepKillzoneEndM));
   if(InpEnableJudasSweepFade && inSweepWindow && CountOpenByMagic(InpMagicSweepFade) == 0)
   {
      if(InpEnableMacroNewsShield && g_ai_stand_down)
      {
         // Blocked by AI News Stand Down
      }
      else if(g_stored_asian_high > 0.0 && g_stored_asian_low < 999999.0)
      {
         // Bearish Judas Sweep of Asian High
         bool sweptAsianHigh = (c1_high >= (g_stored_asian_high + InpSweepBufferUSD)) && 
                               (c1_close < g_stored_asian_high) && 
                               (c1_close < c1_open) && 
                               ((c1_upper_wick / c1_range) >= InpSweepMinWickRatio);
         
         // Bullish Judas Sweep of Asian Low
         bool sweptAsianLow  = (c1_low <= (g_stored_asian_low - InpSweepBufferUSD)) && 
                               (c1_close > g_stored_asian_low) && 
                               (c1_close > c1_open) && 
                               ((c1_lower_wick / c1_range) >= InpSweepMinWickRatio);
         
         if(sweptAsianHigh && (!InpEnableSweepH1Align || !isH1Bull))
         {
            double entryPrice = Bid;
            double sweepSL    = NormalizeDouble(c1_high + InpSweepBufferUSD, Digits);
            double slDist     = sweepSL - entryPrice;
            if(slDist >= 2.00 && slDist <= 12.00)
            {
               double sweepTP = NormalizeDouble(entryPrice - (slDist * InpSweepTargetRR), Digits);
               double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
               double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
               double step    = MarketInfo(Symbol(), MODE_LOTSTEP);
               if(step <= 0) step = 0.01;
               double lot = MathFloor(InpSweepFadeFixedLot / step) * step;
               if(lot < minLot) lot = minLot;
               if(lot > maxLot) lot = maxLot;
               
               int ticket = OrderSend(Symbol(), OP_SELL, lot, entryPrice, InpSlippage, sweepSL, sweepTP, "POI35 Judas Fade SELL", InpMagicSweepFade, 0, clrRed);
               if(ticket > 0)
               {
                  SetOrderInitRisk(ticket, slDist);
                  PrintFormat("[SWEEP FADE SELL SUCCESS] Ticket #%d Lots: %.2f Price: %.2f SL: %.2f TP: %.2f (1:%.1f RR)",
                              ticket, lot, entryPrice, sweepSL, sweepTP, InpSweepTargetRR);
                  ExportMarketState(true);
                  return;
               }
            }
         }
         else if(sweptAsianLow && (!InpEnableSweepH1Align || !isH1Bear))
         {
            double entryPrice = Ask;
            double sweepSL    = NormalizeDouble(c1_low - InpSweepBufferUSD, Digits);
            double slDist     = entryPrice - sweepSL;
            if(slDist >= 2.00 && slDist <= 12.00)
            {
               double sweepTP = NormalizeDouble(entryPrice + (slDist * InpSweepTargetRR), Digits);
               double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
               double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
               double step    = MarketInfo(Symbol(), MODE_LOTSTEP);
               if(step <= 0) step = 0.01;
               double lot = MathFloor(InpSweepFadeFixedLot / step) * step;
               if(lot < minLot) lot = minLot;
               if(lot > maxLot) lot = maxLot;
               
               int ticket = OrderSend(Symbol(), OP_BUY, lot, entryPrice, InpSlippage, sweepSL, sweepTP, "POI35 Judas Fade BUY", InpMagicSweepFade, 0, clrGreen);
               if(ticket > 0)
               {
                  SetOrderInitRisk(ticket, slDist);
                  PrintFormat("[SWEEP FADE BUY SUCCESS] Ticket #%d Lots: %.2f Price: %.2f SL: %.2f TP: %.2f (1:%.1f RR)",
                              ticket, lot, entryPrice, sweepSL, sweepTP, InpSweepTargetRR);
                  ExportMarketState(true);
                  return;
               }
            }
         }
      }
   }
   
   // ====================================================================
   // ENGINE B: LEG 1 - LONDON SNIPER RUNNER (08:00 - 11:30 Server Time)
   //    - Trend Breakout expansion beyond Asian Range with RVOL confirmation
   // ====================================================================
   bool inLondonWindow = (minOfDay >= (InpLondonStartHour * 60 + InpLondonStartMin) && minOfDay <= (InpLondonEndHour * 60 + InpLondonEndMin));
   if(InpEnableLondonSniper && inLondonWindow && CountOpenByMagic(InpMagicLondonSniper) == 0)
   {
      if(InpEnableMacroNewsShield && g_ai_stand_down)
      {
         // Blocked by AI News Stand Down
      }
      else if(g_stored_asian_high > 0.0 && g_stored_asian_low < 999999.0)
      {
         bool sniperRvolOk = false;
         if(InpFilterPreOpenTrap0845 && dt.hour == 8 && dt.min == 45)
            sniperRvolOk = CheckRVOL(1.40);
         else
            sniperRvolOk = CheckRVOL(InpLondonRVOL_Mult);
         
         bool wickOkBuy  = (c1_upper_wick / c1_range) <= 0.40;
         bool wickOkSell = (c1_lower_wick / c1_range) <= 0.40;
         bool isBull = isH1Bull && (c1_close > ema200_m15) && (ema50_m15 > ema200_m15) && wickOkBuy;
         bool isBear = isH1Bear && (c1_close < ema200_m15) && (ema50_m15 < ema200_m15) && wickOkSell;
         bool sniperBodyOk = !(dt.hour == 8 && (c1_body / c1_range) < InpLondonMinBodyRatio);
         
         bool isBuySignal  = sniperRvolOk && sniperBodyOk && isBull && 
                             (c1_close > g_stored_asian_high) && 
                             ((c1_close - g_stored_asian_high) >= InpLondonMinPenetration) && 
                             (c1_close > c1_open);
                             
         bool isSellSignal = sniperRvolOk && sniperBodyOk && isBear && 
                             (c1_close < g_stored_asian_low) && 
                             ((g_stored_asian_low - c1_close) >= InpLondonMinPenetration) && 
                             (c1_close < c1_open);
         
         if(isBuySignal || isSellSignal)
         {
            double atr15_sniper = iATR(Symbol(), PERIOD_M15, 14, 1);
            double dynamicSniperSL = MathMax(InpLondonMinSL_USD, NormalizeDouble(atr15_sniper * InpLondonATR_Mult, 2));
            double dynamicSniperTP = NormalizeDouble(dynamicSniperSL * InpLondonTargetRR, 2);
            
            if(isBuySignal)
            {
               double lot = CalculateLotsCompound(InpLondonRiskPercent, dynamicSniperSL);
               double sl  = NormalizeDouble(Ask - dynamicSniperSL, Digits);
               double tp  = NormalizeDouble(Ask + dynamicSniperTP, Digits);
               int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, InpSlippage, sl, tp, "POI35 London Sniper BUY", InpMagicLondonSniper, 0, clrGreen);
               if(ticket > 0)
               {
                  SetOrderInitRisk(ticket, dynamicSniperSL);
                  PrintFormat("[LONDON SNIPER BUY] Ticket #%d Lots: %.2f Price: %.2f SL: %.2f (%.2f USD) TP: %.2f (%.2f USD)",
                              ticket, lot, Ask, sl, dynamicSniperSL, tp, dynamicSniperTP);
                  ExportMarketState(true);
                  return;
               }
            }
            else if(isSellSignal)
            {
               double lot = CalculateLotsCompound(InpLondonRiskPercent, dynamicSniperSL);
               double sl  = NormalizeDouble(Bid + dynamicSniperSL, Digits);
               double tp  = NormalizeDouble(Bid - dynamicSniperTP, Digits);
               int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, InpSlippage, sl, tp, "POI35 London Sniper SELL", InpMagicLondonSniper, 0, clrRed);
               if(ticket > 0)
               {
                  SetOrderInitRisk(ticket, dynamicSniperSL);
                  PrintFormat("[LONDON SNIPER SELL] Ticket #%d Lots: %.2f Price: %.2f SL: %.2f (%.2f USD) TP: %.2f (%.2f USD)",
                              ticket, lot, Bid, sl, dynamicSniperSL, tp, dynamicSniperTP);
                  ExportMarketState(true);
                  return;
               }
            }
         }
      }
   }
   
   // ====================================================================
   // ENGINE C: LEG 3 - NEW YORK POI SNIPER PRIME v3.5 beta a
   //    - SMC Liquidity Sweeps of PDH, PDL, Asian High, Asian Low
   //    - Role-Reversal Retest (PDH Flip Support / PDL Flip Resistance)
   //    - Dynamic ATR Max SL Scaling & London Fix Blackout Shield
   // ====================================================================
   bool inNYWindow = (minOfDay >= (InpNYStartHour * 60 + InpNYStartMin) && minOfDay <= (InpNYEndHour * 60 + InpNYEndMin));
   bool inFixBlackout = InpEnableLondonFixShield && (minOfDay >= (InpFixStartHour * 60 + InpFixStartMin) && minOfDay <= (InpFixEndHour * 60 + InpFixEndMin));
   
   if(InpEnableNewYorkPOI && inNYWindow && !inFixBlackout && CountOpenByMagic(InpMagicPOISniper) == 0)
   {
      if(InpEnableMacroNewsShield && g_ai_stand_down)
      {
         // Blocked by AI News Stand Down
      }
      else
      {
         double atr15_ny = iATR(Symbol(), PERIOD_M15, 14, 1);
         double maxAllowedSL_USD = InpNYMaxSLPoints * Point;
         if(InpEnableDynamicMaxSL)
         {
            maxAllowedSL_USD = MathMax(maxAllowedSL_USD, NormalizeDouble(atr15_ny * InpNYATR_Mult, Digits));
            if(maxAllowedSL_USD > InpNYAbsMaxSL_USD) maxAllowedSL_USD = InpNYAbsMaxSL_USD;
         }
         double maxAllowedSL_pts = maxAllowedSL_USD / Point;

         // ---------------------------------------------------------------
         // 1. SELL SETUP: Resistance Sweep OR PDL Breakdown Retest
         // ---------------------------------------------------------------
         bool sweepAsianHigh = (c1_high >= g_asian_high && c1_close < g_asian_high);
         bool sweepPDH       = (c1_high >= g_pdh && c1_open < g_pdh && c1_close < g_pdh);
         
         bool retestPDL_Sell = false;
         if(InpEnableRoleReversal && g_pdl > 0.0 && g_pdl < 999999.0)
         {
            retestPDL_Sell = (c1_high >= (g_pdl - InpRoleReversalBufferUSD) && 
                              c1_high <= (g_pdl + InpRoleReversalBufferUSD) && 
                              c1_close < g_pdl);
         }

         bool at_resistance = (sweepAsianHigh || sweepPDH || retestPDL_Sell);
         double upper_wick_ratio = (c1_range > 0) ? (c1_upper_wick / c1_range) : 0;
         
         if(at_resistance && upper_wick_ratio >= InpNYWickThreshold && c1_close < c1_open)
         {
            double sl = NormalizeDouble(c1_high + (InpNYBufferPoints * Point), Digits);
            double entry = Ask;
            double sl_dist_pts = (sl - entry) / Point;
            
            if(sl_dist_pts >= InpNYMinSLPoints && sl_dist_pts <= maxAllowedSL_pts)
            {
               double tp = NormalizeDouble(entry - (sl_dist_pts * Point * InpNYTargetRR), Digits);
               double slUSD = sl_dist_pts * Point;
               double lots = CalculateLotsCompound(InpRiskPercent, slUSD);
               
               int ticket = OrderSend(Symbol(), OP_SELL, lots, Bid, InpSlippage, sl, tp, "POI35ba NY POI SELL", InpMagicPOISniper, 0, clrRed);
               if(ticket > 0)
               {
                  SetOrderInitRisk(ticket, slUSD);
                  PrintFormat("[NY POI SELL SUCCESS] Ticket #%d Lots: %.2f Entry: %.2f SL: %.2f (%.0f pts, DynamicMax: %.0f) TP: %.2f (1:%.1f RR)",
                              ticket, lots, Bid, sl, sl_dist_pts, maxAllowedSL_pts, tp, InpNYTargetRR);
                  ExportMarketState(true);
                  return;
               }
            }
         }
         
         // ---------------------------------------------------------------
         // 2. BUY SETUP: Support Sweep OR PDH Breakout Retest (Role-Reversal)
         // ---------------------------------------------------------------
         bool sweepAsianLow  = (c1_low <= g_asian_low && c1_close > g_asian_low);
         bool sweepPDL       = (c1_low <= g_pdl && c1_open > g_pdl && c1_close > g_pdl);
         
         bool retestPDH_Buy  = false;
         if(InpEnableRoleReversal && g_pdh > 0.0)
         {
            retestPDH_Buy = (c1_low <= (g_pdh + InpRoleReversalBufferUSD) && 
                             c1_low >= (g_pdh - InpRoleReversalBufferUSD) && 
                             c1_close > g_pdh);
         }
         
         bool at_support = (sweepAsianLow || sweepPDL || retestPDH_Buy);
         double lower_wick_ratio = (c1_range > 0) ? (c1_lower_wick / c1_range) : 0;
         
         if(at_support && lower_wick_ratio >= InpNYWickThreshold && c1_close > c1_open)
         {
            double sl = NormalizeDouble(c1_low - (InpNYBufferPoints * Point), Digits);
            double entry = Bid;
            double sl_dist_pts = (entry - sl) / Point;
            
            if(sl_dist_pts >= InpNYMinSLPoints && sl_dist_pts <= maxAllowedSL_pts)
            {
               double tp = NormalizeDouble(entry + (sl_dist_pts * Point * InpNYTargetRR), Digits);
               double slUSD = sl_dist_pts * Point;
               double lots = CalculateLotsCompound(InpRiskPercent, slUSD);
               
               int ticket = OrderSend(Symbol(), OP_BUY, lots, Ask, InpSlippage, sl, tp, "POI35ba NY POI BUY", InpMagicPOISniper, 0, clrBlue);
               if(ticket > 0)
               {
                  SetOrderInitRisk(ticket, slUSD);
                  PrintFormat("[NY POI BUY SUCCESS] Ticket #%d Lots: %.2f Entry: %.2f SL: %.2f (%.0f pts, DynamicMax: %.0f) TP: %.2f (1:%.1f RR)",
                              ticket, lots, Ask, sl, sl_dist_pts, maxAllowedSL_pts, tp, InpNYTargetRR);
                  ExportMarketState(true);
                  return;
               }
            }
         }
      }
   }
}
//+------------------------------------------------------------------+
