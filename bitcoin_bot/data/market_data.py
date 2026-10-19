import ccxt
import pandas as pd
import time

exchange = ccxt.binance({
    "enableRateLimit": True,
    # CCXT defaults to ignoring the runtime's proxy and CA configuration.
    # Requests can use both while retaining TLS verification when enabled.
    "requests_trust_env": True,
    "options": {
        "defaultType": "spot",
        "fetchMarkets": {"types": ["spot"]},
        "fetchCurrencies": False,
        "fetchMargins": False,
    },
})
# Binance's market-data-only host serves public spot endpoints. It does not
# accept private order calls, which also keeps this paper bot read-only.
exchange.urls["api"]["public"] = "https://data-api.binance.vision/api/v3"

def timeframe_to_ms(timeframe):
    unit = timeframe[-1]
    value = int(timeframe[:-1])

    if unit == "m":
        return value * 60 * 1000

    if unit == "h":
        return value * 60 * 60 * 1000

    if unit == "d":
        return value * 24 * 60 * 60 * 1000

    raise ValueError("지원하지 않는 timeframe입니다.")

def get_market_data(symbol, timeframe="5m", limit=10000):

    all_bars = []

    tf_ms = timeframe_to_ms(timeframe)

    now = exchange.milliseconds()

    since = now - (limit * tf_ms)

    while len(all_bars) < limit:

        fetch_limit = min(1000, limit - len(all_bars))

        bars = exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            since=since,
            limit=fetch_limit
        )

        if not bars:
            break

        all_bars.extend(bars)

        since = bars[-1][0] + tf_ms

        time.sleep(0.2)

        if len(bars) < fetch_limit:
            break

    df = pd.DataFrame(
        all_bars,
        columns=[
            "time",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    )

    df = df.drop_duplicates(subset=["time"])
    df = df.sort_values("time")
    df = df.tail(limit)

    # 마지막 진행 중인 캔들 제거
    now = exchange.milliseconds()

    if len(df) > 0:
        last_candle_time = df.iloc[-1]["time"]

        if now < last_candle_time + tf_ms:
            df = df.iloc[:-1]

    return df
