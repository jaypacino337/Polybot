from polybot.signals import Decision, build_signal
from polybot.signals.base import SignalContext


def ctx(yes=0.5, no=0.5):
    return SignalContext(market_name="m", yes_price=yes, no_price=no)


def test_manual_signal_returns_configured_decision():
    assert build_signal("manual", {"decision": "long"}).evaluate(ctx()) == Decision.LONG
    assert build_signal("manual", {"decision": "short"}).evaluate(ctx()) == Decision.SHORT
    assert build_signal("manual").evaluate(ctx()) == Decision.FLAT


def test_moving_average_warms_up_then_signals():
    sig = build_signal("moving_average", {"fast": 2, "slow": 4})
    # warm-up: not enough samples yet
    assert sig.evaluate(ctx(yes=0.10)) == Decision.FLAT
    assert sig.evaluate(ctx(yes=0.10)) == Decision.FLAT
    assert sig.evaluate(ctx(yes=0.10)) == Decision.FLAT
    # 4th sample rising -> fast MA above slow MA -> LONG
    assert sig.evaluate(ctx(yes=0.90)) == Decision.LONG


def test_moving_average_detects_downtrend():
    sig = build_signal("moving_average", {"fast": 2, "slow": 4})
    for p in (0.90, 0.90, 0.90):
        sig.evaluate(ctx(yes=p))
    assert sig.evaluate(ctx(yes=0.10)) == Decision.SHORT


def test_unknown_signal_raises():
    try:
        build_signal("does_not_exist")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown signal")


def test_missing_price_is_flat():
    sig = build_signal("moving_average", {"fast": 2, "slow": 4})
    assert sig.evaluate(SignalContext("m", yes_price=None, no_price=None)) == Decision.FLAT


def test_threshold_signal():
    sig = build_signal("threshold", {"lower": 0.35, "upper": 0.65})
    assert sig.evaluate(ctx(yes=0.80)) == Decision.LONG
    assert sig.evaluate(ctx(yes=0.20)) == Decision.SHORT
    assert sig.evaluate(ctx(yes=0.50)) == Decision.FLAT


def test_momentum_signal():
    sig = build_signal("momentum", {"lookback": 3, "threshold": 0.05})
    for _ in range(3):
        sig.evaluate(ctx(yes=0.50))   # warm up at flat 0.50
    assert sig.evaluate(ctx(yes=0.60)) == Decision.LONG   # +20% vs 3 ago
    sig2 = build_signal("momentum", {"lookback": 3, "threshold": 0.05})
    for _ in range(3):
        sig2.evaluate(ctx(yes=0.50))
    assert sig2.evaluate(ctx(yes=0.40)) == Decision.SHORT  # -20% vs 3 ago


def test_rsi_reversion_oversold_is_long():
    sig = build_signal("rsi", {"period": 3, "oversold": 30, "overbought": 70})
    # steadily falling prices -> low RSI -> LONG (mean-reversion)
    for p in (0.90, 0.80, 0.70, 0.60):
        last = sig.evaluate(ctx(yes=p))
    assert last == Decision.LONG


def test_rsi_reversion_overbought_is_short():
    sig = build_signal("rsi", {"period": 3, "oversold": 30, "overbought": 70})
    for p in (0.10, 0.20, 0.30, 0.40):
        last = sig.evaluate(ctx(yes=p))
    assert last == Decision.SHORT
