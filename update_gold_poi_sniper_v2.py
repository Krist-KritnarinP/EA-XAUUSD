import os
import subprocess

MT4_EXPERTS_DIR = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
SCRATCH_DIR = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
METAEDITOR = r"C:\Program Files (x86)\MetaTrader 4\metaeditor.exe"

source_code = r"""//+------------------------------------------------------------------+
//|                                    Gold_POI_Sniper_Master_v1.mq4 |
//|                                     Institutional POI Engine v2.0 |
//|                                  Copyright 2026, Institutional AI|
//+------------------------------------------------------------------+
#property copyright "Institutional AI"
#property link      "https://antigravity.ai"
#property version   "2.00"
#property strict

//--- INPUT PARAMETERS ---
extern string   SEP_RISK            = "=== RISK & EXECUTION PARAMETERS ===";
extern int      InpMagicNumber      = 778899;
extern double   InpFixedLot         = 0.10;
extern bool     InpUseRiskPercent   = false;
extern double   InpRiskPercent      = 1.0;
extern double   InpMaxLotCap        = 0.50;

extern string   SEP_STRATEGY        = "=== POI SNIPER ENGINE v2.0 ===";
extern double   InpTargetRR         = 3.5;    // Target R:R (Asymmetrical 1:3.5)
extern double   InpBreakevenRR      = 1.5;    // Move SL to BE at 1.5R (Optimized from 2.0R)
extern double   InpMinSLPoints      = 150.0;  // Min SL distance in points ($1.50)
extern double   InpMaxSLPoints      = 450.0;  // Max SL distance in points ($4.50)
extern double   InpWickThreshold    = 0.35;   // Rejection wick threshold (35% of bar)
extern double   InpBufferPoints     = 100.0;  // Buffer beyond wick extreme ($1.00)
extern bool     InpStructuralExit   = true;   // Early bailout when M15 structure breaks

extern string   SEP_TIME            = "=== SESSION & VOLATILITY FILTERS ===";
extern int      InpStartHour        = 8;      // Trading start hour (Server Time)
extern int      InpStartMinute      = 0;
extern int      InpEndHour          = 20;     // Trading end hour (Server Time)
extern int      InpEndMinute        = 30;
extern bool     InpFocusNewYorkOnly = false;  // If true: Trade high-conviction NY only (15:00-20:30)
extern double   InpMinATRPoints     = 80.0;   // Minimum M15 ATR(14) in points ($0.80) to avoid chop

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
   Print("[POI SNIPER v2.0 INIT] Institutional Gold POI Sniper v2.0 Initialized.");
   PrintFormat("[CONFIG] Target RR: 1:%.1f | BE RR: %.1fR | SL Boundary: %.0f-%.0f pts | Structural Exit: %s", 
               InpTargetRR, InpBreakevenRR, InpMinSLPoints, InpMaxSLPoints, InpStructuralExit ? "ON" : "OFF");
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(!IsTesting())
   {
      Comment("");
   }
}

//+------------------------------------------------------------------+
//| Update POIs (PDH, PDL, Asian High/Low)                           |
//+------------------------------------------------------------------+
void UpdatePOIs()
{
   datetime cur_time = TimeCurrent();
   MqlDateTime dt;
   TimeToStruct(cur_time, dt);
   
   // PDH and PDL from D1 bar 1
   g_pdh = iHigh(Symbol(), PERIOD_D1, 1);
   g_pdl = iLow(Symbol(), PERIOD_D1, 1);
   
   // Asian Range calculation (00:00 to 07:00 server time today)
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

//+------------------------------------------------------------------+
//| Check if current time is inside trading window                   |
//+------------------------------------------------------------------+
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
//| Manage Breakeven Lock at InpBreakevenRR (1.5R)                   |
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
               if(sl_pr >= open_pr) continue; // Already at or above BE
               
               double cur_bid = Bid;
               if((cur_bid - open_pr) >= (init_sl_pts * Point * InpBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr + (30.0 * Point), Digits);
                  bool res = OrderModify(OrderTicket(), open_pr, new_sl, OrderTakeProfit(), 0, clrBlue);
                  if(res)
                  {
                     PrintFormat("[BE LOCK SUCCESS] Ticket #%d moved to BE+30pts (Reached %.1fR)", OrderTicket(), InpBreakevenRR);
                  }
               }
            }
            else if(cmd == OP_SELL)
            {
               init_sl_pts = (sl_pr - open_pr) / Point;
               if(sl_pr <= open_pr && sl_pr > 0.0) continue; // Already at or below BE
               
               double cur_ask = Ask;
               if((open_pr - cur_ask) >= (init_sl_pts * Point * InpBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr - (30.0 * Point), Digits);
                  bool res = OrderModify(OrderTicket(), open_pr, new_sl, OrderTakeProfit(), 0, clrRed);
                  if(res)
                  {
                     PrintFormat("[BE LOCK SUCCESS] Ticket #%d moved to BE-30pts (Reached %.1fR)", OrderTicket(), InpBreakevenRR);
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
            
            // Respect Anti-broker ban: Do not close under InpMinHoldingSec
            if((TimeCurrent() - open_t) < InpMinHoldingSec) continue;
            
            double c1_high  = iHigh(Symbol(), PERIOD_M15, 1);
            double c1_low   = iLow(Symbol(), PERIOD_M15, 1);
            double c1_open  = iOpen(Symbol(), PERIOD_M15, 1);
            double c1_close = iClose(Symbol(), PERIOD_M15, 1);
            double c1_range = c1_high - c1_low;
            if(c1_range < 50.0 * Point) continue;
            
            // BUY Position: If M15 prints strong upper wick rejection and closes below previous open
            if(cmd == OP_BUY)
            {
               double upper_wick = c1_high - MathMax(c1_open, c1_close);
               if(Bid > (open_pr + 50.0 * Point)) // in profit
               {
                  if((upper_wick / c1_range) >= 0.45 && c1_close < c1_open)
                  {
                     PrintFormat("[STRUCTURAL BAILOUT BUY] Opposite Rejection Detected on M15. Closing Ticket #%d @ Bid %.2f", OrderTicket(), Bid);
                     bool res = OrderClose(OrderTicket(), OrderLots(), Bid, InpSlippage, clrOrange);
                  }
               }
            }
            // SELL Position: If M15 prints strong lower wick rejection and closes above previous open
            else if(cmd == OP_SELL)
            {
               double lower_wick = MathMin(c1_open, c1_close) - c1_low;
               if(Ask < (open_pr - 50.0 * Point)) // in profit
               {
                  if((lower_wick / c1_range) >= 0.45 && c1_close > c1_open)
                  {
                     PrintFormat("[STRUCTURAL BAILOUT SELL] Opposite Rejection Detected on M15. Closing Ticket #%d @ Ask %.2f", OrderTicket(), Ask);
                     bool res = OrderClose(OrderTicket(), OrderLots(), Ask, InpSlippage, clrOrange);
                  }
               }
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Calculate Lot Size                                               |
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
   
   double atr14 = iATR(Symbol(), PERIOD_M15, 14, 0) / Point;
   
   string txt = "\n  === GOLD POI SNIPER INSTITUTIONAL ENGINE v2.0 ===\n";
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  Server Time    : %s\n", TimeToStr(TimeCurrent(), TIME_DATE|TIME_SECONDS));
   txt += StringFormat("  Trading Window : %02d:%02d - %02d:%02d | In Session: %s\n", 
                       InpStartHour, InpStartMinute, InpEndHour, InpEndMinute, IsTradingTime() ? "ACTIVE" : "STANDBY");
   txt += StringFormat("  Spread (Current): %.1f pts (Max: %d)\n", MarketInfo(Symbol(), MODE_SPREAD), InpMaxSpreadPoints);
   txt += StringFormat("  M15 ATR(14)    : %.1f pts (Min Required: %.1f pts)\n", atr14, InpMinATRPoints);
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  [POI Resistance] PDH: %.2f | Asian High: %.2f\n", g_pdh, g_asian_high);
   txt += StringFormat("  [POI Support]    PDL: %.2f | Asian Low : %.2f\n", g_pdl, g_asian_low);
   txt += StringFormat("  Current Ask/Bid: %.2f / %.2f\n", Ask, Bid);
   txt += "  --------------------------------------------------\n";
   txt += StringFormat("  Risk Settings  : Target RR 1:%.1f | BE Lock at %.1fR\n", InpTargetRR, InpBreakevenRR);
   txt += StringFormat("  SL Boundary    : Min %.0f pts ($%.2f) - Max %.0f pts ($%.2f)\n", 
                       InpMinSLPoints, InpMinSLPoints*Point, InpMaxSLPoints, InpMaxSLPoints*Point);
   txt += StringFormat("  Structural Exit: %s\n", InpStructuralExit ? "ENABLED (Protects Floating Profits)" : "DISABLED");
   txt += "  ==================================================\n";
   Comment(txt);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Always manage breakeven on live ticks
   ManageBreakeven();
   
   // Signal check strictly on New M15 Bar
   datetime cur_bar_time = iTime(Symbol(), PERIOD_M15, 0);
   if(cur_bar_time == g_last_bar_time)
   {
      return;
   }
   g_last_bar_time = cur_bar_time;
   
   // Check Structural Reversal for open trades on bar close
   CheckStructuralExit();
   
   // Update POIs once per new bar
   UpdatePOIs();
   UpdateHUD();
   
   // Active position filter (strictly 1 trade at a time)
   int dummy_t, dummy_type;
   double dummy_o, dummy_s, dummy_tp;
   if(CountOpenPositions(dummy_t, dummy_type, dummy_o, dummy_s, dummy_tp) > 0)
   {
      return;
   }
   
   // Session time filter
   if(!IsTradingTime()) return;
   
   // Volatility chop filter
   double cur_atr = iATR(Symbol(), PERIOD_M15, 14, 0);
   if(cur_atr < (InpMinATRPoints * Point))
   {
      return; // Skip dead chop
   }
   
   // Spread filter
   int cur_spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   if(cur_spread > InpMaxSpreadPoints)
   {
      PrintFormat("[SPREAD SKIP] Spread %d exceeds max %d", cur_spread, InpMaxSpreadPoints);
      return;
   }
   
   // Bar 1 Rejection Analysis
   double c1_high  = iHigh(Symbol(), PERIOD_M15, 1);
   double c1_low   = iLow(Symbol(), PERIOD_M15, 1);
   double c1_open  = iOpen(Symbol(), PERIOD_M15, 1);
   double c1_close = iClose(Symbol(), PERIOD_M15, 1);
   double c1_range = c1_high - c1_low;
   
   if(c1_range < (80.0 * Point)) return; // Skip micro-doji
   
   double c1_upper_wick = c1_high - MathMax(c1_open, c1_close);
   double c1_lower_wick = MathMin(c1_open, c1_close) - c1_low;
   
   // ==========================================
   // SELL SETUP: Rejection at Resistance POI
   // ==========================================
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
         
         PrintFormat("[POI SNIPER v2 SELL TRIGGER] POI Hit | Upper Wick: %.1f%% | Entry: %.2f | SL: %.2f (%.0f pts) | TP: %.2f (1:%.1f RR)",
                     upper_wick_ratio * 100.0, entry, sl, sl_dist_pts, tp, InpTargetRR);
         
         int ticket = OrderSend(Symbol(), OP_SELL, lots, Bid, InpSlippage, sl, tp, "POI_SNIPER_SELL", InpMagicNumber, 0, clrRed);
         if(ticket > 0)
         {
            PrintFormat("[ORDER OPEN SUCCESS] Ticket #%d SELL %.2f lots @ %.2f", ticket, lots, Bid);
            return;
         }
         else
         {
            PrintFormat("[ORDER OPEN ERROR] Error code: %d", GetLastError());
         }
      }
   }
   
   // ==========================================
   // BUY SETUP: Rejection at Support POI
   // ==========================================
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
         
         PrintFormat("[POI SNIPER v2 BUY TRIGGER] POI Hit | Lower Wick: %.1f%% | Entry: %.2f | SL: %.2f (%.0f pts) | TP: %.2f (1:%.1f RR)",
                     lower_wick_ratio * 100.0, entry, sl, sl_dist_pts, tp, InpTargetRR);
         
         int ticket = OrderSend(Symbol(), OP_BUY, lots, Ask, InpSlippage, sl, tp, "POI_SNIPER_BUY", InpMagicNumber, 0, clrBlue);
         if(ticket > 0)
         {
            PrintFormat("[ORDER OPEN SUCCESS] Ticket #%d BUY %.2f lots @ %.2f", ticket, lots, Ask);
            return;
         }
         else
         {
            PrintFormat("[ORDER OPEN ERROR] Error code: %d", GetLastError());
         }
      }
   }
}
//+------------------------------------------------------------------+
"""

# Write Master version
master_path_mt4 = os.path.join(MT4_EXPERTS_DIR, "Gold_POI_Sniper_Master_v1.mq4")
master_path_scratch = os.path.join(SCRATCH_DIR, "Gold_POI_Sniper_Master_v1.mq4")

with open(master_path_mt4, "w", encoding="utf-8") as f:
    f.write(source_code)
with open(master_path_scratch, "w", encoding="utf-8") as f:
    f.write(source_code)

# Write Tester version
tester_code = source_code.replace("Gold_POI_Sniper_Master_v1", "Gold_POI_Sniper_Tester_v1")
tester_path_mt4 = os.path.join(MT4_EXPERTS_DIR, "Gold_POI_Sniper_Tester_v1.mq4")
tester_path_scratch = os.path.join(SCRATCH_DIR, "Gold_POI_Sniper_Tester_v1.mq4")

with open(tester_path_mt4, "w", encoding="utf-8") as f:
    f.write(tester_code)
with open(tester_path_scratch, "w", encoding="utf-8") as f:
    f.write(tester_code)

print("Files written successfully.")

# Compile with MetaEditor
cmd_master = f'"{METAEDITOR}" /compile:"{master_path_mt4}" /log:"{SCRATCH_DIR}\\compile_poi_master.log"'
cmd_tester = f'"{METAEDITOR}" /compile:"{tester_path_mt4}" /log:"{SCRATCH_DIR}\\compile_poi_tester.log"'

subprocess.run(cmd_master, shell=True)
subprocess.run(cmd_tester, shell=True)

print("Compilation invoked.")
