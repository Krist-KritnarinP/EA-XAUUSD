files = [
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Tester_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v2_5.mq4',
    r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Tester_v2_5.mq4'
]

visual_inputs = '''extern string   SEP_VISUAL          = "=== VISUAL CHART OBJECTS & RADAR ===";
extern bool     InpDrawVisualZones  = true;   // TRUE: Draw Asian Box & POI Liquidity Zones on Chart
extern color    InpAsianBoxColor    = C'220,230,250'; // Soft Blue Asian Range Background
extern color    InpPDHColor         = clrCrimson;     // PDH Resistance Line (BSL)
extern color    InpPDLColor         = clrMediumSeaGreen; // PDL Support Line (SSL)
'''

draw_func = '''//+------------------------------------------------------------------+
//| Draw Visual POI Zones, Asian Box & Target Lines on Chart         |
//+------------------------------------------------------------------+
void DrawVisualPOIZones()
{
   if(!InpDrawVisualZones || IsTesting()) return;
   
   datetime cur_time = TimeCurrent();
   datetime today_start = cur_time - (cur_time % 86400);
   datetime asian_start = today_start;
   datetime asian_end   = today_start + 7 * 3600;
   datetime today_end   = today_start + 24 * 3600;
   
   // 1. Asian Session Box (00:00 - 07:00 MT4)
   if(g_asian_high > 0.0 && g_asian_low < 900000.0)
   {
      string boxName = "POI_AsianBox";
      if(ObjectFind(0, boxName) < 0)
      {
         ObjectCreate(0, boxName, OBJ_RECTANGLE, 0, asian_start, g_asian_high, asian_end, g_asian_low);
         ObjectSetInteger(0, boxName, OBJPROP_COLOR, InpAsianBoxColor);
         ObjectSetInteger(0, boxName, OBJPROP_BACK, true);
         ObjectSetInteger(0, boxName, OBJPROP_FILL, true);
         ObjectSetString(0, boxName, OBJPROP_TOOLTIP, "Asian Session Range (00:00-07:00 MT4)");
      }
      else
      {
         ObjectSetInteger(0, boxName, OBJPROP_TIME1, asian_start);
         ObjectSetDouble(0, boxName, OBJPROP_PRICE1, g_asian_high);
         ObjectSetInteger(0, boxName, OBJPROP_TIME2, asian_end);
         ObjectSetDouble(0, boxName, OBJPROP_PRICE2, g_asian_low);
      }
      
      // Asian High Extended Line
      string ahLine = "POI_AsianHigh_Line";
      if(ObjectFind(0, ahLine) < 0)
      {
         ObjectCreate(0, ahLine, OBJ_TREND, 0, asian_end, g_asian_high, today_end, g_asian_high);
         ObjectSetInteger(0, ahLine, OBJPROP_COLOR, clrDodgerBlue);
         ObjectSetInteger(0, ahLine, OBJPROP_STYLE, STYLE_DOT);
         ObjectSetInteger(0, ahLine, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, ahLine, OBJPROP_RAY_RIGHT, true);
         ObjectSetString(0, ahLine, OBJPROP_TEXT, " Asian High (Liquidity Pool)");
      }
      else
      {
         ObjectSetInteger(0, ahLine, OBJPROP_TIME1, asian_end);
         ObjectSetDouble(0, ahLine, OBJPROP_PRICE1, g_asian_high);
         ObjectSetInteger(0, ahLine, OBJPROP_TIME2, today_end);
         ObjectSetDouble(0, ahLine, OBJPROP_PRICE2, g_asian_high);
      }
      
      // Asian Low Extended Line
      string alLine = "POI_AsianLow_Line";
      if(ObjectFind(0, alLine) < 0)
      {
         ObjectCreate(0, alLine, OBJ_TREND, 0, asian_end, g_asian_low, today_end, g_asian_low);
         ObjectSetInteger(0, alLine, OBJPROP_COLOR, clrDodgerBlue);
         ObjectSetInteger(0, alLine, OBJPROP_STYLE, STYLE_DOT);
         ObjectSetInteger(0, alLine, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, alLine, OBJPROP_RAY_RIGHT, true);
         ObjectSetString(0, alLine, OBJPROP_TEXT, " Asian Low (Liquidity Pool)");
      }
      else
      {
         ObjectSetInteger(0, alLine, OBJPROP_TIME1, asian_end);
         ObjectSetDouble(0, alLine, OBJPROP_PRICE1, g_asian_low);
         ObjectSetInteger(0, alLine, OBJPROP_TIME2, today_end);
         ObjectSetDouble(0, alLine, OBJPROP_PRICE2, g_asian_low);
      }
   }
   
   // 2. PDH (Previous Day High - Daily BSL)
   if(g_pdh > 0.0)
   {
      string pdhLine = "POI_PDH_Line";
      if(ObjectFind(0, pdhLine) < 0)
      {
         ObjectCreate(0, pdhLine, OBJ_TREND, 0, today_start, g_pdh, today_end, g_pdh);
         ObjectSetInteger(0, pdhLine, OBJPROP_COLOR, InpPDHColor);
         ObjectSetInteger(0, pdhLine, OBJPROP_STYLE, STYLE_DASH);
         ObjectSetInteger(0, pdhLine, OBJPROP_WIDTH, 2);
         ObjectSetInteger(0, pdhLine, OBJPROP_RAY_RIGHT, true);
         ObjectSetString(0, pdhLine, OBJPROP_TEXT, " [POI] Previous Day High (Daily Buy Stops)");
      }
      else
      {
         ObjectSetInteger(0, pdhLine, OBJPROP_TIME1, today_start);
         ObjectSetDouble(0, pdhLine, OBJPROP_PRICE1, g_pdh);
         ObjectSetInteger(0, pdhLine, OBJPROP_TIME2, today_end);
         ObjectSetDouble(0, pdhLine, OBJPROP_PRICE2, g_pdh);
      }
   }
   
   // 3. PDL (Previous Day Low - Daily SSL)
   if(g_pdl > 0.0)
   {
      string pdlLine = "POI_PDL_Line";
      if(ObjectFind(0, pdlLine) < 0)
      {
         ObjectCreate(0, pdlLine, OBJ_TREND, 0, today_start, g_pdl, today_end, g_pdl);
         ObjectSetInteger(0, pdlLine, OBJPROP_COLOR, InpPDLColor);
         ObjectSetInteger(0, pdlLine, OBJPROP_STYLE, STYLE_DASH);
         ObjectSetInteger(0, pdlLine, OBJPROP_WIDTH, 2);
         ObjectSetInteger(0, pdlLine, OBJPROP_RAY_RIGHT, true);
         ObjectSetString(0, pdlLine, OBJPROP_TEXT, " [POI] Previous Day Low (Daily Sell Stops)");
      }
      else
      {
         ObjectSetInteger(0, pdlLine, OBJPROP_TIME1, today_start);
         ObjectSetDouble(0, pdlLine, OBJPROP_PRICE1, g_pdl);
         ObjectSetInteger(0, pdlLine, OBJPROP_TIME2, today_end);
         ObjectSetDouble(0, pdlLine, OBJPROP_PRICE2, g_pdl);
      }
   }
   
   // 4. Live Radar Indicator Tag (Current Watching Zone)
   string radarName = "POI_LiveRadar_Tag";
   double curPrice = Bid;
   string radarMsg = "";
   color radarColor = clrGray;
   double tagPrice = curPrice;
   
   if(g_pdh > 0.0 && g_asian_high > 0.0)
   {
      double nearestRes = MathMin(g_pdh, g_asian_high);
      if(curPrice >= (nearestRes - 150.0 * Point) && curPrice <= (MathMax(g_pdh, g_asian_high) + 200.0 * Point))
      {
         radarMsg = "🎯 [SELL RADAR ACTIVE] Near POI Resistance - Watching for Sweep & 35% Rejection Wick";
         radarColor = clrCrimson;
         tagPrice = MathMax(g_pdh, g_asian_high) + 80.0 * Point;
      }
   }
   if(radarMsg == "" && g_pdl > 0.0 && g_asian_low < 900000.0)
   {
      double nearestSup = MathMax(g_pdl, g_asian_low);
      if(curPrice <= (nearestSup + 150.0 * Point) && curPrice >= (MathMin(g_pdl, g_asian_low) - 200.0 * Point))
      {
         radarMsg = "🎯 [BUY RADAR ACTIVE] Near POI Support - Watching for Sweep & 35% Rejection Wick";
         radarColor = clrSeaGreen;
         tagPrice = MathMin(g_pdl, g_asian_low) - 80.0 * Point;
      }
   }
   
   if(radarMsg != "")
   {
      if(ObjectFind(0, radarName) < 0)
      {
         ObjectCreate(0, radarName, OBJ_TEXT, 0, cur_time, tagPrice);
         ObjectSetInteger(0, radarName, OBJPROP_COLOR, radarColor);
         ObjectSetInteger(0, radarName, OBJPROP_FONTSIZE, 9);
         ObjectSetString(0, radarName, OBJPROP_FONT, "Segoe UI Semibold");
         ObjectSetString(0, radarName, OBJPROP_TEXT, radarMsg);
      }
      else
      {
         ObjectSetInteger(0, radarName, OBJPROP_TIME1, cur_time);
         ObjectSetDouble(0, radarName, OBJPROP_PRICE1, tagPrice);
         ObjectSetString(0, radarName, OBJPROP_TEXT, radarMsg);
         ObjectSetInteger(0, radarName, OBJPROP_COLOR, radarColor);
      }
   }
   else
   {
      ObjectDelete(0, radarName);
   }
   
   ChartRedraw(0);
}'''

for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        c = f.read()
    
    # 1. Add visual inputs if not present
    if 'InpDrawVisualZones' not in c:
        c = c.replace('extern string   SEP_AI', visual_inputs + '\nextern string   SEP_AI')
    
    # 2. Add DrawVisualPOIZones function
    if 'void DrawVisualPOIZones()' not in c:
        # place before UpdateHUD
        c = c.replace('void UpdateHUD()', draw_func + '\n\nvoid UpdateHUD()')
        
    # 3. Call DrawVisualPOIZones in OnInit, OnTimer, and clean in OnDeinit
    c = c.replace('UpdateHUD();', 'UpdateHUD(); DrawVisualPOIZones();')
    
    if 'ObjectsDeleteAll(0, "POI_");' not in c:
        c = c.replace(
            'Comment("");',
            'Comment(""); ObjectsDeleteAll(0, "POI_"); ChartRedraw(0);'
        )
        
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(c)
    print('Visual zones successfully injected into:', fname)
