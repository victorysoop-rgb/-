import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from core.paper_safety import PaperBook
from paper_decision_bot_safe import quote_prices, run_cycle


class SafeDecisionBotTests(unittest.TestCase):
    def test_stale_and_wide_quote_rejected(self):
        now = datetime(2026, 7, 1, tzinfo=timezone.utc)
        with self.assertRaises(ValueError):
            quote_prices({"bid": 100, "ask": 100.1, "timestamp": 0}, now)
        with self.assertRaises(ValueError):
            quote_prices({"bid": 100, "ask": 101}, now)

    def test_public_market_data_host(self):
        from data.market_data import exchange
        self.assertEqual(exchange.urls["api"]["public"],
                         "https://data-api.binance.vision/api/v3")
        self.assertTrue(exchange.session.trust_env)
        self.assertTrue(exchange.verify)
        self.assertEqual(exchange.options["fetchMarkets"]["types"], ["spot"])

    def test_fresh_closed_bar_opens_only_paper_position(self):
        with tempfile.TemporaryDirectory() as directory:
            book = PaperBook(Path(directory) / "state.json")
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            bar_time = now_ms - 360_000
            candles = pd.DataFrame({
                "time": [bar_time - (299 - i) * 300_000 for i in range(300)],
                "close": [100.0] * 300,
            })
            with (
                patch("data.market_data.get_market_data", return_value=candles),
                patch("data.market_data.exchange.fetch_ticker", return_value={"bid": 100.0, "ask": 100.01}),
                patch("strategy.market_regime_v2.classify_market_regime", return_value="UPTREND"),
                patch("core.score_engine.calculate_long_breakout_score", return_value={"signal": "STRONG_BUY", "score": 90}),
                patch("core.phoenix_score.calculate_phoenix_score", return_value={"phoenix_score": 85}),
            ):
                result = run_cycle(book)
            self.assertIn("PAPER_OPEN", result)
            self.assertEqual(book.state["position"]["signal_bar_ms"], bar_time)


if __name__ == "__main__":
    unittest.main()
