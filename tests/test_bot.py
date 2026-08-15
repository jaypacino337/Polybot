"""Bot-engine tests using a fake CLOB — no network, no keys, no real orders."""
from polybot.bot import Bot
from polybot.clob import OrderResult
from polybot.config import BotSideConfig, Config, MarketConfig, SignalConfig, Secrets, RiskConfig


class FakeClob:
    def __init__(self, yes=0.5, no=0.5):
        self.yes, self.no = yes, no
        self.orders = []
        self.sells = []

    def get_midpoint(self, token_id):
        return self.yes if token_id == "YES" else self.no

    def buy(self, token_id, price, size):
        self.orders.append((token_id, price, size))
        return OrderResult(success=True, order_id="fake", dry_run=True)

    def sell(self, token_id, price, size):
        self.sells.append((token_id, price, size))
        return OrderResult(success=True, order_id="fake", dry_run=True)


def _market(signal_decision, long_on=True, short_on=True):
    return MarketConfig(
        name="m",
        yes_token_id="YES",
        no_token_id="NO",
        long=BotSideConfig(enabled=long_on, order_size_usd=10.0, max_price=0.99),
        short=BotSideConfig(enabled=short_on, order_size_usd=10.0, max_price=0.99),
        signal=SignalConfig(type="manual", params={"decision": signal_decision}),
    )


def _bot(market, clob):
    cfg = Config(poll_interval_seconds=1, markets=[market], risk=RiskConfig())
    secrets = Secrets(
        private_key="", funder_address="", signature_type=0,
        clob_host="x", chain_id=137, dry_run=True,
    )
    return Bot(config=cfg, secrets=secrets, clob=clob)


def test_long_signal_buys_yes_once():
    clob = FakeClob(yes=0.4, no=0.6)
    bot = _bot(_market("long"), clob)
    bot.tick()
    bot.tick()  # already open -> should NOT double-buy
    assert clob.orders == [("YES", 0.4, 10.0 / 0.4)]


def test_short_signal_buys_no():
    clob = FakeClob(yes=0.6, no=0.4)
    bot = _bot(_market("short"), clob)
    bot.tick()
    assert clob.orders == [("NO", 0.4, 10.0 / 0.4)]


def test_disabled_bot_does_not_trade():
    clob = FakeClob()
    bot = _bot(_market("long", long_on=False), clob)
    bot.tick()
    assert clob.orders == []


def test_flat_signal_does_not_trade():
    clob = FakeClob()
    bot = _bot(_market("flat"), clob)
    bot.tick()
    assert clob.orders == []


def test_price_above_max_is_skipped():
    clob = FakeClob(yes=0.995, no=0.005)
    market = _market("long")
    market.long.max_price = 0.95
    bot = _bot(market, clob)
    bot.tick()
    assert clob.orders == []


def test_long_position_closes_when_signal_flips():
    clob = FakeClob(yes=0.4, no=0.6)
    market = _market("long")
    bot = _bot(market, clob)
    bot.tick()                       # signal LONG -> buy YES
    assert len(clob.orders) == 1
    # flip the manual signal to FLAT and tick again -> should sell to close
    bot._markets[0].signal._decision = __import__(
        "polybot.signals.base", fromlist=["Decision"]
    ).Decision.FLAT
    bot.tick()
    assert len(clob.sells) == 1
    assert clob.sells[0][0] == "YES"
    assert bot._markets[0].long_open is False
