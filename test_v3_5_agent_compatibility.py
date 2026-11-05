# ==============================================================================
# QA/QC Compatibility Suite: Gold POI Sniper v3.5 & AI Sentinel Python Bridge
# ==============================================================================

import os
import sys
import json
import unittest
from datetime import datetime as dt, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import gold_ai_agent_poi_v3_5 as agent_v35

class TestGoldPOISniperV35Compatibility(unittest.TestCase):

    def setUp(self):
        self.config = agent_v35.load_poi_config()
        self.mt4_files_dir = self.config.get("mt4_files_dir", "")

    def test_01_version_and_magics(self):
        """Verify v3.5 version branding and 3-engine magic configuration"""
        self.assertIn("v3.5", agent_v35.VERSION)
        self.assertEqual(agent_v35.MAGIC_POI, 778899)
        self.assertEqual(agent_v35.MAGIC_LONDON_SNIPER, 778832)
        self.assertEqual(agent_v35.MAGIC_JUDAS_SWEEP, 778834)
        self.assertEqual(len(agent_v35.BOT_MAGICS), 3)

    def test_02_order_engine_classification(self):
        """Verify strict engine classification for Bot vs User Manual orders"""
        ld_order = {"ticket": 1001, "magic": 778832, "engine": "London Sniper", "type": 0, "profit": 50.0}
        sw_order = {"ticket": 1002, "magic": 778834, "engine": "Judas Sweep Fade", "type": 1, "profit": -10.0}
        ny_order = {"ticket": 1003, "magic": 778899, "engine": "POI NY Sniper", "type": 0, "profit": 120.0}
        user_order = {"ticket": 1004, "magic": 0, "engine": "User Manual", "type": 0, "profit": -40.0}
        pend_order = {"ticket": 1005, "magic": 0, "engine": "User Manual", "type": 3, "profit": 0.0}

        self.assertTrue(agent_v35.is_bot_order(ld_order))
        self.assertTrue(agent_v35.is_bot_order(sw_order))
        self.assertTrue(agent_v35.is_bot_order(ny_order))
        self.assertFalse(agent_v35.is_bot_order(user_order))
        self.assertFalse(agent_v35.is_bot_order(pend_order))

        self.assertEqual(agent_v35.get_engine_name(ld_order), "London Sniper")
        self.assertEqual(agent_v35.get_engine_name(sw_order), "Judas Sweep Fade")
        self.assertEqual(agent_v35.get_engine_name(ny_order), "POI NY Sniper")
        self.assertEqual(agent_v35.get_engine_name(user_order), "User Manual")

    def test_03_streak_breaker_protective_scaling(self):
        """Verify AI Streak Breaker risk multiplier dynamics with noise filtering"""
        # Test 1: Empty closed orders -> 1.0x
        losses, mult, reason = agent_v35.evaluate_streak_breaker([])
        self.assertEqual(losses, 0)
        self.assertEqual(mult, 1.0)

        # Test 2: 1 Bot loss -> 1.0x
        trades_1_loss = [
            {"ticket": 1, "magic": 778832, "profit": -50.0, "close_time": "2026.11.02 09:30:00"}
        ]
        losses, mult, reason = agent_v35.evaluate_streak_breaker(trades_1_loss)
        self.assertEqual(losses, 1)
        self.assertEqual(mult, 1.0)

        # Test 3: 2 Bot losses in a row -> Halve risk to 0.50x
        trades_2_losses = [
            {"ticket": 2, "magic": 778899, "profit": -80.0, "close_time": "2026.11.02 16:30:00"},
            {"ticket": 1, "magic": 778832, "profit": -50.0, "close_time": "2026.11.02 09:30:00"}
        ]
        losses, mult, reason = agent_v35.evaluate_streak_breaker(trades_2_losses)
        self.assertEqual(losses, 2)
        self.assertEqual(mult, 0.50)

        # Test 4: 3 Bot losses in a row -> Quarter risk to 0.25x
        trades_3_losses = [
            {"ticket": 3, "magic": 778834, "profit": -20.0, "close_time": "2026.11.02 17:00:00"},
            {"ticket": 2, "magic": 778899, "profit": -80.0, "close_time": "2026.11.02 16:30:00"},
            {"ticket": 1, "magic": 778832, "profit": -50.0, "close_time": "2026.11.02 09:30:00"}
        ]
        losses, mult, reason = agent_v35.evaluate_streak_breaker(trades_3_losses)
        self.assertEqual(losses, 3)
        self.assertEqual(mult, 0.25)

        # Test 5: Manual trades mixed in -> MUST NOT increment bot streak!
        trades_mixed = [
            {"ticket": 99, "magic": 0, "engine": "User Manual", "profit": -500.0, "close_time": "2026.11.02 18:00:00"},
            {"ticket": 2, "magic": 778899, "profit": -80.0, "close_time": "2026.11.02 16:30:00"},
            {"ticket": 1, "magic": 778832, "profit": -50.0, "close_time": "2026.11.02 09:30:00"}
        ]
        losses, mult, reason = agent_v35.evaluate_streak_breaker(trades_mixed)
        self.assertEqual(losses, 2) # Only the 2 bot trades counted
        self.assertEqual(mult, 0.50)

        # Test 6: Recent win -> Resets back to 1.0x
        trades_recovered = [
            {"ticket": 4, "magic": 778832, "profit": 250.0, "close_time": "2026.11.02 19:00:00"},
            {"ticket": 3, "magic": 778834, "profit": -20.0, "close_time": "2026.11.02 17:00:00"},
            {"ticket": 2, "magic": 778899, "profit": -80.0, "close_time": "2026.11.02 16:30:00"}
        ]
        losses, mult, reason = agent_v35.evaluate_streak_breaker(trades_recovered)
        self.assertEqual(losses, 0)
        self.assertEqual(mult, 1.0)

    def test_04_session_timing_accuracy(self):
        """Verify precision session boundaries matching v3.5 architecture"""
        # 02:00 MT4 -> Asian Range Discovery
        s_name, _, _ = agent_v35.get_poi_session_info("2026.11.02 02:15:00")
        self.assertIn("Asian", s_name)

        # 06:30 MT4 -> London Asian Box Fixation
        s_name, _, _ = agent_v35.get_poi_session_info("2026.11.02 06:30:00")
        self.assertIn("London Asian Range Box", s_name)

        # 09:15 MT4 -> London Dual-Engine Active
        s_name, _, _ = agent_v35.get_poi_session_info("2026.11.02 09:15:00")
        self.assertIn("London Dual-Engine", s_name)

        # 13:00 MT4 -> European Standby
        s_name, _, _ = agent_v35.get_poi_session_info("2026.11.02 13:00:00")
        self.assertIn("European Standby", s_name)

        # 16:30 MT4 -> New York Institutional Open
        s_name, _, _ = agent_v35.get_poi_session_info("2026.11.02 16:30:00")
        self.assertIn("New York Institutional Open", s_name)

        # 19:00 MT4 -> New York Late Trend
        s_name, _, _ = agent_v35.get_poi_session_info("2026.11.02 19:00:00")
        self.assertIn("New York Late Trend", s_name)

        # 22:00 MT4 -> Daily Session Closed / Rollover
        s_name, _, _ = agent_v35.get_poi_session_info("2026.11.02 22:00:00")
        self.assertIn("Rollover", s_name)

    def test_05_sentinel_json_payload_integrity(self):
        """Verify ai_sentinel_poi.json exists, is valid JSON, and contains all required keys"""
        poi_sentinel_path = os.path.join(self.mt4_files_dir, "ai_sentinel_poi.json")
        self.assertTrue(os.path.exists(poi_sentinel_path), f"Missing {poi_sentinel_path}")

        with open(poi_sentinel_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = [
            "version", "stand_down", "ai_risk_multiplier", "base_risk_multiplier",
            "consecutive_losses", "streak_status", "poi_bias", "breaking_headline",
            "active_news_count", "balance", "equity", "timestamp"
        ]
        for key in required_keys:
            self.assertIn(key, data, f"Missing key '{key}' in sentinel payload")

        self.assertIn("v3.5", data["version"])
        self.assertIsInstance(data["stand_down"], bool)
        self.assertIsInstance(data["ai_risk_multiplier"], (int, float))

    def test_06_market_state_parsing(self):
        """Verify live market_state.json exported by MT4 is valid and parsable"""
        state_path = os.path.join(self.mt4_files_dir, "market_state.json")
        self.assertTrue(os.path.exists(state_path), f"Missing {state_path}")

        with open(state_path, "r", encoding="utf-8") as f:
            st = json.load(f)

        self.assertIn("symbol", st)
        self.assertIn("balance", st)
        self.assertIn("equity", st)
        self.assertIn("open_orders", st)
        self.assertIn("recent_closed_orders", st)

    def test_07_binaries_and_compilation(self):
        """Verify Gold_POI_Sniper_Master_v3_5.ex4 is present in MT4 Experts"""
        experts_dir = r"C:\Users\Kritnarin\AppData\Roaming\MetaQuotes\Terminal\50CA3DFB510CC5A8F28B48D1BF2A5702\MQL4\Experts"
        ex4_master = os.path.join(experts_dir, "Gold_POI_Sniper_Master_v3_5.ex4")
        self.assertTrue(os.path.exists(ex4_master), f"Missing compiled binary {ex4_master}")

    def test_08_upcoming_major_red_events_and_election_radar(self):
        """Verify ForexFactory High-Impact Red Events & US Election Radar summary"""
        now_thai = dt.now(timezone(timedelta(hours=7)))
        summary = agent_v35.get_upcoming_major_red_events_summary(now_thai)
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 10)
        self.assertIn("election", agent_v35.base_agent.BREAKING_GOLD_MACRO_KEYWORDS)
        self.assertIn("congress", agent_v35.base_agent.BREAKING_GOLD_MACRO_KEYWORDS)
        self.assertIn("trump", agent_v35.base_agent.BREAKING_GOLD_MACRO_KEYWORDS)

    def test_09_wall_clock_slots_and_30min_config(self):
        """Verify 3-Hour Quant Slots and 30-min News Guard config"""
        expected_slots = ["02:00", "05:00", "08:00", "11:00", "14:00", "17:00", "20:00", "23:00"]
        self.assertEqual(agent_v35.QUANT_3H_SLOTS, expected_slots)
        self.assertEqual(self.config.get("news_stand_down_mins_before"), 30)
        self.assertEqual(self.config.get("news_stand_down_mins_after"), 30)

    def test_10_quant_5_sciences_keys_complete(self):
        """Verify compute_5_sciences_quant returns prev_high, prev_low, elliott_wave"""
        state_path = os.path.join(self.mt4_files_dir, "market_state.json")
        with open(state_path, "r", encoding="utf-8") as f:
            st = json.load(f)
        qd = agent_v35.base_agent.compute_5_sciences_quant(self.mt4_files_dir, "GOLD", st, float(st.get("bid", 3900.0)))
        self.assertIn("prev_high", qd)
        self.assertIn("prev_low", qd)
        self.assertIn("elliott_wave", qd)
        self.assertGreater(qd["prev_high"], 0)
        self.assertGreater(qd["prev_low"], 0)

if __name__ == "__main__":
    unittest.main()
