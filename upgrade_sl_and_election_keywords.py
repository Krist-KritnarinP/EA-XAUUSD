import os
import shutil

base_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"
mt4_experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"

# 1. Upgrade ManagePOIBreakeven in both MQL4 EAs to use GetOrderInitRisk
old_poi_be = """void ManagePOIBreakeven()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicPOISniper)
         {
            double open_pr = OrderOpenPrice();
            double sl_pr   = OrderStopLoss();
            int cmd        = OrderType();
            
            double init_sl_pts = 0.0;
            if(cmd == OP_BUY)
            {
               init_sl_pts = (open_pr - sl_pr) / Point;
               if(sl_pr >= open_pr) continue;
               
               if((Bid - open_pr) >= (init_sl_pts * Point * InpNYBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr + (30.0 * Point), Digits);
                  SafeModifySL(OrderTicket(), open_pr, sl_pr, new_sl, OrderTakeProfit(), cmd, 0.10, clrBlue);
               }
            }
            else if(cmd == OP_SELL)
            {
               init_sl_pts = (sl_pr - open_pr) / Point;
               if(sl_pr <= open_pr && sl_pr > 0.0) continue;
               
               if((open_pr - Ask) >= (init_sl_pts * Point * InpNYBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr - (30.0 * Point), Digits);
                  SafeModifySL(OrderTicket(), open_pr, sl_pr, new_sl, OrderTakeProfit(), cmd, 0.10, clrRed);
               }
            }
         }
      }
   }
}"""

new_poi_be = """void ManagePOIBreakeven()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
      {
         if(OrderSymbol() == Symbol() && OrderMagicNumber() == InpMagicPOISniper)
         {
            int ticket     = OrderTicket();
            double open_pr = OrderOpenPrice();
            double sl_pr   = OrderStopLoss();
            int cmd        = OrderType();
            
            // Use cached initial risk so if user drags SL wider manually, bot still locks BE at original +1.8R!
            double init_risk_usd = GetOrderInitRisk(ticket, open_pr, sl_pr, InpNYMinSLPoints * Point);
            if(cmd == OP_BUY)
            {
               if(sl_pr >= open_pr) continue;
               
               if((Bid - open_pr) >= (init_risk_usd * InpNYBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr + (30.0 * Point), Digits);
                  SafeModifySL(ticket, open_pr, sl_pr, new_sl, OrderTakeProfit(), cmd, 0.10, clrBlue);
               }
            }
            else if(cmd == OP_SELL)
            {
               if(sl_pr <= open_pr && sl_pr > 0.0) continue;
               
               if((open_pr - Ask) >= (init_risk_usd * InpNYBreakevenRR))
               {
                  double new_sl = NormalizeDouble(open_pr - (30.0 * Point), Digits);
                  SafeModifySL(ticket, open_pr, sl_pr, new_sl, OrderTakeProfit(), cmd, 0.10, clrRed);
               }
            }
         }
      }
   }
}"""

for fname in ["Gold_POI_Sniper_Master_v3_5.mq4", "Gold_POI_Sniper_Tester_v3_5.mq4"]:
    fpath = os.path.join(base_dir, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        code = f.read()

    code = code.replace(old_poi_be.replace("\n", "\r\n"), new_poi_be.replace("\n", "\r\n"))
    code = code.replace(old_poi_be, new_poi_be)

    # Also pass ExportMarketState(true) on order open/close/modify so state flushes immediately
    code = code.replace("               ExportMarketState();", "               ExportMarketState(true);")

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(code)
    shutil.copy2(fpath, os.path.join(mt4_experts_dir, fname))
    print(f"[OK] Upgraded ManagePOIBreakeven in {fname}")

# 2. Upgrade BREAKING_GOLD_MACRO_KEYWORDS in gold_ai_agent.py to include Election / Congress / Trump / Senate / Poll keywords
agent_base_path = os.path.join(base_dir, "gold_ai_agent.py")
with open(agent_base_path, "r", encoding="utf-8") as f:
    py_base = f.read()

old_kw = """BREAKING_GOLD_MACRO_KEYWORDS = (
    "gold", "xau", "bullion", "fed", "federal reserve", "powell", "fomc",
    "rate cut", "rate hike", "inflation", "cpi", "ppi", "nonfarm", "payroll",
    "tariff", "trump", "missile", "iran", "israel", "war", "strike", "attack",
    "pentagon", "sanction", "treasury", "yield", "dollar", "central bank",
    "emergency", "geopolit", "ceasefire", "nuclear", "opec", "crude"
)"""

new_kw = """BREAKING_GOLD_MACRO_KEYWORDS = (
    "gold", "xau", "bullion", "fed", "federal reserve", "powell", "fomc",
    "rate cut", "rate hike", "inflation", "cpi", "ppi", "nonfarm", "payroll",
    "tariff", "trump", "election", "midterm", "congress", "senate", "house",
    "white house", "vote", "ballot", "poll", "republican", "democrat",
    "missile", "iran", "israel", "war", "strike", "attack",
    "pentagon", "sanction", "treasury", "yield", "dollar", "central bank",
    "emergency", "geopolit", "ceasefire", "nuclear", "opec", "crude"
)"""

py_base = py_base.replace(old_kw.replace("\n", "\r\n"), new_kw.replace("\n", "\r\n"))
py_base = py_base.replace(old_kw, new_kw)

with open(agent_base_path, "w", encoding="utf-8") as f:
    f.write(py_base)
print("[OK] Upgraded BREAKING_GOLD_MACRO_KEYWORDS in gold_ai_agent.py")
