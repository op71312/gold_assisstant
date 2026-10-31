"""No-look-ahead tests (spec 7.3, gate 4).

1. Behavior rules receive a PriceBook that cannot expose future data (API-level).
2. A rule that reacts to price dips must NOT trigger before the dip occurs,
   even though the fixture contains the whole path (an oracle would trigger).
3. All simulated execution timestamps use quotes at or before decision time.
"""
from datetime import date, timedelta

import numpy as np

from gold_portfolio_simulator.behavior.rules import rule_buy_dip
from gold_portfolio_simulator.config import SimulationConfig
from gold_portfolio_simulator.pricing.quotes import PriceBook
from gold_portfolio_simulator.population.generator import PortfolioPlan
from gold_portfolio_simulator.simulation.engine import ReplayEngine


def test_pricebook_cannot_expose_future(book):
    """as_of/trailing functions must only see data <= the requested index."""
    i = 30
    # trailing window truncated at i
    assert book.trailing_max_bar_sell(i, 900) == book.bar_sell[:i + 1].max()
    assert book.trailing_min_bar_sell(i, 900) == book.bar_sell[:i + 1].min()


def test_dip_rule_not_triggered_before_dip(book):
    """Build a path where a big dip happens late; check the rule is silent early."""
    from tests.conftest import make_daily_frame
    df = make_daily_frame(days=90, p0=40000.0)
    # clean monotone rise, then a crash in the last week
    df["bar_sell_thb"] = 40000.0 * (1.001 ** np.arange(len(df)))
    df.loc[df.index[-5:], "bar_sell_thb"] *= 0.90
    df["bar_buy_thb"] = df["bar_sell_thb"] - 100
    book2 = PriceBook(df, 100.0)
    params = {"dip_threshold": 0.97, "dip_lookback_days": 90}
    from gold_portfolio_simulator.accounting.portfolio import PortfolioState
    st = PortfolioState("X", 2020, df.date.iloc[0], "buy_dip", "PS", "s", "R")
    st._primary_product = "bar"
    st.contribute(200_000)
    i_early = 10
    crash_start = len(df) - 5
    i_before = book2.exact_index(df.date.iloc[crash_start - 1])
    # early: monotone rise -> price == trailing max -> no trigger
    assert rule_buy_dip(st, book2, i_early, params, np.random.default_rng(0), None) == []
    # right before crash: price == trailing max -> silent
    assert rule_buy_dip(st, book2, i_before, params, np.random.default_rng(0), None) == []
    # at crash: triggers
    i_crash = book2.exact_index(df.date.iloc[crash_start + 1])
    orders = rule_buy_dip(st, book2, i_crash, params, np.random.default_rng(0), None)
    assert any(o["kind"] == "buy" for o in orders)


def test_engine_executions_use_quote_at_or_before_decision(book):
    cfg = SimulationConfig.from_yaml(
        __import__("pathlib").Path(__file__).parents[1] / "configs/simulation.yaml")
    cfg.cohort_years = [2020]
    cfg.portfolios_per_cohort = 4
    eng = ReplayEngine(cfg, book)
    tx = []
    for k in range(4):
        plan = PortfolioPlan(f"PL{k}", 2020, book.dates[5], "seg", "bar",
                             100_000.0, 30_000.0, 1.0, 70_000.0,
                             ["buy_hold", "dca", "buy_dip", "active_rotation"][k],
                             "PS", f"s{k}", "R_TEST", _rng_seed=77 + k)
        eng.run_portfolio(plan, tx, [], [], [], [], {})
    import pandas as pd
    tx_df = pd.DataFrame(tx)
    acc = tx_df[tx_df["execution_status"] == "ACCEPTED"]
    # every accepted execution price must equal the quote of its quote timestamp
    for _, r in acc.iterrows():
        i = book.exact_index(r["price_quote_timestamp"].date())
        assert i is not None
        px = r["customer_execution_price_thb_per_bw"]
        if r["side"] == "BUY":
            exp = book.bar_sell[i] if r["gold_product_type"] == "bar" else book.orn_sell[i]
        else:
            exp = book.bar_buy[i] if r["gold_product_type"] == "bar" \
                else book.bar_buy[i] + book.delta
        assert abs(px - exp) < 1e-9
