def calculate_phoenix_score(
    symbol,
    strategy_type,
    regime,
    strategy_score,
    coin_strength_score=0,
    volatility_score=0,
    liquidity_score=0,
    recent_performance_score=0
):
    """
    strategy_type: "LONG" or "SHORT"
    strategy_score: 기존 score_engine 점수 0~100
    """

    total_score = 0
    details = []

    regime_score = 0

    if strategy_type == "LONG" and regime == "UPTREND":
        regime_score = 25
    elif strategy_type == "SHORT" and regime == "DOWNTREND":
        regime_score = 25
    elif regime in ["RANGE", "WEAK"]:
        regime_score = 5
    else:
        regime_score = 0

    total_score += regime_score
    details.append(f"Regime Score: {regime_score}/25")

    strategy_signal_score = min(
        30,
        strategy_score * 0.30
    )

    total_score += strategy_signal_score
    details.append(
        f"Strategy Signal Score: {strategy_signal_score:.1f}/30"
    )

    coin_strength_score = max(
        0,
        min(15, coin_strength_score)
    )

    total_score += coin_strength_score
    details.append(
        f"Coin Strength Score: {coin_strength_score}/15"
    )

    volatility_score = max(
        0,
        min(10, volatility_score)
    )

    total_score += volatility_score
    details.append(
        f"Volatility Score: {volatility_score}/10"
    )

    liquidity_score = max(
        0,
        min(10, liquidity_score)
    )

    total_score += liquidity_score
    details.append(
        f"Liquidity Score: {liquidity_score}/10"
    )

    recent_performance_score = max(
        0,
        min(10, recent_performance_score)
    )

    total_score += recent_performance_score
    details.append(
        f"Recent Performance Score: {recent_performance_score}/10"
    )

    # 중요:
    # SHORT는 아직 검증 DB에서 FAIL이므로 실행 금지.
    # WATCH까지만 허용.
    if strategy_type == "SHORT":
        if total_score >= 80:
            action = "WATCH"
        else:
            action = "NO_TRADE"

    else:
        if total_score >= 90:
            action = "EXECUTE"
        elif total_score >= 80:
            action = "READY"
        elif total_score >= 70:
            action = "WATCH"
        else:
            action = "NO_TRADE"

    return {
        "symbol": symbol,
        "strategy_type": strategy_type,
        "regime": regime,
        "phoenix_score": round(total_score, 2),
        "action": action,
        "details": details
    }