//+------------------------------------------------------------------+
//|                                        Gold_POI_Sniper_Tester_v0.mq4|
//|                        Institutional POI Sniper v0 (Full Day Compound)|
//|                                  Copyright 2026, Institutional AI|
//+------------------------------------------------------------------+
#property copyright "Institutional AI"
#property link      "https://antigravity.ai"
#property version   "1.00"
#property strict

//--- INPUT PARAMETERS ---
extern string   SEP_RISK            = "=== DYNAMIC COMPOUNDING & RISK ===";
extern int      InpMagicNumber      = 778890;
extern bool     InpUseRiskPercent   = true;   // TRUE: Dynamic Compounding (แนวทางที่ 2)
extern double   InpRiskPercent      = 2.0;    // Risk % per trade (2.0% Compound)
extern double   InpFixedLot         = 0.10;   // Fallback lot if UseRiskPercent is false
extern double   InpMaxLotCap        = 1.50;   // Maximum lot ceiling for broker compliance

extern string   SEP_STRATEGY        = "=== POI SNIPER ENGINE v0 ===";
extern double   InpTargetRR         = 3.5;    // Target R:R (1:3.5)
extern double   InpBreakevenRR      = 1.8;    // Move SL to BE at 1.8R
extern double   InpMinSLPoints      = 150.0;  // Min SL distance in points ($1.50)
extern double   InpMaxSLPoints      = 450.0;  // Max SL distance in points ($4.50)
extern double   InpWickThreshold    = 0.35;   // Rejection wick threshold (35% of bar)
extern double   InpBufferPoints     = 100.0;  // Buffer beyond wick extreme ($1.00)
extern bool     InpStructuralExit   = true;   // Early bailout when M15 structure reverses

extern string   SEP_TIME            = "=== TIME & SESSION FILTER (FULL DAY v0) ===";
extern bool     InpFocusNewYorkOnly = false;  // FALSE: Full Day Trading Window (08:00 - 20:30)
extern int      InpStartHour        = 8;      // Start trading at 08:00 Server Time
extern int      InpStartMinute      = 0;
extern int      InpEndHour          = 20;     // End trading at 20:30 Server Time
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
   Print("[POI SNIPER v0 INIT] Institutional Gold POI Sniper v0 (Full Day Compound) Initialized.");
   PrintFormat("[CONFIG] Dynamic Compound: %s (%.1f%%) | Trading Mode: FULL DAY (08:00-20:30) | BE: %.1fR | TP: 1:%.1f", 
               InpUseRiskPercent ? "ON" : "OFF", InpRiskPercent, InpBreakevenRR, InpTargetRR);
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
      return (dt.hour >= 15 && (dt.hour < 20 || (dt.hour == 20 && dt.min <= 30)));
   }
   
   int total_min = dt.hour * 60 + dt.min;
   int start_min = InpStartHour * 60 + InpStartMinute;
   int end_min   = InpEndHour * 60 + InpEndMinute;
   
   return (total_min >= start_min && total_min <= end_min);
}

int CountOpenPositions()
{
   int count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicNumber)
         {
            count++;
         }
      }
   }
   return count;
}

void ManageBreakeven()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicNumber)
         {
            double open_pr = OrderOpenPrice();
            double sl_pr   = OrderStopLoss();
            int cmd        = OrderType();
            
            double init_sl_pts = 0.0;
            if(cmd == OP_BUY)
            {
               init_sl_pts = (open_pr - sl_pr) / Point;
               if(sl_pr >= open_pr) continue;
               
               double cur_bid = Bid;
               if((cur_bid - open_pr) >= (init_sl_pts * Point * InpBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr + (30.0 * Point), Digits);
                  bool res = OrderModify(OrderTicket(), open_pr, new_sl, OrderTakeProfit(), 0, clrBlue);
               }
            }
            else if(cmd == OP_SELL)
            {
               init_sl_pts = (sl_pr - open_pr) / Point;
               if(sl_pr <= open_pr && sl_pr > 0.0) continue;
               
               double cur_ask = Ask;
               if((open_pr - cur_ask) >= (init_sl_pts * Point * InpBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr - (30.0 * Point), Digits);
                  bool res = OrderModify(OrderTicket(), open_pr, new_sl, OrderTakeProfit(), 0, clrRed);
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
   
   string txt = "\n  === GOLD POI SNIPER v0 (FULL DAY COMPOUND) ===\n";
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  Server Time    : %s\n", TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS));
   txt += StringFormat("  Trading Window : FULL DAY (08:00 - 20:30) | In Session: %s\n", IsTradingTime() ? "ACTIVE" : "STANDBY");
   txt += StringFormat("  Compounding    : %s (Risk: %.1f%% / trade | Max Lot: %.2f)\n", 
                       InpUseRiskPercent ? "ACTIVE (Compound Growth)" : "OFF", InpRiskPercent, InpMaxLotCap);
   txt += StringFormat("  Spread (Current): %.1f pts (Max: %d)\n", MarketInfo(Symbol(), MODE_SPREAD), InpMaxSpreadPoints);
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  [POI Resistance] PDH: %.2f | Asian High: %.2f\n", g_pdh, g_asian_high);
   txt += StringFormat("  [POI Support]    PDL: %.2f | Asian Low : %.2f\n", g_pdl, g_asian_low);
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  Target RR      : 1:%.1f | Breakeven Lock: %.1fR\n", InpTargetRR, InpBreakevenRR);
   txt += "  ==================================================\n";
   Comment(txt);
}

void OnTick()
{
   ManageBreakeven();
   
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
         
         int ticket = OrderSend(Symbol(), OP_SELL, lots, Bid, InpSlippage, sl, tp, "POI_v0_SELL", InpMagicNumber, 0, clrRed);
         if(ticket > 0) return;
      }
   }
   
   // BUY Setup
   bool at_support = (c1_low <= g_asian_low || c1_low <= g_pdl);
   double lower_wick_ratio = c1_lower_wick / c1_range;
   
   if(at_support && lower_wick_ratio >= InpWickThreshold && c1_close > c1_open)
   {
      double sl = NormalizeDouble(c1_low - (InpBufferPoints * Point), Digits);
      double entry = Bid;
      double sl_dist_pts = (entry - sl) / Point;
      
      if(sl_dist_pts >= InpMinSLPoints && sl_dist_pts <= InpMaxSLPoints)
      {
         double tp = NormalizeDouble(entry + (sl_dist_pts * Point * InpTargetRR), Digits);
         double lots = CalculateLots(sl_dist_pts);
         
         int ticket = OrderSend(Symbol(), OP_BUY, lots, Ask, InpSlippage, sl, tp, "POI_v0_BUY", InpMagicNumber, 0, clrBlue);
         if(ticket > 0) return;
      }
   }
}
//+------------------------------------------------------------------+
