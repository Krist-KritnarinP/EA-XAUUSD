import os
import shutil

base_dir = r"C:\Users\Kritnarin\.gemini\antigravity\scratch\GoldSniper_MT4"

with open(os.path.join(base_dir, "gold_ai_agent_poi_v3_5.py"), "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add helper function get_upcoming_major_red_events_summary() right before send_poi_heartbeat_report
helper_func = '''def get_upcoming_major_red_events_summary(now_thai):
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

    return "\\n".join(lines)

def send_poi_heartbeat_report(webhook_url, state, api_key=None):'''

code = code.replace("def send_poi_heartbeat_report(webhook_url, state, api_key=None):", helper_func)

# 2. Replace the news summary block in send_poi_heartbeat_report to use get_upcoming_major_red_events_summary
old_news_block = """    today_events = base_agent.get_today_high_impact_events()
    week_events = base_agent.fetch_economic_calendar()
    upcoming_events = [ev for ev in today_events if ev.get("dt_obj") and ev["dt_obj"] >= (now_thai - timedelta(minutes=30))]

    news_lines = []
    if upcoming_events:
        for ev in upcoming_events[:3]:
            news_lines.append(f"• **{ev['title']}** เวลา {ev['time_th']} (คาดการณ์: {ev['forecast']} | ก่อนหน้า: {ev['previous']})")
        news_summary_text = "\\n".join(news_lines)
    else:
        next_ev = None
        for ev in week_events:
            ev_dt = base_agent.parse_event_time_thai(ev.get("date", ""))
            if ev_dt and ev_dt > now_thai:
                next_ev = ev
                break
        if next_ev:
            ev_dt = base_agent.parse_event_time_thai(next_ev.get("date", ""))
            dt_str = (ev_dt.strftime("%a %d/%m %H:%M") + " น.") if ev_dt else "N/A"
            imp = next_ev.get("impact", "High")
            badge = "🔴" if imp == "High" else ("🟠" if imp == "Medium" else "🟡")
            news_summary_text = f"🟢 **ไม่มีข่าวกล่องแดง USD ในช่วงที่เหลือของวันนี้**\\n• ข่าวสำคัญถัดไป: **{badge} {next_ev.get('title')}** ({dt_str}) คาดการณ์: {next_ev.get('forecast') or 'N/A'}"
        else:
            news_summary_text = "🟢 **ไม่มีรายงานข่าวกล่องแดง USD ในช่วงนี้**"
    news_reference_text = news_summary_text + "\\n📌 *Reference: ForexFactory / FairEconomy Economic Calendar (USD High Impact)*\""""

new_news_block = """    today_events = base_agent.get_today_high_impact_events()
    upcoming_today = [ev for ev in today_events if ev.get("dt_obj") and ev["dt_obj"] >= (now_thai - timedelta(minutes=30))]
    today_lines = []
    for ev in upcoming_today[:3]:
        today_lines.append(f"• **ข่าวคืนนี้:** {ev['title']} เวลา `{ev['time_th']}` (คาดการณ์: `{ev['forecast']}` | ก่อนหน้า: `{ev['previous']}`)")
    major_week_summary = get_upcoming_major_red_events_summary(now_thai)
    if today_lines:
        news_summary_text = "\\n".join(today_lines) + "\\n\\n" + major_week_summary
    else:
        news_summary_text = major_week_summary
    news_reference_text = news_summary_text + "\\n📌 *Reference: ForexFactory Official Calendar + Live Geopolitical Election Radar*\""""

code = code.replace(old_news_block.replace("\n", "\r\n"), new_news_block.replace("\n", "\r\n"))
code = code.replace(old_news_block, new_news_block)

# 3. Enhance send_poi_quant_briefing to include Macro & US Election Radar field and pass major red events to Gemini prompt
old_quant_prompt = """    co_pilot_note = ""
    if gemini_key:
        prompt = f\"\"\"สวมบทบาทเป็น Chief Quant Strategist แห่งสถาบันการเงิน สำหรับระบบ Gold POI Sniper v3.5 (Institutional Multi-Engine)
สังเคราะห์บทวิเคราะห์เชิงปริมาณความยาวไม่เกิน 2 บรรทัด สำหรับรอบเวลา {slot_name} น. (ภาษาไทย):
- ราคาทองปัจจุบัน: ${live_p:,.2f}
- โครงสร้าง Dow: {quant_data.get('d1_trend')}
- Fibonacci 23.6%: ${quant_data.get('target_fib_236', 0.0):.2f} | 38.2%: ${quant_data.get('target_fib_382', 0.0):.2f}
- Asian Box: ${quant_data.get('stored_asian_high', 0.0):.2f} - ${quant_data.get('stored_asian_low', 0.0):.2f}

ตอบกลับ JSON strictly เท่านั้น:
{{
  "quant_advice": "บทวิเคราะห์สถาบันและคำแนะนำกลยุทธ์ 2 บรรทัด"
}}\"\"\""""

new_quant_prompt = """    major_macro_text = get_upcoming_major_red_events_summary(now_thai)
    co_pilot_note = ""
    if gemini_key:
        prompt = f\"\"\"สวมบทบาทเป็น Chief Quant Strategist แห่งสถาบันการเงิน สำหรับระบบ Gold POI Sniper v3.5 (Institutional Multi-Engine)
สังเคราะห์บทวิเคราะห์เชิงปริมาณและปัจจัยข่าวใหญ่ (เช่น การเลือกตั้งสภาคองเกรสสหรัฐฯ/ทรัมป์ พรุ่งนี้ และ NFP) ความยาว 2-3 บรรทัด สำหรับรอบเวลา {slot_name} น. (ภาษาไทย):
- ราคาทองปัจจุบัน: ${live_p:,.2f}
- โครงสร้าง Dow: {quant_data.get('d1_trend')}
- Fibonacci 23.6%: ${quant_data.get('target_fib_236', 0.0):.2f} | 38.2%: ${quant_data.get('target_fib_382', 0.0):.2f}
- Asian Box: ${quant_data.get('stored_asian_high', 0.0):.2f} - ${quant_data.get('stored_asian_low', 0.0):.2f}
- ข่าวใหญ่และเหตุการณ์สำคัญสัปดาห์นี้: {major_macro_text}

ตอบกลับ JSON strictly เท่านั้น:
{{
  "quant_advice": "บทวิเคราะห์สถาบันผสานแนวโน้มรับมือข่าวเลือกตั้งสหรัฐฯ/ทรัมป์ และกลยุทธ์ 2-3 บรรทัด"
}}\"\"\""""

code = code.replace(old_quant_prompt.replace("\n", "\r\n"), new_quant_prompt.replace("\n", "\r\n"))
code = code.replace(old_quant_prompt, new_quant_prompt)

old_quant_copilot_field = """            {
                "name": "🧠 4. Co-Pilot AI Synthesis (Gemini 3.5 Flash Lite)",
                "value": f"💡 *\\"{co_pilot_note or 'รักษาวินัยตามแผน London Dual-Engine (08:00-11:30) และ NY Prime (15:00-20:30)'}\\*"",
                "inline": False
            }"""

new_quant_copilot_field = """            {
                "name": "🗳️ 4. ปฏิทินข่าวกล่องแดง & เรดาร์การเมืองสหรัฐฯ (ForexFactory & Election Watch)",
                "value": major_macro_text,
                "inline": False
            },
            {
                "name": "🧠 5. Co-Pilot AI Synthesis (Gemini 3.5 Flash Lite)",
                "value": f"💡 *\\"{co_pilot_note or 'รักษาวินัยตามแผน London Dual-Engine (08:00-11:30) และ NY Prime (15:00-20:30)'}\\*"",
                "inline": False
            }"""

code = code.replace(old_quant_copilot_field.replace("\n", "\r\n"), new_quant_copilot_field.replace("\n", "\r\n"))
code = code.replace(old_quant_copilot_field, new_quant_copilot_field)

# 4. Fix wall-clock alignment for Heartbeat (:00 and :30) and 3-Hour Quant (02, 05, 08, 11, 14, 17, 20, 23) + persistent state
old_loop_init = """    last_news_poll_time = 0
    last_briefing_date = None
    last_heartbeat_post_time = 0
    last_quant_slot_fired = None
    stand_down = False
    cached_active_news = []
    last_headline = "Normal Market Liquidity"
    prev_consec_losses = 0

    # Load known open tickets to prevent duplicate alerts on agent restart
    known_open_tickets = set()
    if os.path.exists(poi_state_file):
        try:
            with open(poi_state_file, "r", encoding="utf-8") as psf:
                ps_data = json.load(psf)
                known_open_tickets = set(ps_data.get("known_open_tickets", []))
        except Exception:
            pass"""

new_loop_init = """    last_news_poll_time = 0
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
            pass"""

code = code.replace(old_loop_init.replace("\n", "\r\n"), new_loop_init.replace("\n", "\r\n"))
code = code.replace(old_loop_init, new_loop_init)

old_sched_block = """            # 3. 5-Sciences Quantitative Briefing (Every 3 Hours: 02, 05, 08, 11, 14, 17, 20, 23 strictly to Quant Room)
            if webhook_quant:
                for slot in QUANT_3H_SLOTS:
                    slot_h = int(slot.split(":")[0])
                    if now_thai.hour == slot_h and now_thai.minute < 5 and last_quant_slot_fired != (today_str + "_" + slot):
                        try:
                            qd = base_agent.compute_5_sciences_quant(mt4_dir, symbol, state, gold_price)
                            res = send_poi_quant_briefing(webhook_quant, slot, state, qd, gemini_key)
                            if res:
                                last_quant_slot_fired = today_str + "_" + slot
                                base_agent.safe_print(f"\\n    [💬 DISCORD NOTIFIED] Full 5-Sciences Quantitative Briefing ({slot}) sent to 5-Sciences Quant room!")
                        except Exception as q_ex:
                            pass

            # 4. Periodic Discord Heartbeat (Every 30 Minutes strictly to Heartbeat Room)
            if webhook_heartbeat and (now_ts - last_heartbeat_post_time) >= (hb_interval_mins * 60):
                last_heartbeat_post_time = now_ts
                try:
                    send_poi_heartbeat_report(webhook_heartbeat, state, gemini_key)
                    base_agent.safe_print(f"\\n    [💬 DISCORD NOTIFIED] 30-min Heartbeat Report sent to Heartbeat room! ({now_thai.strftime('%H:%M:%S')})")
                except Exception as hb_ex:
                    pass"""

new_sched_block = """            # 3. 5-Sciences Quantitative Briefing (Strictly aligned to wall-clock 02:00, 05:00, 08:00, 11:00, 14:00, 17:00, 20:00, 23:00 Thai Time)
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
                                base_agent.safe_print(f"\\n    [💬 DISCORD NOTIFIED] Wall-Clock 5-Sciences Quant Briefing ({slot} น.) sent to Quant room!")
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
                            base_agent.safe_print(f"\\n    [💬 DISCORD NOTIFIED] Wall-Clock 30-min Heartbeat ({now_thai.hour:02d}:{now_thai.minute:02d} น.) sent to Heartbeat room!")
                        except Exception as hb_ex:
                            pass"""

code = code.replace(old_sched_block.replace("\n", "\r\n"), new_sched_block.replace("\n", "\r\n"))
code = code.replace(old_sched_block, new_sched_block)

# Also update state saving on new_ticket_detected to preserve schedule keys
old_save_tickets = """                try:
                    with open(poi_state_file, "w", encoding="utf-8") as psf:
                        json.dump({"known_open_tickets": list(known_open_tickets), "updated_at": dt.now().isoformat()}, psf, indent=2)
                except Exception:"""

new_save_tickets = """                try:
                    with open(poi_state_file, "w", encoding="utf-8") as psf:
                        json.dump({
                            "known_open_tickets": list(known_open_tickets),
                            "last_briefing_date": last_briefing_date,
                            "last_heartbeat_slot_fired": last_heartbeat_slot_fired,
                            "last_quant_slot_fired": last_quant_slot_fired,
                            "updated_at": dt.now().isoformat()
                        }, psf, indent=2)
                except Exception:"""

code = code.replace(old_save_tickets.replace("\n", "\r\n"), new_save_tickets.replace("\n", "\r\n"))
code = code.replace(old_save_tickets, new_save_tickets)

for target in ["gold_ai_agent_poi_v3_5.py", "gold_ai_agent_poi_v2_5.py"]:
    with open(os.path.join(base_dir, target), "w", encoding="utf-8") as f:
        f.write(code)
    print(f"[OK] Upgraded wall-clock schedule & Election Radar in {target}")
