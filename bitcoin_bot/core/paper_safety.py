"""Persistent paper-only accounting; this module never sends exchange orders."""

from __future__ import annotations

import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class PaperBook:
    def __init__(self, path: str | Path, initial_equity: float = 10_000.0):
        self.path = Path(path)
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
            if self.state.get("version") != 1 or self.state.get("equity", 0) <= 0:
                raise ValueError("Invalid paper state; inspect it before restarting")
        else:
            self.state = {
                "version": 1, "equity": float(initial_equity),
                "day": None, "day_start_equity": float(initial_equity),
                "day_trades": 0, "consecutive_losses": 0,
                "position": None, "last_signal_bar": {}, "closed_trades": [],
            }
            self._save()

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".paper-", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(self.state, file, ensure_ascii=False, indent=2, allow_nan=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _date(now: datetime) -> str:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("A timezone-aware timestamp is required")
        return now.astimezone(timezone.utc).date().isoformat()

    def _new_day(self, now: datetime) -> None:
        day = self._date(now)
        if self.state["day"] != day:
            self.state["day"] = day
            self.state["day_start_equity"] = self.state["equity"]
            self.state["day_trades"] = 0
            self.state["consecutive_losses"] = 0
            self._save()

    def can_open(self, now: datetime) -> tuple[bool, str]:
        self._new_day(now)
        state = self.state
        if state["position"] is not None:
            return False, "POSITION_OPEN"
        if state["equity"] <= state["day_start_equity"] * 0.99:
            return False, "DAILY_LOSS_LIMIT"
        if state["day_trades"] >= 4:
            return False, "MAX_DAILY_TRADES"
        if state["consecutive_losses"] >= 2:
            return False, "CONSECUTIVE_LOSSES"
        return True, "OK"

    def open_long(self, symbol: str, ask: float, now: datetime,
                  signal_bar_ms: int) -> tuple[bool, str]:
        allowed, reason = self.can_open(now)
        if not allowed:
            return False, reason
        if not math.isfinite(ask) or ask <= 0:
            return False, "INVALID_ASK"
        if signal_bar_ms <= self.state["last_signal_bar"].get(symbol, -1):
            return False, "SIGNAL_BAR_ALREADY_USED"
        entry = ask * 1.0002  # adverse simulated entry slippage
        notional = min(self.state["equity"], self.state["equity"] * 0.0025 / 0.0035)
        self.state["position"] = {
            "symbol": symbol, "entry": entry, "stop": entry * 0.9975,
            "target": entry * 1.007, "quantity": notional / entry,
            "notional": notional, "opened_at": now.isoformat(),
            "signal_bar_ms": signal_bar_ms,
        }
        self.state["last_signal_bar"][symbol] = signal_bar_ms
        self._save()
        return True, "PAPER_POSITION_OPENED"

    def on_bid(self, bid: float, now: datetime) -> dict | None:
        position = self.state["position"]
        if position is None:
            return None
        self._date(now)
        if not math.isfinite(bid) or bid <= 0:
            raise ValueError("Invalid market bid")
        opened = datetime.fromisoformat(position["opened_at"])
        if now < opened:
            raise ValueError("Quote precedes entry")
        if bid <= position["stop"]:
            reason, reference = "STOP", bid  # gap may be worse than stop
        elif bid >= position["target"]:
            reason, reference = "TARGET", position["target"]
        elif (now - opened).total_seconds() >= 3600:
            reason, reference = "TIME", bid
        else:
            return None
        exit_price = reference * 0.9998  # adverse simulated exit slippage
        pnl = position["quantity"] * (exit_price - position["entry"])
        pnl -= position["notional"] * 0.0008  # assumed round-trip fees
        self._new_day(now)
        self.state["equity"] += pnl
        self.state["day_trades"] += 1
        self.state["consecutive_losses"] = self.state["consecutive_losses"] + 1 if pnl < 0 else 0
        closed = {
            "symbol": position["symbol"], "opened_at": position["opened_at"],
            "closed_at": now.isoformat(), "reason": reason,
            "entry": position["entry"], "exit": exit_price,
            "notional": position["notional"], "pnl": pnl,
            "equity_after": self.state["equity"],
        }
        self.state["closed_trades"].append(closed)
        self.state["position"] = None
        self._save()
        return closed
