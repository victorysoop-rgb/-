"""Paper-only Phoenix decision bot. No exchange orders or API keys are used."""

from __future__ import annotations

import argparse
import fcntl
import math
import time
from datetime import datetime, timezone
from pathlib import Path

from core.paper_safety import PaperBook


SYMBOLS = ("BTC/USDT", "ETH/USDT", "SOL/USDT")
TIMEFRAME_MS = 300_000


def quote_prices(ticker: dict, now: datetime) -> tuple[float, float]:
    timestamp = ticker.get("timestamp")
    if timestamp is not None and abs(now.timestamp() * 1000 - float(timestamp)) > 90_000:
        raise ValueError("Stale market quote")
    bid, ask = float(ticker["bid"]), float(ticker["ask"])
    if not all(math.isfinite(x) and x > 0 for x in (bid, ask)):
        raise ValueError("Invalid market quote")
    if ask < bid or (ask - bid) / ((ask + bid) / 2) > 0.002:
        raise ValueError("Wide or crossed market spread")
    return bid, ask


def run_cycle(book: PaperBook) -> str:
    from data.market_data import exchange, get_market_data
    from core.market_strength import calculate_coin_strength_scores, calculate_price_change
    from core.phoenix_score import calculate_phoenix_score
    from core.score_engine import calculate_long_breakout_score
    from strategy.market_regime_v2 import classify_market_regime

    now = datetime.now(timezone.utc)
    position = book.state["position"]
    if position is not None:
        bid, _ = quote_prices(exchange.fetch_ticker(position["symbol"]), now)
        closed = book.on_bid(bid, now)
        if closed:
            return f"CLOSED {closed['symbol']} {closed['reason']} PnL={closed['pnl']:.2f}"
        return f"HOLD {position['symbol']} observed_bid={bid:.8f}"

    allowed, reason = book.can_open(now)
    if not allowed:
        return f"NO_TRADE {reason}"
    market = {}
    for symbol in SYMBOLS:
        candles = get_market_data(symbol, timeframe="5m", limit=300)
        if len(candles) >= 250:
            market[symbol] = candles
    if not market:
        return "NO_TRADE insufficient closed candles"
    changes = {symbol: calculate_price_change(df, lookback=12)
               for symbol, df in market.items()}
    strength = calculate_coin_strength_scores(changes, "LONG")
    candidates = []
    for symbol, candles in market.items():
        signal_bar_ms = int(candles.iloc[-1]["time"])
        age_ms = int(now.timestamp() * 1000) - (signal_bar_ms + TIMEFRAME_MS)
        if age_ms < 0 or age_ms > 180_000:
            continue
        if signal_bar_ms <= book.state["last_signal_bar"].get(symbol, -1):
            continue
        regime = classify_market_regime(symbol)
        long_result = calculate_long_breakout_score(candles.copy(), regime)
        if regime != "UPTREND" or long_result["signal"] != "STRONG_BUY":
            continue
        phoenix = calculate_phoenix_score(
            symbol=symbol, strategy_type="LONG", regime=regime,
            strategy_score=long_result["score"], coin_strength_score=strength[symbol],
            volatility_score=5, liquidity_score=8, recent_performance_score=5,
        )
        # The original fixed inputs cap Phoenix at 88, below its 90 trade
        # threshold. The breakout signal gates this paper experiment; Phoenix
        # only ranks candidates. Its profitability remains unverified.
        candidates.append((phoenix["phoenix_score"], symbol, signal_bar_ms))
    if not candidates:
        return "NO_TRADE no fresh long breakout in uptrend"

    _, symbol, signal_bar_ms = max(candidates)
    _, ask = quote_prices(exchange.fetch_ticker(symbol), now)
    opened, reason = book.open_long(symbol, ask, now, signal_bar_ms)
    if opened:
        return f"PAPER_OPEN {symbol} ask={ask:.8f} signal_bar={signal_bar_ms}"
    return f"NO_TRADE {reason}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=Path("paper_state.json"))
    parser.add_argument("--loop", action="store_true", help="Repeat every 60 seconds")
    args = parser.parse_args()
    lock_path = args.state.with_suffix(args.state.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(2, f"Another paper bot uses {args.state}\n")
        book = PaperBook(args.state)
        while True:
            try:
                print(datetime.now(timezone.utc).isoformat(), run_cycle(book), flush=True)
            except Exception as exc:
                print(datetime.now(timezone.utc).isoformat(), "DATA_ERROR", repr(exc), flush=True)
                if not args.loop:
                    parser.exit(2)
            if not args.loop:
                break
            time.sleep(60)


if __name__ == "__main__":
    main()
