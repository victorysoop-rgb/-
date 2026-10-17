import pandas as pd
import ta

from data.market_data import get_market_data


def get_latest_row(df, current_time):
    past = df[df["time"] <= current_time]

    if len(past) == 0:
        return None

    return past.iloc[-1]


def classify_market_regime(symbol="ETH/USDT"):

    df_1h = get_market_data(
        symbol,
        timeframe="1h",
        limit=300
    )

    df_4h = get_market_data(
        symbol,
        timeframe="4h",
        limit=300
    )

    current_time = df_1h.iloc[-1]["time"]

    df_1h["EMA20"] = ta.trend.ema_indicator(
        df_1h["close"],
        window=20
    )

    df_1h["EMA50"] = ta.trend.ema_indicator(
        df_1h["close"],
        window=50
    )

    df_1h["ADX"] = ta.trend.adx(
        df_1h["high"],
        df_1h["low"],
        df_1h["close"],
        window=14
    )

    df_4h["EMA50"] = ta.trend.ema_indicator(
        df_4h["close"],
        window=50
    )

    df_4h["EMA200"] = ta.trend.ema_indicator(
        df_4h["close"],
        window=200
    )

    row_1h = get_latest_row(df_1h, current_time)
    row_4h = get_latest_row(df_4h, current_time)

    if row_1h is None or row_4h is None:
        return "UNKNOWN"

    if (
        pd.isna(row_1h["EMA20"])
        or pd.isna(row_1h["EMA50"])
        or pd.isna(row_1h["ADX"])
        or pd.isna(row_4h["EMA50"])
        or pd.isna(row_4h["EMA200"])
    ):
        return "UNKNOWN"

    trend_4h_up = row_4h["EMA50"] > row_4h["EMA200"]
    trend_4h_down = row_4h["EMA50"] < row_4h["EMA200"]

    trend_1h_up = row_1h["EMA20"] > row_1h["EMA50"]
    trend_1h_down = row_1h["EMA20"] < row_1h["EMA50"]

    strong_trend = row_1h["ADX"] >= 20
    weak_trend = row_1h["ADX"] < 20

    if trend_4h_up and trend_1h_up and strong_trend:
        return "UPTREND"

    if trend_4h_down and trend_1h_down and strong_trend:
        return "DOWNTREND"

    if weak_trend:
        return "RANGE"

    return "WEAK"