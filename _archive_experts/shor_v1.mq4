//+------------------------------------------------------------------+
//|                                                      shor_v1.mq4 |
//|                               Copyright 2026, Institutional Quant|
//|                        shor v1 - Statistical Gold Scalper Engine |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Institutional Quant"
#property link      "https://github.com/GoldSniper"
#property version   "1.00"
#property strict

//--- INPUT PARAMETERS: RISK & LOT ---
extern string   s_risk_settings             = "=== Risk & Lot Management ===";
input double    InpFixedLot                 = 0.03;       // Fixed Lot Size (0.02 - 0.05 recommended)
input double    InpTargetProfitUSD          = 8.00;       // Target Profit ($6.0 - $10.0 USD per oz)
input double    InpStopLossUSD              = 4.50;       // Stop Loss ($4.0 - $5.0 USD per oz)
input bool      InpEnableBreakeven          = true;       // Enable Breakeven Lock
input double    InpBreakevenTriggerUSD      = 4.00;       // Move SL to BE when profit reaches ($)
input double    InpBreakevenLockUSD         = 0.50;       // Lock profit amount on BE ($)
input int       InpMaxSpreadPoints          = 60;         // Max Allowed Spread (Points)
input int       InpMagicNumber              = 777101;     // Unique EA Magic Number

//--- INPUT PARAMETERS: 2 GOLDEN SESSIONS (THAI TIME UTC+7) ---
extern string   s_session_filters           = "=== 2 Golden Scalping Sessions (Thai Time UTC+7) ===";
input int       InpThaiTimeOffset           = 5;          // Thai Time minus Server Time (XM = 5 hours in summer/4 in winter)
input string    InpLondonSessionStart       = "14:00";    // London Golden Session Start (Thai Time)
input string    InpLondonSessionEnd         = "16:00";    // London Golden Session End (Thai Time)
input string    InpNYSessionStart           = "20:00";    // New York Golden Session Start (Thai Time)
input string    InpNYSessionEnd             = "22:30";    // New York Golden Session End (Thai Time)
input int       InpMaxTradesPerSession      = 1;          // Max trades per Golden Window (No overtrading)

//--- INPUT PARAMETERS: RADAR & FIBO ---
extern string   s_radar_settings            = "=== Asian Box & Fibo Radar ===";
input int       InpAsianStartHour           = 5;          // Asian Box Start (Thai Hour: 05:00)
input int       InpAsianEndHour             = 14;         // Asian Box End (Thai Hour: 14:00)
input int       InpRSI_Period               = 14;         // RSI Period for Exhaustion
input double    InpRSI_Oversold             = 35.0;       // RSI Oversold Hook Level
input double    InpRSI_Overbought           = 65.0;       // RSI Overbought Hook Level
input double    InpSweepBufferUSD           = 0.50;       // Min Sweep beyond Asian border ($)

//--- GLOBAL STATE VARIABLES ---
double   g_asian_high   = 0.0;
double   g_asian_low    = 0.0;
double   g_asian_eq     = 0.0;
datetime g_last_asian_calc_day = 0;
int      g_london_trades_today = 0;
int      g_ny_trades_today     = 0;
datetime g_last_trade_day      = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("[shor v1] Initialized successfully. Symbol: ", Symbol(), " | Magic: ", InpMagicNumber);
   UpdateAsianBox();
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Comment("");
}

//+------------------------------------------------------------------+
//| Get Current Thai Time (UTC+7)                                    |
//+------------------------------------------------------------------+
datetime GetThaiTime()
{
   return (TimeCurrent() + InpThaiTimeOffset * 3600);
}

//+------------------------------------------------------------------+
//| Check if current Thai time is in active range                    |
//+------------------------------------------------------------------+
bool IsInTimeRange(datetime t, string start_str, string end_str)
{
   int start_h = (int)StringToInteger(StringSubstr(start_str, 0, 2));
   int start_m = (int)StringToInteger(StringSubstr(start_str, 3, 2));
   int end_h   = (int)StringToInteger(StringSubstr(end_str, 0, 2));
   int end_m   = (int)StringToInteger(StringSubstr(end_str, 3, 2));

   MqlDateTime dt;
   TimeToStruct(t, dt);
   int cur_minutes = dt.hour * 60 + dt.min;
   int start_minutes = start_h * 60 + start_m;
   int end_minutes   = end_h * 60 + end_m;

   return (cur_minutes >= start_minutes && cur_minutes <= end_minutes);
}

//+------------------------------------------------------------------+
//| Update Asian Box High / Low / Equilibrium                        |
//+------------------------------------------------------------------+
void UpdateAsianBox()
{
   datetime thai_now = GetThaiTime();
   MqlDateTime dt_now;
   TimeToStruct(thai_now, dt_now);

   datetime today_zero_thai = thai_now - (dt_now.hour * 3600 + dt_now.min * 60 + dt_now.sec);
   datetime asian_start_thai = today_zero_thai + InpAsianStartHour * 3600;
   datetime asian_end_thai   = today_zero_thai + InpAsianEndHour * 3600;

   // Convert to Server Time
   datetime asian_start_server = asian_start_thai - InpThaiTimeOffset * 3600;
   datetime asian_end_server   = asian_end_thai - InpThaiTimeOffset * 3600;

   int i_start = iBarShift(Symbol(), PERIOD_M15, asian_start_server, false);
   int i_end   = iBarShift(Symbol(), PERIOD_M15, asian_end_server, false);

   if(i_start < 0 || i_end < 0) return;
   if(i_end > i_start) { int tmp = i_start; i_start = i_end; i_end = tmp; }

   int count = i_start - i_end + 1;
   if(count <= 0) return;

   int highest_bar = iHighest(Symbol(), PERIOD_M15, MODE_HIGH, count, i_end);
   int lowest_bar  = iLowest(Symbol(), PERIOD_M15, MODE_LOW, count, i_end);

   if(highest_bar >= 0 && lowest_bar >= 0)
   {
      g_asian_high = High[highest_bar];
      g_asian_low  = Low[lowest_bar];
      g_asian_eq   = (g_asian_high + g_asian_low) / 2.0;
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Reset daily counters
   datetime thai_now = GetThaiTime();
   MqlDateTime dt;
   TimeToStruct(thai_now, dt);
   datetime today_thai = thai_now - (dt.hour * 3600 + dt.min * 60 + dt.sec);

   if(today_thai != g_last_trade_day)
   {
      g_london_trades_today = 0;
      g_ny_trades_today     = 0;
      g_last_trade_day      = today_thai;
   }

   // 1. Maintain Asian Box
   UpdateAsianBox();

   // 2. Manage Breakeven on Open Trades
   ManageBreakeven();

   // 3. Render High-Tech HUD Display
   RenderHUD();

   // 4. Spread Filter
   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   if(spread > InpMaxSpreadPoints) return;

   // 5. Check if any order already open for this EA
   if(CountOpenOrders() > 0) return;

   // 6. Check Active Golden Sessions
   bool in_london = IsInTimeRange(thai_now, InpLondonSessionStart, InpLondonSessionEnd);
   bool in_ny     = IsInTimeRange(thai_now, InpNYSessionStart, InpNYSessionEnd);

   if(!in_london && !in_ny) return;

   // Session Trade Limit Check
   if(in_london && g_london_trades_today >= InpMaxTradesPerSession) return;
   if(in_ny && g_ny_trades_today >= InpMaxTradesPerSession) return;

   // Ensure valid Asian Box
   if(g_asian_high <= 0 || g_asian_low <= 0 || (g_asian_high - g_asian_low) < 5.0) return;

   // 7. Technical Signals: Fibo, Asian Sweep & M5 Rejection
   double bid = Bid;
   double ask = Ask;
   double rsi_m5  = iRSI(Symbol(), PERIOD_M5, InpRSI_Period, PRICE_CLOSE, 0);
   double rsi_m15 = iRSI(Symbol(), PERIOD_M15, InpRSI_Period, PRICE_CLOSE, 0);

   double m5_open  = iOpen(Symbol(), PERIOD_M5, 1);
   double m5_close = iClose(Symbol(), PERIOD_M5, 1);
   double m5_high  = iHigh(Symbol(), PERIOD_M5, 1);
   double m5_low   = iLow(Symbol(), PERIOD_M5, 1);
   double m5_body  = MathAbs(m5_close - m5_open);
   double lower_wick = MathMin(m5_open, m5_close) - m5_low;
   double upper_wick = m5_high - MathMax(m5_open, m5_close);

   // --- SETUP A: BUY (Discount Zone + Asian Low Sweep Fade) ---
   // Price is below Asian Equilibrium, low swept below Asian Low, and printed strong rejection
   if(bid < g_asian_eq)
   {
      bool swept_low = (Low[0] <= g_asian_low - InpSweepBufferUSD || m5_low <= g_asian_low);
      bool bullish_rejection = (lower_wick >= m5_body * 1.2 && m5_close >= m5_low + lower_wick);
      bool rsi_hook_up = (rsi_m5 < InpRSI_Oversold || rsi_m15 < 40.0);

      if(swept_low && (bullish_rejection || rsi_hook_up))
      {
         double sl = NormalizeDouble(ask - InpStopLossUSD, Digits);
         double tp = NormalizeDouble(ask + InpTargetProfitUSD, Digits);

         // Double check minimum 6 USD target
         if(tp - ask >= 6.00)
         {
            int ticket = OrderSend(Symbol(), OP_BUY, InpFixedLot, ask, 30, sl, tp, "shor v1 Buy Sweep", InpMagicNumber, 0, clrGreen);
            if(ticket > 0)
            {
               Print("[shor v1] BUY EXECUTION #", ticket, " @ ", ask, " | SL: ", sl, " | TP: ", tp);
               if(in_london) g_london_trades_today++;
               if(in_ny) g_ny_trades_today++;
               return;
            }
         }
      }
   }

   // --- SETUP B: SELL (Premium Zone + Asian High Sweep Fade) ---
   // Price is above Asian Equilibrium, high swept above Asian High, and printed strong rejection
   if(bid > g_asian_eq)
   {
      bool swept_high = (High[0] >= g_asian_high + InpSweepBufferUSD || m5_high >= g_asian_high);
      bool bearish_rejection = (upper_wick >= m5_body * 1.2 && m5_close <= m5_high - upper_wick);
      bool rsi_hook_down = (rsi_m5 > InpRSI_Overbought || rsi_m15 > 60.0);

      if(swept_high && (bearish_rejection || rsi_hook_down))
      {
         double sl = NormalizeDouble(bid + InpStopLossUSD, Digits);
         double tp = NormalizeDouble(bid - InpTargetProfitUSD, Digits);

         // Double check minimum 6 USD target
         if(bid - tp >= 6.00)
         {
            int ticket = OrderSend(Symbol(), OP_SELL, InpFixedLot, bid, 30, sl, tp, "shor v1 Sell Sweep", InpMagicNumber, 0, clrRed);
            if(ticket > 0)
            {
               Print("[shor v1] SELL EXECUTION #", ticket, " @ ", bid, " | SL: ", sl, " | TP: ", tp);
               if(in_london) g_london_trades_today++;
               if(in_ny) g_ny_trades_today++;
               return;
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Manage Breakeven Protection                                      |
//+------------------------------------------------------------------+
void ManageBreakeven()
{
   if(!InpEnableBreakeven) return;

   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != InpMagicNumber) continue;

      if(OrderType() == OP_BUY)
      {
         double profit_dist = Bid - OrderOpenPrice();
         if(profit_dist >= InpBreakevenTriggerUSD)
         {
            double be_sl = NormalizeDouble(OrderOpenPrice() + InpBreakevenLockUSD, Digits);
            if(OrderStopLoss() < be_sl || OrderStopLoss() == 0.0)
            {
               bool mod = OrderModify(OrderTicket(), OrderOpenPrice(), be_sl, OrderTakeProfit(), 0, clrGold);
               if(mod) Print("[shor v1] BUY #", OrderTicket(), " Breakeven Locked at: ", be_sl);
            }
         }
      }
      else if(OrderType() == OP_SELL)
      {
         double profit_dist = OrderOpenPrice() - Ask;
         if(profit_dist >= InpBreakevenTriggerUSD)
         {
            double be_sl = NormalizeDouble(OrderOpenPrice() - InpBreakevenLockUSD, Digits);
            if(OrderStopLoss() > be_sl || OrderStopLoss() == 0.0)
            {
               bool mod = OrderModify(OrderTicket(), OrderOpenPrice(), be_sl, OrderTakeProfit(), 0, clrGold);
               if(mod) Print("[shor v1] SELL #", OrderTicket(), " Breakeven Locked at: ", be_sl);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Count Active Open Orders for this EA                             |
//+------------------------------------------------------------------+
int CountOpenOrders()
{
   int count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicNumber)
         {
            if(OrderType() == OP_BUY || OrderType() == OP_SELL)
               count++;
         }
      }
   }
   return count;
}

//+------------------------------------------------------------------+
//| Render Institutional HUD Comment on MT4 Chart                    |
//+------------------------------------------------------------------+
void RenderHUD()
{
   datetime thai_now = GetThaiTime();
   MqlDateTime dt;
   TimeToStruct(thai_now, dt);

   bool in_london = IsInTimeRange(thai_now, InpLondonSessionStart, InpLondonSessionEnd);
   bool in_ny     = IsInTimeRange(thai_now, InpNYSessionStart, InpNYSessionEnd);
   string session_status = in_london ? "🟢 LONDON GOLDEN WINDOW (ACTIVE)" : (in_ny ? "🟢 NEW YORK GOLDEN WINDOW (ACTIVE)" : "⚪ STANDBY (OUT OF WINDOW)");

   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   double span = g_asian_high - g_asian_low;

   string txt = "";
   txt += "========================================================\n";
   txt += "   🏹  shor v1 - INSTITUTIONAL STATISTICAL SCALPER      \n";
   txt += "========================================================\n";
   txt += StringFormat(" • เวลาไทย (Thai Time): %02d:%02d:%02d\n", dt.hour, dt.min, dt.sec);
   txt += StringFormat(" • สถานะเซสชั่น: %s\n", session_status);
   txt += StringFormat(" • สเปรดสด: %d pts (ลิมิตสูงสุด: %d pts)\n", spread, InpMaxSpreadPoints);
   txt += "--------------------------------------------------------\n";
   txt += StringFormat(" • Asian High (เพดาน): $%.2f\n", g_asian_high);
   txt += StringFormat(" • Asian Low (ฐานรับ): $%.2f\n", g_asian_low);
   txt += StringFormat(" • Asian Equilibrium (50%%): $%.2f (Span: $%.2f)\n", g_asian_eq, span);
   txt += "--------------------------------------------------------\n";
   txt += StringFormat(" • เป้าหมายกำไร (TP): $%.2f USD (600 - 1,000 pts)\n", InpTargetProfitUSD);
   txt += StringFormat(" • ตัดขาดทุน (SL): $%.2f USD | Breakeven: $%.2f USD\n", InpStopLossUSD, InpBreakevenTriggerUSD);
   txt += StringFormat(" • ขนาด Lot: %.2f | ไม้ที่เปิดค้าง: %d ไม้\n", InpFixedLot, CountOpenOrders());
   txt += StringFormat(" • โควตาเทรดวันนี้: ลอนดอน (%d/%d) | นิวยอร์ก (%d/%d)\n", g_london_trades_today, InpMaxTradesPerSession, g_ny_trades_today, InpMaxTradesPerSession);
   txt += "========================================================\n";

   Comment(txt);
}
