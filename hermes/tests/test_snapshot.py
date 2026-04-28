from hermes.snapshot import MarketSnapshot, diff


def _snap(bid: float, ask: float, ts: float = 0.0, yes: float = 0.5) -> MarketSnapshot:
    return MarketSnapshot(
        slug="x",
        ts=ts,
        yes_price=yes,
        no_price=1 - yes,
        bid_size=bid,
        ask_size=ask,
        spread=0.0,
        volume_24h=0.0,
    )


def test_imbalance_zero_when_one_side_empty():
    prev = _snap(1000, 1000, ts=0)
    curr = _snap(0, 5_000_000, ts=180)  # the dead-market case from the 1h run
    d = diff(prev, curr)
    assert d["imbalance"] == 0.0
    assert d["two_sided_book"] is False


def test_imbalance_zero_when_one_side_below_min():
    prev = _snap(1000, 1000, ts=0)
    curr = _snap(50, 5000, ts=180)  # bid present but tiny
    d = diff(prev, curr)
    assert d["imbalance"] == 0.0
    assert d["two_sided_book"] is False


def test_imbalance_real_when_two_sided():
    prev = _snap(1000, 1000, ts=0)
    curr = _snap(8000, 2000, ts=180)
    d = diff(prev, curr)
    assert d["two_sided_book"] is True
    assert d["imbalance"] == 0.6  # (8000-2000)/10000


def test_diff_does_not_explode_on_zero_prev_price():
    prev = _snap(1000, 1000, ts=0, yes=0.0)
    curr = _snap(1000, 1000, ts=180, yes=0.5)
    d = diff(prev, curr)
    assert d["price_delta"] == 0.5
    # division by max(prev_price, 1e-6) keeps this finite
    assert d["price_pct"] > 0
