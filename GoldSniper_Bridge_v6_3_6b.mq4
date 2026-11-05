//+------------------------------------------------------------------+
//|                                      GoldSniper_Bridge_v6_3_5_beta.mq4 |
//|                                  Copyright 2026, Quant AI Engine |
//|        Gold Sniper v6.3.1 Institutional Live XM Bridge Engine    |
//|  [Jackpot Lock + NY 3.5% Risk + Squeeze Scalper BE & $5.00 TP]   |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Quant AI Engine"
#property link      "https://github.com/gold-sniper-institutional"
#property version   "6.36"
#property strict

//+------------------------------------------------------------------+
//| Master Operating Mode Enumeration                                |
//+------------------------------------------------------------------+
enum ENUM_FLIP_MODE
{
   MODE_TRI_SESSION_ULTRA = 0, // [Tri-Session Ultra] London Sniper + NY Cash Flow + Asia Trend Sweeper
   MODE_INSTITUTIONAL_DUAL= 1, // [Institutional Dual] London Sniper + New York Cash Flow (Pure Trend, 0% Asia Noise)
   MODE_SNIPER_PURE_v55   = 2, // [Sniper Pure v5.5] London Only Heavy-Hitter ($28 TP, Max Profit Factor 2.87)
   MODE_SCALPER_ONLY      = 3  // [Scalper Only] Asia Trend-Aligned Mean Reversion
};

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
//--- 1. MASTER MODE & ISOLATED RISK CONTROLLER
input string          Header_Master           = "=== MASTER V6.3.6b INSTITUTIONAL QUAD-ENGINE APEX (BUG-01 & BUG-02 FIXED) ===";
input ENUM_FLIP_MODE  OperatingMode           = MODE_TRI_SESSION_ULTRA; // Master Operating Architecture
input double          SniperRiskPercent       = 5.0;            // London Sniper Risk (% of Equity - 2x Lot)
input double          NYRiskPercent           = 3.5;            // New York Continuation Risk (3.5% of Equity)
input double          ScalperRiskPercent      = 1.0;            // Asian Scalper Micro-Risk (% of Equity - Safe)
input bool            EnableEmergencyKillFlip = true;           // AAA+ Privilege: Emergency Kill & Flip conflicting Scalper
input bool            EnableJackpotLock       = true;           // Jackpot Lock: Halt NY if London made >= $100 profit today!
input double          JackpotProfitUSD        = 100.0;          // Jackpot Daily Profit Target Lock Level
input int             MaxSniperDailyLosses    = 2;              // Max Sniper Daily Losses Before London Lock
input int             MaxNYDailyLosses        = 1;              // Max New York Daily Losses
input int             MaxScalperDailyLosses   = 1;              // Max Scalper Daily Losses (Stops Scalper only!)
input double          DailyProfitTargetPct    = 15.0;           // Daily Profit Target Lock (+15%)
input double          DailyLossLimitPct       = 10.0;           // Global Daily Loss Limit (-10%)

//--- 2. LONDON SNIPER RUNNER (v6.3.6a Universal Dynamic ATR Engine)
input string          Header_Sniper           = "=== LONDON SNIPER RUNNER (08:00-11:30) ===";
input int             PreMarketStartHour      = 4;              // Asian Range Measure Start (04:00)
input int             PreMarketEndHour        = 8;              // Asian Range Measure End (08:00)
input int             LondonTradeStartHour    = 8;              // London Window Start (08:00)
input int             LondonTradeEndHour      = 11;             // London Window End Hour (11:30)
input double          LondonMinPenetrationUSD = 2.00;           // Min Penetration ($2.00 Judas Shield)
input double          LondonMinBodyRatio      = 0.60;           // Min Candle Body Ratio (60%)
input double          LondonRVOL_Multiplier   = 1.10;           // RVOL Multiplier (1.10x SMA20)
input bool            FilterPreOpenTrap0845   = true;           // Shield: Require 1.4x RVOL at 08:45 Pre-Open
input double          Sniper_Min_SL_USD       = 8.00;           // London Min Base SL USD ($8.00)
input double          Sniper_ATR_Multiplier   = 1.60;           // Dynamic ATR SL Multiplier (1.6x M15 ATR)
input double          Sniper_RR_Ratio         = 3.50;           // Risk/Reward Ratio (3.5:1 Runner Target)
input bool            EnableDynamicRatchet    = true;           // Dynamic Ratchet Trailing (BE @ 1.75R, +1.25R @ 2.5R)
input bool            EnablePartialTP         = false;          // Partial TP 50% (Default False to let runners breathe full)
input double          PartialTPRatio          = 2.00;           // Partial TP Trigger Ratio (2.0R)
input bool            UseSunsetExit           = true;           // Sunset Handover Exit at 13:00 Server Time
input int             SunsetHour              = 13;             // Sunset Exit Hour (13:00)
input double          SunsetProfitLockRatio   = 1.25;           // Sunset Profit Lock Ratio (1.25R)
input int             MagicSniper             = 888632;         // Magic Number Sniper v6.3.6a

//--- 3. NEW YORK INSTITUTIONAL ENGINE (v6.3.6a ICT Silver Bullet & Breaker Block)
input string          Header_NY               = "=== NEW YORK INSTITUTIONAL ENGINE (16:00-17:45 ICT FVG) ===";
input int             NYTradeStartHour        = 16;             // NY Session Start Hour (16:00 - Post-News Golden Expansion)
input int             NYTradeStartMin         = 0;              // NY Session Start Minute (16:00)
input int             NYTradeEndHour          = 17;             // NY Session End Hour (17:45 - Cutoff Before London Fix Reversal)
input int             NYTradeEndMin           = 45;             // NY Session End Minute
input double          NY_Min_SL_USD           = 6.00;           // Min Base SL USD ($6.00 Tightened)
input double          NY_ATR_Multiplier       = 1.40;           // Dynamic ATR SL Multiplier (1.4x M15 ATR)
input double          NY_RR_Ratio             = 2.50;           // Risk/Reward Ratio (2.5:1 Target)
input double          NY_RVOL_Multiplier      = 1.05;           // New York RVOL Multiplier (1.05x)
input double          NY_MinADX               = 18.0;           // Min ADX Trend Strength Filter
input bool            NY_RequireLondonAlign   = true;           // Require alignment with London Trend
input double          NY_MaxADR_Percent       = 100.0;          // Max ADR % (Exhaustion Filter: Skip chasing if London already ran >100% ADR)
input bool            NY_RequireICT_FVG       = true;           // Require Fair Value Gap (FVG) or Displacement for Precision Entry
input int             MagicNY                 = 888633;         // Magic Number New York v6.3.6a

//--- 4. CASH FLOW SCALPER ENGINE (Asian Squeeze Range Sweeper v6.3.6 SMC Equilibrium)
input string          Header_Scalper          = "=== ASIAN SQUEEZE SWEEPER (02:30-06:00 SMC EQ) ===";
input int             AsianInitStartHour      = 0;              // Asian Initial Balance Start (00:00)
input int             AsianInitEndHour        = 2;              // Asian Initial Balance End Hour (02:30)
input int             AsianInitEndMin         = 30;             // Asian Initial Balance End Minute
input int             AsianTradeStartHour     = 2;              // Asian Trade Start Hour (02:30)
input int             AsianTradeEndHour       = 6;              // Asian Trade End Hour (06:00 - Cutoff before pre-London)
input double          AsianMinRangeUSD        = 3.00;           // Min Asian Initial Range (Filter dead markets)
input double          AsianMaxRangeUSD        = 12.00;          // Max Asian Initial Range ($12.00 Golden Ceiling)
input double          AsianMinWickRatio       = 0.40;           // Rejection Wick Ratio (>= 40% Strong Pinbar)
input double          AsianMinSweepUSD        = 1.00;           // Min Sweep Outside Initial Range ($1.00)
input bool            Asian_PureMeanReversion = false;          // H1 Macro Trend Bias Required (Proven High Win-Rate Guardian)
input double          ScalperSL_BufferUSD     = 1.50;           // Buffer beyond extreme sweep wick ($1.50)
input double          Scalper_Min_SL_USD      = 2.50;           // Min Base SL USD ($2.50)
input double          Scalper_Max_SL_USD      = 4.50;           // Max SL USD ($4.50 Tight Controlled Risk)
input double          ScalperMinTP_USD        = 5.00;           // Min Scalper Take Profit USD ($5.00)
input bool            EnableScalperBE         = true;           // Asian Scalper Breakeven Lock at +$2.50
input double          ScalperBETriggerUSD     = 2.50;           // Scalper Breakeven Trigger USD (+$2.50)
input bool            AutoCloseBeforeLondon   = true;           // Auto-close open scalp at 06:30 before European pre-market
input int             AutoCloseHourAsian      = 6;              // Auto-close Hour (06:30)
input int             AutoCloseMinAsian       = 30;             // Auto-close Minute
input int             MagicScalper            = 888631;         // Magic Number Scalper v6.3.6

//--- 5. LIQUIDITY SWEEP FADE ENGINE (Smart Money Stop-Hunt Alpha v6.3.6a Institutional)
input string          Header_SweepFade        = "=== LIQUIDITY SWEEP FADE (v6.3.6a JUDAS ALPHA) ===";
input bool            EnableSweepFadeTrade    = true;           // Enable Auto-Trade on Liquidity Sweep Fade (Default True for Full Auto)
input bool            EnableSweepFadeSignal   = true;           // Enable Broadcast Grade A+ Alpha Sweep Signal to Discord
input double          SweepFadeFixedLot       = 0.02;           // Enforced Fixed Lot Size for Sweep Fade (0.02 Lot)
input double          SweepMinWickRatio       = 0.40;           // Min Rejection Wick Ratio (>= 40% Pin-bar / Rejection - Like 41% Winner)
input double          SweepBufferUSD          = 2.50;           // Stop Buffer beyond extreme sweep wick ($2.50 Institutional Penetration)
input double          SweepRR_Multiplier      = 5.00;           // Asymmetric R:R Runner Multiplier (1:5.0)
input double          SweepBE_Trigger_R       = 1.50;           // Breakeven Lock Trigger (+1.50R Profit)
input bool            EnableSweepDynamicTrail = true;           // Progressive Runner Ratchet & Dynamic Trend Trailing
input double          SweepTrailDistance_R    = 1.50;           // Trailing Distance behind peak for deep runners (1.50R)
input int             SweepKillzoneStartHour  = 8;              // London Killzone Window Start (08:00 Server)
input int             SweepKillzoneEndHour    = 11;             // London Killzone Window End Hour (11:30 Server)
input int             SweepKillzoneEndMin     = 30;             // London Killzone Window End Minute
input bool            EnableSweepPartialTP    = true;           // 2-Tier Partial TP: Lock 50% at +1.5R and run 50% to 5.0R!
input double          SweepPartialRatio       = 1.50;           // Partial TP Trigger (+1.50R)
input int             SweepTrapMaxBars        = 6;              // Max Bars to wait for Stop-Hunt Sweep (6 bars = 90 mins)
input int             MagicSweepFade          = 888634;         // Magic Number Sweep Fade v6.3.6a

//--- 6. VOLATILITY & SAFEGUARDS
input string          Header_Safeguards       = "=== VOLATILITY SAFEGUARDS ===";
input int             MaxSpreadPoints         = 150;            // Max Spread (Points)
input double          MaxCandleRangeUSD       = 22.00;          // Exhaustion Shield ($22.00)
input double          SpikeThresholdUSD       = 5.00;           // Shockwave Spike Threshold ($5.00 in 5s)
input bool            EnableMacroNewsShield   = true;           // AI Macro News Shield: Auto-pause entries during High-Impact news
input int             EMAFastPeriod           = 50;             // Fast Trend EMA
input int             EMASlowPeriod           = 200;            // Slow Trend EMA
input int             SlippagePoints          = 30;             // Slippage Tolerance

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
datetime LastBarTime               = 0;
datetime LastResetDay              = 0;
datetime LastTickTime              = 0;
double   LastTickPrice             = 0.0;
bool     SpikeAlert                = false;
datetime SpikeTime                 = 0;
bool     AiNewsStandDown           = false;
bool     AiAsianScalpAllowed       = true;
datetime LastExportTime            = 0;

int      DailyTotalTrades          = 0;
int      DailySniperLossCount      = 0;
int      DailyNYLossCount          = 0;
int      DailyScalperLossCount     = 0;
int      DailySweepLossCount       = 0;
double   DailyPnL                  = 0.0;
double   DailySniperPnL            = 0.0;
double   DailySweepPnL             = 0.0;
double   DailyPnLPct               = 0.0;
double   StartDayEquity            = 0.0;
bool     DailyTargetReached        = false;
bool     DailyGlobalLossReached    = false;

// Stored Asian Pre-Market Range for London Sniper
double   StoredAsianHigh           = 0.0;
double   StoredAsianLow            = 0.0;
datetime StoredAsianDate           = 0;

// Liquidity Sweep Trap State Variables (v6.3.6a)
bool     SweepTrapArmed            = false;
int      SweepTrapSide             = -1;             // OP_BUY or OP_SELL
double   SweepTrapLevel            = 0.0;            // The retail SL level to be hunted
double   SweepTrapBaitEntry        = 0.0;            // Retail bait entry price
datetime SweepTrapArmedTime        = 0;
int      SweepTrapBarCount         = 0;
string   SweepTrapReason           = "";

// London Session Consensus Tracking for New York Alignment
int      LondonDirectionToday      = 0; // +1 for BUY, -1 for SELL, 0 for None

// Partial TP Tracking
bool     PartialTPExecuted         = false;
int      PartialOriginalTicket     = 0;

// Signal Feed Broadcast Tracking (A+, A, B+)
string   LatestSignalJson          = "null";
datetime LastSignalTime            = 0;

void SaveTrapStateToGV()
{
   if(IsTesting()) return;
   GlobalVariableSet("GS_TrapArmed", SweepTrapArmed ? 1.0 : 0.0);
   GlobalVariableSet("GS_TrapSide", (double)SweepTrapSide);
   GlobalVariableSet("GS_TrapLevel", SweepTrapLevel);
   GlobalVariableSet("GS_TrapBarCount", (double)SweepTrapBarCount);
}

void LoadTrapStateFromGV(datetime today)
{
   if(IsTesting()) return;
   if(GlobalVariableCheck("GS_ResetDay") && (datetime)GlobalVariableGet("GS_ResetDay") == today)
   {
      if(GlobalVariableCheck("GS_StartDayEquity"))
         StartDayEquity = GlobalVariableGet("GS_StartDayEquity");
      if(GlobalVariableCheck("GS_AsianHigh") && GlobalVariableCheck("GS_AsianLow"))
      {
         double ah = GlobalVariableGet("GS_AsianHigh");
         double al = GlobalVariableGet("GS_AsianLow");
         if(ah > 0.0 && al > 0.0 && al < 999999.0)
         {
            StoredAsianHigh = ah;
            StoredAsianLow  = al;
            StoredAsianDate = today;
         }
      }
      if(GlobalVariableCheck("GS_TrapArmed"))
      {
         SweepTrapArmed    = (GlobalVariableGet("GS_TrapArmed") > 0.5);
         SweepTrapSide     = (int)GlobalVariableGet("GS_TrapSide");
         SweepTrapLevel    = GlobalVariableGet("GS_TrapLevel");
         SweepTrapBarCount = (int)GlobalVariableGet("GS_TrapBarCount");
      }
   }
}

void BroadcastSignal(string grade, string dir, double entry, double sl, double tp, string strategy, string reason)
{
   // Grade A+ and AAA+ institutional setups ALWAYS bypass the 5-minute cooldown
   bool isHighPriority = (grade == "A+" || grade == "AAA+");
   if(!isHighPriority && (TimeCurrent() - LastSignalTime < 300)) return;
   LastSignalTime = TimeCurrent();
   
   double slDist = MathAbs(entry - sl);
   double tpDist = MathAbs(tp - entry);
   double rr = (slDist > 0) ? (tpDist / slDist) : 0.0;
   
   string sigId = "SIG_" + grade + "_" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   StringReplace(sigId, "+", "P");
   StringReplace(sigId, ".", "");
   StringReplace(sigId, " ", "_");
   StringReplace(sigId, ":", "");
   
   LatestSignalJson = "{" +
      "\"id\": \"" + sigId + "\", " +
      "\"grade\": \"" + grade + "\", " +
      "\"direction\": \"" + dir + "\", " +
      "\"entry\": " + DoubleToString(entry, Digits) + ", " +
      "\"sl\": " + DoubleToString(sl, Digits) + ", " +
      "\"tp\": " + DoubleToString(tp, Digits) + ", " +
      "\"sl_usd\": " + DoubleToString(slDist, 2) + ", " +
      "\"tp_usd\": " + DoubleToString(tpDist, 2) + ", " +
      "\"rr\": \"1 : " + DoubleToString(rr, 2) + "\", " +
      "\"strategy\": \"" + strategy + "\", " +
      "\"reason\": \"" + reason + "\", " +
      "\"time\": \"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\"" +
   "}";
}
int OnInit()
{
   Print("===================================================================");
   Print(" ⚡ GOLD SNIPER v6.3.6b INSTITUTIONAL LIVE XM BRIDGE LOADED (Immutable 1R + Anti-Spam SL)");
   Print(" Architecture: ", EnumToString(OperatingMode));
   Print(" Sniper Runner: Dynamic ATR SL (Min $", Sniper_Min_SL_USD, ", ", Sniper_ATR_Multiplier, "x) | TP RR: ", Sniper_RR_Ratio, ":1 | Risk: ", SniperRiskPercent, "%");
   Print(" NY Trend-Rider: Dynamic ATR SL (Min $", NY_Min_SL_USD, ", ", NY_ATR_Multiplier, "x) | TP: RR ", NY_RR_Ratio, ":1 | Risk: ", NYRiskPercent, "%");
   Print(" Asian Sweeper: SMC Equilibrium (02:30-06:00) | Buffer: $", ScalperSL_BufferUSD, " | Min TP: $", ScalperMinTP_USD, " | Risk: ", ScalperRiskPercent, "%");
   Print(" Jackpot Lock: ", EnableJackpotLock ? ("ACTIVE (Locks NY if Sniper PnL >= $" + DoubleToString(JackpotProfitUSD, 1) + ")") : "DISABLED");
   Print(" Ratchet Trailing: ", EnableDynamicRatchet ? "ACTIVE (+1.75R & +2.5R locks)" : "DISABLED");
   Print(" Liquidity Sweep Fade: ", EnableSweepFadeTrade ? "AUTO-TRADE ACTIVE" : "SIGNAL FEED ONLY", " | Enforced Fixed Lot: ", DoubleToString(SweepFadeFixedLot, 2), " | Target RR 1:", SweepRR_Multiplier, " | Min Wick: ", DoubleToString(SweepMinWickRatio*100, 0), "%");
   Print(" Sweep Fade Trailing: BE @ +", DoubleToString(SweepBE_Trigger_R, 2), "R | Progressive Runner Ratchet: ", EnableSweepDynamicTrail ? "ACTIVE (+1.25R @ 2.5R, +2.5R @ 3.5R, Dynamic Trail @ 1.5R)" : "DISABLED");
   Print(" Safeguards: Spike Guard $5.00, Macro News Shield Active");
   Print("===================================================================");
   CheckDailyResetAndStats();
   CheckAiNewsSentinel();
   if(!IsTesting()) ExportMarketState(true);
   UpdateChartDashboard();
   EventSetTimer(3);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Comment("");
   Print("[GoldSniper Bridge v6.3.6b Apex] Deinitialized. Reason code: ", reason);
}

void OnTimer()
{
   if(!IsTesting())
   {
      CheckDailyResetAndStats();
      CheckAiNewsSentinel();
      ExportMarketState(true);
      UpdateChartDashboard();
   }
}

//+------------------------------------------------------------------+
//| Velocity Spike & Spread Spike Safeguard (Rolling 5-Second Window)|
//+------------------------------------------------------------------+
void CheckVelocitySpike()
{
   datetime now = TimeCurrent();
   double bid = Bid;
   
   if(LastTickTime == 0 || (now - LastTickTime) > 5)
   {
      LastTickTime  = now;
      LastTickPrice = bid;
   }
   else
   {
      double priceDiff = MathAbs(bid - LastTickPrice);
      if(priceDiff >= SpikeThresholdUSD)
      {
         SpikeAlert = true;
         SpikeTime  = now;
         int elapsedSec = (int)MathMax(1, now - LastTickTime);
         Print("[VELOCITY SHOCKWAVE] Price moved $", DoubleToString(priceDiff, 2), " in ", elapsedSec, " seconds! Pausing execution.");
         LastTickTime  = now;
         LastTickPrice = bid;
      }
   }
   
   if(SpikeAlert && (now - SpikeTime) > 60)
   {
      SpikeAlert = false;
   }
}

//+------------------------------------------------------------------+
//| Daily Reset and Discipline Stats Tracker (All 4 Engines)         |
//+------------------------------------------------------------------+
void CheckDailyResetAndStats()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   datetime today = StringToTime(StringFormat("%04d.%02d.%02d 00:00", dt.year, dt.mon, dt.day));
   
   if(today != LastResetDay)
   {
      bool isSameDayReload = (!IsTesting() && GlobalVariableCheck("GS_ResetDay") && (datetime)GlobalVariableGet("GS_ResetDay") == today);
      LastResetDay           = today;
      DailySniperLossCount   = 0;
      DailyNYLossCount       = 0;
      DailyScalperLossCount  = 0;
      DailySweepLossCount    = 0;
      DailyTotalTrades       = 0;
      DailyPnL               = 0.0;
      DailySniperPnL         = 0.0;
      DailySweepPnL          = 0.0;
      DailyPnLPct            = 0.0;
      DailyTargetReached     = false;
      DailyGlobalLossReached = false;
      LondonDirectionToday   = 0;
      PartialTPExecuted      = false;
      PartialOriginalTicket  = 0;
      
      if(isSameDayReload)
      {
         LoadTrapStateFromGV(today);
      }
      else
      {
         StartDayEquity    = AccountEquity();
         StoredAsianHigh   = 0.0;
         StoredAsianLow    = 0.0;
         StoredAsianDate   = 0;
         SweepTrapArmed    = false;
         SweepTrapBarCount = 0;
         if(!IsTesting())
         {
            GlobalVariableSet("GS_ResetDay", (double)today);
            GlobalVariableSet("GS_StartDayEquity", StartDayEquity);
            GlobalVariableSet("GS_AsianHigh", 0.0);
            GlobalVariableSet("GS_AsianLow", 0.0);
            SaveTrapStateToGV();
         }
      }
   }
   
   if(StartDayEquity <= 0) StartDayEquity = AccountEquity();
   
   double closedProfitToday = 0.0;
   double sniperProfitToday = 0.0;
   double sweepProfitToday  = 0.0;
   int sniperLosses  = 0;
   int nyLosses      = 0;
   int scalperLosses = 0;
   int sweepLosses   = 0;
   int todayTradeCount = 0;
   int totalHistory = OrdersHistoryTotal();
   
   for(int i = totalHistory - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_HISTORY))
      {
         int m = OrderMagicNumber();
         if((m == MagicScalper || m == MagicSniper || m == MagicNY || m == MagicSweepFade) && OrderSymbol() == Symbol())
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
            if(OrderCloseTime() >= today)
            {
               double pnl = OrderProfit() + OrderSwap() + OrderCommission();
               closedProfitToday += pnl;
               if(m == MagicSniper) sniperProfitToday += pnl;
               else if(m == MagicSweepFade) sweepProfitToday += pnl;
               if(pnl < 0)
               {
                  if(m == MagicSniper) sniperLosses++;
                  else if(m == MagicNY) nyLosses++;
                  else if(m == MagicScalper) scalperLosses++;
                  else if(m == MagicSweepFade) sweepLosses++;
               }
            }
         }
      }
   }
   
   double floatingProfit = 0.0;
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         int m = OrderMagicNumber();
         if((m == MagicScalper || m == MagicSniper || m == MagicNY || m == MagicSweepFade) && OrderSymbol() == Symbol())
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
            double fp = OrderProfit() + OrderSwap() + OrderCommission();
            floatingProfit += fp;
            if(m == MagicSniper) sniperProfitToday += fp;
            else if(m == MagicSweepFade) sweepProfitToday += fp;
         }
      }
   }
   
   DailyTotalTrades      = todayTradeCount;
   DailySniperLossCount  = sniperLosses;
   DailyNYLossCount      = nyLosses;
   DailyScalperLossCount = scalperLosses;
   DailySweepLossCount   = sweepLosses;
   DailySniperPnL        = sniperProfitToday;
   DailySweepPnL         = sweepProfitToday;
   DailyPnL              = closedProfitToday + floatingProfit;
   DailyPnLPct           = (StartDayEquity > 0) ? (DailyPnL / StartDayEquity) * 100.0 : 0.0;
   
   // Global Profit Target Lock (+15%)
   if(DailyPnLPct >= DailyProfitTargetPct)
   {
      if(!DailyTargetReached)
         Print("[CIRCUIT BREAKER v6.3] Daily profit target (+", DailyProfitTargetPct, "%) reached! PnL: $", DailyPnL, ". Halting for today.");
      DailyTargetReached = true;
   }
   
   // Global Account Loss Lock (-10%)
   if(DailyPnLPct <= -DailyLossLimitPct)
   {
      if(!DailyGlobalLossReached)
         Print("[CIRCUIT BREAKER v6.3] Global daily loss limit (-", DailyLossLimitPct, "%) reached! Halting all trading.");
      DailyGlobalLossReached = true;
   }
}

//+------------------------------------------------------------------+
//| Adaptive Lot Size Calculation by Engine Risk                     |
//+------------------------------------------------------------------+
double CalculateLotSize(double riskPct, double slUSD)
{
   double riskUsd = AccountEquity() * (riskPct / 100.0);
   double contractSize = MarketInfo(Symbol(), MODE_LOTSIZE);
   if(contractSize <= 0) contractSize = 100.0;
   
   double rawLot = riskUsd / (slUSD * contractSize);
   
   double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   if(lotStep <= 0) lotStep = 0.01;
   
   double finalLot = MathFloor(rawLot / lotStep) * lotStep;
   if(finalLot < minLot) finalLot = minLot;
   if(finalLot > maxLot) finalLot = maxLot;
   
   return finalLot;
}

//+------------------------------------------------------------------+
//| Check RVOL (Relative Volume vs SMA20)                            |
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
//| EMERGENCY KILL & FLIP: AAA+ SIGNAL PRIORITY PREEMPTION           |
//+------------------------------------------------------------------+
void HandleEmergencyKillAndFlip(int newSignalType, string setupDesc)
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderMagicNumber() == MagicScalper && OrderSymbol() == Symbol())
         {
            int ticket = OrderTicket();
            double lots = OrderLots();
            int oType  = OrderType();
            
            // 1. OPPOSITE DIRECTION: Emergency Kill Scalper at market price!
            if(oType != newSignalType)
            {
               double closePrice = (oType == OP_BUY) ? Bid : Ask;
               bool res = OrderClose(ticket, lots, closePrice, SlippagePoints, clrRed);
               if(res)
               {
                  Print("[EMERGENCY KILL & FLIP v6.3] ⚡ Opposite Scalper #", ticket, " killed at market! Launching: ", setupDesc);
               }
            }
            // 2. SAME DIRECTION: Cash Out Scalper to Clear Runway for Heavy Runner!
            else
            {
               double closePrice = (oType == OP_BUY) ? Bid : Ask;
               bool res = OrderClose(ticket, lots, closePrice, SlippagePoints, clrGreen);
               if(res)
               {
                  Print("[PROMOTION & CASH LOCK v6.3] 💰 Scalper #", ticket, " banked profit! Launching: ", setupDesc);
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+

// ============================================================================
// [v6.3.6b SURGICAL FIX-01 & FIX-02 + BROKER ANTI-BAN SHIELD]
// IMMUTABLE 1R LOCK, $0.15 STEP GUARD & 10-SECOND PER-TICKET SERVER COOLDOWN
// ============================================================================
int      GS636B_RiskTickets[200];
double   GS636B_RiskValues[200];
datetime GS636B_LastModTime[200];
datetime GS636B_LastCloseTime[200];
int      GS636B_RiskCount = 0;

int GetOrCreateTicketSlot636B(int ticket)
{
   for(int i = 0; i < GS636B_RiskCount; i++)
   {
      if(GS636B_RiskTickets[i] == ticket) return i;
   }
   int idx = GS636B_RiskCount % 200;
   GS636B_RiskTickets[idx]   = ticket;
   GS636B_RiskValues[idx]    = 0.0;
   GS636B_LastModTime[idx]   = 0;
   GS636B_LastCloseTime[idx] = 0;
   if(GS636B_RiskCount < 200) GS636B_RiskCount++;
   return idx;
}

void SetOrderInitRisk636B(int ticket, double riskUSD)
{
   if(ticket <= 0 || riskUSD <= 0.0) return;
   string gvKey = "GS636B_InitRisk_" + IntegerToString(ticket);
   if(!IsTesting())
   {
      GlobalVariableSet(gvKey, riskUSD);
   }
   int idx = GetOrCreateTicketSlot636B(ticket);
   GS636B_RiskValues[idx] = riskUSD;
}

double GetOrderInitRisk636B(int ticket, double openP, double curSL, double curTP, double rrRatio, double minFallbackUSD)
{
   if(ticket > 0)
   {
      string gvKey = "GS636B_InitRisk_" + IntegerToString(ticket);
      if(!IsTesting() && GlobalVariableCheck(gvKey))
      {
         double val = GlobalVariableGet(gvKey);
         if(val >= 1.50 && val <= 50.0) return val;
      }
      for(int i = 0; i < GS636B_RiskCount; i++)
      {
         if(GS636B_RiskTickets[i] == ticket && GS636B_RiskValues[i] >= 1.50)
            return GS636B_RiskValues[i];
      }
   }
   // First-time fallback: derive once from initial SL (if SL is on loss side) or initial TP, then lock it permanently!
   double derived = 0.0;
   if(curSL > 0.0)
   {
      double slDist = MathAbs(openP - curSL);
      if(slDist >= 2.00 && slDist <= 35.00)
         derived = NormalizeDouble(slDist, 2);
   }
   if(derived <= 0.0 && curTP > 0.0 && rrRatio > 0.0)
   {
      double tpDist = MathAbs(curTP - openP) / rrRatio;
      if(tpDist >= 2.00 && tpDist <= 35.00)
         derived = NormalizeDouble(tpDist, 2);
   }
   if(derived < 2.00) derived = minFallbackUSD;
   if(ticket > 0) SetOrderInitRisk636B(ticket, derived);
   return derived;
}

bool SafeModifySL636B(int ticket, double openP, double curSL, double targetSL, double curTP, int oType, double minStepUSD, color modColor)
{
   if(!IsTesting() && (!IsTradeAllowed() || IsTradeContextBusy())) return false;

   targetSL = NormalizeDouble(targetSL, Digits);
   curSL    = NormalizeDouble(curSL, Digits);
   if(MathAbs(targetSL - curSL) < minStepUSD) return false;

   double stopDist   = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
   double freezeDist = MarketInfo(Symbol(), MODE_FREEZELEVEL) * Point;
   double minBrokerDist = MathMax(stopDist, freezeDist) + (2.0 * Point);

   if(oType == OP_BUY)
   {
      if(curSL > 0.0 && targetSL < (curSL + minStepUSD)) return false;
      if((Bid - targetSL) < minBrokerDist) return false;
   }
   else if(oType == OP_SELL)
   {
      if(curSL > 0.0 && targetSL > (curSL - minStepUSD)) return false;
      if((targetSL - Ask) < minBrokerDist) return false;
   }
   else return false;

   // Broker Anti-Ban Cooldown: Enforce minimum 10 seconds between OrderModify attempts on the same ticket!
   int idx = GetOrCreateTicketSlot636B(ticket);
   datetime now = TimeCurrent();
   if(!IsTesting() && (now - GS636B_LastModTime[idx]) < 10) return false;
   GS636B_LastModTime[idx] = now;

   ResetLastError();
   bool res = OrderModify(ticket, openP, targetSL, curTP, 0, modColor);
   if(!res)
   {
      int err = GetLastError();
      Print("[BROKER SHIELD v6.3.6b] OrderModify paused 10s on #", ticket, " (Err ", err, "). Anti-spam cooldown active.");
   }
   return res;
}

bool SafeCloseOrder636B(int ticket, double lots, double closePrice, int slippage, color closeColor)
{
   if(!IsTesting() && (!IsTradeAllowed() || IsTradeContextBusy())) return false;

   double freezeDist = MarketInfo(Symbol(), MODE_FREEZELEVEL) * Point;
   if(OrderSelect(ticket, SELECT_BY_TICKET))
   {
      double curSL = OrderStopLoss();
      double curTP = OrderTakeProfit();
      if(freezeDist > 0.0)
      {
         if(curSL > 0.0 && MathAbs(closePrice - curSL) <= freezeDist) return false;
         if(curTP > 0.0 && MathAbs(closePrice - curTP) <= freezeDist) return false;
      }
   }

   // Broker Anti-Ban Cooldown: Enforce minimum 10 seconds between OrderClose attempts on the same ticket!
   int idx = GetOrCreateTicketSlot636B(ticket);
   datetime now = TimeCurrent();
   if(!IsTesting() && (now - GS636B_LastCloseTime[idx]) < 10) return false;
   GS636B_LastCloseTime[idx] = now;

   ResetLastError();
   bool res = OrderClose(ticket, lots, closePrice, slippage, closeColor);
   if(!res)
   {
      int err = GetLastError();
      Print("[BROKER SHIELD v6.3.6b] OrderClose paused 10s on #", ticket, " (Err ", err, "). Anti-spam cooldown active.");
   }
   return res;
}

//+------------------------------------------------------------------+
//| Manage Positions (v6.3.6b Immutable 1R + Anti-Spam SafeModifySL) |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   double spreadOffset = (MarketInfo(Symbol(), MODE_SPREAD) * Point);
   double minStep = 0.15; // [BUG-02 FIX] Minimum $0.15 (15 points) step guard prevents 1-cent floating spread spam!
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         int m = OrderMagicNumber();
         if(OrderSymbol() == Symbol())
         {
            int ticket    = OrderTicket();
            int oType     = OrderType();
            double openP  = OrderOpenPrice();
            double curSL  = OrderStopLoss();
            double curTP  = OrderTakeProfit();
            double lots   = OrderLots();
            
            // 1. ASIAN SCALPER MANAGEMENT (Breakeven + Auto-Close at 06:30)
            if(m == MagicScalper)
            {
               double scalpProfitUSD = (oType == OP_BUY) ? (Bid - openP) : (openP - Ask);
               
               if(EnableScalperBE && scalpProfitUSD >= ScalperBETriggerUSD)
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + spreadOffset + 0.50, Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrSkyBlue))
                        Print("[SCALPER BE v6.3.6b] Scalp Buy #", ticket, " SL locked at Risk-Free +$0.50 (Profit: +$", scalpProfitUSD, ")");
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - spreadOffset - 0.50, Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrOrange))
                        Print("[SCALPER BE v6.3.6b] Scalp Sell #", ticket, " SL locked at Risk-Free +$0.50 (Profit: +$", scalpProfitUSD, ")");
                  }
               }
               
               if(AutoCloseBeforeLondon)
               {
                  if((dt.hour == AutoCloseHourAsian && dt.min >= AutoCloseMinAsian) || dt.hour > AutoCloseHourAsian)
                  {
                     double cPrice = (oType == OP_BUY) ? Bid : Ask;
                     double pnl = OrderProfit() + OrderSwap() + OrderCommission();
                     if(SafeCloseOrder636B(ticket, lots, cPrice, SlippagePoints, clrSilver))
                     {
                        Print("[SCALPER AUTO-CLOSE v6.3.6b] Scalp #", ticket, " closed at 06:30 (PnL: $", pnl, ") before European pre-market.");
                        continue;
                     }
                  }
               }
            }
            
            // -------------------------------------------------------------
            // 2. LONDON SNIPER RUNNER MANAGEMENT (v6.3.6b Immutable 1R)
            // -------------------------------------------------------------
            if(m == MagicSniper)
            {
               double profitUSD = (oType == OP_BUY) ? (Bid - openP) : (openP - Ask);
               
               // [BUG-01 FIX] Immutable initial 1R risk locked at order creation (unaffected by manual TP edits!)
               double sniperRiskUSD = GetOrderInitRisk636B(ticket, openP, curSL, curTP, Sniper_RR_Ratio, Sniper_Min_SL_USD);
               
               // A. DYNAMIC RATCHET TRAILING
               if(EnableDynamicRatchet)
               {
                  // Stage 2: Profit >= 2.50R -> Lock in +1.25R Guaranteed Profit
                  if(profitUSD >= (sniperRiskUSD * 2.50))
                  {
                     if(oType == OP_BUY)
                     {
                        double targetSL = NormalizeDouble(openP + (sniperRiskUSD * 1.25), Digits);
                        if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrLime))
                           Print("[SNIPER RATCHET STAGE 2 v6.3.6b] Sniper Buy #", ticket, " SL locked at +1.25R (+", NormalizeDouble(sniperRiskUSD * 1.25, 2), " USD)");
                     }
                     else if(oType == OP_SELL)
                     {
                        double targetSL = NormalizeDouble(openP - (sniperRiskUSD * 1.25), Digits);
                        if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrLime))
                           Print("[SNIPER RATCHET STAGE 2 v6.3.6b] Sniper Sell #", ticket, " SL locked at +1.25R (+", NormalizeDouble(sniperRiskUSD * 1.25, 2), " USD)");
                     }
                  }
                  // Stage 1: Profit >= 1.75R -> Move SL to Risk-Free (spread + 0.50 cover)
                  else if(profitUSD >= (sniperRiskUSD * 1.75))
                  {
                     if(oType == OP_BUY)
                     {
                        double targetSL = NormalizeDouble(openP + spreadOffset + 0.50, Digits);
                        if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrBlue))
                           Print("[SNIPER RATCHET STAGE 1 v6.3.6b] Sniper Buy #", ticket, " SL moved to Risk-Free Breakeven");
                     }
                     else if(oType == OP_SELL)
                     {
                        double targetSL = NormalizeDouble(openP - spreadOffset - 0.50, Digits);
                        if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrBlue))
                           Print("[SNIPER RATCHET STAGE 1 v6.3.6b] Sniper Sell #", ticket, " SL moved to Risk-Free Breakeven");
                     }
                  }
               }
               
               // B. OPTIONAL PARTIAL TP 50%
               if(EnablePartialTP && !PartialTPExecuted && profitUSD >= (sniperRiskUSD * PartialTPRatio))
               {
                  double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                  double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                  double closeLot = MathFloor((lots * 0.50) / lotStep) * lotStep;
                  
                  if(closeLot >= minLot && (lots - closeLot) >= minLot)
                  {
                     double cPrice = (oType == OP_BUY) ? Bid : Ask;
                     if(SafeCloseOrder636B(ticket, closeLot, cPrice, SlippagePoints, clrGold))
                     {
                        PartialTPExecuted = true;
                        Print("[PARTIAL TP v6.3.6b] Closed 50% at +$", profitUSD, ". Setting BE on remaining ticket...");
                        for(int k = 0; k < OrdersTotal(); k++)
                        {
                           if(OrderSelect(k, SELECT_BY_POS, MODE_TRADES))
                           {
                              if(OrderMagicNumber() == MagicSniper && OrderSymbol() == Symbol())
                              {
                                 int remTicket = OrderTicket();
                                 SetOrderInitRisk636B(remTicket, sniperRiskUSD);
                                 double beSL = (OrderType() == OP_BUY) ? 
                                    NormalizeDouble(OrderOpenPrice() + spreadOffset + 0.30, Digits) :
                                    NormalizeDouble(OrderOpenPrice() - spreadOffset - 0.30, Digits);
                                 SafeModifySL636B(remTicket, OrderOpenPrice(), OrderStopLoss(), beSL, OrderTakeProfit(), OrderType(), minStep, clrBlue);
                                 break;
                              }
                           }
                        }
                     }
                  }
               }
               
               // C. SUNSET HANDOVER RULE (13:00 Server Time Exit before US Session)
               if(UseSunsetExit && dt.hour >= SunsetHour)
               {
                  if(profitUSD >= (sniperRiskUSD * SunsetProfitLockRatio))
                  {
                     double cPrice = (oType == OP_BUY) ? Bid : Ask;
                     if(SafeCloseOrder636B(ticket, lots, cPrice, SlippagePoints, clrGold))
                     {
                        Print("[SUNSET EXIT v6.3.6b] Sniper #", ticket, " locked profit +$", profitUSD, " before US Session.");
                        continue;
                     }
                  }
               }
            }
            
            // -------------------------------------------------------------
            // 4. LIQUIDITY SWEEP FADE RUNNER MANAGEMENT (v6.3.6b Immutable 1R)
            // -------------------------------------------------------------
            if(m == MagicSweepFade)
            {
               double profitUSD = (oType == OP_BUY) ? (Bid - openP) : (openP - Ask);
               
               // [BUG-01 FIX] Immutable initial 1R risk locked at order creation (unaffected by manual TP edits!)
               double sweepRiskUSD = GetOrderInitRisk636B(ticket, openP, curSL, curTP, SweepRR_Multiplier, 3.0);

               // 2-TIER PARTIAL TAKE PROFIT (+1.5R Lock 50%, Run remaining 50% to 5.0R)
               if(EnableSweepPartialTP && profitUSD >= (sweepRiskUSD * SweepPartialRatio))
               {
                  string gvKey = "GS_SwPart_" + IntegerToString(ticket);
                  if(!GlobalVariableCheck(gvKey))
                  {
                     double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                     double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                     if(lotStep <= 0) lotStep = 0.01;
                     double closeLot = MathFloor((lots * 0.50) / lotStep) * lotStep;
                     if(closeLot >= minLot && (lots - closeLot) >= minLot)
                     {
                        double cPrice = (oType == OP_BUY) ? Bid : Ask;
                        if(SafeCloseOrder636B(ticket, closeLot, cPrice, SlippagePoints, clrGold))
                        {
                           GlobalVariableSet(gvKey, 1.0);
                           Print("[SWEEP FADE 2-TIER v6.3.6b] Partial TP: Closed 50% (", closeLot, " Lots) at +1.5R (+", profitUSD, " USD). Moving remaining lot to Breakeven!");
                           
                           int childTicket = -1;
                           for(int k = OrdersTotal() - 1; k >= 0; k--)
                           {
                              if(OrderSelect(k, SELECT_BY_POS, MODE_TRADES))
                              {
                                 if(OrderMagicNumber() == MagicSweepFade && OrderSymbol() == Symbol() && OrderType() == oType)
                                 {
                                    childTicket = OrderTicket();
                                    break;
                                 }
                              }
                           }
                           
                           if(childTicket > 0 && OrderSelect(childTicket, SELECT_BY_TICKET))
                           {
                              string childGv = "GS_SwPart_" + IntegerToString(childTicket);
                              GlobalVariableSet(childGv, 1.0);
                              SetOrderInitRisk636B(childTicket, sweepRiskUSD); // Propagate immutable 1R to child ticket!
                              
                              double beSL = (oType == OP_BUY) ? 
                                 NormalizeDouble(OrderOpenPrice() + spreadOffset + 0.30, Digits) :
                                 NormalizeDouble(OrderOpenPrice() - spreadOffset - 0.30, Digits);
                              if(SafeModifySL636B(childTicket, OrderOpenPrice(), OrderStopLoss(), beSL, OrderTakeProfit(), oType, minStep, clrBlue))
                                 Print("[SWEEP FADE 2-TIER v6.3.6b] Child Ticket #", childTicket, " SL moved to Risk-Free Breakeven successfully!");
                           }
                           continue;
                        }
                     }
                  }
               }

               // Stage 3 & Dynamic Progressive Trailing: Profit >= 3.50R
               if(EnableSweepDynamicTrail && profitUSD >= (sweepRiskUSD * 3.50))
               {
                  if(oType == OP_BUY)
                  {
                     double trailSL  = NormalizeDouble(Bid - (sweepRiskUSD * SweepTrailDistance_R), Digits);
                     double lockSL   = NormalizeDouble(openP + (sweepRiskUSD * 2.50), Digits);
                     double targetSL = MathMax(lockSL, trailSL);
                     
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrLime))
                        Print("[SWEEP FADE DYNAMIC TRAIL v6.3.6b] Buy #", ticket, " SL trailed to ", targetSL, " (Locked Profit: +", NormalizeDouble(targetSL - openP, 2), " USD)");
                  }
                  else if(oType == OP_SELL)
                  {
                     double trailSL  = NormalizeDouble(Ask + (sweepRiskUSD * SweepTrailDistance_R), Digits);
                     double lockSL   = NormalizeDouble(openP - (sweepRiskUSD * 2.50), Digits);
                     double targetSL = MathMin(lockSL, trailSL);
                     
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrLime))
                        Print("[SWEEP FADE DYNAMIC TRAIL v6.3.6b] Sell #", ticket, " SL trailed to ", targetSL, " (Locked Profit: +", NormalizeDouble(openP - targetSL, 2), " USD)");
                  }
               }
               // Stage 2: Profit >= 2.50R -> Lock in +1.25R Guaranteed Profit
               else if(EnableSweepDynamicTrail && profitUSD >= (sweepRiskUSD * 2.50))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + (sweepRiskUSD * 1.25), Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrLime))
                        Print("[SWEEP FADE RATCHET STAGE 2 v6.3.6b] Buy #", ticket, " SL locked at +1.25R (+", NormalizeDouble(sweepRiskUSD * 1.25, 2), " USD)");
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - (sweepRiskUSD * 1.25), Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrLime))
                        Print("[SWEEP FADE RATCHET STAGE 2 v6.3.6b] Sell #", ticket, " SL locked at +1.25R (+", NormalizeDouble(sweepRiskUSD * 1.25, 2), " USD)");
                  }
               }
               // Stage 1: Profit >= SweepBE_Trigger_R (Default +1.50R) -> Move SL to Risk-Free Breakeven
               else if(profitUSD >= (sweepRiskUSD * SweepBE_Trigger_R))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + spreadOffset + 0.30, Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrBlue))
                        Print("[SWEEP FADE BE STAGE 1 v6.3.6b] Buy #", ticket, " SL moved to Risk-Free Breakeven (+1.50R reached)");
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - spreadOffset - 0.30, Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrBlue))
                        Print("[SWEEP FADE BE STAGE 1 v6.3.6b] Sell #", ticket, " SL moved to Risk-Free Breakeven (+1.50R reached)");
                  }
               }
            }

            // -------------------------------------------------------------
            // 3. NEW YORK INSTITUTIONAL TREND-RIDER MANAGEMENT (v6.3.6b Immutable 1R)
            // -------------------------------------------------------------
            if(m == MagicNY)
            {
               double profitUSD = (oType == OP_BUY) ? (Bid - openP) : (openP - Ask);
               
               // [BUG-01 FIX] Immutable initial 1R risk locked at order creation (unaffected by manual TP edits!)
               double initialRiskUSD = GetOrderInitRisk636B(ticket, openP, curSL, curTP, NY_RR_Ratio, NY_Min_SL_USD);
               
               // Stage 2: Profit Ratchet (+0.75R Lock) when profit reaches 1.50R
               if(profitUSD >= (initialRiskUSD * 1.50))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + (initialRiskUSD * 0.75), Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrGreen))
                        Print("[NY RATCHET STAGE 2 v6.3.6b] NY Buy #", ticket, " SL locked at +0.75R (+", NormalizeDouble(initialRiskUSD * 0.75, 2), " USD)");
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - (initialRiskUSD * 0.75), Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrGreen))
                        Print("[NY RATCHET STAGE 2 v6.3.6b] NY Sell #", ticket, " SL locked at +0.75R (+", NormalizeDouble(initialRiskUSD * 0.75, 2), " USD)");
                  }
               }
               // Stage 1: Breakeven Lock (+0.50 cover) when profit reaches 1.00R
               else if(profitUSD >= initialRiskUSD)
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + spreadOffset + 0.50, Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrBlue))
                        Print("[NY RATCHET STAGE 1 v6.3.6b] NY Buy #", ticket, " SL moved to Breakeven (+0.50 cover)");
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - spreadOffset - 0.50, Digits);
                     if(SafeModifySL636B(ticket, openP, curSL, targetSL, curTP, oType, minStep, clrBlue))
                        Print("[NY RATCHET STAGE 1 v6.3.6b] NY Sell #", ticket, " SL moved to Breakeven (+0.50 cover)");
                  }
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check AI Macro News Sentinel from Python Engine                  |
//+------------------------------------------------------------------+
void CheckAiNewsSentinel()
{
   if(IsTesting() || !EnableMacroNewsShield)
   {
      AiNewsStandDown = false;
      return;
   }
   if(!FileIsExist("ai_sentinel.json")) return;
   int handle = FileOpen("ai_sentinel.json", FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE) return;
   string content = "";
   while(!FileIsEnding(handle)) content += FileReadString(handle);
   FileClose(handle);
   if(StringFind(content, "\"stand_down\": true") >= 0)
   {
      if(!AiNewsStandDown)
         Print("[AI NEWS SENTINEL v6.3.6a] High-Impact Macro News Active! Stand-Down engaged to prevent slippage.");
      AiNewsStandDown = true;
   }
   else
   {
      if(AiNewsStandDown)
         Print("[AI NEWS SENTINEL v6.3.6a] News window cleared. Stand-Down disengaged.");
      AiNewsStandDown = false;
   }
   
   if(StringFind(content, "\"asian_scalp_allowed\": false") >= 0)
   {
      if(AiAsianScalpAllowed)
         Print("[AI NEWS SENTINEL v6.3.6a] Asian Scalper halted by AI Bridge (High-Volatility / Geopolitical Event)!");
      AiAsianScalpAllowed = false;
   }
   else
   {
      AiAsianScalpAllowed = true;
   }
}

//+------------------------------------------------------------------+
//| Export Market State to CSV and JSON (Bridge for Python AI Agent) |
//+------------------------------------------------------------------+
void ExportMarketState(bool forceExport = false)
{
   if(!forceExport && TimeCurrent() == LastExportTime) return;
   LastExportTime = TimeCurrent();

   // 1. Lightweight CSV
   int handleCsv = FileOpen("bridge_market_state.csv", FILE_WRITE|FILE_CSV, ",");
   if(handleCsv != INVALID_HANDLE)
   {
      FileWrite(handleCsv, "Symbol", "Time", "Bid", "Ask", "Spread", "H1_Trend", "M15_Trend", "Asian_High", "Asian_Low", "DailyPnL", "DailyTrades", "DailySniperPnL");
      string h1Trend = (iClose(Symbol(), PERIOD_H1, 1) > iMA(Symbol(), PERIOD_H1, EMASlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 1)) ? "BULL" : "BEAR";
      string m15Trend = (iClose(Symbol(), PERIOD_M15, 1) > iMA(Symbol(), PERIOD_M15, EMAFastPeriod, 0, MODE_EMA, PRICE_CLOSE, 1)) ? "BULL" : "BEAR";
      FileWrite(handleCsv, Symbol(), TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS), DoubleToStr(Bid, Digits), DoubleToStr(Ask, Digits), 
                IntegerToString((int)MarketInfo(Symbol(), MODE_SPREAD)), h1Trend, m15Trend, 
                DoubleToStr(StoredAsianHigh, Digits), DoubleToStr(StoredAsianLow, Digits), 
                DoubleToStr(DailyPnL, 2), IntegerToString(DailyTotalTrades), DoubleToStr(DailySniperPnL, 2));
      FileClose(handleCsv);
   }

   double barHigh0 = iHigh(Symbol(), PERIOD_M15, 0);
   double barLow0  = iLow(Symbol(), PERIOD_M15, 0);

   // 2. Full JSON State for Python AI Agent v6.3.6a
   string json = "{\n";
   json += "  \"version\": \"6.3.5-Beta\",\n";
   json += "  \"sweep_fade_trade_enabled\": " + (EnableSweepFadeTrade ? "true" : "false") + ",\n";
   json += "  \"sweep_fade_fixed_lot\": " + DoubleToString(SweepFadeFixedLot, 2) + ",\n";
   json += "  \"sweep_fade_be_r\": " + DoubleToString(SweepBE_Trigger_R, 2) + ",\n";
   json += "  \"sweep_fade_trailing\": " + (EnableSweepDynamicTrail ? "true" : "false") + ",\n";
   json += "  \"sweep_trap_armed\": " + (SweepTrapArmed ? "true" : "false") + ",\n";
   json += "  \"sweep_trap_level\": " + DoubleToString(SweepTrapLevel, Digits) + ",\n";
   json += "  \"symbol\": \"" + Symbol() + "\",\n";
   json += "  \"server_time\": \"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS) + "\",\n";
   json += "  \"bid\": " + DoubleToString(Bid, Digits) + ",\n";
   json += "  \"ask\": " + DoubleToString(Ask, Digits) + ",\n";
   json += "  \"bar_high\": " + DoubleToString(barHigh0, Digits) + ",\n";
   json += "  \"bar_low\": " + DoubleToString(barLow0, Digits) + ",\n";
   json += "  \"spread_points\": " + IntegerToString((int)MarketInfo(Symbol(), MODE_SPREAD)) + ",\n";
   json += "  \"balance\": " + DoubleToString(AccountBalance(), 2) + ",\n";
   json += "  \"equity\": " + DoubleToString(AccountEquity(), 2) + ",\n";
   json += "  \"daily_pnl\": " + DoubleToString(DailyPnL, 2) + ",\n";
   json += "  \"daily_pnl_pct\": " + DoubleToString(DailyPnLPct, 2) + ",\n";
   json += "  \"daily_sniper_pnl\": " + DoubleToString(DailySniperPnL, 2) + ",\n";
   json += "  \"daily_sweep_pnl\": " + DoubleToString(DailySweepPnL, 2) + ",\n";
   json += "  \"daily_total_trades\": " + IntegerToString(DailyTotalTrades) + ",\n";
   json += "  \"daily_sniper_losses\": " + IntegerToString(DailySniperLossCount) + ",\n";
   json += "  \"daily_ny_losses\": " + IntegerToString(DailyNYLossCount) + ",\n";
   json += "  \"daily_scalper_losses\": " + IntegerToString(DailyScalperLossCount) + ",\n";
   json += "  \"daily_sweep_losses\": " + IntegerToString(DailySweepLossCount) + ",\n";
   json += "  \"jackpot_locked\": " + ((EnableJackpotLock && DailySniperPnL >= JackpotProfitUSD) ? "true" : "false") + ",\n";
   json += "  \"daily_target_hit\": " + (DailyTargetReached ? "true" : "false") + ",\n";
   json += "  \"daily_loss_hit\": " + (DailyGlobalLossReached ? "true" : "false") + ",\n";
   json += "  \"spike_alert\": " + (SpikeAlert ? "true" : "false") + ",\n";
   json += "  \"news_stand_down\": " + (AiNewsStandDown ? "true" : "false") + ",\n";
   json += "  \"stored_asian_high\": " + DoubleToString(StoredAsianHigh, Digits) + ",\n";
   json += "  \"stored_asian_low\": " + DoubleToString(StoredAsianLow, Digits) + ",\n";
   json += "  \"london_direction\": " + IntegerToString(LondonDirectionToday) + ",\n";
   json += "  \"latest_signal\": " + LatestSignalJson + ",\n";
   
   int openCount = 0;
   string openOrdersJson = "[";
   for(int i = 0; i < OrdersTotal(); i++)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol())
         {
            int m = OrderMagicNumber();
            if(openCount > 0) openOrdersJson += ", ";
            string mName = "User_Manual";
            if(m == MagicSniper) mName = "Sniper";
            else if(m == MagicNY) mName = "NewYork";
            else if(m == MagicScalper) mName = "Scalper";
            else if(m == MagicSweepFade) mName = "SweepFade";
            
            openOrdersJson += "{\"ticket\": " + IntegerToString(OrderTicket()) + 
                              ", \"magic\": " + IntegerToString(m) +
                              ", \"engine\": \"" + mName + "\"" +
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
   json += "  \"open_orders\": " + openOrdersJson + ",\n";

   // Export today's closed market orders for Python AI Agent lifecycle tracking
   MqlDateTime dtNow;
   TimeToStruct(TimeCurrent(), dtNow);
   datetime todayStart = StringToTime(StringFormat("%04d.%02d.%02d 00:00", dtNow.year, dtNow.mon, dtNow.day));
   int closedCount = 0;
   string closedOrdersJson = "[";
   for(int h = OrdersHistoryTotal() - 1; h >= 0; h--)
   {
      if(OrderSelect(h, SELECT_BY_POS, MODE_HISTORY))
      {
         if(OrderSymbol() == Symbol() && OrderType() <= OP_SELL && OrderCloseTime() >= todayStart)
         {
            int m = OrderMagicNumber();
            if(closedCount > 0) closedOrdersJson += ", ";
            string mName = "User_Manual";
            if(m == MagicSniper) mName = "Sniper";
            else if(m == MagicNY) mName = "NewYork";
            else if(m == MagicScalper) mName = "Scalper";
            else if(m == MagicSweepFade) mName = "SweepFade";

            double netProfit = OrderProfit() + OrderSwap() + OrderCommission();
            closedOrdersJson += "{\"ticket\": " + IntegerToString(OrderTicket()) +
                                ", \"magic\": " + IntegerToString(m) +
                                ", \"engine\": \"" + mName + "\"" +
                                ", \"type\": " + IntegerToString(OrderType()) +
                                ", \"lots\": " + DoubleToString(OrderLots(), 2) +
                                ", \"open_price\": " + DoubleToString(OrderOpenPrice(), Digits) +
                                ", \"close_price\": " + DoubleToString(OrderClosePrice(), Digits) +
                                ", \"sl\": " + DoubleToString(OrderStopLoss(), Digits) +
                                ", \"tp\": " + DoubleToString(OrderTakeProfit(), Digits) +
                                ", \"profit\": " + DoubleToString(netProfit, 2) +
                                ", \"close_time\": \"" + TimeToString(OrderCloseTime(), TIME_DATE|TIME_SECONDS) + "\"}";
            closedCount++;
            if(closedCount >= 15) break;
         }
      }
   }
   closedOrdersJson += "]";
   json += "  \"recent_closed_orders\": " + closedOrdersJson + "\n";
   json += "}\n";

   int handleJson = FileOpen("market_state.json", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handleJson != INVALID_HANDLE)
   {
      FileWriteString(handleJson, json);
      FileClose(handleJson);
   }
}

//+------------------------------------------------------------------+
//| Main Strategy Logic Execution (Quad-Engine Institutional Apex)   |
//+------------------------------------------------------------------+
void RunDualModeStrategy()
{
   if(SpikeAlert) return;
   if(AiNewsStandDown) return; // Paused during verified High-Impact News Release
   
   // Execution strictly occurs on NEW M15 BAR
   datetime currentBarTime = iTime(Symbol(), PERIOD_M15, 0);
   if(currentBarTime == LastBarTime) return;
   
   int currentSpread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   if(currentSpread > MaxSpreadPoints) return;
   LastBarTime = currentBarTime;
   
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   double timeDec = dt.hour + (dt.min / 60.0);
   
   double c1 = iClose(Symbol(), PERIOD_M15, 1);
   double o1 = iOpen(Symbol(), PERIOD_M15, 1);
   double h1 = iHigh(Symbol(), PERIOD_M15, 1);
   double l1 = iLow(Symbol(), PERIOD_M15, 1);
   double range1 = h1 - l1;
   
   double c2 = iClose(Symbol(), PERIOD_M15, 2);
   double o2 = iOpen(Symbol(), PERIOD_M15, 2);
   
   if(range1 <= 0.50 || range1 > MaxCandleRangeUSD) return;
   
   double upperWick = h1 - MathMax(c1, o1);
   double lowerWick = MathMin(c1, o1) - l1;
   double body1     = MathAbs(c1 - o1);
   
   // Multi-Timeframe Macro Trend Indicators
   double ema50_h1   = iMA(Symbol(), PERIOD_H1, EMAFastPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   double ema200_h1  = iMA(Symbol(), PERIOD_H1, EMASlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   double c1_h1      = iClose(Symbol(), PERIOD_H1, 1);
   bool isH1Bull     = (c1_h1 > ema200_h1) && (ema50_h1 > ema200_h1);
   bool isH1Bear     = (c1_h1 < ema200_h1) && (ema50_h1 < ema200_h1);
   
   double ema50_m15  = iMA(Symbol(), PERIOD_M15, EMAFastPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   double ema200_m15 = iMA(Symbol(), PERIOD_M15, EMASlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 1);
   
   datetime midnight = StringToTime(StringFormat("%04d.%02d.%02d 00:00", dt.year, dt.mon, dt.day));
   
   // Ensure Pre-London Asian Box is always computed after 08:00 for both Auto-Bot & Secondary Signal Scanner
   if(dt.hour >= PreMarketEndHour && (StoredAsianDate != midnight || StoredAsianHigh <= 0.0))
   {
      datetime preStart = midnight + (PreMarketStartHour * 3600);
      datetime preEnd   = midnight + (PreMarketEndHour * 3600);
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
         StoredAsianHigh = preHigh;
         StoredAsianLow  = preLow;
         StoredAsianDate = midnight;
         if(!IsTesting())
         {
            GlobalVariableSet("GS_AsianHigh", StoredAsianHigh);
            GlobalVariableSet("GS_AsianLow", StoredAsianLow);
            GlobalVariableSet("GS_AsianDate", (double)StoredAsianDate);
         }
      }
   }

   // Determine Session Windows (Auto-Order Execution Flags)
   bool allowScalper = false;
   bool allowSniper  = false;
   bool allowNY      = false;
   
   if(!DailyTargetReached && !DailyGlobalLossReached)
   {
      if(OperatingMode == MODE_SNIPER_PURE_v55)
      {
         allowSniper = (dt.hour >= LondonTradeStartHour && (dt.hour < LondonTradeEndHour || (dt.hour == LondonTradeEndHour && dt.min <= 30)));
      }
      else if(OperatingMode == MODE_INSTITUTIONAL_DUAL)
      {
         allowSniper = (dt.hour >= LondonTradeStartHour && (dt.hour < LondonTradeEndHour || (dt.hour == LondonTradeEndHour && dt.min <= 30)));
         allowNY     = (timeDec >= (NYTradeStartHour + NYTradeStartMin/60.0) && timeDec <= (NYTradeEndHour + NYTradeEndMin/60.0));
      }
      else if(OperatingMode == MODE_SCALPER_ONLY)
      {
         allowScalper = (timeDec >= (AsianTradeStartHour + AsianInitEndMin/60.0) && timeDec < AsianTradeEndHour);
      }
      else // MODE_TRI_SESSION_ULTRA
      {
         if(timeDec >= (AsianTradeStartHour + AsianInitEndMin/60.0) && timeDec < AsianTradeEndHour)
            allowScalper = true;
         if(dt.hour >= LondonTradeStartHour && (dt.hour < LondonTradeEndHour || (dt.hour == LondonTradeEndHour && dt.min <= 30)))
            allowSniper = true;
         if(timeDec >= (NYTradeStartHour + NYTradeStartMin/60.0) && timeDec <= (NYTradeEndHour + NYTradeEndMin/60.0))
            allowNY = true;
      }
   }
   
   bool primaryOrderOpenedThisBar = false;

   // ====================================================================
   // 1. ENGINE A: ASIAN SQUEEZE RANGE SWEEPER (02:30 - 06:00)
   // ====================================================================
   if(allowScalper && AiAsianScalpAllowed && DailyScalperLossCount < MaxScalperDailyLosses)
   {
      bool scalperActive = false;
      for(int i = 0; i < OrdersTotal(); i++)
      {
         if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
         {
            if((OrderMagicNumber() == MagicScalper || OrderMagicNumber() == MagicSniper) && OrderSymbol() == Symbol())
            {
               scalperActive = true;
               break;
            }
         }
      }
      
      if(!scalperActive)
      {
         datetime initStart = midnight + (AsianInitStartHour * 3600);
         datetime initEnd   = midnight + (AsianInitEndHour * 3600) + (AsianInitEndMin * 60);
         
         double aHigh = -1.0;
         double aLow  = 999999.0;
         int aBars = 0;
         
         for(int b = 1; b < 40; b++)
         {
            datetime bt = iTime(Symbol(), PERIOD_M15, b);
            if(bt < initStart) break;
            if(bt >= initStart && bt < initEnd)
            {
               double bh = iHigh(Symbol(), PERIOD_M15, b);
               double bl = iLow(Symbol(), PERIOD_M15, b);
               if(bh > aHigh) aHigh = bh;
               if(bl < aLow)  aLow  = bl;
               aBars++;
            }
         }
         
                           double asianSpan = aHigh - aLow;
         // V6.3.6 SMC EQUILIBRIUM FILTER: Range must be between $3.00 and $12.00!
         if(aBars >= 6 && aHigh > 0 && aLow < 999999.0 && asianSpan >= AsianMinRangeUSD && asianSpan <= AsianMaxRangeUSD)
         {
            double asianEquilibrium = NormalizeDouble((aHigh + aLow) / 2.0, Digits);
            
            // H1 Trend Alignment Filter (Proven High Win-Rate Guardian)
            bool sellBiasOk = Asian_PureMeanReversion ? true : isH1Bear;
            bool buyBiasOk  = Asian_PureMeanReversion ? true : isH1Bull;

            // SMC Premium Zone Sell: Swept Asian High + Upper Wick Rejection + Price in Premium Zone (> EQ)
            if(sellBiasOk && h1 >= (aHigh + AsianMinSweepUSD) && (upperWick / range1) >= AsianMinWickRatio && c1 <= aHigh && Bid > asianEquilibrium)
            {
               double slDist = MathMax(Scalper_Min_SL_USD, MathMin(Scalper_Max_SL_USD, NormalizeDouble((h1 + ScalperSL_BufferUSD) - Bid, 2)));
               double tpDist = MathMax(ScalperMinTP_USD, NormalizeDouble(Bid - asianEquilibrium, 2));
               double lot = CalculateLotSize(ScalperRiskPercent, slDist);
               double sl  = NormalizeDouble(Bid + slDist, Digits);
               double tp  = NormalizeDouble(Bid - tpDist, Digits);
               int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, SlippagePoints, sl, tp, "v6.3.6 Scalp SELL (SMC EQ)", MagicScalper, 0, clrOrange);
               if(ticket > 0)
               {
                  DailyTotalTrades++;
                  primaryOrderOpenedThisBar = true;
                  string rReason = "Range $" + DoubleToString(asianSpan, 2) + ", Premium Sell to EQ $" + DoubleToString(asianEquilibrium, 2) + " (R:R 1:" + DoubleToString(tpDist/slDist, 1) + ")";
                  BroadcastSignal("A+", "SELL", Bid, sl, tp, "Asian SMC Liquidity Sweeper", rReason);
                  Print("[ASIAN SMC SELL v6.3.6] Ticket: #", ticket, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " TP: ", tp, " (EQ Target: ", asianEquilibrium, ")");
               }
            }
            // SMC Discount Zone Buy: Swept Asian Low + Lower Wick Rejection + Price in Discount Zone (< EQ)
            else if(buyBiasOk && l1 <= (aLow - AsianMinSweepUSD) && (lowerWick / range1) >= AsianMinWickRatio && c1 >= aLow && Ask < asianEquilibrium)
            {
               double slDist = MathMax(Scalper_Min_SL_USD, MathMin(Scalper_Max_SL_USD, NormalizeDouble(Ask - (l1 - ScalperSL_BufferUSD), 2)));
               double tpDist = MathMax(ScalperMinTP_USD, NormalizeDouble(asianEquilibrium - Ask, 2));
               double lot = CalculateLotSize(ScalperRiskPercent, slDist);
               double sl  = NormalizeDouble(Ask - slDist, Digits);
               double tp  = NormalizeDouble(Ask + tpDist, Digits);
               int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.6 Scalp BUY (SMC EQ)", MagicScalper, 0, clrSkyBlue);
               if(ticket > 0)
               {
                  DailyTotalTrades++;
                  primaryOrderOpenedThisBar = true;
                  string rReason = "Range $" + DoubleToString(asianSpan, 2) + ", Discount Buy to EQ $" + DoubleToString(asianEquilibrium, 2) + " (R:R 1:" + DoubleToString(tpDist/slDist, 1) + ")";
                  BroadcastSignal("A+", "BUY", Ask, sl, tp, "Asian SMC Liquidity Sweeper", rReason);
                  Print("[ASIAN SMC BUY v6.3.6] Ticket: #", ticket, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " TP: ", tp, " (EQ Target: ", asianEquilibrium, ")");
               }
            }
         }
      }
   }
   
   // ====================================================================
   // 2. ENGINE B: LONDON SNIPER RUNNER (08:00 - 11:30) [v5.5 Unchoked Core]
   // ====================================================================
   if(!primaryOrderOpenedThisBar && allowSniper && DailySniperLossCount < MaxSniperDailyLosses)
   {
      if(StoredAsianHigh > 0.0 && StoredAsianLow < 999999.0)
      {
         bool sniperRvolOk = false;
         if(FilterPreOpenTrap0845 && dt.hour == 8 && dt.min == 45)
            sniperRvolOk = CheckRVOL(1.40);
         else
            sniperRvolOk = CheckRVOL(LondonRVOL_Multiplier);
         
         bool wickOkBuy  = (upperWick / range1) <= 0.40;
         bool wickOkSell = (lowerWick / range1) <= 0.40;
         bool isBull = isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15) && wickOkBuy;
         bool isBear = isH1Bear && (c1 < ema200_m15) && (ema50_m15 < ema200_m15) && wickOkSell;
         bool sniperBodyOk = !(dt.hour == 8 && (body1 / range1) < LondonMinBodyRatio);
         
         bool isBuySignal  = sniperRvolOk && sniperBodyOk && isBull && (c1 > StoredAsianHigh) && ((c1 - StoredAsianHigh) >= LondonMinPenetrationUSD) && (c1 > o1);
         bool isSellSignal = sniperRvolOk && sniperBodyOk && isBear && (c1 < StoredAsianLow) && ((StoredAsianLow - c1) >= LondonMinPenetrationUSD) && (c1 < o1);
         
         if(isBuySignal || isSellSignal)
         {
            if(EnableEmergencyKillFlip)
            {
               string setupDesc = isBuySignal ? "AAA+ London Bullish Breakout" : "AAA+ London Bearish Breakdown";
               HandleEmergencyKillAndFlip(isBuySignal ? OP_BUY : OP_SELL, setupDesc);
            }
            
            bool sniperAlreadyActive = false;
            for(int i = 0; i < OrdersTotal(); i++)
            {
               if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
               {
                  if(OrderMagicNumber() == MagicSniper && OrderSymbol() == Symbol())
                  {
                     sniperAlreadyActive = true;
                     break;
                  }
               }
            }
            
            if(!sniperAlreadyActive)
            {
               // Universal Dynamic ATR SL & Target for London Sniper (Adaptive to Volatility Regime)
               double atr15_sniper = iATR(Symbol(), PERIOD_M15, 14, 1);
               double dynamicSniperSL = MathMax(Sniper_Min_SL_USD, NormalizeDouble(atr15_sniper * Sniper_ATR_Multiplier, 2));
               double dynamicSniperTP = NormalizeDouble(dynamicSniperSL * Sniper_RR_Ratio, 2);
               
               if(isBuySignal)
               {
                  double lot = CalculateLotSize(SniperRiskPercent, dynamicSniperSL);
                  double sl  = NormalizeDouble(Ask - dynamicSniperSL, Digits);
                  double tp  = NormalizeDouble(Ask + dynamicSniperTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.6b Sniper BUY", MagicSniper, 0, clrGreen);
                  if(ticket > 0)
                  {
                     SetOrderInitRisk636B(ticket, dynamicSniperSL);
                     DailyTotalTrades++;
                     LondonDirectionToday = 1;
                     primaryOrderOpenedThisBar = true;
                     BroadcastSignal("A+", "BUY", Ask, sl, tp, "London Institutional Breakout", "Asian High Penetrated with RVOL & Macro Bull Trend");
                     Print("[SNIPER RUNNER BUY v6.3.6a] Ticket: #", ticket, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " (", dynamicSniperSL, " USD) TP: ", tp, " (", dynamicSniperTP, " USD)");
                  }
               }
               else if(isSellSignal)
               {
                  double lot = CalculateLotSize(SniperRiskPercent, dynamicSniperSL);
                  double sl  = NormalizeDouble(Bid + dynamicSniperSL, Digits);
                  double tp  = NormalizeDouble(Bid - dynamicSniperTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, SlippagePoints, sl, tp, "v6.3.6b Sniper SELL", MagicSniper, 0, clrRed);
                  if(ticket > 0)
                  {
                     SetOrderInitRisk636B(ticket, dynamicSniperSL);
                     DailyTotalTrades++;
                     LondonDirectionToday = -1;
                     primaryOrderOpenedThisBar = true;
                     BroadcastSignal("A+", "SELL", Bid, sl, tp, "London Institutional Breakout", "Asian Low Penetrated with RVOL & Macro Bear Trend");
                     Print("[SNIPER RUNNER SELL v6.3.6a] Ticket: #", ticket, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " (", dynamicSniperSL, " USD) TP: ", tp, " (", dynamicSniperTP, " USD)");
                  }
               }
            }
         }
      }
   }
   
   // ====================================================================
   // 3. ENGINE C: NEW YORK INSTITUTIONAL TREND-RIDER ENGINE (16:00 - 18:30)
   // ====================================================================
   if(!primaryOrderOpenedThisBar && allowNY && DailyNYLossCount < MaxNYDailyLosses && !(EnableJackpotLock && DailySniperPnL >= JackpotProfitUSD))
   {
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
            // 1. ADR Exhaustion Filter: Check 5-Day Average Daily Range vs Today's Expansion
            double adr5 = 0;
            for(int d = 1; d <= 5; d++) adr5 += (iHigh(Symbol(), PERIOD_D1, d) - iLow(Symbol(), PERIOD_D1, d));
            adr5 /= 5.0;
            double todayRange = iHigh(Symbol(), PERIOD_D1, 0) - iLow(Symbol(), PERIOD_D1, 0);
            bool adrExhausted = (adr5 > 0.0 && (todayRange / adr5) >= (NY_MaxADR_Percent / 100.0));
            
            // Dynamic ATR Stop Loss & Target Calculation (Adaptive Volatility Sizing)
            double atr15 = iATR(Symbol(), PERIOD_M15, 14, 1);
            double dynamicSL = MathMax(NY_Min_SL_USD, NormalizeDouble(atr15 * NY_ATR_Multiplier, 2));
            double dynamicTP = NormalizeDouble(dynamicSL * NY_RR_Ratio, 2);
            
            // 2. ICT Fair Value Gap (FVG) & Displacement Detection on M15
            double h2 = iHigh(Symbol(), PERIOD_M15, 2);
            double l2 = iLow(Symbol(), PERIOD_M15, 2);
            double h0 = iHigh(Symbol(), PERIOD_M15, 0);
            double l0 = iLow(Symbol(), PERIOD_M15, 0);
            
            // Bullish Displacement & FVG: Bar 1 exploded green leaving gap between Bar 2 High and Bar 0 Low
            bool bullDisplacement = (c1 > o1) && ((body1 / range1) >= 0.45);
            bool bullFVG = bullDisplacement && (l0 > h2);
            
            // Bearish Displacement & FVG: Bar 1 exploded red leaving gap between Bar 2 Low and Bar 0 High
            bool bearDisplacement = (c1 < o1) && ((body1 / range1) >= 0.45);
            bool bearFVG = bearDisplacement && (h0 < l2);
            
            // BUY Trend-Rider: H1 Macro Bull + M15 EMAs Bull + London Direction Alignment + No ADR Exhaustion
            bool buyDirectionOk = !adrExhausted && isH1Bull && (c1 > ema200_m15) && (ema50_m15 > ema200_m15);
            if(NY_RequireLondonAlign && LondonDirectionToday < 0) buyDirectionOk = false; // Block counter-trend Sell from London
            
            if(buyDirectionOk)
            {
               bool testedEMA = (l1 <= ema50_m15 + 1.50) && (c1 > ema50_m15);
               bool isBullRejection = (c1 > o1) && (((lowerWick / range1) >= 0.30) || ((body1 / range1) >= 0.45)) && ((upperWick / range1) <= 0.35);
               bool validBuyTrigger = false;
               string setupSubDesc = "";
               
               // 100% Pure ICT FVG Entry (Zero Retail EMA50 Fallback)
               if(bullFVG)
               {
                  validBuyTrigger = true;
                  setupSubDesc = "ICT Bullish FVG Imbalance Expansion";
               }
               
               if(validBuyTrigger)
               {
                  double lot = CalculateLotSize(NYRiskPercent, dynamicSL);
                  double sl  = NormalizeDouble(Ask - dynamicSL, Digits);
                  double tp  = NormalizeDouble(Ask + dynamicTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.6b NY Buy", MagicNY, 0, clrBlue);
                  if(ticket > 0)
                  {
                     SetOrderInitRisk636B(ticket, dynamicSL);
                     DailyTotalTrades++;
                     primaryOrderOpenedThisBar = true;
                     BroadcastSignal("A+", "BUY", Ask, sl, tp, "New York Institutional Engine", setupSubDesc + " with Macro Bull Consensus");
                     Print("[NEW YORK INSTITUTIONAL BUY v6.3.6a] Ticket: #", ticket, " Setup: ", setupSubDesc, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " TP: ", tp);
                  }
               }
            }
            
            // SELL Trend-Rider: H1 Macro Bear + M15 EMAs Bear + London Direction Alignment + No ADR Exhaustion
            bool sellDirectionOk = !adrExhausted && isH1Bear && (c1 < ema200_m15) && (ema50_m15 < ema200_m15);
            if(NY_RequireLondonAlign && LondonDirectionToday > 0) sellDirectionOk = false; // Block counter-trend Buy from London
            
            if(sellDirectionOk)
            {
               bool testedEMA = (h1 >= ema50_m15 - 1.50) && (c1 < ema50_m15);
               bool isBearRejection = (c1 < o1) && (((upperWick / range1) >= 0.30) || ((body1 / range1) >= 0.45)) && ((lowerWick / range1) <= 0.35);
               bool validSellTrigger = false;
               string setupSubDesc = "";
               
               // 100% Pure ICT FVG Entry (Zero Retail EMA50 Fallback)
               if(bearFVG)
               {
                  validSellTrigger = true;
                  setupSubDesc = "ICT Bearish FVG Imbalance Breakdown";
               }
               
               if(validSellTrigger)
               {
                  double lot = CalculateLotSize(NYRiskPercent, dynamicSL);
                  double sl  = NormalizeDouble(Bid + dynamicSL, Digits);
                  double tp  = NormalizeDouble(Bid - dynamicTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, SlippagePoints, sl, tp, "v6.3.6b NY Sell", MagicNY, 0, clrMagenta);
                  if(ticket > 0)
                  {
                     SetOrderInitRisk636B(ticket, dynamicSL);
                     DailyTotalTrades++;
                     primaryOrderOpenedThisBar = true;
                     BroadcastSignal("A+", "SELL", Bid, sl, tp, "New York Institutional Engine", setupSubDesc + " with Macro Bear Consensus");
                     Print("[NEW YORK INSTITUTIONAL SELL v6.3.6a] Ticket: #", ticket, " Setup: ", setupSubDesc, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " TP: ", tp);
                  }
               }
            }
         }
      }
   }

   // ====================================================================
   // 4. ENGINE D: THE LIQUIDITY SWEEP FADE (v6.3.6a Dual-Trap Engine)
   //    - Runs independently of Secondary Grade A signals & works in Strategy Tester!
   //    - Active Institutional Window: 06:00 - 20:45 Server Time (10:00 - 00:45 Thai)
   //    - Dual Radar: (1) Armed EMA50 Pullback Bait Sweep + (2) Asian Box Stop-Hunt Sweep
   // ====================================================================
   double atr_m15_sweep = iATR(Symbol(), PERIOD_M15, 14, 1);
   if(atr_m15_sweep <= 0.0) atr_m15_sweep = 6.0;
   bool allowSweepSession = (timeDec >= 6.0 && timeDec <= 20.75);

   bool sweepAlreadyActive = false;
   for(int s = 0; s < OrdersTotal(); s++)
   {
      if(OrderSelect(s, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderMagicNumber() == MagicSweepFade && OrderSymbol() == Symbol())
         {
            sweepAlreadyActive = true;
            break;
         }
      }
   }

   bool sweepExecutedThisBar = false;

   // Phase A1: Evaluate Armed EMA50 Pullback Trap on Bar Close
   if(SweepTrapArmed)
   {
      SweepTrapBarCount++;
      if(SweepTrapBarCount > SweepTrapMaxBars)
      {
         Print("[TRAP EXPIRED v6.3.6a] Sweep Trap at $", SweepTrapLevel, " expired after ", SweepTrapMaxBars, " bars.");
         SweepTrapArmed = false;
         SaveTrapStateToGV();
      }
      else if(!primaryOrderOpenedThisBar && !sweepAlreadyActive && allowSweepSession && !DailyTargetReached && !DailyGlobalLossReached && DailySweepLossCount < 2)
      {
         // Case 1: Bearish Trap -> Retail Sell stops swept above SweepTrapLevel, Pin-Bar closes back below
         if(SweepTrapSide == OP_SELL)
         {
            bool sweptRetailStops = (h1 >= SweepTrapLevel);
            bool closedBackBelow  = (c1 < SweepTrapLevel);
            bool strongUpperWick  = ((upperWick / range1) >= SweepMinWickRatio);
            bool bearishCandle    = (c1 < o1);

            if(sweptRetailStops && closedBackBelow && strongUpperWick && bearishCandle)
            {
               double entryPrice = Bid;
               double sweepSL    = NormalizeDouble(h1 + SweepBufferUSD, Digits);
               double slDist     = sweepSL - entryPrice;

               if(slDist >= 2.00 && slDist <= 12.00)
               {
                  double sweepTP = NormalizeDouble(entryPrice - (slDist * SweepRR_Multiplier), Digits);

                  if(EnableSweepFadeTrade)
                  {
                     double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                     double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
                     double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                     if(lotStep <= 0) lotStep = 0.01;
                     double lot = MathFloor(SweepFadeFixedLot / lotStep) * lotStep;
                     if(lot < minLot) lot = minLot;
                     if(lot > maxLot) lot = maxLot;
                     int ticket = OrderSend(Symbol(), OP_SELL, lot, entryPrice, SlippagePoints, sweepSL, sweepTP, "v6.3.6b Sweep Fade SELL", MagicSweepFade, 0, clrRed);
                     if(ticket > 0)
                     {
                        DailyTotalTrades++;
                        sweepExecutedThisBar = true;
                        SetOrderInitRisk636B(ticket, slDist);
                        Print("[SWEEP FADE SELL ORDER v6.3.6a] Ticket: #", ticket, " Lots: ", lot, " Price: ", entryPrice, " SL: ", sweepSL, " TP: ", sweepTP, " (RR 1:", SweepRR_Multiplier, ")");
                     }
                  }

                  if(EnableSweepFadeSignal)
                  {
                     string reason = "Retail B+ Stop-Hunt Swept at $" + DoubleToString(SweepTrapLevel, 2) + 
                                     " (High $" + DoubleToString(h1, 2) + "), Pin-bar Rejection Wick " + 
                                     DoubleToString((upperWick / range1) * 100, 0) + "%, Asymmetric R:R 1:" + DoubleToString(SweepRR_Multiplier, 1);
                     BroadcastSignal("A+", "SELL", entryPrice, sweepSL, sweepTP, "The Liquidity Sweep Fade (Judas Stop-Hunt)", reason);
                  }

                  SweepTrapArmed = false;
                  SaveTrapStateToGV();
               }
            }
         }
         // Case 2: Bullish Trap -> Retail Buy stops swept below SweepTrapLevel, Pin-Bar closes back above
         else if(SweepTrapSide == OP_BUY)
         {
            bool sweptRetailStops = (l1 <= SweepTrapLevel);
            bool closedBackAbove  = (c1 > SweepTrapLevel);
            bool strongLowerWick  = ((lowerWick / range1) >= SweepMinWickRatio);
            bool bullishCandle    = (c1 > o1);

            if(sweptRetailStops && closedBackAbove && strongLowerWick && bullishCandle)
            {
               double entryPrice = Ask;
               double sweepSL    = NormalizeDouble(l1 - SweepBufferUSD, Digits);
               double slDist     = entryPrice - sweepSL;

               if(slDist >= 2.00 && slDist <= 12.00)
               {
                  double sweepTP = NormalizeDouble(entryPrice + (slDist * SweepRR_Multiplier), Digits);

                  if(EnableSweepFadeTrade)
                  {
                     double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                     double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
                     double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                     if(lotStep <= 0) lotStep = 0.01;
                     double lot = MathFloor(SweepFadeFixedLot / lotStep) * lotStep;
                     if(lot < minLot) lot = minLot;
                     if(lot > maxLot) lot = maxLot;
                     int ticket = OrderSend(Symbol(), OP_BUY, lot, entryPrice, SlippagePoints, sweepSL, sweepTP, "v6.3.6b Sweep Fade BUY", MagicSweepFade, 0, clrGreen);
                     if(ticket > 0)
                     {
                        DailyTotalTrades++;
                        sweepExecutedThisBar = true;
                        SetOrderInitRisk636B(ticket, slDist);
                        Print("[SWEEP FADE BUY ORDER v6.3.6a] Ticket: #", ticket, " Lots: ", lot, " Price: ", entryPrice, " SL: ", sweepSL, " TP: ", sweepTP, " (RR 1:", SweepRR_Multiplier, ")");
                     }
                  }

                  if(EnableSweepFadeSignal)
                  {
                     string reason = "Retail B+ Stop-Hunt Swept at $" + DoubleToString(SweepTrapLevel, 2) + 
                                     " (Low $" + DoubleToString(l1, 2) + "), Pin-bar Rejection Wick " + 
                                     DoubleToString((lowerWick / range1) * 100, 0) + "%, Asymmetric R:R 1:" + DoubleToString(SweepRR_Multiplier, 1);
                     BroadcastSignal("A+", "BUY", entryPrice, sweepSL, sweepTP, "The Liquidity Sweep Fade (Judas Stop-Hunt)", reason);
                  }

                  SweepTrapArmed = false;
                  SaveTrapStateToGV();
               }
            }
         }
      }
      else
      {
         SaveTrapStateToGV();
      }
   }

   // Phase A2: Direct Asian High / Low Stop-Hunt Sweep Radar (v6.3.6a Strict London Killzone 08:00-11:30)
   if(!primaryOrderOpenedThisBar && !sweepExecutedThisBar && !sweepAlreadyActive && allowSweepSession && !DailyTargetReached && !DailyGlobalLossReached && DailySweepLossCount < 2)
   {
      double sweepCutoff = SweepKillzoneEndHour + (SweepKillzoneEndMin / 60.0);
      if(StoredAsianHigh > 0.0 && StoredAsianLow < 999999.0 && timeDec >= SweepKillzoneStartHour && timeDec <= sweepCutoff)
      {
         // Bearish Judas Sweep of Asian High (Swept >= AsianHigh + SweepBufferUSD, closed back below AsianHigh with >= 35% upper wick)
         bool sweptAsianHigh = (h1 >= (StoredAsianHigh + SweepBufferUSD)) && (c1 < StoredAsianHigh) && (c1 < o1) && ((upperWick / range1) >= SweepMinWickRatio);
         // Bullish Judas Sweep of Asian Low (Swept <= AsianLow - SweepBufferUSD, closed back above AsianLow with >= 35% lower wick)
         bool sweptAsianLow  = (l1 <= (StoredAsianLow - SweepBufferUSD)) && (c1 > StoredAsianLow) && (c1 > o1) && ((lowerWick / range1) >= SweepMinWickRatio);

         if(sweptAsianHigh)
         {
            double entryPrice = Bid;
            double sweepSL    = NormalizeDouble(h1 + SweepBufferUSD, Digits);
            double slDist     = sweepSL - entryPrice;
            if(slDist >= 2.00 && slDist <= 12.00)
            {
               double sweepTP = NormalizeDouble(entryPrice - (slDist * SweepRR_Multiplier), Digits);
               if(EnableSweepFadeTrade)
               {
                  double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                  double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
                  double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                  if(lotStep <= 0) lotStep = 0.01;
                  double lot = MathFloor(SweepFadeFixedLot / lotStep) * lotStep;
                  if(lot < minLot) lot = minLot;
                  if(lot > maxLot) lot = maxLot;
                  int ticket = OrderSend(Symbol(), OP_SELL, lot, entryPrice, SlippagePoints, sweepSL, sweepTP, "v6.3.6b Box Sweep SELL", MagicSweepFade, 0, clrRed);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     sweepExecutedThisBar = true;
                        SetOrderInitRisk636B(ticket, slDist);
                     Print("[ASIAN BOX SWEEP FADE SELL v6.3.6a] Ticket: #", ticket, " Lots: ", lot, " Price: ", entryPrice, " SL: ", sweepSL, " TP: ", sweepTP);
                  }
               }
               if(EnableSweepFadeSignal)
               {
                  string reason = "Asian High Stop-Hunt Swept at $" + DoubleToString(StoredAsianHigh, 2) +
                                  " (Spike High $" + DoubleToString(h1, 2) + "), Rejection Wick " +
                                  DoubleToString((upperWick / range1) * 100, 0) + "%, Asymmetric R:R 1:" + DoubleToString(SweepRR_Multiplier, 1);
                  BroadcastSignal("A+", "SELL", entryPrice, sweepSL, sweepTP, "The Liquidity Sweep Fade (Asian High Stop-Hunt)", reason);
               }
            }
         }
         else if(sweptAsianLow)
         {
            double entryPrice = Ask;
            double sweepSL    = NormalizeDouble(l1 - SweepBufferUSD, Digits);
            double slDist     = entryPrice - sweepSL;
            if(slDist >= 2.00 && slDist <= 12.00)
            {
               double sweepTP = NormalizeDouble(entryPrice + (slDist * SweepRR_Multiplier), Digits);
               if(EnableSweepFadeTrade)
               {
                  double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
                  double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
                  double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
                  if(lotStep <= 0) lotStep = 0.01;
                  double lot = MathFloor(SweepFadeFixedLot / lotStep) * lotStep;
                  if(lot < minLot) lot = minLot;
                  if(lot > maxLot) lot = maxLot;
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, entryPrice, SlippagePoints, sweepSL, sweepTP, "v6.3.6b Box Sweep BUY", MagicSweepFade, 0, clrGreen);
                  if(ticket > 0)
                  {
                     DailyTotalTrades++;
                     sweepExecutedThisBar = true;
                        SetOrderInitRisk636B(ticket, slDist);
                     Print("[ASIAN BOX SWEEP FADE BUY v6.3.6a] Ticket: #", ticket, " Lots: ", lot, " Price: ", entryPrice, " SL: ", sweepSL, " TP: ", sweepTP);
                  }
               }
               if(EnableSweepFadeSignal)
               {
                  string reason = "Asian Low Stop-Hunt Swept at $" + DoubleToString(StoredAsianLow, 2) +
                                  " (Spike Low $" + DoubleToString(l1, 2) + "), Rejection Wick " +
                                  DoubleToString((lowerWick / range1) * 100, 0) + "%, Asymmetric R:R 1:" + DoubleToString(SweepRR_Multiplier, 1);
                  BroadcastSignal("A+", "BUY", entryPrice, sweepSL, sweepTP, "The Liquidity Sweep Fade (Asian Low Stop-Hunt)", reason);
               }
            }
         }
      }
   }

   // Phase B: Arm Trap on Retail EMA50 Pullback Bait (Always evaluated even if Grade A signal triggers)
   if(!sweepExecutedThisBar && allowSweepSession)
   {
      double ema50Touch = MathMax(1.20, atr_m15_sweep * 0.25);
      if(isH1Bull && c1 > ema200_m15 && ema50_m15 > ema200_m15)
      {
         if(l1 <= (ema50_m15 + ema50Touch) && c1 > ema50_m15)
         {
            double retailSL = NormalizeDouble(l1 - MathMax(3.50, atr_m15_sweep * 0.85), Digits);
            if(!SweepTrapArmed || SweepTrapSide != OP_BUY || retailSL < SweepTrapLevel)
            {
               SweepTrapArmed     = true;
               SweepTrapSide      = OP_BUY;
               SweepTrapLevel     = retailSL;
               SweepTrapBaitEntry = Ask;
               SweepTrapArmedTime = TimeCurrent();
               SweepTrapBarCount  = 0;
               SweepTrapReason    = "Bullish EMA50 Pullback Bait in H1 Bull Trend";
               SaveTrapStateToGV();
               Print("[TRAP ARMED v6.3.6a] Retail Buy Bait detected at $", Ask, ". Monitoring for Stop-Hunt Sweep at $", SweepTrapLevel);
            }
         }
      }
      else if(isH1Bear && c1 < ema200_m15 && ema50_m15 < ema200_m15)
      {
         if(h1 >= (ema50_m15 - ema50Touch) && c1 < ema50_m15)
         {
            double retailSL = NormalizeDouble(h1 + MathMax(3.50, atr_m15_sweep * 0.85), Digits);
            if(!SweepTrapArmed || SweepTrapSide != OP_SELL || retailSL > SweepTrapLevel)
            {
               SweepTrapArmed     = true;
               SweepTrapSide      = OP_SELL;
               SweepTrapLevel     = retailSL;
               SweepTrapBaitEntry = Bid;
               SweepTrapArmedTime = TimeCurrent();
               SweepTrapBarCount  = 0;
               SweepTrapReason    = "Bearish EMA50 Pullback Bait in H1 Bear Trend";
               SaveTrapStateToGV();
               Print("[TRAP ARMED v6.3.6a] Retail Sell Bait detected at $", Bid, ". Monitoring for Stop-Hunt Sweep at $", SweepTrapLevel);
            }
         }
      }
   }

   // 5. SCAN SECONDARY SIGNALS (Grade A & Grade B Advisory Signal Feed for User)
   if(!primaryOrderOpenedThisBar && !sweepExecutedThisBar)
   {
      ScanSecondarySignals(c1, o1, h1, l1, range1, upperWick, lowerWick, body1, isH1Bull, isH1Bear, ema50_m15, ema200_m15, dt, timeDec);
   }

   // Force immediate JSON state export when a new M15 bar is processed
   if(!IsTesting())
   {
      ExportMarketState(true);
   }
}

//+------------------------------------------------------------------+
//| Secondary Signal Feed Scanner (Grade A & B - Advisory Feed Only) |
//+------------------------------------------------------------------+
void ScanSecondarySignals(double c1, double o1, double h1, double l1, double range1, double upperWick, double lowerWick, double body1, bool isH1Bull, bool isH1Bear, double ema50_m15, double ema200_m15, MqlDateTime &dt, double timeDec)
{
   if(IsTesting()) return;
   double atr_m15 = iATR(Symbol(), PERIOD_M15, 14, 1);
   if(atr_m15 <= 0.0) atr_m15 = 6.0;
   double dynSL_A  = NormalizeDouble(MathMax(7.00, atr_m15 * 1.30), 2);
   double dynSL_B  = NormalizeDouble(MathMax(5.50, atr_m15 * 1.00), 2);

   // 1. GRADE A: London Breakout / Breakdown (Moderate Volume or Extended Window)
   if(StoredAsianHigh > 0.0 && StoredAsianLow < 999999.0 && timeDec >= 8.0 && timeDec <= 14.5)
   {
      if(isH1Bull && c1 > StoredAsianHigh && (c1 - StoredAsianHigh) >= 1.00 && c1 > o1)
      {
         if(CheckRVOL(0.85))
         {
            double entry = Ask;
            double sl    = NormalizeDouble(Ask - dynSL_A, Digits);
            double tp    = NormalizeDouble(Ask + (dynSL_A * 2.50), Digits);
            BroadcastSignal("A", "BUY", entry, sl, tp, "London High-Probability Breakout", "Asian High Penetrated >= $1.00, H1 Trend Bullish, Dynamic ATR SL $" + DoubleToString(dynSL_A, 2));
            return;
         }
      }
      else if(isH1Bear && c1 < StoredAsianLow && (StoredAsianLow - c1) >= 1.00 && c1 < o1)
      {
         if(CheckRVOL(0.85))
         {
            double entry = Bid;
            double sl    = NormalizeDouble(Bid + dynSL_A, Digits);
            double tp    = NormalizeDouble(Bid - (dynSL_A * 2.50), Digits);
            BroadcastSignal("A", "SELL", entry, sl, tp, "London High-Probability Breakdown", "Asian Low Penetrated >= $1.00, H1 Trend Bearish, Dynamic ATR SL $" + DoubleToString(dynSL_A, 2));
            return;
         }
      }
   }
   
   // 2. GRADE A: New York Trend Pullback & Continuation (14:00 - 20:30, Full ADX >= 15.0 Coverage)
   if(timeDec >= 14.0 && timeDec <= 20.5)
   {
      double adxVal = iADX(Symbol(), PERIOD_M15, 14, PRICE_CLOSE, MODE_MAIN, 1);
      double touchZone = MathMax(1.80, atr_m15 * 0.35);
      if(adxVal >= 15.0)
      {
         if(isH1Bull && c1 > ema200_m15)
         {
            bool testedEMA = (l1 <= ema50_m15 + touchZone) && (c1 > ema50_m15);
            bool isBullReversal = (c1 > o1) && ((body1 / range1) >= 0.40);
            if(testedEMA && isBullReversal)
            {
               double entry = Ask;
               double sl    = NormalizeDouble(Ask - dynSL_A, Digits);
               double tp    = NormalizeDouble(Ask + (dynSL_A * 2.00), Digits);
               BroadcastSignal("A", "BUY", entry, sl, tp, "New York Pullback Continuation", "Bullish Continuation Bar at EMA50, ADX " + DoubleToString(adxVal, 1) + ", Dynamic ATR SL $" + DoubleToString(dynSL_A, 2));
               return;
            }
         }
         else if(isH1Bear && c1 < ema200_m15)
         {
            bool testedEMA = (h1 >= ema50_m15 - touchZone) && (c1 < ema50_m15);
            bool isBearReversal = (c1 < o1) && ((body1 / range1) >= 0.40);
            if(testedEMA && isBearReversal)
            {
               double entry = Bid;
               double sl    = NormalizeDouble(Bid + dynSL_A, Digits);
               double tp    = NormalizeDouble(Bid - (dynSL_A * 2.00), Digits);
               BroadcastSignal("A", "SELL", entry, sl, tp, "New York Pullback Continuation", "Bearish Continuation Bar at EMA50, ADX " + DoubleToString(adxVal, 1) + ", Dynamic ATR SL $" + DoubleToString(dynSL_A, 2));
               return;
            }
         }
      }
   }

   // 3. GRADE B: M15 EMA200 Institutional Defense & RSI(14) Pullback Exhaustion
   double rsi14 = iRSI(Symbol(), PERIOD_M15, 14, PRICE_CLOSE, 1);
   double ema200Touch = MathMax(1.50, atr_m15 * 0.30);
   if(isH1Bull)
   {
      bool ema200Bounce = (l1 <= (ema200_m15 + ema200Touch) && c1 > ema200_m15 && c1 > o1);
      bool rsiOversold  = (rsi14 <= 38.0 && c1 > o1 && (body1 / range1) >= 0.45);
      if(ema200Bounce || rsiOversold)
      {
         double entry = Ask;
         double sl    = NormalizeDouble(Ask - dynSL_B, Digits);
         double tp    = NormalizeDouble(Ask + (dynSL_B * 1.80), Digits);
         string reason = ema200Bounce ? "Institutional M15 EMA200 Defense Bounce" : ("M15 RSI(" + DoubleToString(rsi14, 1) + ") Bullish Pullback Exhaustion");
         BroadcastSignal("B", "BUY", entry, sl, tp, "Tactical Swing Pullback Setup", reason + " in H1 Bullish Regime");
         return;
      }
   }
   else if(isH1Bear)
   {
      bool ema200Reject = (h1 >= (ema200_m15 - ema200Touch) && c1 < ema200_m15 && c1 < o1);
      bool rsiOverbought = (rsi14 >= 62.0 && c1 < o1 && (body1 / range1) >= 0.45);
      if(ema200Reject || rsiOverbought)
      {
         double entry = Bid;
         double sl    = NormalizeDouble(Bid + dynSL_B, Digits);
         double tp    = NormalizeDouble(Bid - (dynSL_B * 1.80), Digits);
         string reason = ema200Reject ? "Institutional M15 EMA200 Resistance Reject" : ("M15 RSI(" + DoubleToString(rsi14, 1) + ") Bearish Pullback Exhaustion");
         BroadcastSignal("B", "SELL", entry, sl, tp, "Tactical Swing Pullback Setup", reason + " in H1 Bearish Regime");
         return;
      }
   }
}

//+------------------------------------------------------------------+
//| On-Chart Status HUD Dashboard                                    |
//+------------------------------------------------------------------+
void UpdateChartDashboard()
{
   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   double h1Fast = iMA(Symbol(), PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE, 1);
   double h1Slow = iMA(Symbol(), PERIOD_H1, 200, 0, MODE_EMA, PRICE_CLOSE, 1);
   string h1Trend = (h1Fast > h1Slow) ? "BULLISH [GREEN]" : ((h1Fast < h1Slow) ? "BEARISH [RED]" : "NEUTRAL");
   
   datetime now = TimeCurrent();
   int h = TimeHour(now);
   int m = TimeMinute(now);
   
   string activeSession = "SWEEP FADE RADAR ACTIVE (06:00 - 20:45)";
   if(h >= 2 && (h < 6 || (h == 2 && m >= 30)))
      activeSession = "ASIAN SQUEEZE SWEEPER (02:30 - 06:00)";
   else if(h >= 8 && (h < 11 || (h == 11 && m <= 30)))
      activeSession = "LONDON SNIPER + SWEEP FADE (08:00 - 11:30)";
   else if(h >= 16 && (h < 18 || (h == 18 && m <= 30)))
      activeSession = "NEW YORK TREND-RIDER + SWEEP FADE (16:00 - 18:30)";
   else if(h < 2 || h >= 21)
      activeSession = "STAND-BY / ACCUMULATION";
      
   string sentinelStatus = AiNewsStandDown ? "ACTIVE [STAND-DOWN NEWS WINDOW]" : "READY [ALL CLEAR]";
   string jackpotStatus = (EnableJackpotLock && DailySniperPnL >= JackpotProfitUSD) ? "LOCKED (+$" + DoubleToString(DailySniperPnL, 2) + " BANKED - NY HALTED)" : "READY";
   string sweepStatus = SweepTrapArmed ? ("ARMED @ $" + DoubleToString(SweepTrapLevel, 2) + " (Bar " + IntegerToString(SweepTrapBarCount) + "/" + IntegerToString(SweepTrapMaxBars) + ")") : "SCANNING (EMA50 + ASIAN BOX)";

   string text = "========================================================\n" +
                 "  🏹 GOLD SNIPER v6.3.6b INSTITUTIONAL APEX (XM LIVE)\n" +
                 "========================================================\n" +
                 " Server Time: " + TimeToStr(now, TIME_DATE|TIME_SECONDS) + "\n" +
                 " Current Session: " + activeSession + "\n" +
                 " H1 Macro Bias: " + h1Trend + "\n" +
                 " Sweep Fade Radar: " + sweepStatus + "\n" +
                 " AI Macro Sentinel: " + sentinelStatus + "\n" +
                 " Jackpot Lock: " + jackpotStatus + "\n" +
                 "--------------------------------------------------------\n" +
                 " Equity: $" + DoubleToString(AccountEquity(), 2) + " | Balance: $" + DoubleToString(AccountBalance(), 2) + "\n" +
                 " Today PnL: $" + DoubleToString(DailyPnL, 2) + " (" + DoubleToString(DailyPnLPct, 2) + "%)\n" +
                 " Sniper PnL: $" + DoubleToString(DailySniperPnL, 2) + " | Sweep PnL: $" + DoubleToString(DailySweepPnL, 2) + "\n" +
                 " Daily Trades: " + IntegerToString(DailyTotalTrades) + "\n" +
                 " Live Spread: " + IntegerToString(spread) + " pts (Max: " + IntegerToString(MaxSpreadPoints) + ")\n" +
                 " Open Orders: " + IntegerToString(OrdersTotal()) + "\n" +
                 "========================================================";
   Comment(text);
}

void OnTick()
{
   CheckDailyResetAndStats();
   CheckVelocitySpike();
   CheckAiNewsSentinel();
   ManageOpenPositions();
   
   if(IsTesting())
   {
      RunDualModeStrategy();
   }
   else
   {
      ExportMarketState(false);
      RunDualModeStrategy();
   }
   UpdateChartDashboard();
}

