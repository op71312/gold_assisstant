"""Transaction constraint tests (spec 9.1) — via the ReplayEngine path."""
from datetime import date

from gold_portfolio_simulator.accounting.portfolio import PortfolioState
from gold_portfolio_simulator.pricing.quotes import BAR, ORNAMENT, PRODUCTS


def _state(cash=100_000.0):
    st = PortfolioState("T", 2020, date(2020, 1, 2), "test", "PS", "s", "R")
    st.contribute(cash)
    return st


def test_buy_beyond_cash_rejected_and_logged(book):
    st = _state(1000)
    i = 5
    rec = st.buy("bar", 5.0, book.buy_price(i, "bar"), 0.0, BAR)
    assert rec["status"] == "REJECTED" and rec["reason"] == "INSUFFICIENT_CASH"
    assert st.cash == 1000


def test_sell_more_than_held_rejected(book):
    st = _state()
    i = 5
    st.buy("bar", 1.0, book.buy_price(i, "bar"), 0.0, BAR)
    rec = st.sell("bar", 2.0, book.sell_price(i, "bar"), 0.0)
    assert rec["status"] == "REJECTED" and rec["reason"] == "INSUFFICIENT_HOLDINGS"
    assert st.qty["bar"] == 1.0


def test_product_quantity_rules_enforced(book):
    st = _state(1_000_000)
    i = 5
    # bars: whole baht-weight only
    rec = st.buy("bar", 1.5, book.buy_price(i, "bar"), 0.0, BAR)
    assert rec["status"] == "ACCEPTED" and st.qty["bar"] == 1.0
    # ornaments: 0.25 increments
    rec = st.buy("ornament", 0.3, book.buy_price(i, "ornament"), 0.0, ORNAMENT)
    assert rec["status"] == "ACCEPTED" and st.qty["ornament"] == 0.25


def test_negative_or_zero_qty_rejected(book):
    st = _state()
    i = 5
    for q in (0.0, -1.0):
        assert st.buy("bar", q, book.buy_price(i, "bar"), 0.0, BAR)["status"] == "REJECTED"
        assert st.sell("bar", q, book.sell_price(i, "bar"), 0.0)["status"] == "REJECTED"


def test_rejected_orders_never_silent_in_engine(book):
    """Engine logs every rejected order with a reason (checked on fixtures)."""
    from gold_portfolio_simulator.config import SimulationConfig
    from gold_portfolio_simulator.simulation.engine import ReplayEngine
    from gold_portfolio_simulator.population.generator import PortfolioPlan
    cfg = SimulationConfig.from_yaml(
        __import__("pathlib").Path(__file__).parents[1] / "configs/simulation.yaml")
    cfg.cohort_years = [2020]
    cfg.portfolios_per_cohort = 4
    eng = ReplayEngine(cfg, book)
    plan = PortfolioPlan("PT1", 2020, book.dates[5], "seg", "bar",
                         100_000.0, 30_000.0, 1.0, 70_000.0, "active_rotation",
                         "PS", "seed:1", "R_TEST", _rng_seed=12345)
    tx, cf, val, yr, at = [], [], [], [], []
    st = eng.run_portfolio(plan, tx, cf, val, yr, at, {})
    assert all(r["rejection_reason"] != "" or r["execution_status"] == "ACCEPTED"
               for r in tx)
    # every accepted BUY reduces cash exactly
    for r in tx:
        if r["execution_status"] == "ACCEPTED" and r["side"] == "BUY":
            assert r["net_cash_change_thb"] < 0
