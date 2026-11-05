import os
from compile_mq4 import compile_mq4

bridge_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Bridge_v6_3_6.mq4"
tester_path = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Tester_v6_3_6.mq4"

def update_file(fpath):
    with open(fpath, "r", encoding="latin1") as f:
        text = f.read()

    # 1. Update NY Hours & Header
    old_ny_header = '''input string          Header_NY               = "=== NEW YORK INSTITUTIONAL ENGINE (15:30-19:00 ICT/SMC) ===";
input int             NYTradeStartHour        = 15;             // NY Session Start Hour (15:30 - US Cash Open)
input int             NYTradeStartMin         = 30;             // NY Session Start Minute (15:30)
input int             NYTradeEndHour          = 19;             // NY Session End Hour (19:00)
input int             NYTradeEndMin           = 0;              // NY Session End Minute'''

    new_ny_header = '''input string          Header_NY               = "=== NEW YORK INSTITUTIONAL ENGINE (16:00-17:45 ICT FVG) ===";
input int             NYTradeStartHour        = 16;             // NY Session Start Hour (16:00 - Post-News Golden Expansion)
input int             NYTradeStartMin         = 0;              // NY Session Start Minute (16:00)
input int             NYTradeEndHour          = 17;             // NY Session End Hour (17:45 - Cutoff Before London Fix Reversal)
input int             NYTradeEndMin           = 45;             // NY Session End Minute'''

    assert old_ny_header in text, f"old_ny_header not found in {fpath}"
    text = text.replace(old_ny_header, new_ny_header)

    # 2. Eliminate EMA50 Pullback fallback in New York (100% Pure ICT FVG)
    old_buy_fvg = '''               if(bullFVG)
               {
                  validBuyTrigger = true;
                  setupSubDesc = "ICT Bullish FVG Imbalance Expansion";
               }
               else if(!NY_RequireICT_FVG || (testedEMA && isBullRejection))
               {
                  validBuyTrigger = true;
                  setupSubDesc = "EMA50 Pullback Continuation";
               }'''

    new_buy_fvg = '''               // 100% Pure ICT FVG Entry (Zero Retail EMA50 Fallback)
               if(bullFVG)
               {
                  validBuyTrigger = true;
                  setupSubDesc = "ICT Bullish FVG Imbalance Expansion";
               }'''

    assert old_buy_fvg in text, f"old_buy_fvg not found in {fpath}"
    text = text.replace(old_buy_fvg, new_buy_fvg)

    old_sell_fvg = '''               if(bearFVG)
               {
                  validSellTrigger = true;
                  setupSubDesc = "ICT Bearish FVG Imbalance Breakdown";
               }
               else if(!NY_RequireICT_FVG || (testedEMA && isBearRejection))
               {
                  validSellTrigger = true;
                  setupSubDesc = "EMA50 Pullback Continuation";
               }'''

    new_sell_fvg = '''               // 100% Pure ICT FVG Entry (Zero Retail EMA50 Fallback)
               if(bearFVG)
               {
                  validSellTrigger = true;
                  setupSubDesc = "ICT Bearish FVG Imbalance Breakdown";
               }'''

    assert old_sell_fvg in text, f"old_sell_fvg not found in {fpath}"
    text = text.replace(old_sell_fvg, new_sell_fvg)

    # 3. Fix Error 4108 on Partial Close by acquiring new child ticket
    old_partial_code = '''                        if(OrderClose(ticket, closeLot, cPrice, SlippagePoints, clrGold))
                        {
                           GlobalVariableSet(gvKey, 1.0);
                           Print("[SWEEP FADE 2-TIER v6.3.6] Partial TP: Closed 50% (", closeLot, " Lots) at +1.5R (+", profitUSD, " USD). Moving remaining lot to Breakeven!");
                           
                           // Re-select to adjust SL to Breakeven
                           if(OrderSelect(ticket, SELECT_BY_TICKET))
                           {
                              double beSL = (oType == OP_BUY) ? 
                                 NormalizeDouble(openP + spreadOffset + 0.30, Digits) :
                                 NormalizeDouble(openP - spreadOffset - 0.30, Digits);
                              double stopDist = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
                              double freezeDist = MarketInfo(Symbol(), MODE_FREEZELEVEL) * Point;
                              double minDist = MathMax(stopDist, freezeDist);
                              bool canMod = (oType == OP_BUY) ? ((Bid - beSL) >= minDist) : ((beSL - Ask) >= minDist);
                              if(canMod)
                              {
                                 bool modRes = OrderModify(ticket, openP, beSL, curTP, 0, clrBlue);
                                 if(!modRes) Print("[SWEEP FADE 2-TIER v6.3.6] OrderModify Error: ", GetLastError());
                              }
                           }
                        }'''

    new_partial_code = '''                        if(OrderClose(ticket, closeLot, cPrice, SlippagePoints, clrGold))
                        {
                           GlobalVariableSet(gvKey, 1.0);
                           Print("[SWEEP FADE 2-TIER v6.3.6] Partial TP: Closed 50% (", closeLot, " Lots) at +1.5R (+", profitUSD, " USD). Moving remaining lot to Breakeven!");
                           
                           // Locate the remaining open child ticket generated by MT4
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
                              GlobalVariableSet(childGv, 1.0); // Mark child so it never partial-closes again
                              
                              double beSL = (oType == OP_BUY) ? 
                                 NormalizeDouble(OrderOpenPrice() + spreadOffset + 0.30, Digits) :
                                 NormalizeDouble(OrderOpenPrice() - spreadOffset - 0.30, Digits);
                              double stopDist = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
                              double freezeDist = MarketInfo(Symbol(), MODE_FREEZELEVEL) * Point;
                              double minDist = MathMax(stopDist, freezeDist);
                              bool canMod = (oType == OP_BUY) ? ((Bid - beSL) >= minDist) : ((beSL - Ask) >= minDist);
                              if(canMod)
                              {
                                 bool modRes = OrderModify(childTicket, OrderOpenPrice(), beSL, OrderTakeProfit(), 0, clrBlue);
                                 if(modRes)
                                    Print("[SWEEP FADE 2-TIER v6.3.6] Child Ticket #", childTicket, " SL moved to Risk-Free Breakeven successfully!");
                                 else
                                    Print("[SWEEP FADE 2-TIER v6.3.6] OrderModify Error on #", childTicket, ": ", GetLastError());
                              }
                           }
                        }'''

    assert old_partial_code in text, f"old_partial_code not found in {fpath}"
    text = text.replace(old_partial_code, new_partial_code)

    with open(fpath, "w", encoding="latin1") as f:
        f.write(text)
    print(f"Successfully updated {os.path.basename(fpath)}")

# Update both
update_file(bridge_path)
update_file(tester_path)

# Compile both
ok1 = compile_mq4(bridge_path)
ok2 = compile_mq4(tester_path)
print("Bridge Compile Result:", ok1)
print("Tester Compile Result:", ok2)
