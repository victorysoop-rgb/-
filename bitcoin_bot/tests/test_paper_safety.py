import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.paper_safety import PaperBook


class PaperBookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "state.json"
        self.now = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)

    def test_restart_preserves_position_and_prevents_duplicate_signal(self):
        book = PaperBook(self.path)
        self.assertTrue(book.open_long("BTC/USDT", 100, self.now, 1000)[0])
        restarted = PaperBook(self.path)
        self.assertEqual(restarted.can_open(self.now)[1], "POSITION_OPEN")
        self.assertEqual(restarted.on_bid(101, self.now + timedelta(minutes=1))["reason"], "TARGET")
        self.assertEqual(restarted.open_long("BTC/USDT", 100, self.now, 1000)[1],
                         "SIGNAL_BAR_ALREADY_USED")

    def test_stop_gap_and_loss_streak(self):
        book = PaperBook(self.path)
        for bar in (1000, 2000):
            self.assertTrue(book.open_long("BTC/USDT", 100, self.now, bar)[0])
            closed = book.on_bid(99.6, self.now + timedelta(minutes=1))
            self.assertEqual(closed["reason"], "STOP")
            self.assertLess(closed["exit"], 99.6)
        self.assertEqual(book.can_open(self.now)[1], "CONSECUTIVE_LOSSES")

    def test_corrupt_state_is_not_reset(self):
        self.path.write_text('{"version":0,"equity":10000}', encoding="utf-8")
        with self.assertRaises(ValueError):
            PaperBook(self.path)


if __name__ == "__main__":
    unittest.main()
