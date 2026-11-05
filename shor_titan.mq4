//+------------------------------------------------------------------+
//|                                                   shor_titan.mq4 |
//|                               Copyright 2026, Institutional Quant|
//|                 APEX SHOR-TITAN - High-Frequency Hybrid Scalper  |
//+------------------------------------------------------------------+
#property copyright "Copyright 2026, Institutional Quant"
#property link      "https://github.com/GoldSniper"
#property version   "2.00"
#property strict

//--- 1. RISK & LOT MANAGEMENT ---
extern string   s_risk_settings             = "=== Risk & Stepwise Harvesting ===";
input double    InpBaseLot                  = 0.04;       // Base Lot Size (Must be even, e.g., 0.04 for 2x0.02 split)
input double    InpStopLossUSD              = 3.50;       // Initial Stop Loss ($3.50 USD per oz -> Capped Loss)
input double    InpTP1_CashUSD              = 4.50;       // TP1: Cash Harvest Trigger ($4.50 USD -> Closes 50% Lot)
input double    InpTP2_RunnerUSD            = 10.50;      // TP2: Full Runner Target ($10.50 USD per oz)
input double    InpBreakevenLockUSD         = 1.00;       // Breakeven Profit Lock Amount ($1.00 USD -> Safely Above Spread)
input bool      InpEnableTrailing           = true;       // Enable Dynamic Volatility Trailing for 50% Runner
input double    InpTrailingStartUSD         = 6.00;       // Start Trailing after profit exceeds ($6.00 USD)
input double    InpTrailingDistanceUSD      = 3.00;       // Trailing distance behind price ($3.00 USD)
input int       InpMaxSpreadPoints          = 60;         // Max Allowed Spread (Points)
input int       InpMagicNumber              = 777202;     // Unique Magic Number for SHOR-TITAN

//--- 2. TIME-OF-DAY GOLDEN SESSIONS (THAI TIME UTC+7) ---
extern string   s_session_settings          = "=== 2 Golden Scalping Sessions (Thai Time UTC+7) ===";
input int       InpThaiTimeOffset           = 5;          // Thai Time minus Server Time (XM = 5h in Summer/4h in Winter)
input string    InpLondonSessionStart       = "14:00";    // London Golden Window Start (Thai Time)
input string    InpLondonSessionEnd         = "16:00";    // London Golden Window End (Thai Time)
input string    InpNYSessionStart           = "20:00";    // New York Golden Window Start (Thai Time)
input string    InpNYSessionEnd             = "22:30";    // New York Golden Window End (Thai Time)
input int       InpMaxTradesPerSession      = 2;          // Max trades per Golden Window (Clean & disciplined)

//--- 3. QUANTITATIVE Z-SCORE & SMC RADAR ---
extern string   s_radar_settings            = "=== Quantitative Z-Score & Asian Box Radar ===";
input int       InpAsianStartHour           = 5;          // Asian Box Start (Thai Hour: 05:00)
input int       InpAsianEndHour             = 14;         // Asian Box End (Thai Hour: 14:00)
input int       InpZScorePeriod             = 20;         // Z-Score Rolling Period (Chart Bars)
input double    InpZScoreThreshold          = 2.00;       // Statistical Deviation Threshold (2.00 Sigma)
input int       InpRSI_Period               = 14;         // RSI Exhaustion Period
input double    InpRSI_Oversold             = 35.0;       // RSI Oversold Hook Threshold
input double    InpRSI_Overbought           = 65.0;       // RSI Overbought Hook Threshold
input double    InpSweepBufferUSD           = 0.50;       // Min Asian Border Penetration Buffer ($)
input double    InpSpikeFilterUSD           = 6.00;       // Shockwave Filter ($6.00 in 1 min -> Pause entries 3m)

//--- INTERNAL GLOBAL VARIABLES ---
double   g_asian_high          = 0.0;
double   g_asian_low           = 0.0;
double   g_asian_eq            = 0.0;
datetime g_last_asian_calc_day = 0;
int      g_london_trades_today = 0;
int      g_ny_trades_today     = 0;
datetime g_last_trade_day      = 0;
datetime g_spike_pause_until   = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("[SHOR-TITAN v2] Initialized successfully. Symbol: ", Symbol(), " | Magic: ", InpMagicNumber);
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
//| Time Range Checker                                               |
//+------------------------------------------------------------------+
bool IsInTimeRange(datetime t, string start_str, string end_str)
{
   int start_h = (int)StringToInteger(StringSubstr(start_str, 0, 2));
   int start_m = (int)StringToInteger(StringSubstr(start_str, 3, 2));
   int end_h   = (int)StringToInteger(StringSubstr(end_str, 0, 2));
   int end_m   = (int)StringToInteger(StringSubstr(end_str, 3, 2));

   MqlDateTime dt;
   TimeToStruct(t, dt);
   int cur_minutes   = dt.hour * 60 + dt.min;
   int start_minutes = start_h * 60 + start_m;
   int end_minutes   = end_h * 60 + end_m;

   return (cur_minutes >= start_minutes && cur_minutes <= end_minutes);
}

//+------------------------------------------------------------------+
//| Calculate Rolling Z-Score dynamically matching chart Period      |
//+------------------------------------------------------------------+
double CalculateZScore(int period)
{
   int tf = Period();
   double sum = 0.0;
   for(int i = 1; i <= period; i++)
   {
      sum += iClose(Symbol(), tf, i);
   }
   double mean = sum / period;

   double sum_sq = 0.0;
   for(int i = 1; i <= period; i++)
   {
      double diff = iClose(Symbol(), tf, i) - mean;
      sum_sq += diff * diff;
   }
   double std_dev = MathSqrt(sum_sq / period);
   if(std_dev <= 0.0) std_dev = 0.01;

   double current_p = Bid;
   return (current_p - mean) / std_dev;
}

//+------------------------------------------------------------------+
//| Update Asian Box Boundaries                                      |
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
      g_asian_high = iHigh(Symbol(), PERIOD_M15, highest_bar);
      g_asian_low  = iLow(Symbol(), PERIOD_M15, lowest_bar);
      g_asian_eq   = (g_asian_high + g_asian_low) / 2.0;
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // 1. Maintain Daily Counters
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

   // 2. Shockwave Spike Filter (1-minute flash anomaly > $6.00)
   if((iHigh(Symbol(), PERIOD_M1, 0) - iLow(Symbol(), PERIOD_M1, 0)) >= InpSpikeFilterUSD)
   {
      g_spike_pause_until = TimeCurrent() + 180; // Pause 3 minutes for post-shockwave cooling
   }

   // 3. Maintain Asian Box
   UpdateAsianBox();

   // 4. Execute Stepwise Harvesting & Dynamic Trailing on Open Orders
   ManageOpenOrders();

   // 5. Render HUD Display
   RenderHUD();

   // 6. Volatility & Shockwave Block
   if(TimeCurrent() < g_spike_pause_until) return;

   // 7. Spread Guard
   int spread = (int)MarketInfo(Symbol(), MODE_SPREAD);
   if(spread > InpMaxSpreadPoints) return;

   // 8. Max Simultaneous Positions: 1 Position at a time
   if(CountActivePositions() > 0) return;

   // 9. Golden Session Windows Check
   bool in_london = IsInTimeRange(thai_now, InpLondonSessionStart, InpLondonSessionEnd);
   bool in_ny     = IsInTimeRange(thai_now, InpNYSessionStart, InpNYSessionEnd);

   if(!in_london && !in_ny) return;
   if(in_london && g_london_trades_today >= InpMaxTradesPerSession) return;
   if(in_ny && g_ny_trades_today >= InpMaxTradesPerSession) return;

   // Ensure valid Asian Box exists
   if(g_asian_high <= 0 || g_asian_low <= 0 || (g_asian_high - g_asian_low) < 5.0) return;

   // 10. Quantitative Indicator Calculation (Dynamic to Chart Timeframe, e.g. M15/M5)
   int tf = Period();
   double bid = Bid;
   double ask = Ask;
   double z_score = CalculateZScore(InpZScorePeriod);
   double rsi_chart = iRSI(Symbol(), tf, InpRSI_Period, PRICE_CLOSE, 0);
   double rsi_m15   = iRSI(Symbol(), PERIOD_M15, InpRSI_Period, PRICE_CLOSE, 0);

   double bar_open   = iOpen(Symbol(), tf, 1);
   double bar_close  = iClose(Symbol(), tf, 1);
   double bar_high   = iHigh(Symbol(), tf, 1);
   double bar_low    = iLow(Symbol(), tf, 1);
   double bar_body   = MathAbs(bar_close - bar_open);
   double lower_wick = MathMin(bar_open, bar_close) - bar_low;
   double upper_wick = bar_high - MathMax(bar_open, bar_close);

   // --- STRATEGY A: QUANT BUY (Discount Zone + Z-Score Reversion + Sweep Rejection) ---
   if(bid < g_asian_eq)
   {
      bool swept_low = (Low[0] <= (g_asian_low + InpSweepBufferUSD) || bar_low <= g_asian_low);
      bool z_extreme_buy = (z_score <= -InpZScoreThreshold);
      bool bullish_wick = (lower_wick >= bar_body * 0.8 && bar_close >= bar_low + lower_wick);
      bool rsi_oversold = (rsi_chart <= InpRSI_Oversold || rsi_m15 <= 38.0);

      // Trigger condition: Extreme deviation + (Rejection wick OR swept low with RSI hook)
      if((z_extreme_buy || swept_low) && (bullish_wick || rsi_oversold))
      {
         double sl = NormalizeDouble(ask - InpStopLossUSD, Digits);
         double tp = NormalizeDouble(ask + InpTP2_RunnerUSD, Digits);

         int ticket = OrderSend(Symbol(), OP_BUY, InpBaseLot, ask, 30, sl, tp, "SHOR-TITAN Buy", InpMagicNumber, 0, clrGreen);
         if(ticket > 0)
         {
            Print("[SHOR-TITAN] BUY ORDER PLACED #", ticket, " @ ", ask, " | SL: ", sl, " | TP2: ", tp, " | Z-Score: ", DoubleToString(z_score, 2));
            if(in_london) g_london_trades_today++;
            if(in_ny) g_ny_trades_today++;
            return;
         }
      }
   }

   // --- STRATEGY B: QUANT SELL (Premium Zone + Z-Score Reversion + Sweep Rejection) ---
   if(bid > g_asian_eq)
   {
      bool swept_high = (High[0] >= (g_asian_high - InpSweepBufferUSD) || bar_high >= g_asian_high);
      bool z_extreme_sell = (z_score >= InpZScoreThreshold);
      bool bearish_wick = (upper_wick >= bar_body * 0.8 && bar_close <= bar_high - upper_wick);
      bool rsi_overbought = (rsi_chart >= InpRSI_Overbought || rsi_m15 >= 62.0);

      // Trigger condition: Extreme deviation + (Rejection wick OR swept high with RSI hook)
      if((z_extreme_sell || swept_high) && (bearish_wick || rsi_overbought))
      {
         double sl = NormalizeDouble(bid + InpStopLossUSD, Digits);
         double tp = NormalizeDouble(bid - InpTP2_RunnerUSD, Digits);

         int ticket = OrderSend(Symbol(), OP_SELL, InpBaseLot, bid, 30, sl, tp, "SHOR-TITAN Sell", InpMagicNumber, 0, clrRed);
         if(ticket > 0)
         {
            Print("[SHOR-TITAN] SELL ORDER PLACED #", ticket, " @ ", bid, " | SL: ", sl, " | TP2: ", tp, " | Z-Score: ", DoubleToString(z_score, 2));
            if(in_london) g_london_trades_today++;
            if(in_ny) g_ny_trades_today++;
            return;
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Stepwise Micro-Harvesting & Dynamic Trailing Engine              |
//+------------------------------------------------------------------+
void ManageOpenOrders()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol() || OrderMagicNumber() != InpMagicNumber) continue;

      double open_p = OrderOpenPrice();
      double cur_lot = OrderLots();
      double half_lot = NormalizeDouble(InpBaseLot / 2.0, 2);

      // --- 1. BUY ORDER MANAGEMENT ---
      if(OrderType() == OP_BUY)
      {
         double profit_usd = Bid - open_p;

         // A. Stepwise Micro-Harvesting: Partial Close 50% Lot at +$3.50 USD
         if(profit_usd >= InpTP1_CashUSD && cur_lot > half_lot)
         {
            double close_lot = half_lot;
            bool closed_half = OrderClose(OrderTicket(), close_lot, Bid, 30, clrGold);
            if(closed_half)
            {
               Print("[SHOR-TITAN] 💰 TP1 HARVEST: Closed 50% (", close_lot, " lots) at +$", profit_usd, " USD profit!");
            }
         }

         // B. Instant Breakeven Lock: Move SL to Open + $0.50 USD once profit reaches InpTP1_CashUSD
         if(profit_usd >= InpTP1_CashUSD)
         {
            double be_sl = NormalizeDouble(open_p + InpBreakevenLockUSD, Digits);
            if(OrderStopLoss() < be_sl || OrderStopLoss() == 0.0)
            {
               bool mod = OrderModify(OrderTicket(), open_p, be_sl, OrderTakeProfit(), 0, clrAqua);
               if(mod) Print("[SHOR-TITAN] 🛡️ SL MOVED TO BREAKEVEN: Locked at ", be_sl);
            }
         }

         // C. Dynamic Volatility Trailing Stop on Remaining 50% Runner
         if(InpEnableTrailing && profit_usd >= InpTrailingStartUSD)
         {
            double trail_sl = NormalizeDouble(Bid - InpTrailingDistanceUSD, Digits);
            double be_sl    = NormalizeDouble(open_p + InpBreakevenLockUSD, Digits);
            double new_sl   = MathMax(trail_sl, be_sl);

            if(new_sl > OrderStopLoss() + (0.30 * Point * 10))
            {
               bool mod_trail_buy = OrderModify(OrderTicket(), open_p, new_sl, OrderTakeProfit(), 0, clrLime);
            }
         }
      }

      // --- 2. SELL ORDER MANAGEMENT ---
      else if(OrderType() == OP_SELL)
      {
         double profit_usd = open_p - Ask;

         // A. Stepwise Micro-Harvesting: Partial Close 50% Lot at +$3.50 USD
         if(profit_usd >= InpTP1_CashUSD && cur_lot > half_lot)
         {
            double close_lot = half_lot;
            bool closed_half = OrderClose(OrderTicket(), close_lot, Ask, 30, clrGold);
            if(closed_half)
            {
               Print("[SHOR-TITAN] 💰 TP1 HARVEST: Closed 50% (", close_lot, " lots) at +$", profit_usd, " USD profit!");
            }
         }

         // B. Instant Breakeven Lock: Move SL to Open - $0.50 USD once profit reaches InpTP1_CashUSD
         if(profit_usd >= InpTP1_CashUSD)
         {
            double be_sl = NormalizeDouble(open_p - InpBreakevenLockUSD, Digits);
            if(OrderStopLoss() > be_sl || OrderStopLoss() == 0.0)
            {
               bool mod = OrderModify(OrderTicket(), open_p, be_sl, OrderTakeProfit(), 0, clrAqua);
               if(mod) Print("[SHOR-TITAN] 🛡️ SL MOVED TO BREAKEVEN: Locked at ", be_sl);
            }
         }

         // C. Dynamic Volatility Trailing Stop on Remaining 50% Runner
         if(InpEnableTrailing && profit_usd >= InpTrailingStartUSD)
         {
            double trail_sl = NormalizeDouble(Ask + InpTrailingDistanceUSD, Digits);
            double be_sl    = NormalizeDouble(open_p - InpBreakevenLockUSD, Digits);
            double new_sl   = MathMin(trail_sl, be_sl);

            if(OrderStopLoss() == 0.0 || new_sl < OrderStopLoss() - (0.30 * Point * 10))
            {
               bool mod_trail_sell = OrderModify(OrderTicket(), open_p, new_sl, OrderTakeProfit(), 0, clrLime);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Count Active Open Positions for this EA                          |
//+------------------------------------------------------------------+
int CountActivePositions()
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
//| Render High-Frequency Tactical HUD Display                      |
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
   double z = CalculateZScore(InpZScorePeriod);

   string txt = "";
   txt += "========================================================\n";
   txt += "   ⚡  APEX SHOR-TITAN - NEXT-GEN QUANT SCALPER        \n";
   txt += "========================================================\n";
   txt += StringFormat(" • เวลาไทย (Thai Time): %02d:%02d:%02d\n", dt.hour, dt.min, dt.sec);
   string tf_str = (Period() == PERIOD_M15) ? "M15" : ((Period() == PERIOD_M5) ? "M5" : (string)Period());
   txt += StringFormat(" • สถิติ Z-Score (%s): %+.2f Sigma (Limit: ±%.1fσ)\n", tf_str, z, InpZScoreThreshold);
   txt += StringFormat(" • สเปรดสด: %d pts (ลิมิตสูงสุด: %d pts)\n", spread, InpMaxSpreadPoints);
   txt += "--------------------------------------------------------\n";
   txt += StringFormat(" • Asian High: $%.2f | Low: $%.2f\n", g_asian_high, g_asian_low);
   txt += StringFormat(" • Asian Equilibrium (50%%): $%.2f (Span: $%.2f)\n", g_asian_eq, span);
   txt += "--------------------------------------------------------\n";
   txt += StringFormat(" • TP1 (Cash Harvest 50%%): +$%.2f USD + Auto Breakeven\n", InpTP1_CashUSD);
   txt += StringFormat(" • TP2 (Runner Target): +$%.2f USD | Initial SL: -$%.2f USD\n", InpTP2_RunnerUSD, InpStopLossUSD);
   txt += StringFormat(" • Base Lot: %.2f | ไม้ที่เปิดค้าง: %d ไม้\n", InpBaseLot, CountActivePositions());
   txt += StringFormat(" • โควตาเทรดวันนี้: ลอนดอน (%d/%d) | นิวยอร์ก (%d/%d)\n", g_london_trades_today, InpMaxTradesPerSession, g_ny_trades_today, InpMaxTradesPerSession);
   txt += "========================================================\n";

   Comment(txt);
}
