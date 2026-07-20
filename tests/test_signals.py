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
