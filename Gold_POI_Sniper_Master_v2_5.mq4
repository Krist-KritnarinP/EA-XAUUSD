//+------------------------------------------------------------------+
//|                                    Gold_POI_Sniper_Master_v2_5.mq4 |
//|                     Institutional POI Sniper v2.5 (Apex Compound)|
//|                                  Copyright 2026, Institutional AI|
//+------------------------------------------------------------------+
#property copyright "Institutional AI"
#property link      "https://antigravity.ai"
#property version   "2.50"
#property strict

//--- INPUT PARAMETERS ---
extern string   SEP_RISK            = "=== DYNAMIC COMPOUNDING & RISK ===";
extern int      InpMagicNumber      = 778899;
extern bool     InpUseRiskPercent   = true;   // TRUE: Dynamic Compounding for $1,000/mo growth
extern double   InpRiskPercent      = 2.5;    // Risk % per trade (2.0% - 3.0% recommended)
extern double   InpFixedLot         = 0.10;   // Fallback lot if UseRiskPercent is false
extern double   InpMaxLotCap        = 2.00;   // Maximum lot ceiling for broker compliance

extern string   SEP_STRATEGY        = "=== POI SNIPER ENGINE v2.5 ===";
extern double   InpTargetRR         = 3.5;    // Target R:R (Asymmetrical 1:3.5)
extern double   InpBreakevenRR      = 1.8;    // Sweet spot Breakeven (1.8R gives Gold breathing room)
extern double   InpMinSLPoints      = 150.0;  // Min SL distance in points ($1.50)
extern double   InpMaxSLPoints      = 450.0;  // Max SL distance in points ($4.50)
extern double   InpWickThreshold    = 0.35;   // Rejection wick threshold (35% of bar)
extern double   InpBufferPoints     = 100.0;  // Buffer beyond wick extreme ($1.00)
extern bool     InpStructuralExit   = true;   // Early bailout when M15 structure breaks in profit

extern string   SEP_TIME            = "=== SESSION SELECTION & ATR FILTER ===";
extern bool     InpFocusNewYorkOnly = true;   // TRUE: High-Conviction NY Session Only (15:00-20:30)
extern int      InpStartHour        = 8;      // Fallback start hour if FocusNewYorkOnly = false
extern int      InpStartMinute      = 0;
extern int      InpEndHour          = 20;     // Fallback end hour
extern int      InpEndMinute        = 30;
extern double   InpMinATRPoints     = 80.0;   // Minimum M15 ATR(14) in points ($0.80) to avoid dead chop

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

// Forward Declarations
void UpdatePOIs();
void ExportMarketState();
void UpdateHUD();

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("[POI SNIPER v2.5 INIT] Step 1: Starting OnInit...");
   EventSetTimer(1); // 1-second live timer for HUD & Market State export
   UpdatePOIs();
   ExportMarketState();
   UpdateHUD();
   
   Print("[POI SNIPER v2.5 INIT] Institutional Gold POI Sniper v2.5 Initialized successfully.");
   PrintFormat("[CONFIG] Dynamic Risk: %s (%.1f%%) | Focus NY: %s | BE RR: %.1fR | Target RR: 1:%.1f", 
               InpUseRiskPercent ? "ON" : "OFF", InpRiskPercent, InpFocusNewYorkOnly ? "YES (15:00-20:30)" : "FULL DAY",
               InpBreakevenRR, InpTargetRR);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   if(!IsTesting())
   {
      Comment("");
   }
}

//+------------------------------------------------------------------+
//| Expert timer function (Runs every 1 second)                      |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(!IsTesting())
   {
      UpdatePOIs();
      ExportMarketState();
      UpdateHUD();
   }
}

//+------------------------------------------------------------------+
//| Update POIs (PDH, PDL, Asian High/Low)                           |
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
//| Export Real-Time Market State for Python AI Sentinel             |
//+------------------------------------------------------------------+
void ExportMarketState()
{
   if(IsTesting()) return;
   
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
            string eng = (m == InpMagicNumber) ? "POI Sniper" : "User Manual";
            
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
            string eng = (m == InpMagicNumber) ? "POI Sniper" : "User Manual";
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
   json += "  \"open_orders\": " + openOrdersJson + ",\n";
   json += "  \"recent_closed_orders\": " + closedOrdersJson + "\n";
   json += "}\n";
   
   int hFile = FileOpen("market_state.json", FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(hFile != INVALID_HANDLE)
   {
      FileWriteString(hFile, json);
      FileClose(hFile);
   }
   else
   {
      Print("[POI SNIPER v2.5 ERROR] FileOpen market_state.json failed! Error = ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Check if current time is inside trading window                   |
//+------------------------------------------------------------------+
bool IsTradingTime()
{
   datetime cur_time = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   
   // New York Session High-Conviction Window
   if(InpFocusNewYorkOnly)
   {
      return (dt.hour >= 15 && (dt.hour < 20 || (dt.hour == 20 && dt.min <= 30)));
   }
   
   // Full day trading window
   int total_min = dt.hour * 60 + dt.min;
   int start_min = InpStartHour * 60 + InpStartMinute;
   int end_min   = InpEndHour * 60 + InpEndMinute;
   
   return (total_min >= start_min && total_min <= end_min);
}

//+------------------------------------------------------------------+
//| Count active positions for this EA                               |
//+------------------------------------------------------------------+
int CountOpenPositions(int &pos_ticket, int &pos_type, double &pos_open, double &pos_sl, double &pos_tp)
{
   int count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicNumber)
         {
            count++;
            pos_ticket = OrderTicket();
            pos_type   = OrderType();
            pos_open   = OrderOpenPrice();
            pos_sl     = OrderStopLoss();
            pos_tp     = OrderTakeProfit();
         }
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| Manage Breakeven Lock at InpBreakevenRR (1.8R)                   |
//+------------------------------------------------------------------+
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
               if(sl_pr >= open_pr) continue; // Already at BE
               
               double cur_bid = Bid;
               if((cur_bid - open_pr) >= (init_sl_pts * Point * InpBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr + (30.0 * Point), Digits);
                  bool res = OrderModify(OrderTicket(), open_pr, new_sl, OrderTakeProfit(), 0, clrBlue);
                  if(res)
                  {
                     PrintFormat("[BE LOCK SUCCESS] Ticket #%d moved to BE+30pts (Reached %.1fR)", OrderTicket(), InpBreakevenRR);
                     ExportMarketState();
                  }
               }
            }
            else if(cmd == OP_SELL)
            {
               init_sl_pts = (sl_pr - open_pr) / Point;
               if(sl_pr <= open_pr && sl_pr > 0.0) continue; // Already at BE
               
               double cur_ask = Ask;
               if((open_pr - cur_ask) >= (init_sl_pts * Point * InpBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr - (30.0 * Point), Digits);
                  bool res = OrderModify(OrderTicket(), open_pr, new_sl, OrderTakeProfit(), 0, clrRed);
                  if(res)
                  {
                     PrintFormat("[BE LOCK SUCCESS] Ticket #%d moved to BE-30pts (Reached %.1fR)", OrderTicket(), InpBreakevenRR);
                     ExportMarketState();
                  }
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Check Structural Reversal & Early Bailout                        |
//+------------------------------------------------------------------+
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
               if(Bid > (open_pr + 60.0 * Point)) // in solid profit
               {
                  if((upper_wick / c1_range) >= 0.45 && c1_close < c1_open)
                  {
                     PrintFormat("[STRUCTURAL BAILOUT BUY] Opposite Rejection Detected on M15. Closing Ticket #%d @ Bid %.2f", OrderTicket(), Bid);
                     bool res = OrderClose(OrderTicket(), OrderLots(), Bid, InpSlippage, clrOrange);
                     if(res) ExportMarketState();
                  }
               }
            }
            else if(cmd == OP_SELL)
            {
               double lower_wick = MathMin(c1_open, c1_close) - c1_low;
               if(Ask < (open_pr - 60.0 * Point)) // in solid profit
               {
                  if((lower_wick / c1_range) >= 0.45 && c1_close > c1_open)
                  {
                     PrintFormat("[STRUCTURAL BAILOUT SELL] Opposite Rejection Detected on M15. Closing Ticket #%d @ Ask %.2f", OrderTicket(), Ask);
                     bool res = OrderClose(OrderTicket(), OrderLots(), Ask, InpSlippage, clrOrange);
                     if(res) ExportMarketState();
                  }
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Calculate Lot Size (Compound vs Fixed)                           |
//+------------------------------------------------------------------+
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

//+------------------------------------------------------------------+
//| Update Institutional Visual HUD                                  |
//+------------------------------------------------------------------+
void UpdateHUD()
{
   if(IsTesting()) return; // Ultra-fast backtesting bypass
   
   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   
   // Count open orders by engine
   int poiCount = 0;
   double poiProfit = 0.0;
   int manualCount = 0;
   double manualProfit = 0.0;
   
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol())
         {
            double p = OrderProfit() + OrderSwap() + OrderCommission();
            if(OrderMagicNumber() == InpMagicNumber)
            {
               poiCount++;
               poiProfit += p;
            }
            else
            {
               manualCount++;
               manualProfit += p;
            }
         }
      }
   }
   
   string txt = "\n  === GOLD POI SNIPER APEX COMPOUND ENGINE v2.5 ===\n";
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  Server Time    : %s\n", TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS));
   txt += StringFormat("  Mode           : Focus New York [%s] | In Window: %s\n", 
                       InpFocusNewYorkOnly ? "15:00-20:30" : "08:00-20:30", IsTradingTime() ? "ACTIVE" : "STANDBY");
   txt += StringFormat("  Compounding    : %s (Risk: %.1f%% / trade | Max Lot: %.2f)\n", 
                       InpUseRiskPercent ? "ACTIVE (Compound Growth)" : "OFF", InpRiskPercent, InpMaxLotCap);
   txt += StringFormat("  Spread (Current): %d pts (Max: %d)\n", spread, InpMaxSpreadPoints);
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  [POI Resistance] PDH: %.2f | Asian High: %.2f\n", g_pdh, g_asian_high);
   txt += StringFormat("  [POI Support]    PDL: %.2f | Asian Low : %.2f\n", g_pdl, g_asian_low);
   txt += StringFormat("  Current Price  : Ask %.2f | Bid %.2f\n", Ask, Bid);
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  Target RR      : 1:%.1f | Breakeven Lock: %.1fR (+30 pts)\n", InpTargetRR, InpBreakevenRR);
   txt += StringFormat("  SL Range       : Min %.0f pts ($%.2f) - Max %.0f pts ($%.2f)\n", 
                       InpMinSLPoints, InpMinSLPoints*Point, InpMaxSLPoints, InpMaxSLPoints*Point);
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  Open POI Orders: %d ไม้ (Floating PnL: $%.2f)\n", poiCount, poiProfit);
   txt += StringFormat("  Open User Orders: %d ไม้ (Floating PnL: $%.2f)\n", manualCount, manualProfit);
   txt += StringFormat("  Total Equity   : $%.2f | Balance: $%.2f\n", AccountEquity(), AccountBalance());
   txt += "  ==================================================\n";
   Comment(txt);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   ManageBreakeven();
   ExportMarketState();
   
   datetime cur_bar_time = iTime(Symbol(), PERIOD_M15, 0);
   if(cur_bar_time == g_last_bar_time)
   {
      return;
   }
   g_last_bar_time = cur_bar_time;
   
   CheckStructuralExit();
   UpdatePOIs();
   UpdateHUD();
   
   int dummy_t, dummy_type;
   double dummy_o, dummy_s, dummy_tp;
   if(CountOpenPositions(dummy_t, dummy_type, dummy_o, dummy_s, dummy_tp) > 0)
   {
      return;
   }
   
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
         
         PrintFormat("[POI APEX SELL] Entry: %.2f | SL: %.2f (%.0f pts) | TP: %.2f (1:%.1f RR) | Lots: %.2f",
                     entry, sl, sl_dist_pts, tp, InpTargetRR, lots);
         
         int ticket = OrderSend(Symbol(), OP_SELL, lots, Bid, InpSlippage, sl, tp, "POI_SNIPER_SELL", InpMagicNumber, 0, clrRed);
         if(ticket > 0)
         {
            PrintFormat("[ORDER SUCCESS] Ticket #%d SELL %.2f lots @ %.2f", ticket, lots, Bid);
            ExportMarketState();
            return;
         }
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
         
         PrintFormat("[POI APEX BUY] Entry: %.2f | SL: %.2f (%.0f pts) | TP: %.2f (1:%.1f RR) | Lots: %.2f",
                     entry, sl, sl_dist_pts, tp, InpTargetRR, lots);
         
         int ticket = OrderSend(Symbol(), OP_BUY, lots, Ask, InpSlippage, sl, tp, "POI_SNIPER_BUY", InpMagicNumber, 0, clrBlue);
         if(ticket > 0)
         {
            PrintFormat("[ORDER SUCCESS] Ticket #%d BUY %.2f lots @ %.2f", ticket, lots, Ask);
            ExportMarketState();
            return;
         }
      }
   }
}
//+------------------------------------------------------------------+
