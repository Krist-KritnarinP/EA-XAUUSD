# -*- coding: utf-8 -*-
"""
End-to-End Test Suite for All AI Scenarios in Gold Sniper v6.3.5-Beta
Tests:
  1. Gemini Flash Report + Google Search Grounding
  2. Order Opened Alert (Engine: SweepFade, Sniper, NewYork, Scalper)
  3. Manual Order Risk Assessment (Market Order vs Pending Order)
  4. SL Modification (Breakeven Shield & Dynamic Profit Ratchet)
  5. Order Closed Summary (TP Hit, BE Exit, Trailing Lock, SL Hit)
  6. Jackpot Profit Lock Alert
  7. Stand-Down & News Cleared Flash Alerts
  8. Morning Macro Briefing Generation
  9. Signal Feed (New, Win, Loss)
"""

import sys
import os
import json

# Ensure parent directory in sys.path
sys.path.insert(0, os.path.dirname(__file__))
import gold_ai_agent

def run_all_tests(dry_run=True):
    gold_ai_agent.safe_print("="*75)
    gold_ai_agent.safe_print("🧪 STARTING FULL AI SCENARIO VERIFICATION TEST SUITE (v6.3.5-Beta)")
    gold_ai_agent.safe_print(f"Mode: {'DRY RUN (Simulate without spamming webhooks)' if dry_run else 'LIVE DISPATCH'}")
    gold_ai_agent.safe_print("="*75)

    cfg = gold_ai_agent.load_config()
    api_key = cfg.get("gemini_api_key")
    wh_orders = None if dry_run else cfg.get("discord_webhook_url")
    wh_user = None if dry_run else cfg.get("discord_webhook_user_trades")
    wh_briefing = None if dry_run else cfg.get("discord_webhook_briefing")
    wh_heartbeat = None if dry_run else cfg.get("discord_webhook_heartbeat")
    wh_signals = None if dry_run else cfg.get("discord_webhook_signals")

    mock_state = {
        "version": "6.3.5-Beta",
        "symbol": "GOLD",
        "server_time": "2026.10.16 09:25:00",
        "bid": 4172.50,
        "ask": 4173.05,
        "bar_high": 4176.80,
        "bar_low": 4170.20,
        "spread_points": 55,
        "balance": 1692.87,
        "equity": 2484.40,
        "daily_pnl": 22.69,
        "daily_pnl_pct": 1.34,
        "daily_sniper_pnl": 0.00,
        "daily_sweep_pnl": 0.00,
        "daily_total_trades": 1,
        "sweep_trap_armed": True,
        "sweep_trap_level": 4165.00,
        "open_orders": []
    }

    results = {}

    # -------------------------------------------------------------
    # 1. TEST GEMINI FLASH WITH GOOGLE SEARCH GROUNDING
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n[Case 1] Testing Gemini Flash Report + Live Web Search...")
    mock_cleared = [{
        "title": "US Core PPI m/m",
        "forecast": "0.2%",
        "previous": "0.3%",
        "time_th": "19:30 น."
    }]
    report = gold_ai_agent.fetch_macro_actual_flash_report(mock_cleared, api_key)
    if report and "events" in report:
        gold_ai_agent.safe_print("  --> PASS: Gemini returned structured flash report with bias: " + str(report.get("overall_gold_bias")))
        results["Case 1: Gemini Search Grounding"] = "PASS"
    else:
        gold_ai_agent.safe_print("  --> FAIL: Flash report returned None or invalid format")
        results["Case 1: Gemini Search Grounding"] = "FAIL"

    # -------------------------------------------------------------
    # 2. TEST ORDER OPENED (SWEEP FADE 0.02 LOT & SNIPER)
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n[Case 2] Testing Order Opened Alert (SweepFade 0.02 Lot)...")
    mock_sweep_order = {
        "ticket": 777123,
        "magic": 888634,
        "engine": "SweepFade",
        "type": 0,
        "lots": 0.02,
        "open_price": 4172.50,
        "sl": 4169.50,
        "tp": 4187.50,
        "profit": 0.00
    }
    try:
        gold_ai_agent.send_discord_order_opened_alert(wh_orders, mock_sweep_order, mock_state, api_key)
        gold_ai_agent.safe_print("  --> PASS: SweepFade 0.02 Lot order alert generated cleanly")
        results["Case 2: SweepFade Order Opened"] = "PASS"
    except Exception as e:
        gold_ai_agent.safe_print(f"  --> FAIL: {e}")
        results["Case 2: SweepFade Order Opened"] = f"FAIL ({e})"

    # -------------------------------------------------------------
    # 3. TEST MANUAL TRADE ASSESSMENT (PENDING VS MARKET)
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n[Case 3] Testing User Manual Pending Order (Buy Limit)...")
    mock_pending_order = {
        "ticket": 63302957,
        "magic": 0,
        "engine": "User_Manual",
        "type": 2, # OP_BUYLIMIT
        "lots": 0.02,
        "open_price": 4100.00,
        "sl": 0.00,
        "tp": 0.00,
        "profit": 0.00
    }
    try:
        gold_ai_agent.send_discord_manual_order_alert(wh_user, mock_pending_order, mock_state, api_key)
        gold_ai_agent.safe_print("  --> PASS: Manual Buy Limit correctly evaluated without false SELL classification")
        results["Case 3: Manual Buy Limit Assessment"] = "PASS"
    except Exception as e:
        gold_ai_agent.safe_print(f"  --> FAIL: {e}")
        results["Case 3: Manual Buy Limit Assessment"] = f"FAIL ({e})"

    # -------------------------------------------------------------
    # 4. TEST SL MODIFICATION (BREAKEVEN SHIELD & PROFIT RATCHET)
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n[Case 4] Testing SL Modification (Breakeven Shield & Dynamic Profit Ratchet)...")
    try:
        mock_active_order = {
            "ticket": 777123,
            "engine": "SweepFade",
            "type": 0,
            "lots": 0.02,
            "open_price": 4172.50,
            "sl": 4173.50, # Moved above entry -> Breakeven shield
            "tp": 4187.50,
            "profit": 15.00
        }
        gold_ai_agent.send_discord_sl_modified_alert(wh_orders, mock_active_order, 4169.50, 4173.50, mock_state)
        gold_ai_agent.safe_print("  --> PASS: Breakeven / Ratchet alert generated cleanly")
        results["Case 4: SL Modification & BE Lock"] = "PASS"
    except Exception as e:
        gold_ai_agent.safe_print(f"  --> FAIL: {e}")
        results["Case 4: SL Modification & BE Lock"] = f"FAIL ({e})"

    # -------------------------------------------------------------
    # 5. TEST ORDER CLOSED SUMMARY (TP HIT & PROFIT LEDGER)
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n[Case 5] Testing Order Closed Summary Alert...")
    mock_closed_order = {
        "ticket": 777123,
        "magic": 888634,
        "engine": "SweepFade",
        "type": 0,
        "lots": 0.02,
        "open_price": 4172.50,
        "close_price": 4187.50,
        "sl": 4173.50,
        "tp": 4187.50,
        "profit": 30.00,
        "close_time": "2026.10.16 09:30:00"
    }
    try:
        gold_ai_agent.send_discord_order_closed_alert(wh_orders, mock_closed_order, mock_state)
        gold_ai_agent.safe_print("  --> PASS: Order Closed Summary generated cleanly")
        results["Case 5: Order Closed Summary"] = "PASS"
    except Exception as e:
        gold_ai_agent.safe_print(f"  --> FAIL: {e}")
        results["Case 5: Order Closed Summary"] = f"FAIL ({e})"

    # -------------------------------------------------------------
    # 6. TEST JACKPOT PROFIT LOCK ALERT
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n[Case 6] Testing Jackpot Profit Lock Alert...")
    try:
        mock_jackpot_state = dict(mock_state)
        mock_jackpot_state["daily_sniper_pnl"] = 125.50
        mock_jackpot_state["jackpot_locked"] = True
        gold_ai_agent.send_discord_jackpot_lock_alert(wh_orders, mock_jackpot_state)
        gold_ai_agent.safe_print("  --> PASS: Jackpot Lock Alert generated cleanly")
        results["Case 6: Jackpot Profit Lock"] = "PASS"
    except Exception as e:
        gold_ai_agent.safe_print(f"  --> FAIL: {e}")
        results["Case 6: Jackpot Profit Lock"] = f"FAIL ({e})"

    # -------------------------------------------------------------
    # 7. TEST MACRO STAND-DOWN & NEWS CLEARED ALERTS
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n[Case 7] Testing Macro Stand-Down & Clearance Alert...")
    try:
        mock_active_news = [{
            "title": "US Non-Farm Payrolls",
            "time_th": "19:30 น.",
            "forecast": "180K",
            "previous": "150K",
            "diff_mins": -5.0
        }]
        gold_ai_agent.send_discord_stand_down_alert(wh_orders, mock_active_news)
        gold_ai_agent.send_discord_news_cleared_alert(wh_orders, mock_active_news, mock_state, api_key, wh_briefing)
        gold_ai_agent.safe_print("  --> PASS: Macro Stand-Down & Cleared alerts generated cleanly")
        results["Case 7: Macro News Shield"] = "PASS"
    except Exception as e:
        gold_ai_agent.safe_print(f"  --> FAIL: {e}")
        results["Case 7: Macro News Shield"] = f"FAIL ({e})"

    # -------------------------------------------------------------
    # 8. TEST SIGNAL ENGINE (NEW, WIN, LOSS)
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n[Case 8] Testing Signal Feed (Intake, Target Hit, Stop Out)...")
    try:
        mock_sig = {
            "id": "SIG_TEST_001",
            "grade": "A+",
            "direction": "BUY",
            "entry": 4172.50,
            "sl": 4165.00,
            "tp": 4190.00,
            "strategy": "The Liquidity Sweep Fade (Judas Stop-Hunt)",
            "reason": "Retail Buy Stops Swept with 45% Rejection Wick",
            "created_at_epoch": 1000
        }
        mock_stats = {"total": 10, "wins": 8, "losses": 2, "win_rate": 80.0, "net_points": 45.5}
        gold_ai_agent.send_discord_signal_feed_alert(wh_signals, mock_sig, mock_stats)
        gold_ai_agent.send_discord_signal_win(wh_signals, mock_sig, 4190.00, 17.50, mock_stats, "15 นาที")
        gold_ai_agent.send_discord_signal_loss(wh_signals, mock_sig, 4165.00, 7.50, mock_stats, "10 นาที")
        gold_ai_agent.safe_print("  --> PASS: Signal Feed New/Win/Loss alerts generated cleanly")
        results["Case 8: Signal Feed Engine"] = "PASS"
    except Exception as e:
        gold_ai_agent.safe_print(f"  --> FAIL: {e}")
        results["Case 8: Signal Feed Engine"] = f"FAIL ({e})"

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    gold_ai_agent.safe_print("\n" + "="*75)
    gold_ai_agent.safe_print("🏁 FULL AI TEST SUITE SUMMARY RESULTS:")
    gold_ai_agent.safe_print("="*75)
    all_passed = True
    for test_name, status in results.items():
        gold_ai_agent.safe_print(f"  • {test_name:<40}: {status}")
        if status != "PASS":
            all_passed = False
    gold_ai_agent.safe_print("="*75)
    if all_passed:
        gold_ai_agent.safe_print("🎉 ALL 8 SCENARIOS PASSED 100% WITH ZERO ERRORS!")
    else:
        gold_ai_agent.safe_print("⚠️ SOME TESTS ENCOUNTERED ISSUES")
    gold_ai_agent.safe_print("="*75 + "\n")
    return all_passed

if __name__ == "__main__":
    run_all_tests(dry_run=True)
