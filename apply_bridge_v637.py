import os

bridge_path = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\GoldSniper_Bridge_v6_3_7_beta.mq4"

with open(bridge_path, "r", encoding="latin1") as f:
    code = f.read()

# Replace NY Buy block
old_buy = """               if(validBuyTrigger)
               {
                  double lot = CalculateLotSize(NYRiskPercent, dynamicSL);
                  double sl  = NormalizeDouble(Ask - dynamicSL, Digits);
                  double tp  = NormalizeDouble(Ask + dynamicTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.6b NY Buy", MagicNY, 0, clrBlue);
                  if(ticket > 0)
                  {
                     SetOrderInitRisk637B(ticket, dynamicSL);
                     DailyTotalTrades++;
                     primaryOrderOpenedThisBar = true;
                     BroadcastSignal("A+", "BUY", Ask, sl, tp, "New York Institutional Engine", setupSubDesc + " with Macro Bull Consensus");
                     Print("[NEW YORK INSTITUTIONAL BUY v6.3.6a] Ticket: #", ticket, " Setup: ", setupSubDesc, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " TP: ", tp);
                  }
               }"""

new_buy = """               if(validBuyTrigger)
               {
                  double lowest3 = MathMin(l1, MathMin(l2, iLow(Symbol(), PERIOD_M15, 3)));
                  double swingDistBuy = NormalizeDouble(Ask - (lowest3 - (0.50 * Point * 10)), 2);
                  double atrDistBuy   = NormalizeDouble(atr15 * NY_ATR_Multiplier, 2);
                  dynamicSL = MathMax(NY_Min_SL_USD, MathMax(swingDistBuy, atrDistBuy));
                  if(dynamicSL > 13.50) dynamicSL = 13.50;

                  double lot = CalculateLotSize(NYRiskPercent, dynamicSL);
                  double sl  = NormalizeDouble(Ask - dynamicSL, Digits);
                  double tp  = NormalizeDouble(Ask + dynamicTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_BUY, lot, Ask, SlippagePoints, sl, tp, "v6.3.7b NY Buy", MagicNY, 0, clrBlue);
                  if(ticket > 0)
                  {
                     SetOrderInitRisk637B(ticket, dynamicSL);
                     DailyTotalTrades++;
                     primaryOrderOpenedThisBar = true;
                     BroadcastSignal("A+", "BUY", Ask, sl, tp, "New York Institutional Engine", setupSubDesc + " with Macro Bull Consensus");
                     Print("[NEW YORK INSTITUTIONAL BUY v6.3.7-Beta] Ticket: #", ticket, " Setup: ", setupSubDesc, " Lots: ", lot, " Price: ", Ask, " SL: ", sl, " TP: ", tp);
                  }
               }"""

# Replace NY Sell block
old_sell = """               if(validSellTrigger)
               {
                  double lot = CalculateLotSize(NYRiskPercent, dynamicSL);
                  double sl  = NormalizeDouble(Bid + dynamicSL, Digits);
                  double tp  = NormalizeDouble(Bid - dynamicTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, SlippagePoints, sl, tp, "v6.3.6b NY Sell", MagicNY, 0, clrMagenta);
                  if(ticket > 0)
                  {
                     SetOrderInitRisk637B(ticket, dynamicSL);
                     DailyTotalTrades++;
                     primaryOrderOpenedThisBar = true;
                     BroadcastSignal("A+", "SELL", Bid, sl, tp, "New York Institutional Engine", setupSubDesc + " with Macro Bear Consensus");
                     Print("[NEW YORK INSTITUTIONAL SELL v6.3.6a] Ticket: #", ticket, " Setup: ", setupSubDesc, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " TP: ", tp);
                  }
               }"""

new_sell = """               if(validSellTrigger)
               {
                  double highest3 = MathMax(h1, MathMax(h2, iHigh(Symbol(), PERIOD_M15, 3)));
                  double swingDistSell = NormalizeDouble((highest3 + (0.50 * Point * 10)) - Bid, 2);
                  double atrDistSell   = NormalizeDouble(atr15 * NY_ATR_Multiplier, 2);
                  dynamicSL = MathMax(NY_Min_SL_USD, MathMax(swingDistSell, atrDistSell));
                  if(dynamicSL > 13.50) dynamicSL = 13.50;

                  double lot = CalculateLotSize(NYRiskPercent, dynamicSL);
                  double sl  = NormalizeDouble(Bid + dynamicSL, Digits);
                  double tp  = NormalizeDouble(Bid - dynamicTP, Digits);
                  int ticket = OrderSend(Symbol(), OP_SELL, lot, Bid, SlippagePoints, sl, tp, "v6.3.7b NY Sell", MagicNY, 0, clrMagenta);
                  if(ticket > 0)
                  {
                     SetOrderInitRisk637B(ticket, dynamicSL);
                     DailyTotalTrades++;
                     primaryOrderOpenedThisBar = true;
                     BroadcastSignal("A+", "SELL", Bid, sl, tp, "New York Institutional Engine", setupSubDesc + " with Macro Bear Consensus");
                     Print("[NEW YORK INSTITUTIONAL SELL v6.3.7-Beta] Ticket: #", ticket, " Setup: ", setupSubDesc, " Lots: ", lot, " Price: ", Bid, " SL: ", sl, " TP: ", tp);
                  }
               }"""

assert old_buy in code, "old_buy not found!"
code = code.replace(old_buy, new_buy, 1)

assert old_sell in code, "old_sell not found!"
code = code.replace(old_sell, new_sell, 1)

with open(bridge_path, "w", encoding="latin1") as f:
    f.write(code)

print("GoldSniper_Bridge_v6_3_7_beta.mq4 updated successfully!")
