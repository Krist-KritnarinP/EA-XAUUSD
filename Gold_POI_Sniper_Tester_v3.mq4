//+------------------------------------------------------------------+
//|                                    Gold_POI_Sniper_Tester_v3.mq4 |
//|                     Institutional POI Sniper v3.1 (Macro Guard)   |
//|                                  Copyright 2026, Institutional AI|
//+------------------------------------------------------------------+
#property copyright "Institutional AI"
#property link      "https://antigravity.ai"
#property version   "1.01"
#property strict

//--- INPUT PARAMETERS ---
extern string   SEP_RISK            = "=== DYNAMIC COMPOUNDING & RISK ===";
extern int      InpMagicNumber      = 778893;
extern bool     InpUseRiskPercent   = true;   // Dynamic Compounding for Exponential Growth
extern double   InpRiskPercent      = 2.5;    // Risk % per trade (2.0% - 3.0%)
extern double   InpFixedLot         = 0.10;   // Fallback lot if UseRiskPercent is false
extern double   InpMaxLotCap        = 2.00;   // Maximum lot ceiling

extern string   SEP_STRATEGY        = "=== POI SNIPER ENGINE v3.1 ===";
extern double   InpTargetRR         = 3.5;    // Target R:R (1:3.5)
extern double   InpBreakevenRR      = 1.8;    // Static Breakeven Trigger (1.8R)
extern double   InpMinSLPoints      = 150.0;  // Min SL distance in points ($1.50)
extern double   InpMaxSLPoints      = 450.0;  // Max SL distance in points ($4.50)
extern double   InpWickThreshold    = 0.35;   // Rejection wick threshold (35% of bar)
extern double   InpBufferPoints     = 100.0;  // Buffer beyond wick extreme ($1.00)

extern string   SEP_TRAILING        = "=== DYNAMIC STRUCTURAL TRAILING (v3.0) ===";
extern bool     InpUseDynamicTrail  = true;   // Enable Structural Trailing behind M15 swings
extern double   InpTrailTriggerRR   = 1.2;    // Start trailing once profit reaches >= 1.2R
extern int      InpTrailSwingBars   = 3;      // Number of bars to look back for Swing Low/High
extern double   InpTrailBufferPts   = 50.0;   // Buffer below swing low / above swing high (50 pts = $0.50)
extern bool     InpUseTimeDecay     = true;   // Enable Time-Decay BE Lock
extern double   InpTimeDecayHours   = 2.0;    // Smart Time-Decay: Move to BE if position open >= 2.0 hrs
extern double   InpTimeDecayTrigger = 0.9;    // Smart Time-Decay: Profit threshold (0.9R)
extern bool     InpStructuralExit   = true;   // Early bailout when M15 structure reverses

extern string   SEP_MACRO           = "=== MACRO CRASH & TREND GUARD ===";
extern bool     InpUseMacroCrashGuard = true; // Block BUY at PDL if D1 dump or price < H4 EMA50
extern int      InpH4EMAPeriod      = 50;     // H4 Trend EMA Period
extern double   InpD1DumpATRMult    = 1.0;    // D1 dump threshold multiplier of D1 ATR

extern string   SEP_TIME            = "=== TIME & SESSION FILTER ===";
extern bool     InpFocusNewYorkOnly = true;   // High-Conviction NY Session Only (15:00-20:30)
extern int      InpStartHour        = 15;     // Start hour
extern int      InpEndHour          = 20;     // End hour
extern int      InpEndMinute        = 30;
extern double   InpMinATRPoints     = 80.0;   // Minimum M15 ATR(14) in points

extern string   SEP_SAFETY          = "=== BROKER COMPLIANCE & SAFETY ===";
extern int      InpMaxSpreadPoints  = 65;     // Max allowable spread (points)
extern int      InpMinHoldingSec    = 180;    // Anti-Broker Ban: Min holding time
extern int      InpSlippage         = 30;

//--- GLOBAL VARIABLES ---
datetime g_last_bar_time = 0;
double   g_pdh = 0.0;
double   g_pdl = 0.0;
double   g_asian_high = 0.0;
double   g_asian_low = 0.0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("[POI SNIPER v3.1 INIT] Institutional Gold POI Sniper v3.1 (Macro Guard) Initialized.");
   PrintFormat("[CONFIG] Dynamic Trail: %s | Time Decay: %s | Macro Crash Guard: %s | Focus NY: %s", 
               InpUseDynamicTrail ? "ON" : "OFF", InpUseTimeDecay ? "ON" : "OFF",
               InpUseMacroCrashGuard ? "ON (Anti-Falling-Knife)" : "OFF", InpFocusNewYorkOnly ? "YES" : "NO");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   if(!IsTesting()) Comment("");
}

void UpdatePOIs()
{
   datetime cur_time = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   
   g_pdh = iHigh(Symbol(), PERIOD_D1, 1);
   g_pdl = iLow(Symbol(), PERIOD_D1, 1);
   
   datetime today_start = cur_time - (cur_time % 86400);
   int shift_start = iBarShift(Symbol(), PERIOD_M15, today_start);
   
   double a_high = 0.0;
   double a_low = 999999.0;
   bool found_asian = false;
   
   for(int s = shift_start; s >= 0; s--)
   {
      datetime bar_t = iTime(Symbol(), PERIOD_M15, s);
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

bool IsTradingTime()
{
   datetime cur_time = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   
   if(InpFocusNewYorkOnly)
   {
      return (dt.hour >= InpStartHour && (dt.hour < InpEndHour || (dt.hour == InpEndHour && dt.min <= InpEndMinute)));
   }
   
   int total_min = dt.hour * 60 + dt.min;
   int start_min = 8 * 60;
   int end_min   = 20 * 60 + 30;
   return (total_min >= start_min && total_min <= end_min);
}

int CountOpenPositions()
{
   int count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicNumber) count++;
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| Manage Breakeven & Dynamic Structural Trailing (v3.0)            |
//+------------------------------------------------------------------+
void ManageTrailingAndBreakeven()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicNumber)
         {
            double open_pr = OrderOpenPrice();
            double sl_pr   = OrderStopLoss();
            double tp_pr   = OrderTakeProfit();
            int cmd        = OrderType();
            datetime op_t  = OrderOpenTime();
            double hrs_held = (TimeCurrent() - op_t) / 3600.0;
            
            double init_sl_pts = 0.0;
            
            // BUY ORDER MANAGEMENT
            if(cmd == OP_BUY)
            {
               init_sl_pts = (open_pr - sl_pr) / Point;
               if(init_sl_pts <= 0) init_sl_pts = 300.0;
               
               double cur_bid = Bid;
               double cur_profit_pts = (cur_bid - open_pr) / Point;
               
               // 1. Smart Time Decay Guard: If held >= InpTimeDecayHours and in profit >= InpTimeDecayTrigger, lock BE
               if(InpUseTimeDecay && hrs_held >= InpTimeDecayHours && (sl_pr < open_pr || sl_pr == 0.0))
               {
                  if(cur_profit_pts >= (init_sl_pts * InpTimeDecayTrigger))
                  {
                     double new_sl = NormalizeDouble(open_pr + (30.0 * Point), Digits);
                     bool res = OrderModify(OrderTicket(), open_pr, new_sl, tp_pr, 0, clrBlue);
                     if(res) PrintFormat("[SMART TIME DECAY BE LOCK BUY] Ticket #%d held %.1f hrs & reached %.1fR -> BE+30pts", OrderTicket(), hrs_held, InpTimeDecayTrigger);
                     continue;
                  }
               }
               
               // 2. Static BE at InpBreakevenRR (1.8R)
               if(cur_profit_pts >= (init_sl_pts * InpBreakevenRR) && sl_pr < open_pr)
               {
                  double new_sl = NormalizeDouble(open_pr + (30.0 * Point), Digits);
                  bool res = OrderModify(OrderTicket(), open_pr, new_sl, tp_pr, 0, clrBlue);
                  if(res) PrintFormat("[BE LOCK BUY] Ticket #%d reached %.1fR -> BE+30pts", OrderTicket(), InpBreakevenRR);
                  continue;
               }
               
               // 3. Dynamic Structural Trailing once profit reaches >= InpTrailTriggerRR (1.2R)
               if(InpUseDynamicTrail && cur_profit_pts >= (init_sl_pts * InpTrailTriggerRR))
               {
                  int lowest_bar = iLowest(Symbol(), PERIOD_M15, MODE_LOW, InpTrailSwingBars, 1);
                  if(lowest_bar > 0)
                  {
                     double swing_low = iLow(Symbol(), PERIOD_M15, lowest_bar);
                     double trail_sl = NormalizeDouble(swing_low - (InpTrailBufferPts * Point), Digits);
                     
                     if(trail_sl > (sl_pr + (10.0 * Point)) && trail_sl < (cur_bid - (30.0 * Point)))
                     {
                        bool res = OrderModify(OrderTicket(), open_pr, trail_sl, tp_pr, 0, clrAqua);
                        if(res) PrintFormat("[DYNAMIC STRUCTURAL TRAIL BUY] Ticket #%d trailed to Swing Low %.2f", OrderTicket(), trail_sl);
                     }
                  }
               }
            }
            // SELL ORDER MANAGEMENT
            else if(cmd == OP_SELL)
            {
               init_sl_pts = (sl_pr - open_pr) / Point;
               if(init_sl_pts <= 0) init_sl_pts = 300.0;
               
               double cur_ask = Ask;
               double cur_profit_pts = (open_pr - cur_ask) / Point;
               
               // 1. Smart Time Decay Guard: If held >= InpTimeDecayHours and in profit >= InpTimeDecayTrigger, lock BE
               if(InpUseTimeDecay && hrs_held >= InpTimeDecayHours && (sl_pr > open_pr || sl_pr == 0.0))
               {
                  if(cur_profit_pts >= (init_sl_pts * InpTimeDecayTrigger))
                  {
                     double new_sl = NormalizeDouble(open_pr - (30.0 * Point), Digits);
                     bool res = OrderModify(OrderTicket(), open_pr, new_sl, tp_pr, 0, clrRed);
                     if(res) PrintFormat("[SMART TIME DECAY BE LOCK SELL] Ticket #%d held %.1f hrs & reached %.1fR -> BE-30pts", OrderTicket(), hrs_held, InpTimeDecayTrigger);
                     continue;
                  }
               }
               
               // 2. Static BE at InpBreakevenRR
               if(cur_profit_pts >= (init_sl_pts * InpBreakevenRR) && (sl_pr > open_pr || sl_pr == 0.0))
               {
                  double new_sl = NormalizeDouble(open_pr - (30.0 * Point), Digits);
                  bool res = OrderModify(OrderTicket(), open_pr, new_sl, tp_pr, 0, clrRed);
                  if(res) PrintFormat("[BE LOCK SELL] Ticket #%d reached %.1fR -> BE-30pts", OrderTicket(), InpBreakevenRR);
                  continue;
               }
               
               // 3. Dynamic Structural Trailing
               if(InpUseDynamicTrail && cur_profit_pts >= (init_sl_pts * InpTrailTriggerRR))
               {
                  int highest_bar = iHighest(Symbol(), PERIOD_M15, MODE_HIGH, InpTrailSwingBars, 1);
                  if(highest_bar > 0)
                  {
                     double swing_high = iHigh(Symbol(), PERIOD_M15, highest_bar);
                     double trail_sl = NormalizeDouble(swing_high + (InpTrailBufferPts * Point), Digits);
                     
                     if((sl_pr == 0.0 || trail_sl < (sl_pr - (10.0 * Point))) && trail_sl > (cur_ask + (30.0 * Point)))
                     {
                        bool res = OrderModify(OrderTicket(), open_pr, trail_sl, tp_pr, 0, clrMagenta);
                        if(res) PrintFormat("[DYNAMIC STRUCTURAL TRAIL SELL] Ticket #%d trailed to Swing High %.2f", OrderTicket(), trail_sl);
                     }
                  }
               }
            }
         }
      }
   }
}

void CheckStructuralExit()
{
   if(!InpStructuralExit) return;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicNumber)
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
                     bool res = OrderClose(OrderTicket(), OrderLots(), Bid, InpSlippage, clrOrange);
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
                     bool res = OrderClose(OrderTicket(), OrderLots(), Ask, InpSlippage, clrOrange);
                  }
               }
            }
         }
      }
   }
}

double CalculateLots(double sl_dist_pts)
{
   if(!InpUseRiskPercent)
   {
      double lot = InpFixedLot;
      if(lot > InpMaxLotCap) lot = InpMaxLotCap;
      return lot;
   }
   
   double balance = AccountBalance();
   double risk_amount = balance * (InpRiskPercent / 100.0);
   double tick_val = MarketInfo(Symbol(), MODE_TICKVALUE);
   if(tick_val <= 0.0) tick_val = 1.0;
   
   double raw_lots = risk_amount / (sl_dist_pts * tick_val);
   double step = MarketInfo(Symbol(), MODE_LOTSTEP);
   double min_lot = MarketInfo(Symbol(), MODE_MINLOT);
   double max_lot = MarketInfo(Symbol(), MODE_MAXLOT);
   
   double calc_lots = MathFloor(raw_lots / step) * step;
   if(calc_lots < min_lot) calc_lots = min_lot;
   if(calc_lots > max_lot) calc_lots = max_lot;
   if(calc_lots > InpMaxLotCap) calc_lots = InpMaxLotCap;
   
   return calc_lots;
}

void UpdateHUD()
{
   if(IsTesting()) return;
   
   string txt = "\n  === GOLD POI SNIPER v3.1 (MACRO CRASH GUARD) ===\n";
   txt += "  --------------------------------------------------------\n";
   txt += StringFormat("  Server Time    : %s\n", TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS));
   txt += StringFormat("  Mode           : Focus New York (15:00-20:30) | In Session: %s\n", IsTradingTime() ? "ACTIVE" : "STANDBY");
   txt += StringFormat("  Compounding    : %s (Risk: %.1f%% / trade | Max Lot: %.2f)\n", 
                       InpUseRiskPercent ? "ACTIVE" : "OFF", InpRiskPercent, InpMaxLotCap);
   txt += StringFormat("  Dynamic Trail  : %s (Trigger >= %.1fR | %d M15 Bars Swing)\n", 
                       InpUseDynamicTrail ? "ACTIVE" : "OFF", InpTrailTriggerRR, InpTrailSwingBars);
   txt += StringFormat("  Macro Guard    : %s (Blocks BUY at PDL if D1 dump or price < H4 EMA50)\n",
                       InpUseMacroCrashGuard ? "ACTIVE (Anti-Falling-Knife)" : "OFF");
   txt += StringFormat("  Spread (Current): %.1f pts (Max: %d)\n", MarketInfo(Symbol(), MODE_SPREAD), InpMaxSpreadPoints);
   txt += "  --------------------------------------------------------\n";
   txt += StringFormat("  [POI Resistance] PDH: %.2f | Asian High: %.2f\n", g_pdh, g_asian_high);
   txt += StringFormat("  [POI Support]    PDL: %.2f | Asian Low : %.2f\n", g_pdl, g_asian_low);
   txt += StringFormat("  Target RR      : 1:%.1f | Static BE: %.1fR\n", InpTargetRR, InpBreakevenRR);
   txt += "  ========================================================\n";
   Comment(txt);
}

void OnTick()
{
   ManageTrailingAndBreakeven();
   
   datetime cur_bar_time = iTime(Symbol(), PERIOD_M15, 0);
   if(cur_bar_time == g_last_bar_time) return;
   g_last_bar_time = cur_bar_time;
   
   CheckStructuralExit();
   UpdatePOIs();
   UpdateHUD();
   
   if(CountOpenPositions() > 0) return;
   if(!IsTradingTime()) return;
   
   double cur_atr = iATR(Symbol(), PERIOD_M15, 14, 0);
   if(cur_atr < (InpMinATRPoints * Point)) return;
   
   int cur_spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   if(cur_spread > InpMaxSpreadPoints) return;
   
   // Macro Crash Guard (Anti-Falling-Knife at PDL):
   double d1_open   = iOpen(Symbol(), PERIOD_D1, 1);
   double d1_close  = iClose(Symbol(), PERIOD_D1, 1);
   double d1_high   = iHigh(Symbol(), PERIOD_D1, 1);
   double d1_low    = iLow(Symbol(), PERIOD_D1, 1);
   double d1_atr    = iATR(Symbol(), PERIOD_D1, 14, 1);
   double h4_ema50  = iMA(Symbol(), PERIOD_H4, InpH4EMAPeriod, 0, MODE_EMA, PRICE_CLOSE, 0);
   
   bool is_d1_dump = (d1_close < d1_open) && ((d1_high - d1_low) >= (d1_atr * InpD1DumpATRMult));
   bool is_below_h4 = (Bid < h4_ema50);
   bool block_buy_pdl = InpUseMacroCrashGuard && (is_d1_dump && is_below_h4);

   double c1_high  = iHigh(Symbol(), PERIOD_M15, 1);
   double c1_low   = iLow(Symbol(), PERIOD_M15, 1);
   double c1_open  = iOpen(Symbol(), PERIOD_M15, 1);
   double c1_close = iClose(Symbol(), PERIOD_M15, 1);
   double c1_range = c1_high - c1_low;
   
   if(c1_range < (80.0 * Point)) return;
   
   double c1_upper_wick = c1_high - MathMax(c1_open, c1_close);
   double c1_lower_wick = MathMin(c1_open, c1_close) - c1_low;
   
   // SELL Setup
   bool at_resistance = (c1_high >= g_asian_high || c1_high >= g_pdh);
   double upper_wick_ratio = c1_upper_wick / c1_range;
   
   if(at_resistance && upper_wick_ratio >= InpWickThreshold && c1_close < c1_open)
   {
      double sl = NormalizeDouble(c1_high + (InpBufferPoints * Point), Digits);
      double entry = Ask;
      double sl_dist_pts = (sl - entry) / Point;
      
      if(sl_dist_pts >= InpMinSLPoints && sl_dist_pts <= InpMaxSLPoints)
      {
         double tp = NormalizeDouble(entry - (sl_dist_pts * Point * InpTargetRR), Digits);
         double lots = CalculateLots(sl_dist_pts);
         
         int ticket = OrderSend(Symbol(), OP_SELL, lots, Bid, InpSlippage, sl, tp, "POI_v3_SELL", InpMagicNumber, 0, clrRed);
         if(ticket > 0) return;
      }
   }
   
   // BUY Setup
   bool at_support = (c1_low <= g_asian_low || c1_low <= g_pdl);
   double lower_wick_ratio = c1_lower_wick / c1_range;
   
   if(at_support && lower_wick_ratio >= InpWickThreshold && c1_close > c1_open)
   {
      // If at PDL and macro crash guard active, block the falling knife!
      if(c1_low <= g_pdl && block_buy_pdl)
      {
         PrintFormat("[MACRO CRASH GUARD] BUY at PDL Blocked! D1 Dump: %s | Below H4 EMA50 (%.2f): %s",
                     is_d1_dump ? "YES" : "NO", h4_ema50, is_below_h4 ? "YES" : "NO");
         return;
      }
      
      double sl = NormalizeDouble(c1_low - (InpBufferPoints * Point), Digits);
      double entry = Bid;
      double sl_dist_pts = (entry - sl) / Point;
      
      if(sl_dist_pts >= InpMinSLPoints && sl_dist_pts <= InpMaxSLPoints)
      {
         double tp = NormalizeDouble(entry + (sl_dist_pts * Point * InpTargetRR), Digits);
         double lots = CalculateLots(sl_dist_pts);
         
         int ticket = OrderSend(Symbol(), OP_BUY, lots, Ask, InpSlippage, sl, tp, "POI_v3_BUY", InpMagicNumber, 0, clrBlue);
         if(ticket > 0) return;
      }
   }
}
//+------------------------------------------------------------------+
