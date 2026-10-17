def calculate_coin_strength_scores(price_changes, strategy_type):
    """
    price_changes 예시:
    {
        "BTC/USDT": -1.2,
        "ETH/USDT": -2.5,
        "SOL/USDT": 0.3
    }

    LONG  = 가장 강한 코인에 높은 점수
    SHORT = 가장 약한 코인에 높은 점수
    """

    scores = {}

    sorted_items = sorted(
        price_changes.items(),
        key=lambda x: x[1],
        reverse=True
    )

    if strategy_type == "LONG":
        ranked = sorted_items
    else:
        ranked = list(reversed(sorted_items))

    point_table = [15, 10, 5]

    for i, item in enumerate(ranked):
        symbol = item[0]

        if i < len(point_table):
            scores[symbol] = point_table[i]
        else:
            scores[symbol] = 0

    return scores


def calculate_price_change(df, lookback=12):
    """
    5분봉 기준 lookback=12 → 최근 1시간 변화율
    """

    if len(df) <= lookback:
        return 0

    current_price = df.iloc[-1]["close"]
    past_price = df.iloc[-lookback]["close"]

    change = (
        (current_price - past_price)
        / past_price
    ) * 100

    return change