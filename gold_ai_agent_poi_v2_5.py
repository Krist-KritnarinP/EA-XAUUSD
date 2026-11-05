# ==============================================================================
# Gold POI Sniper v3.5 - AI Sentinel Agent Engine (Full Institutional Suite)
# Integrated for:
#   1. London Dual-Engine (London Sniper Trend Breakout + Judas Sweep Fade)
#   2. New York Institutional POI Prime (SMC Liquidity Sweeps)
#   3. 3-Color Macro News Sentinel (ForexFactory / Investing)
#   4. Real-Time Breaking Geopolitical News Sentinel (Zero Duplicate, News Guard Only)
#   5. 5-Sciences Institutional Quant Briefing every 3 Hours (02, 05, 08, 11, 14, 17, 20, 23)
#   6. Periodic System Heartbeat Report every 30 Minutes with Multi-Engine Orders Transparency
#   7. AI Streak Breaker (Consecutive Loss Auto-Protective Risk Scaler)
#   8. Full Multi-Room Discord Webhook Dispatcher
# ==============================================================================

import os
import sys
import time
import json
import urllib.request
import xml.etree.ElementTree as ET
import hashlib
from datetime import datetime as dt, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import gold_ai_agent as base_agent

VERSION = "Gold POI Sniper v3.5 (London Dual-Engine + New York POI Prime)"
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

# Magic numbers of the 3 engines
MAGIC_POI = 778899           # NY POI Sniper
MAGIC_LONDON_SNIPER = 778832 # London Trend Breakout Runner
MAGIC_JUDAS_SWEEP = 778834   # Judas Sweep Contrarian Fade

BOT_MAGICS = {
    MAGIC_POI: "POI NY Sniper",
    MAGIC_LONDON_SNIPER: "London Sniper",
    MAGIC_JUDAS_SWEEP: "Judas Sweep Fade"
}

# 3-Hour Institutional Quant Slots (Thai Time GMT+7)
QUANT_3H_SLOTS = ["02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00"]

def load_poi_config():
    return base_agent.load_config()

def is_bot_order(o):
    """Identifies whether an order belongs to one of the 3 Gold POI Sniper v3.5 engines"""
    m = int(o.get("magic", 0))
    eng = str(o.get("engine", ""))
    if m in BOT_MAGICS:
        return True
    if any(k in eng for k in ["POI", "London", "Judas", "Sweep", "Sniper"]):
        return True
    return False

def get_engine_name(o):
    """Returns official engine name for an order"""
    m = int(o.get("magic", 0))
    if m in BOT_MAGICS:
        return BOT_MAGICS[m]
    eng = str(o.get("engine", ""))
    if "London" in eng: return "London Sniper"
    if "Sweep" in eng or "Judas" in eng: return "Judas Sweep Fade"
    if "POI" in eng: return "POI NY Sniper"
    return "User Manual"

def get_poi_session_info(server_time):
    """
    Returns precise POI v3.5 institutional session name, hours, and status.
    Combines London Dual-Engine (08:00-11:30) and New York POI Prime (15:00-20:30).
    """
    try:
        h = int(server_time.split(" ")[1].split(":")[0])
        m = int(server_time.split(" ")[1].split(":")[1])
    except Exception:
        h, m = 0, 0

    if 0 <= h < 4:
        session_name = "🌏 Asian Range Discovery & Liquidity Mapping"
        session_hours = "00:00 - 04:00 (MT4) | 05:00 - 09:00 น. (ไทย)"
        action_note = "สำรวจและบันทึกราคาสะสมกรอบแรกช่วงเปิดตลาดเอเชีย"
    elif 4 <= h < 8:
        session_name = "📐 London Asian Range Box Fixation (04:00 - 08:00)"
        session_hours = "04:00 - 08:00 (MT4) | 09:00 - 13:00 น. (ไทย)"
        action_note = "คำนวณและล็อคกรอบ High/Low สำหรับเป็นฐานรองรับ London Dual-Engine"
    elif 8 <= h < 11 or (h == 11 and m <= 30):
        session_name = "🇬🇧 London Dual-Engine Active (London Sniper + Judas Sweep Fade)"
        session_hours = "08:00 - 11:30 (MT4) | 13:00 - 16:30 น. (ไทย)"
        action_note = "ดักเทรนด์เบรคเอาท์ (London Sniper 1:3.5R) หรือดักตบกับดักสภาพคล่อง (Judas Sweep Fade 1:5.0R)"
    elif 11 <= h < 15:
        session_name = "⏸️ European Standby & Pre-NY Preparation"
        session_hours = "11:30 - 15:00 (MT4) | 16:30 - 20:00 น. (ไทย)"
        action_note = "พักระบบ ไม่รับคำสั่งใหม่ ป้องกันความผันผวนหลอกช่วงกลางวันยุโรป"
    elif 15 <= h < 18:
        session_name = "🎯 New York Institutional Open (POI Prime Sweep)"
        session_hours = "15:00 - 18:00 (MT4) | 20:00 - 23:00 น. (ไทย)"
        action_note = "ช่วงกวาดสภาพคล่อง POI สูงสุด (New York Open | Win Rate 65.2% | SMC Level Sweeps)"
    elif 18 <= h < 20 or (h == 20 and m <= 30):
        session_name = "🚀 New York Late Trend & TP Target Extension"
        session_hours = "18:00 - 20:30 (MT4) | 23:00 - 01:30 น. (ไทย)"
        action_note = "รันเทรนด์ตามโครงสร้างสถาบัน มุ่งสู่เป้าหมาย TP 1:3.50 RR พร้อม Structural Bailout Guard"
    else:
        session_name = "🛡️ Daily Session Closed & Rollover Protection"
        session_hours = "20:30 - 23:59 (MT4) | 01:30 - 05:00 น. (ไทย)"
        action_note = "ปิดรับคำสั่งใหม่ ป้องกันช่วงเปลี่ยนวันและสเปรดถ่าง (Rollover Window)"
    return session_name, session_hours, action_note

def get_upcoming_major_red_events_summary(now_thai):
    """Returns formatted summary of upcoming High-Impact RED USD events across the week (including US Congressional Elections / Trump & NFP)"""
    week_events = base_agent.fetch_economic_calendar()
    red_upcoming = []
    next_any = None
    for ev in week_events:
        ev_dt = base_agent.parse_event_time_thai(ev.get("date", ""))
        if ev_dt and ev_dt >= (now_thai - timedelta(minutes=30)):
            if next_any is None:
                next_any = (ev, ev_dt)
            if ev.get("impact") == "High":
                red_upcoming.append((ev, ev_dt))

    lines = []
    if next_any:
        ev, ev_dt = next_any
        imp = ev.get("impact", "Low")
        badge = "🔴" if imp == "High" else ("🟠" if imp == "Medium" else "🟡")
        dt_str = ev_dt.strftime("%a %d/%m %H:%M") + " น."
        lines.append(f"• **ข่าวระยะใกล้ถัดไป:** {badge} **{ev.get('title')}** ({dt_str}) | คาดการณ์: `{ev.get('forecast') or 'N/A'}` | ก่อนหน้า: `{ev.get('previous') or 'N/A'}`")

    if red_upcoming:
        lines.append("🚨 **ไฮไลท์ข่าวกล่องแดงใหญ่ประจำสัปดาห์ (High-Impact Macro & US Election Radar):**")
        for ev, ev_dt in red_upcoming[:4]:
            dt_str = ev_dt.strftime("%a %d/%m %H:%M") + " น."
            title_raw = ev.get("title", "")
            extra_tag = " 🗳️ **[จับตาเลือกตั้งสภาคองเกรสสหรัฐฯ / นโยบาย Trump กระทบดอลลาร์-ทองคำรุนแรง!]**" if "Election" in title_raw else ""
            fc_str = f" (คาดการณ์: `{ev.get('forecast')}` | ก่อนหน้า: `{ev.get('previous')}`)" if (ev.get("forecast") or ev.get("previous")) else ""
            lines.append(f"  🔴 **{title_raw}** — `{dt_str}`{fc_str}{extra_tag}")
    else:
        lines.append("🟢 **ไม่มีข่าวกล่องแดง USD เพิ่มเติมในสัปดาห์นี้**")

    return "\n".join(lines)

def send_poi_heartbeat_report(webhook_url, state, api_key=None):
    """Dispatches 30-min heartbeat report customized for Gold POI Sniper v3.5 with 3-engine orders transparency"""
    if not webhook_url:
        return

    now_thai = dt.now(timezone(timedelta(hours=7)))
    time_thai_str = now_thai.strftime("%d/%m/%Y %H:%M:%S") + " น."

    cur_hour = now_thai.hour
    cur_min = now_thai.minute
    cycle_index = (cur_hour * 2) + (1 if cur_min < 30 else 2)
    cycle_str = f"{cycle_index}/48"

    equity = float(state.get("equity", 0.0))
    balance = float(state.get("balance", 0.0))
    bid = float(state.get("bid", 0.0))
    ask = float(state.get("ask", 0.0))
    spread = int(state.get("spread", 0))
    gold_price = bid if bid > 0 else float(state.get("close", 3875.61))
    server_time = state.get("server_time", "")

    session_name, session_hours, action_note = get_poi_session_info(server_time)

    today_events = base_agent.get_today_high_impact_events()
    upcoming_today = [ev for ev in today_events if ev.get("dt_obj") and ev["dt_obj"] >= (now_thai - timedelta(minutes=30))]
    today_lines = []
    for ev in upcoming_today[:3]:
        today_lines.append(f"• **ข่าวคืนนี้:** {ev['title']} เวลา `{ev['time_th']}` (คาดการณ์: `{ev['forecast']}` | ก่อนหน้า: `{ev['previous']}`)")
    major_week_summary = get_upcoming_major_red_events_summary(now_thai)
    if today_lines:
        news_summary_text = "\n".join(today_lines) + "\n\n" + major_week_summary
    else:
        news_summary_text = major_week_summary
    news_reference_text = news_summary_text + "\n📌 *Reference: ForexFactory Official Calendar + Live Geopolitical Election Radar*"

    ai_bias = "SIDEWAY ⚪"
    ai_forecast = "ราคาทองคำเคลื่อนไหวในกรอบสะสมกำลัง เฝ้าระวังการกวาดสภาพคล่อง Asian Range / PDH / PDL"
    ai_levels = f"แนวรับ POI ${gold_price - 12:.2f} | แนวต้าน POI ${gold_price + 12:.2f}"

    if api_key:
        prompt = f"""คุณคือ AI Analyst ประจำระบบ Gold POI Sniper v3.5 (Institutional Multi-Engine)
กรุณาวิเคราะห์แนวโน้มทองคำสั้นกระชับ (2 บรรทัด) สำหรับรอบ 30 นาที:
- ราคาทองปัจจุบัน: ${gold_price:,.2f}
- เซสชันตลาด: {session_name} ({session_hours})
- สภาวะระบบ: {action_note}
- ข่าวเศรษฐกิจ: {news_summary_text}

ตอบเป็น JSON strictly โครงสร้าง:
{{
  "bias": "BULLISH 🟢 หรือ BEARISH 🔴 หรือ SIDEWAY ⚪",
  "forecast": "คำอธิบายคาดการณ์แนวโน้มสั้นๆ 1-2 บรรทัด สไตล์สถาบัน",
  "levels": "แนวรับสำคัญ $xxxx | แนวต้านสำคัญ $xxxx"
}}"""
        res_json = base_agent.call_gemini_json_safe(prompt, api_key, temperature=0.2, timeout=8)
        if res_json:
            ai_bias = res_json.get("bias", ai_bias)
            ai_forecast = res_json.get("forecast", ai_forecast)
            ai_levels = res_json.get("levels", ai_levels)

    # Parse open orders with strict 3-engine classification
    open_orders = state.get("open_orders", [])
    poi_market_orders = []
    london_market_orders = []
    sweep_market_orders = []
    user_market_orders = []
    pending_orders = []

    for o in open_orders:
        t_type = int(o.get("type", 0))
        magic = int(o.get("magic", 0))
        eng = str(o.get("engine", ""))

        if t_type in (0, 1):
            if magic == MAGIC_LONDON_SNIPER or "London" in eng:
                london_market_orders.append(o)
            elif magic == MAGIC_JUDAS_SWEEP or "Sweep" in eng or "Judas" in eng:
                sweep_market_orders.append(o)
            elif magic == MAGIC_POI or "POI" in eng:
                poi_market_orders.append(o)
            else:
                user_market_orders.append(o)
        else:
            pending_orders.append(o)

    bot_orders = poi_market_orders + london_market_orders + sweep_market_orders
    total_market_count = len(bot_orders) + len(user_market_orders)
    bot_float = sum(float(o.get("profit", 0.0)) for o in bot_orders)
    user_float = sum(float(o.get("profit", 0.0)) for o in user_market_orders)
    total_float = bot_float + user_float

    float_str = f"+${total_float:.2f}" if total_float >= 0 else f"-${abs(total_float):.2f}"
    bot_float_str = f"+${bot_float:.2f}" if bot_float >= 0 else f"-${abs(bot_float):.2f}"
    user_float_str = f"+${user_float:.2f}" if user_float >= 0 else f"-${abs(user_float):.2f}"

    if total_market_count == 0 and len(pending_orders) == 0:
        desc = (f"🟢 **ระบบ Gold POI Sniper v3.5 เชื่อมต่อตลาด 100%** (รอบที่ `{cycle_str}` ของวัน)\n"
                f"ขณะนี้ **ไม่มีออเดอร์ค้างในพอร์ต (0 ไม้)** ทั้งไม้บอทและไม้มือ ดักซุ่มยิง ณ จุดเกิดเหตุ POI และ London Dual-Engine")
        embed_color = 0x3498db
    else:
        bot_breakdown = []
        if london_market_orders: bot_breakdown.append(f"London Sniper `{len(london_market_orders)} ไม้`")
        if sweep_market_orders:  bot_breakdown.append(f"Sweep Fade `{len(sweep_market_orders)} ไม้`")
        if poi_market_orders:    bot_breakdown.append(f"NY POI `{len(poi_market_orders)} ไม้`")
        bot_detail = f" ({', '.join(bot_breakdown)})" if bot_breakdown else ""

        desc = (f"⚡ **ตรวจพบสถานะการถือครองออเดอร์ในพอร์ต (รวม {total_market_count} ไม้สด + {len(pending_orders)} Pending)**\n"
                f"🤖 **ไม้บอท v3.5:** `{len(bot_orders)} ไม้`{bot_detail} (Floating: `{bot_float_str}`)\n"
                f"👤 **ผู้ใช้ User Manual:** `{len(user_market_orders)} ไม้` (Floating: `{user_float_str}`)\n"
                f"💰 **กำไรลอยตัวรวม (Floating PnL):** `{float_str}` | **Equity:** `${equity:,.2f}`")
        embed_color = 0x2ecc71 if total_float >= 0 else 0xe67e22

    spread_disp = f"{spread} pts" if spread > 0 else "Live"
    ask_disp = f" / ${ask:,.2f}" if ask > 0 else ""

    fields = [
        {
            "name": f"⏰ 1. เซสชันตลาด & สถานะ Multi-Engine Radar (รอบที่ {cycle_str})",
            "value": (
                f"• **เซสชันปัจจุบัน:** `{session_name}`\n"
                f"• **กรอบเวลา:** `{session_hours}`\n"
                f"• **กลยุทธ์ช่วงนี้:** {action_note}\n"
                f"• **เวลาไทย:** `{time_thai_str}` | **MT4:** `{server_time}`"
            ),
            "inline": False
        },
        {
            "name": "💰 2. ข้อมูลพอร์ต & ราคาทองคำสด",
            "value": (
                f"🪙 **Gold Bid/Ask:** `${gold_price:,.2f}{ask_disp}` (Spread: `{spread_disp}`)\n"
                f"💵 **Balance / Equity:** `${balance:,.2f}` / `${equity:,.2f}`\n"
                f"📈 **Floating PnL รวม:** `{float_str}` ({(total_float / balance * 100.0) if balance > 0 else 0.0:+.2f}%)\n"
                f"📊 **สถานะคำสั่งในพอร์ต:** `บอท v3.5: {len(bot_orders)} ไม้ | ไม้มือ: {len(user_market_orders)} ไม้ | Pending: {len(pending_orders)} รายการ`"
            ),
            "inline": False
        }
    ]

    if total_market_count > 0 or len(pending_orders) > 0:
        order_sections = []
        if bot_orders:
            order_sections.append(f"**🤖 ไม้บอท [Gold POI Sniper v3.5] ({len(bot_orders)} ไม้สด | {bot_float_str}):**")
            for o in bot_orders:
                t = o.get("ticket", 0)
                t_type = "BUY" if o.get("type", 0) == 0 else "SELL"
                lots = float(o.get("lots", 0.0))
                op = float(o.get("open_price", 0.0))
                sl = float(o.get("sl", 0.0))
                tp = float(o.get("tp", 0.0))
                p = float(o.get("profit", 0.0))
                eng = get_engine_name(o)
                p_disp = f"+${p:.2f}" if p >= 0 else f"-${abs(p):.2f}"
                order_sections.append(f"• `#{t}` `[{eng}]` `{t_type} {lots:.2f}L` @ `${op:.2f}` (SL: {sl:.2f} | TP: {tp:.2f}) ➔ กำไรลอยตัว: `{p_disp}`")

        if user_market_orders:
            if order_sections:
                order_sections.append("")
            order_sections.append(f"**👤 ไม้ผู้ใช้ [User Manual] ({len(user_market_orders)} ไม้สด | {user_float_str}):**")
            for o in user_market_orders:
                t = o.get("ticket", 0)
                t_type = "BUY" if o.get("type", 0) == 0 else "SELL"
                lots = float(o.get("lots", 0.0))
                op = float(o.get("open_price", 0.0))
                sl = float(o.get("sl", 0.0))
                tp = float(o.get("tp", 0.0))
                p = float(o.get("profit", 0.0))
                p_disp = f"+${p:.2f}" if p >= 0 else f"-${abs(p):.2f}"
                order_sections.append(f"• `#{t}` `{t_type} {lots:.2f}L` @ `${op:.2f}` (SL: {sl:.2f} | TP: {tp:.2f}) ➔ กำไรลอยตัว: `{p_disp}`")

        if pending_orders:
            if order_sections:
                order_sections.append("")
            order_sections.append(f"**⏳ คำสั่งรอเปิด [Pending Orders] ({len(pending_orders)} รายการ):**")
            pend_type_map = {2: "BUY LIMIT", 3: "SELL LIMIT", 4: "BUY STOP", 5: "SELL STOP"}
            for o in pending_orders:
                t = o.get("ticket", 0)
                p_type_name = pend_type_map.get(int(o.get("type", 0)), f"TYPE_{o.get('type')}")
                lots = float(o.get("lots", 0.0))
                op = float(o.get("open_price", 0.0))
                sl = float(o.get("sl", 0.0))
                tp = float(o.get("tp", 0.0))
                order_sections.append(f"• `#{t}` `{p_type_name} {lots:.2f}L` @ `${op:.2f}` (SL: {sl:.2f} | TP: {tp:.2f})")

        fields.append({
            "name": f"📦 3. รายละเอียดคำสั่งในพอร์ต (บอท {len(bot_orders)} + มือ {len(user_market_orders)} + Pending {len(pending_orders)})",
            "value": "\n".join(order_sections)[:1020],
            "inline": False
        })
        news_idx = 4
        forecast_idx = 5
    else:
        news_idx = 3
        forecast_idx = 4

    fields.append({
        "name": f"🔴 {news_idx}. อัปเดตข่าวเศรษฐกิจล่าสุด & Reference",
        "value": news_reference_text,
        "inline": False
    })
    fields.append({
        "name": f"🧭 {forecast_idx}. คาดการณ์แนวโน้มทองคำรอบนี้ (AI Forecast: {ai_bias})",
        "value": f"• **ทิศทางหลัก:** `{ai_bias}`\n• **บทวิเคราะห์:** {ai_forecast}\n• **ระดับราคาสำคัญ:** `{ai_levels}`",
        "inline": False
    })

    embed = {
        "title": f"💓 [HEARTBEAT REPORT] Gold POI Sniper v3.5 • รอบที่ {cycle_str}",
        "description": desc,
        "color": embed_color,
        "fields": fields,
        "footer": {"text": f"Gold POI Sniper v3.5 | Institutional Multi-Engine AI Sentinel | รอบที่ {cycle_str} (ทุก 30 นาที)"},
        "timestamp": dt.now(timezone.utc).isoformat()
    }
    base_agent.post_discord_embed(webhook_url, embed)

def send_poi_quant_briefing(webhook_url, slot_name, state, quant_data, gemini_key=None):
    """Dispatches rich 5-sciences institutional quant briefing for Gold POI Sniper v3.5"""
    if not webhook_url or not quant_data:
        return False
    now_thai = dt.now(timezone(timedelta(hours=7)))
    now_str = now_thai.strftime("%d/%m/%Y %H:%M") + " น."
    live_p = quant_data.get("live_price", 0.0)

    major_macro_text = get_upcoming_major_red_events_summary(now_thai)
    co_pilot_note = ""
    if gemini_key:
        prompt = f"""สวมบทบาทเป็น Chief Quant Strategist แห่งสถาบันการเงิน สำหรับระบบ Gold POI Sniper v3.5 (Institutional Multi-Engine)
สังเคราะห์บทวิเคราะห์เชิงปริมาณและปัจจัยข่าวใหญ่ (เช่น การเลือกตั้งสภาคองเกรสสหรัฐฯ/ทรัมป์ พรุ่งนี้ และ NFP) ความยาว 2-3 บรรทัด สำหรับรอบเวลา {slot_name} น. (ภาษาไทย):
- ราคาทองปัจจุบัน: ${live_p:,.2f}
- โครงสร้าง Dow: {quant_data.get('d1_trend')}
- Fibonacci 23.6%: ${quant_data.get('target_fib_236', 0.0):.2f} | 38.2%: ${quant_data.get('target_fib_382', 0.0):.2f}
- Asian Box: ${quant_data.get('stored_asian_high', 0.0):.2f} - ${quant_data.get('stored_asian_low', 0.0):.2f}
- ข่าวใหญ่และเหตุการณ์สำคัญสัปดาห์นี้: {major_macro_text}

ตอบกลับ JSON strictly เท่านั้น:
{{
  "quant_advice": "บทวิเคราะห์สถาบันผสานแนวโน้มรับมือข่าวเลือกตั้งสหรัฐฯ/ทรัมป์ และกลยุทธ์ 2-3 บรรทัด"
}}"""
        res = base_agent.call_gemini_json_safe(prompt, gemini_key, temperature=0.2, timeout=8)
        if res and "quant_advice" in res:
            co_pilot_note = str(res["quant_advice"]).strip()

    title = f"📊 [{slot_name} INSTITUTIONAL QUANT BRIEFING] Gold POI Sniper v3.5 • 5 ศาสตร์สถาบัน"
    p_bull = quant_data.get('p_bull', 0.53)
    p_bear = 1.0 - p_bull
    edge_text = f"🟢 ความน่าจะเป็นฝั่ง BUY `{p_bull*100:.1f}%` vs 🔴 ความน่าจะเป็นฝั่ง SELL `{p_bear*100:.1f}%`"
    edge_rec = "ได้เปรียบฝั่ง Buy (รอ Buy on Dip ที่แนว POI ล่าง)" if p_bull >= 0.50 else "ได้เปรียบฝั่ง Sell (รอ Fade Rally ที่แนว POI บน)"

    embed = {
        "title": title,
        "description": f"🏦 **บทวิเคราะห์เชิงปริมาณ 5 ศาสตร์สถาบัน (2,148 แท่ง D1 + M15 POI Structure)**\n"
                       f"🪙 **ราคาทองสด:** `${live_p:,.2f}` │ 📅 **วัน:** `{quant_data.get('weekday_name')}` │ ⏰ `{now_str}`\n\n"
                       f"⚖️ **Institutional Probability Matrix:**\n{edge_text}\n🎯 **คำแนะนำกลยุทธ์:** {edge_rec}",
        "color": 0x3498db,
        "fields": [
            {
                "name": "📐 1. Dow Theory & Market Structure (D1 / H4 / H1)",
                "value": f"• **โครงสร้าง D1:** `{quant_data.get('d1_trend')}`\n"
                         f"• **Previous Day High (PDH):** `${(quant_data.get('prev_high') or state.get('pdh', 0.0)):.2f}`\n"
                         f"• **Previous Day Low (PDL):** `${(quant_data.get('prev_low') or state.get('pdl', 0.0)):.2f}`",
                "inline": False
            },
            {
                "name": "🪤 2. Asian Range POI Liquidity Boundary",
                "value": f"• **Asian High:** `${quant_data.get('stored_asian_high', 0.0):.2f}`\n"
                         f"• **Asian Low:** `${quant_data.get('stored_asian_low', 0.0):.2f}`\n"
                         f"• **กรอบเอเชีย (Span):** `{quant_data.get('asian_span', 0.0):.2f} pts`",
                "inline": False
            },
            {
                "name": "🌊 3. Elliott Wave & Harmonic Fibonacci Confluence",
                "value": f"• **Elliott Wave Regime:** `{quant_data.get('elliott_wave')}`\n"
                         f"• **Fibonacci Retracement 23.6%:** `${quant_data.get('target_fib_236', 0.0):.2f}`\n"
                         f"• **Fibonacci Retracement 38.2%:** `${quant_data.get('target_fib_382', 0.0):.2f}`\n"
                         f"• **Fibonacci 50.0% Equilibrium:** `${quant_data.get('target_fib_500', 0.0):.2f}`",
                "inline": False
            },
            {
                "name": "🧠 4. Co-Pilot AI Synthesis (Gemini 3.5 Flash Lite)",
                "value": f"💡 *\"{co_pilot_note or 'รักษาวินัยตามแผน London Dual-Engine (08:00-11:30) และ NY Prime (15:00-20:30)'}\"*",
                "inline": False
            }
        ],
        "footer": {"text": f"Gold POI Sniper v3.5 | Institutional Quant Engine | รอบ {slot_name} น."},
        "timestamp": dt.now(timezone.utc).isoformat()
    }
    return base_agent.post_discord_embed(webhook_url, embed)

def fetch_poi_breaking_news_sentinel(api_key, webhook_briefing=None, webhook_orders=None, state=None):
    """
    Customized 2-Stage Zero-Cost Live Breaking News for Gold POI Sniper v3.5
    Guarantees zero duplicates: webhook_briefing is strictly ignored,
    routing critical news shocks ONLY to #🚨-news-guard (webhook_orders).
    """
    res = base_agent.fetch_live_breaking_news_sentinel(
        api_key=api_key,
        webhook_briefing=None,         # Zero-overlap: Never duplicate to Morning Briefing room!
        webhook_orders=webhook_orders, # Exclusively sent to #🚨-news-guard!
        state=state
    )
    return res

def send_poi_morning_news_briefing(webhook_url, api_key=None):
    """Customized Morning Macro Briefing for Gold POI Sniper v3.5 (Exclusively sent to Morning Briefing Room)"""
    return base_agent.send_discord_morning_news_briefing(webhook_url, api_key)

def evaluate_streak_breaker(closed_orders):
    """
    Evaluates recent closed orders from MT4 to calculate the consecutive loss streak.
    Strictly filters Gold POI Sniper bot orders (all 3 engines)
    so user manual trades do not penalize the bot.
    Dynamically scales ai_risk_multiplier:
      - 0 or 1 loss: 1.0x (Normal compound risk)
      - 2 losses in a row: 0.5x (Halve risk to protect capital)
      - 3+ losses in a row: 0.25x (Quarter risk to neutralize drawdown streak)
      - Resets to 1.0x immediately on a winning trade!
    """
    if not closed_orders:
        return 0, 1.0, "NO_CLOSED_ORDERS_TODAY"

    bot_trades = []
    for order in closed_orders:
        if is_bot_order(order):
            bot_trades.append(order)

    bot_trades.sort(key=lambda x: str(x.get("close_time", "")), reverse=True)

    consec_losses = 0
    for t in bot_trades:
        profit = float(t.get("profit", 0.0))
        if profit <= 0:
            consec_losses += 1
        else:
            break

    if consec_losses <= 1:
        risk_mult = 1.0
        reason = "NORMAL_REGIME"
    elif consec_losses == 2:
        risk_mult = 0.50
        reason = "CAUTION_HALVE_RISK (2 Consecutive Losses)"
    else:
        risk_mult = 0.25
        reason = f"DEFENSIVE_SHIELD_ENGAGED ({consec_losses} Consecutive Losses)"

    return consec_losses, risk_mult, reason

def run_poi_ai_agent():
    base_agent.disable_quickedit()
    config = load_poi_config()
    mt4_dir = config.get("mt4_files_dir", "")
    symbol = config.get("symbol", "GOLD")
    state_file = os.path.join(mt4_dir, "market_state.json")
    sentinel_poi_file = os.path.join(mt4_dir, "ai_sentinel_poi.json")
    sentinel_compat_file = os.path.join(mt4_dir, "ai_sentinel.json")
    poi_state_file = os.path.join(SCRIPT_DIR, "poi_agent_state.json")

    gemini_key = config.get("gemini_api_key", "")
    webhook_orders = config.get("discord_webhook_orders") or config.get("discord_webhook_url")
    webhook_user = config.get("discord_webhook_user_trades") or webhook_orders
    webhook_morning = config.get("discord_webhook_morning_briefing") or config.get("discord_webhook_briefing") or webhook_orders
    webhook_quant = config.get("discord_webhook_quant_5sciences") or config.get("discord_webhook_briefing") or webhook_orders
    webhook_news = config.get("discord_webhook_news_guard") or config.get("discord_webhook_signals") or webhook_orders
    webhook_heartbeat = config.get("discord_webhook_heartbeat") or webhook_orders

    b_mins = int(config.get("news_stand_down_mins_before", 15))
    a_mins = int(config.get("news_stand_down_mins_after", 15))
    hb_interval_mins = int(config.get("heartbeat_interval_mins", 30))

    base_agent.safe_print("======================================================================")
    base_agent.safe_print("  [*] System Suite: Gold POI Sniper v3.5 (London Dual + New York POI)")
    base_agent.safe_print("  [*] Gemini AI Studio: ACTIVE (gemini-3.5-flash-lite Free Tier 500 RPD)")
    base_agent.safe_print("  [*] Engine A: London Sniper (Breakout Runner | 08:00 - 11:30 MT4)")
    base_agent.safe_print("  [*] Engine B: Judas Sweep Fade (Contrarian Trap Hunter | 08:00 - 11:30 MT4)")
    base_agent.safe_print("  [*] Engine C: New York POI Sniper (SMC Liquidity Prime | 15:00 - 20:30 MT4)")
    base_agent.safe_print("  [*] 5-Sciences Quant Engine: ACTIVE (Slots: 02, 05, 08, 11, 14, 17, 20, 23)")
    base_agent.safe_print("  [*] Heartbeat Monitor: ACTIVE (Every 30 Mins to #💓-heartbeat-check)")
    base_agent.safe_print("  [*] Zero-Duplicate News Guard: ENGAGED (#🚨-news-guard Only)")
    base_agent.safe_print("  [*] Discord 6-Room Multi-Dispatcher: ACTIVE (Bot, Manual, Briefing, Quant, News, Heartbeat)")
    base_agent.safe_print("======================================================================")
    base_agent.safe_print("  [+] Synchronizing with Gold POI Sniper v3.5 MT4 Bridge Engine...\n")

    last_news_poll_time = 0
    last_briefing_date = None
    last_heartbeat_slot_fired = None
    last_quant_slot_fired = None
    stand_down = False
    cached_active_news = []
    last_headline = "Normal Market Liquidity"
    prev_consec_losses = 0

    # Load known open tickets and wall-clock schedule state to prevent duplicate or missed alerts
    known_open_tickets = set()
    if os.path.exists(poi_state_file):
        try:
            with open(poi_state_file, "r", encoding="utf-8") as psf:
                ps_data = json.load(psf)
                known_open_tickets = set(ps_data.get("known_open_tickets", []))
                last_briefing_date = ps_data.get("last_briefing_date")
                last_heartbeat_slot_fired = ps_data.get("last_heartbeat_slot_fired")
                last_quant_slot_fired = ps_data.get("last_quant_slot_fired")
        except Exception:
            pass
    elif os.path.exists(state_file):
        init_st = base_agent.read_market_state_safe(state_file) or {}
        for o in init_st.get("open_orders", []):
            if o.get("ticket"):
                known_open_tickets.add(o.get("ticket"))

    while True:
        try:
            now_ts = time.time()
            now_dt = dt.now(timezone.utc)
            now_thai = dt.now(timezone(timedelta(hours=7)))
            today_str = now_thai.strftime("%Y-%m-%d")
            time_hm_str = now_thai.strftime("%H:%M")

            # 1. Read MT4 Market State
            state = {}
            if os.path.exists(state_file):
                state = base_agent.read_market_state_safe(state_file) or {}

            closed_orders = state.get("recent_closed_orders", [])
            open_orders = state.get("open_orders", [])
            balance = float(state.get("balance", 2000.0))
            equity = float(state.get("equity", 2000.0))
            spread = float(state.get("spread", 50.0))
            gold_price = float(state.get("bid", 0.0))
            if gold_price <= 0.0:
                gold_price = 3875.61

            # 2. Morning Macro Briefing (Once daily at 06:30-08:00 Thai Time strictly to Morning Briefing Room)
            if last_briefing_date != today_str and now_thai.hour >= 6 and (now_thai.hour > 6 or now_thai.minute >= 30):
                if webhook_morning and gemini_key:
                    try:
                        send_poi_morning_news_briefing(webhook_morning, gemini_key)
                        last_briefing_date = today_str
                        base_agent.safe_print(f"\n    [💬 DISCORD NOTIFIED] Morning Macro Briefing sent strictly to Morning Briefing Room! ({time_hm_str})")
                    except Exception:
                        pass

            # 3. 5-Sciences Quantitative Briefing (Strictly aligned to wall-clock 02:00, 05:00, 08:00, 11:00, 14:00, 17:00, 20:00, 23:00 Thai Time)
            is_weekend = (now_thai.weekday() == 5 and now_thai.hour >= 4) or (now_thai.weekday() == 6) or (now_thai.weekday() == 0 and now_thai.hour < 5)
            if webhook_quant and not is_weekend:
                for slot in QUANT_3H_SLOTS:
                    slot_h = int(slot.split(":")[0])
                    slot_key = f"{today_str}_{slot}"
                    if now_thai.hour == slot_h and now_thai.minute < 15 and last_quant_slot_fired != slot_key:
                        try:
                            qd = base_agent.compute_5_sciences_quant(mt4_dir, symbol, state, gold_price)
                            res = send_poi_quant_briefing(webhook_quant, slot, state, qd, gemini_key)
                            if res:
                                last_quant_slot_fired = slot_key
                                with open(poi_state_file, "w", encoding="utf-8") as psf:
                                    json.dump({
                                        "known_open_tickets": list(known_open_tickets),
                                        "last_briefing_date": last_briefing_date,
                                        "last_heartbeat_slot_fired": last_heartbeat_slot_fired,
                                        "last_quant_slot_fired": last_quant_slot_fired,
                                        "updated_at": dt.now().isoformat()
                                    }, psf, indent=2)
                                base_agent.safe_print(f"\n    [💬 DISCORD NOTIFIED] Wall-Clock 5-Sciences Quant Briefing ({slot} น.) sent to Quant room!")
                        except Exception as q_ex:
                            pass

            # 4. Periodic Discord Heartbeat (Strictly aligned to wall-clock :00 and :30 of every hour, NOT agent boot time!)
            if webhook_heartbeat:
                if now_thai.minute in (0, 30):
                    hb_slot_key = f"{today_str}_{now_thai.hour:02d}:{now_thai.minute:02d}"
                    if last_heartbeat_slot_fired != hb_slot_key:
                        last_heartbeat_slot_fired = hb_slot_key
                        try:
                            send_poi_heartbeat_report(webhook_heartbeat, state, gemini_key)
                            with open(poi_state_file, "w", encoding="utf-8") as psf:
                                json.dump({
                                    "known_open_tickets": list(known_open_tickets),
                                    "last_briefing_date": last_briefing_date,
                                    "last_heartbeat_slot_fired": last_heartbeat_slot_fired,
                                    "last_quant_slot_fired": last_quant_slot_fired,
                                    "updated_at": dt.now().isoformat()
                                }, psf, indent=2)
                            base_agent.safe_print(f"\n    [💬 DISCORD NOTIFIED] Wall-Clock 30-min Heartbeat ({now_thai.hour:02d}:{now_thai.minute:02d} น.) sent to Heartbeat room!")
                        except Exception as hb_ex:
                            pass

            # 5. Check Macro News Stand-Down (every 30 seconds strictly to News Guard Room)
            if now_ts - last_news_poll_time >= 30:
                last_news_poll_time = now_ts
                try:
                    cached_active_news = base_agent.check_active_live_news_now(before_mins=b_mins, after_mins=a_mins)
                    high_news = [n for n in cached_active_news if str(n.get("impact", "")).lower() in ["high", "red"]]
                    new_stand_down = len(high_news) > 0

                    if new_stand_down and not stand_down:
                        stand_down = True
                        if webhook_news:
                            base_agent.send_discord_stand_down_alert(webhook_news, high_news)
                    elif not new_stand_down and stand_down:
                        stand_down = False
                        base_agent.safe_print(f"\n    [💬 DISCORD NOTIFIED] News Stand-Down Cleared. Market Liquidity Normal!")
                    stand_down = new_stand_down
                except Exception:
                    pass

                # Breaking News RSS Check (Exclusively sent to News Guard Room, zero duplication)
                try:
                    breaking_dict = fetch_poi_breaking_news_sentinel(
                        api_key=gemini_key,
                        webhook_briefing=None,        # Never duplicate to Morning Briefing!
                        webhook_orders=webhook_news,  # Strictly to News Guard Room!
                        state=state
                    )
                    if isinstance(breaking_dict, dict) and breaking_dict.get("is_breaking_shock", False):
                        stand_down = True
                        hl = breaking_dict.get("headline", "")
                        if hl:
                            last_headline = hl
                            base_agent.safe_print(f"\n    [🚨 DISCORD NOTIFIED] Critical Geopolitical Shock sent to News Guard: {hl}")
                except Exception:
                    pass

            # 6. Check for new open orders to dispatch Discord notification
            current_open_tickets = set()
            new_ticket_detected = False
            for o in open_orders:
                t_id = o.get("ticket")
                if t_id:
                    current_open_tickets.add(t_id)
                    if t_id not in known_open_tickets:
                        known_open_tickets.add(t_id)
                        new_ticket_detected = True
                        t_type = "BUY" if o.get("type") == 0 else "SELL"
                        lots = float(o.get("lots", 0.0))
                        open_p = float(o.get("open_price", 0.0))
                        sl_p = float(o.get("sl", 0.0))
                        tp_p = float(o.get("tp", 0.0))
                        is_bot = is_bot_order(o)
                        eng_name = get_engine_name(o)

                        if not is_bot:
                            # User Manual Trade Alert -> send strictly to Manual Trades Room!
                            base_agent.safe_print(f"\n    [📱 DISCORD NOTIFIED] User Manual {t_type} Order #{t_id} sent to Manual Trades room!")
                            if webhook_user:
                                base_agent.send_discord_manual_order_alert(webhook_user, o, state, gemini_key)
                        else:
                            # Bot Trade Alert -> send strictly to Bot Orders Room with specific Engine badge!
                            target_rr = "1:5.0 (Partial TP @ 1.5R)" if "Sweep" in eng_name else "1:3.5"
                            base_agent.safe_print(f"\n    [🎯 DISCORD NOTIFIED] [{eng_name}] {t_type} Order #{t_id} ({lots:.2f}L @ {open_p:.2f}) sent to Bot Orders room!")
                            if webhook_orders:
                                embed = {
                                    "title": f"🎯 Gold POI Sniper v3.5: [{eng_name}] {t_type} #{t_id}",
                                    "color": 0x00FF00 if t_type == "BUY" else 0xFF4444,
                                    "description": (
                                        f"**Engine:** `{eng_name}` (Magic: `{o.get('magic')}`)\n"
                                        f"**Symbol:** `{symbol}` │ **Lots:** `{lots:.2f}L`\n"
                                        f"**Entry Price:** `${open_p:.2f}`\n"
                                        f"**Stop Loss:** `${sl_p:.2f}` │ **Take Profit:** `${tp_p:.2f}`\n"
                                        f"**Target RR:** `{target_rr}`"
                                    ),
                                    "timestamp": dt.now(timezone.utc).isoformat()
                                }
                                base_agent.post_discord_embed(webhook_orders, embed)

            if new_ticket_detected or len(current_open_tickets) != len(known_open_tickets):
                known_open_tickets = current_open_tickets
                try:
                    with open(poi_state_file, "w", encoding="utf-8") as psf:
                        json.dump({
                            "known_open_tickets": list(known_open_tickets),
                            "last_briefing_date": last_briefing_date,
                            "last_heartbeat_slot_fired": last_heartbeat_slot_fired,
                            "last_quant_slot_fired": last_quant_slot_fired,
                            "updated_at": dt.now().isoformat()
                        }, psf, indent=2)
                except Exception:
                    pass

            # 7. Evaluate Streak Breaker (sent strictly to News Guard Room)
            consec_losses, risk_mult, streak_reason = evaluate_streak_breaker(closed_orders)
            effective_risk_mult = 0.0 if stand_down else risk_mult

            if consec_losses >= 2 and consec_losses != prev_consec_losses:
                prev_consec_losses = consec_losses
                base_agent.safe_print(f"\n    [⚠️ DISCORD NOTIFIED] AI Streak Breaker: {consec_losses} Losses Detected. Risk scaled to {risk_mult:.2f}x!")
                if webhook_news:
                    embed_sb = {
                        "title": "⚠️ [AI STREAK BREAKER] ปรับลดความเสี่ยงปกป้องทุนอัตโนมัติ",
                        "color": 0xE67E22,
                        "description": f"**สถานะ:** ตรวจพบการขาดทุนติดต่อกัน `{consec_losses}` ไม้ (เฉพาะบอท v3.5)\n"
                                       f"🛡️ **เกราะป้องกันทุน:** ปรับลด Risk Multiplier เหลือ `{risk_mult:.2f}x`\n"
                                       f"📌 *ระบบจะกลับคืนสู่ความเสี่ยงปกติ 1.0x ทันทีเมื่อมีไม้ชนะครั้งถัดไป*",
                        "timestamp": dt.now(timezone.utc).isoformat()
                    }
                    base_agent.post_discord_embed(webhook_news, embed_sb)

            # 8. Build and Write AI Sentinel Payload
            sentinel_payload = {
                "version": VERSION,
                "stand_down": stand_down,
                "ai_risk_multiplier": effective_risk_mult,
                "base_risk_multiplier": risk_mult,
                "consecutive_losses": consec_losses,
                "streak_status": streak_reason,
                "poi_bias": "BOTH",
                "breaking_headline": last_headline,
                "active_news_count": len(cached_active_news),
                "active_news": cached_active_news,
                "balance": balance,
                "equity": equity,
                "timestamp": now_dt.isoformat()
            }

            for target_path in [sentinel_poi_file, sentinel_compat_file]:
                try:
                    tmp_file = target_path + ".tmp"
                    with open(tmp_file, "w", encoding="utf-8") as f:
                        json.dump(sentinel_payload, f, indent=2, ensure_ascii=False)
                    if os.path.exists(target_path):
                        os.replace(tmp_file, target_path)
                    else:
                        os.rename(tmp_file, target_path)
                except Exception:
                    pass

            # 9. Format and Render Dynamic Live Ticker
            time_disp = dt.now().strftime("%H:%M:%S")
            float_pnl = equity - balance
            float_pnl_pct = (float_pnl / balance * 100.0) if balance > 0 else 0.0

            # Cumulative Bot closed PnL (all 3 engines)
            bot_closed_pnl = sum(
                float(o.get("profit", 0.0))
                for o in closed_orders
                if is_bot_order(o)
            )

            # Open orders breakdown by engine
            open_ld_count = sum(1 for o in open_orders if int(o.get("type", 0)) in (0, 1) and (int(o.get("magic", 0)) == MAGIC_LONDON_SNIPER or "London" in str(o.get("engine", ""))))
            open_sw_count = sum(1 for o in open_orders if int(o.get("type", 0)) in (0, 1) and (int(o.get("magic", 0)) == MAGIC_JUDAS_SWEEP or "Sweep" in str(o.get("engine", "")) or "Judas" in str(o.get("engine", ""))))
            open_poi_count = sum(1 for o in open_orders if int(o.get("type", 0)) in (0, 1) and (int(o.get("magic", 0)) == MAGIC_POI or "POI" in str(o.get("engine", ""))))
            open_bot_count = open_ld_count + open_sw_count + open_poi_count
            open_user_count = sum(1 for o in open_orders if int(o.get("type", 0)) in (0, 1) and not is_bot_order(o))
            open_pend_count = sum(1 for o in open_orders if int(o.get("type", 0)) not in (0, 1))

            sentinel_disp = "STAND-DOWN" if stand_down else "CLEAR"
            status_disp = "READY" if not stand_down else "NEWS_HALT"

            status_line = (
                f"[{time_disp}] Gold: ${gold_price:.2f} | "
                f"Eq: ${equity:,.2f} | "
                f"Float: {float_pnl_pct:+.1f}% (${float_pnl:+.2f}) | "
                f"Bot Closed: ${bot_closed_pnl:+.2f} | "
                f"Open: [Bot: {open_bot_count} (LD:{open_ld_count}/SW:{open_sw_count}/NY:{open_poi_count}) | User: {open_user_count} | Pend: {open_pend_count}] | "
                f"RiskMult: {risk_mult:.2f}x | "
                f"News: [{sentinel_disp}] | "
                f"Status: [{status_disp}]   "
            )

            try:
                sys.stdout.write(status_line + "\r")
                sys.stdout.flush()
            except Exception:
                base_agent.safe_print(status_line)

            time.sleep(1)

        except KeyboardInterrupt:
            base_agent.safe_print("\n[!] Stopping POI AI Agent cleanly...")
            break
        except Exception as ex:
            time.sleep(2)

if __name__ == "__main__":
    run_poi_ai_agent()
