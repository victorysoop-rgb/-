import ta


def calculate_long_breakout_score(df, regime):

    score = 0
    details = []

    df["EMA9"] = ta.trend.ema_indicator(df["close"], window=9)
    df["EMA20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["RSI"] = ta.momentum.rsi(df["close"], window=14)
    df["VOL_AVG"] = df["volume"].rolling(20).mean()

    last = df.iloc[-1]

    if regime == "UPTREND":
        score += 20
        details.append("Regime UPTREND +20")
    else:
        details.append("Regime not UPTREND +0")

    if last["EMA9"] > last["EMA20"]:
        score += 20
        details.append("EMA9 > EMA20 +20")
    else:
        details.append("EMA trend weak +0")

    if 45 <= last["RSI"] <= 65:
        score += 15
        details.append("RSI good +15")
    elif 40 <= last["RSI"] <= 70:
        score += 7
        details.append("RSI acceptable +7")
    else:
        details.append("RSI bad +0")

    if last["volume"] > last["VOL_AVG"] * 1.2:
        score += 20
        details.append("Volume strong +20")
    elif last["volume"] > last["VOL_AVG"] * 1.05:
        score += 12
        details.append("Volume ok +12")
    else:
        details.append("Volume weak +0")

    recent_high = df["high"].rolling(8).max().iloc[-2]

    if last["high"] > recent_high:
        score += 25
        details.append("Breakout +25")
    else:
        details.append("No breakout +0")

    if score >= 85:
        signal = "STRONG_BUY"
    elif score >= 75:
        signal = "BUY"
    elif score >= 60:
        signal = "WATCH"
    else:
        signal = "NO_TRADE"

    return {
        "score": score,
        "signal": signal,
        "details": details
    }


def calculate_short_pullback_score(df, regime):

    score = 0
    details = []

    df["EMA9"] = ta.trend.ema_indicator(df["close"], window=9)
    df["EMA20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["EMA50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["RSI"] = ta.momentum.rsi(df["close"], window=14)
    df["VOL_AVG"] = df["volume"].rolling(20).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    if regime == "DOWNTREND":
        score += 25
        details.append("Regime DOWNTREND +25")
    else:
        details.append("Regime not DOWNTREND +0")

    if last["EMA9"] < last["EMA20"] < last["EMA50"]:
        score += 25
        details.append("EMA bearish alignment +25")
    elif last["EMA9"] < last["EMA20"]:
        score += 12
        details.append("EMA short-term bearish +12")
    else:
        details.append("EMA bearish weak +0")

    pullback = (
        last["high"] >= last["EMA20"] * 0.998
        and last["close"] < last["EMA20"]
    )

    if pullback:
        score += 20
        details.append("Pullback to EMA20 +20")
    else:
        details.append("No EMA20 pullback +0")

    rejection = (
        last["close"] < last["open"]
        and last["close"] < prev["close"]
    )

    if rejection:
        score += 15
        details.append("Bearish rejection candle +15")
    else:
        details.append("No bearish rejection +0")

    if 35 <= last["RSI"] <= 55:
        score += 10
        details.append("RSI short zone +10")
    elif 30 <= last["RSI"] <= 60:
        score += 5
        details.append("RSI acceptable +5")
    else:
        details.append("RSI bad +0")

    if last["volume"] >= last["VOL_AVG"] * 0.8:
        score += 5
        details.append("Volume acceptable +5")
    else:
        details.append("Volume weak +0")

    if score >= 85:
        signal = "STRONG_SELL"
    elif score >= 75:
        signal = "SELL"
    elif score >= 60:
        signal = "WATCH"
    else:
        signal = "NO_TRADE"

    return {
        "score": score,
        "signal": signal,
        "details": details
    }