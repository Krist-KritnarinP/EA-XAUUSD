import os

def update_anti_ban(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        c = f.read()

    # 1. Update SafeModifySL with 10-second Cooldown & Cooldown Tracking
    old_safe_mod = """bool SafeModifySL(int ticket, double openP, double curSL, double targetSL, double curTP, int oType, double minStepUSD, color modColor)
{
   if(!IsTesting() && (!IsTradeAllowed() || IsTradeContextBusy())) return false;
   targetSL = NormalizeDouble(targetSL, Digits);
   curSL    = NormalizeDouble(curSL, Digits);
   if(MathAbs(targetSL - curSL) < minStepUSD) return false;
   
   double stopLevel = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
   if(stopLevel <= 0.0) stopLevel = 30.0 * Point;
   
   if(oType == OP_BUY)
   {
      if(Bid - targetSL < stopLevel) return false;
      if(curSL > 0.0 && targetSL <= curSL) return false;
   }
   else if(oType == OP_SELL)
   {
      if(targetSL - Ask < stopLevel) return false;
      if(curSL > 0.0 && targetSL >= curSL) return false;
   }
   
   bool res = OrderModify(ticket, openP, targetSL, curTP, 0, modColor);
   if(res && !IsTesting()) ExportMarketState();
   return res;
}"""

    new_safe_mod = """#define MAX_MOD_COOLDOWN_TICKETS 300
static int      s_lastModTicket[MAX_MOD_COOLDOWN_TICKETS];
static datetime s_lastModTime[MAX_MOD_COOLDOWN_TICKETS];
static int      s_lastModCount = 0;

//+------------------------------------------------------------------+
//| Anti-Broker Ban Safe SL Modification (10s Cooldown + Anti-Spam)   |
//+------------------------------------------------------------------+
bool SafeModifySL(int ticket, double openP, double curSL, double targetSL, double curTP, int oType, double minStepUSD, color modColor)
{
   if(!IsTesting() && (!IsTradeAllowed() || IsTradeContextBusy())) return false;
   
   // Anti-Broker Ban Time-Cooldown: Min 10s between modifications on the same ticket!
   if(!IsTesting())
   {
      datetime nowT = TimeCurrent();
      for(int k = 0; k < s_lastModCount; k++)
      {
         if(s_lastModTicket[k] == ticket)
         {
            if((nowT - s_lastModTime[k]) < 10) return false; // Throttled! Zero broker server flood
            break;
         }
      }
   }
   
   targetSL = NormalizeDouble(targetSL, Digits);
   curSL    = NormalizeDouble(curSL, Digits);
   if(MathAbs(targetSL - curSL) < minStepUSD) return false;
   
   double stopLevel = MarketInfo(Symbol(), MODE_STOPLEVEL) * Point;
   if(stopLevel <= 0.0) stopLevel = 30.0 * Point;
   
   if(oType == OP_BUY)
   {
      if(Bid - targetSL < stopLevel) return false;
      if(curSL > 0.0 && targetSL <= curSL) return false;
   }
   else if(oType == OP_SELL)
   {
      if(targetSL - Ask < stopLevel) return false;
      if(curSL > 0.0 && targetSL >= curSL) return false;
   }
   
   bool res = OrderModify(ticket, openP, targetSL, curTP, 0, modColor);
   if(res && !IsTesting())
   {
      datetime nowT = TimeCurrent();
      bool found = false;
      for(int k = 0; k < s_lastModCount; k++)
      {
         if(s_lastModTicket[k] == ticket)
         {
            s_lastModTime[k] = nowT;
            found = true;
            break;
         }
      }
      if(!found && s_lastModCount < MAX_MOD_COOLDOWN_TICKETS)
      {
         s_lastModTicket[s_lastModCount] = ticket;
         s_lastModTime[s_lastModCount]   = nowT;
         s_lastModCount++;
      }
      ExportMarketState();
   }
   return res;
}"""

    # 2. Update ManageLondonRatchet to completely remove spreadOffset and enforce 1-time discrete step
    old_london_ratchet = """            // A. DYNAMIC RATCHET TRAILING
            if(InpEnableLondonRatchet)
            {
               // Stage 2: Profit >= 2.50R -> Lock in +1.25R Guaranteed Profit
               if(profitUSD >= (riskUSD * 2.50))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + (riskUSD * 1.25), Digits);
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrLime);
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - (riskUSD * 1.25), Digits);
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrLime);
                  }
               }
               // Stage 1: Profit >= 1.75R -> Move SL to Risk-Free (spread + 0.50 cover)
               else if(profitUSD >= (riskUSD * 1.75))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + spreadOffset + 0.50, Digits);
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrBlue);
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - spreadOffset - 0.50, Digits);
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrBlue);
                  }
               }
            }"""

    new_london_ratchet = """            // A. DYNAMIC RATCHET TRAILING (DISCRETE 2-STAGE - ZERO SPREAD JITTER)
            if(InpEnableLondonRatchet)
            {
               // Stage 2: Profit >= 2.50R -> Lock in +1.25R Guaranteed Profit (Fires EXACTLY ONCE)
               if(profitUSD >= (riskUSD * 2.50))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + (riskUSD * 1.25), Digits);
                     if(curSL < targetSL - 0.10)
                        SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - (riskUSD * 1.25), Digits);
                     if(curSL > targetSL + 0.10 || curSL == 0.0)
                        SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
                  }
               }
               // Stage 1: Profit >= 1.75R -> Move SL to Risk-Free Breakeven (Fixed +$0.50 USD Cover - Fires EXACTLY ONCE)
               else if(profitUSD >= (riskUSD * 1.75))
               {
                  if(oType == OP_BUY)
                  {
                     double targetSL = NormalizeDouble(openP + 0.50, Digits);
                     if(curSL < openP + 0.30) // Only fire ONCE when SL is still below breakeven!
                        SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrBlue);
                  }
                  else if(oType == OP_SELL)
                  {
                     double targetSL = NormalizeDouble(openP - 0.50, Digits);
                     if(curSL > openP - 0.30 || curSL == 0.0) // Only fire ONCE when SL is still above breakeven!
                        SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrBlue);
                  }
               }
            }"""

    # 3. Update Judas Sweep beSL (clean fixed +0.50 without spreadOffset)
    old_sweep_be = """                            double beSL = (oType == OP_BUY) ? 
                               NormalizeDouble(OrderOpenPrice() + spreadOffset + 0.30, Digits) :
                               NormalizeDouble(OrderOpenPrice() - spreadOffset - 0.30, Digits);"""

    new_sweep_be = """                            double beSL = (oType == OP_BUY) ? 
                               NormalizeDouble(OrderOpenPrice() + 0.50, Digits) :
                               NormalizeDouble(OrderOpenPrice() - 0.50, Digits);"""

    # 4. Update Judas Sweep Trailing (Stage 2 and 3 discrete 1-time checks)
    old_sweep_stages = """            // Progressive Trailing: Stage 3 (Profit >= 3.50R)
            if(InpEnableSweepDynamicTr && profitUSD >= (sweepRiskUSD * 3.50))
            {
               if(oType == OP_BUY)
               {
                  double trailSL  = NormalizeDouble(Bid - (sweepRiskUSD * InpSweepTrailDistance_R), Digits);
                  double lockSL   = NormalizeDouble(openP + (sweepRiskUSD * 2.50), Digits);
                  double targetSL = MathMax(lockSL, trailSL);
                  SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrLime);
               }
               else if(oType == OP_SELL)
               {
                  double trailSL  = NormalizeDouble(Ask + (sweepRiskUSD * InpSweepTrailDistance_R), Digits);
                  double lockSL   = NormalizeDouble(openP - (sweepRiskUSD * 2.50), Digits);
                  double targetSL = MathMin(lockSL, trailSL);
                  SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrLime);
               }
            }
            // Stage 2: Profit >= 2.50R -> Lock in +1.25R Guaranteed Profit
            else if(InpEnableSweepDynamicTr && profitUSD >= (sweepRiskUSD * 2.50))
            {
               if(oType == OP_BUY)
               {
                  double targetSL = NormalizeDouble(openP + (sweepRiskUSD * 1.25), Digits);
                  SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrLime);
               }
               else if(oType == OP_SELL)
               {
                  double targetSL = NormalizeDouble(openP - (sweepRiskUSD * 1.25), Digits);
                  SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.20, clrLime);
               }
            }"""

    new_sweep_stages = """            // Progressive Ratchet: Stage 3 (Profit >= 3.50R -> Lock +2.50R) (Fires EXACTLY ONCE)
            if(InpEnableSweepDynamicTr && profitUSD >= (sweepRiskUSD * 3.50))
            {
               if(oType == OP_BUY)
               {
                  double targetSL = NormalizeDouble(openP + (sweepRiskUSD * 2.50), Digits);
                  if(curSL < targetSL - 0.10)
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
               }
               else if(oType == OP_SELL)
               {
                  double targetSL = NormalizeDouble(openP - (sweepRiskUSD * 2.50), Digits);
                  if(curSL > targetSL + 0.10 || curSL == 0.0)
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
               }
            }
            // Stage 2: Profit >= 2.50R -> Lock in +1.25R Guaranteed Profit (Fires EXACTLY ONCE)
            else if(InpEnableSweepDynamicTr && profitUSD >= (sweepRiskUSD * 2.50))
            {
               if(oType == OP_BUY)
               {
                  double targetSL = NormalizeDouble(openP + (sweepRiskUSD * 1.25), Digits);
                  if(curSL < targetSL - 0.10)
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
               }
               else if(oType == OP_SELL)
               {
                  double targetSL = NormalizeDouble(openP - (sweepRiskUSD * 1.25), Digits);
                  if(curSL > targetSL + 0.10 || curSL == 0.0)
                     SafeModifySL(ticket, openP, curSL, targetSL, curTP, oType, 0.50, clrLime);
               }
            }"""

    updated = False
    if old_safe_mod in c:
        c = c.replace(old_safe_mod, new_safe_mod)
        print(f"[{os.path.basename(filepath)}] Applied Anti-Spam Cooldown to SafeModifySL")
        updated = True
    else:
        print(f"[{os.path.basename(filepath)}] Mismatch in SafeModifySL")

    if old_london_ratchet in c:
        c = c.replace(old_london_ratchet, new_london_ratchet)
        print(f"[{os.path.basename(filepath)}] Removed spreadOffset & applied 1-time discrete guard to London Ratchet")
        updated = True
    else:
        print(f"[{os.path.basename(filepath)}] Mismatch in London Ratchet")

    if old_sweep_be in c:
        c = c.replace(old_sweep_be, new_sweep_be)
        print(f"[{os.path.basename(filepath)}] Removed spreadOffset from Sweep BE")
        updated = True
    else:
        print(f"[{os.path.basename(filepath)}] Mismatch in Sweep BE")

    if old_sweep_stages in c:
        c = c.replace(old_sweep_stages, new_sweep_stages)
        print(f"[{os.path.basename(filepath)}] Applied 1-time discrete guard to Sweep Stages 2 & 3")
        updated = True
    else:
        print(f"[{os.path.basename(filepath)}] Mismatch in Sweep Stages")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(c)
    print(f"[{os.path.basename(filepath)}] Saved successfully!")

files = [
    r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v3_5.mq4",
    r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Tester_v3_5.mq4",
    r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Master_v3_5.mq4",
    r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts\Gold_POI_Sniper_Tester_v3_5.mq4"
]

for f in files:
    update_anti_ban(f)
