import os

def add_htf_shield(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Inputs
    target_inp = 'extern double   InpLondonMinPenetration = 2.00;   // Min Penetration beyond Asian Box ($2.00 Judas Shield)'
    htf_inputs = ('extern bool     InpEnableHTFShield      = true;   // Enable H1/H4/D1 Support/Resistance Collision Shield\n'
                  'extern double   InpHTFBufferUSD         = 6.00;   // Min Distance from H1/H4/D1 Support/Resistance ($6.00)\n'
                  'extern double   InpLondonMinPenetration = 2.00;   // Min Penetration beyond Asian Box ($2.00 Judas Shield)')
    if target_inp in text and 'InpEnableHTFShield' not in text:
        text = text.replace(target_inp, htf_inputs)

    # 2. Add Function definition before OnInit
    fn_code = '''//+------------------------------------------------------------------+
//| Multi-Timeframe (H1, H4, D1) Support & Resistance Shield        |
//+------------------------------------------------------------------+
bool IsNearHTFSupportOrResistance(int orderType, double price, double bufferUSD)
{
   if(!InpEnableHTFShield) return false;
   
   // 1. D1 Key Levels (PDL & PDH)
   double d1_pdl = iLow(Symbol(), PERIOD_D1, 1);
   double d1_pdh = iHigh(Symbol(), PERIOD_D1, 1);
   
   // 2. H4 Key Swings (Last 6 H4 bars = 24 hours)
   int lowestH4Idx  = iLowest(Symbol(), PERIOD_H4, MODE_LOW, 6, 1);
   int highestH4Idx = iHighest(Symbol(), PERIOD_H4, MODE_HIGH, 6, 1);
   double h4_support    = iLow(Symbol(), PERIOD_H4, lowestH4Idx);
   double h4_resistance = iHigh(Symbol(), PERIOD_H4, highestH4Idx);
   
   // 3. Major Psychological Round Numbers ($50 intervals: 3900, 3950, 4000)
   double roundFloor = MathFloor(price / 50.0) * 50.0;
   double roundCeil  = MathCeil(price / 50.0) * 50.0;
   
   if(orderType == OP_SELL)
   {
      // A. Too close to D1 PDL from above
      if(price >= d1_pdl && (price - d1_pdl) < bufferUSD)
      {
         PrintFormat("[HTF SHIELD BLOCKED SELL] Price %.2f is too close to D1 PDL %.2f", price, d1_pdl);
         return true;
      }
      // B. Too close to H4 Support from above
      if(price >= h4_support && (price - h4_support) < bufferUSD)
      {
         PrintFormat("[HTF SHIELD BLOCKED SELL] Price %.2f is too close to H4 Support %.2f", price, h4_support);
         return true;
      }
      // C. Too close to Major Psychological Round Floor ($3,900, etc.)
      if((price - roundFloor) < (bufferUSD * 0.8))
      {
         PrintFormat("[HTF SHIELD BLOCKED SELL] Price %.2f is too close to Round Floor %.2f", price, roundFloor);
         return true;
      }
   }
   else if(orderType == OP_BUY)
   {
      // A. Too close to D1 PDH from below
      if(price <= d1_pdh && (d1_pdh - price) < bufferUSD)
      {
         PrintFormat("[HTF SHIELD BLOCKED BUY] Price %.2f is too close to D1 PDH %.2f", price, d1_pdh);
         return true;
      }
      // B. Too close to H4 Resistance from below
      if(price <= h4_resistance && (h4_resistance - price) < bufferUSD)
      {
         PrintFormat("[HTF SHIELD BLOCKED BUY] Price %.2f is too close to H4 Resistance %.2f", price, h4_resistance);
         return true;
      }
      // C. Too close to Major Psychological Round Ceiling ($3,950, etc.)
      if((roundCeil - price) < (bufferUSD * 0.8))
      {
         PrintFormat("[HTF SHIELD BLOCKED BUY] Price %.2f is too close to Round Ceiling %.2f", price, roundCeil);
         return true;
      }
   }
   return false;
}
'''

    if 'bool IsNearHTFSupportOrResistance' not in text:
        idx = text.find('int OnInit()')
        if idx != -1:
            text = text[:idx] + fn_code + '\n' + text[idx:]

    # 3. Apply to buy/sell execution
    target_buy = 'if(isBuySignal)'
    target_sell = 'else if(isSellSignal)'
    new_buy = 'if(isBuySignal && !IsNearHTFSupportOrResistance(OP_BUY, Ask, InpHTFBufferUSD))'
    new_sell = 'else if(isSellSignal && !IsNearHTFSupportOrResistance(OP_SELL, Bid, InpHTFBufferUSD))'

    if target_buy in text and new_buy not in text:
        text = text.replace(target_buy, new_buy)
    if target_sell in text and new_sell not in text:
        text = text.replace(target_sell, new_sell)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('HTF Shield added to:', path)

add_htf_shield(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Master_v3_5.mq4')
add_htf_shield(r'C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4\Gold_POI_Sniper_Tester_v3_5.mq4')
