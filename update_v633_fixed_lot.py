import os
from compile_mq4 import compile_mq4

files_to_update = [
    r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Bridge_v6_3_3.mq4",
    r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\GoldSniper_Tester_v6_3_3.mq4"
]

old_master = '''input ENUM_FLIP_MODE  OperatingMode           = MODE_TRI_SESSION_ULTRA; // Master Operating Architecture
input double          SniperRiskPercent       = 5.0;            // London Sniper Risk (% of Equity - 2x Lot)'''

new_master = '''input ENUM_FLIP_MODE  OperatingMode           = MODE_TRI_SESSION_ULTRA; // Master Operating Architecture
input bool            UseFixedLot             = true;           // Enforce Fixed Lot Size (0.02) for All Trades
input double          FixedLotSize            = 0.02;           // Enforced Fixed Lot Size (0.02 Lot)
input double          SniperRiskPercent       = 5.0;            // London Sniper Dynamic Risk (% if FixedLot=false)'''

old_calc = '''double CalculateLotSize(double riskPct, double slUSD)
{
   double riskUsd = AccountEquity() * (riskPct / 100.0);'''

new_calc = '''double CalculateLotSize(double riskPct, double slUSD)
{
   if(UseFixedLot)
   {
      double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
      double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
      double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
      if(lotStep <= 0) lotStep = 0.01;
      double lot = MathFloor(FixedLotSize / lotStep) * lotStep;
      if(lot < minLot) lot = minLot;
      if(lot > maxLot) lot = maxLot;
      return lot;
   }

   double riskUsd = AccountEquity() * (riskPct / 100.0);'''

for fpath in files_to_update:
    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()
    
    assert old_master in code, f"old_master not found in {fpath}"
    assert old_calc in code, f"old_calc not found in {fpath}"
    
    code = code.replace(old_master, new_master)
    code = code.replace(old_calc, new_calc)
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(code)
    
    ok = compile_mq4(fpath)
    print(f"Compiled {os.path.basename(fpath)}: OK = {ok}")
