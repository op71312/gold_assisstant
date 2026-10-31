"""Attribution reconciliation tests (spec 10.3 / 12.6).

For arbitrary event paths the components must reconcile with total P&L:
  total == price_effect + timing_effect + product_effect - fees
(within floating-point tolerance)."""
import numpy as np

from gold_portfolio_simulator.accounting.portfolio import PortfolioState
from gold_portfolio_simulator.pricing.quotes import BAR, ORNAMENT


def decompose(st, book, i_end, buys, sales, fees, ig_begin=0.0, M_begin=0.0):
    """Reference implementation of the documented decomposition.
    ig_begin/M_begin must be captured BEFORE the first event of the window
    (engine convention: the year boundary precedes all events)."""
    M_end = st.liquidation_value(book, i_end)
    sum_buy_L = sum(q * L for q, L, p, prod, i in buys)
    sum_sale_L = sum(q * L for q, L, s, prod, i in sales)
    sum_buy_t = sum(q * (L - p) for q, L, p, prod, i in buys)
    sum_sale_t = sum(q * (s - L) for q, L, s, prod, i in sales)
    product_effect = 0.0
    for q, L, p, prod, i in buys:
        if prod == "ornament":
            product_effect += q * ((L - book.bar_buy[i]) - (p - book.bar_sell[i]))
    price_effect = M_end - M_begin - sum_buy_L + sum_sale_L
    timing = sum_buy_t + sum_sale_t - product_effect
    total = st.invested_gain_cum(book, i_end) - ig_begin
    return total, price_effect + timing + product_effect - fees


def test_attribution_reconciles_simple_path(book):
    st = PortfolioState("A", 2020, book.dates[0], "t", "PS", "s", "R")
    st.contribute(200_000)
    i0 = 5
    ig_begin = st.invested_gain_cum(book, i0)   # captured before any trade
    buys, sales, fees = [], [], 0.0
    i1, i2 = 20, 40
    p = book.buy_price(i0, "bar")
    st.buy("bar", 1.0, p, 0.0, BAR)
    buys.append((1.0, book.liquidation_price(i0, "bar"), p, "bar", i0))
    p2 = book.buy_price(i1, "bar")
    st.buy("bar", 1.0, p2, 0.0, BAR)
    buys.append((1.0, book.liquidation_price(i1, "bar"), p2, "bar", i1))
    s = book.sell_price(i2, "bar")
    st.sell("bar", 1.0, s, 0.0)
    sales.append((1.0, book.liquidation_price(i2, "bar"), s, "bar", i2))
    total, comps = decompose(st, book, i2, buys, sales, fees, ig_begin)
    assert abs(total - comps) < 1e-6


def test_attribution_reconciles_ornament_with_wage(book):
    st = PortfolioState("B", 2020, book.dates[0], "t", "PS", "s", "R")
    st.contribute(200_000)
    i0, i1 = 10, 45
    ig_begin = st.invested_gain_cum(book, i0)
    buys, sales, fees = [], [], 0.0
    p = book.buy_price(i0, "ornament")
    st.buy("ornament", 1.0, p, 0.0, ORNAMENT)
    buys.append((1.0, book.liquidation_price(i0, "ornament"), p, "ornament", i0))
    s = book.sell_price(i1, "ornament")
    st.sell("ornament", 1.0, s, 0.0)
    sales.append((1.0, book.liquidation_price(i1, "ornament"), s, "ornament", i1))
    total, comps = decompose(st, book, i1, buys, sales, fees, ig_begin)
    assert abs(total - comps) < 1e-6
    # ornament product cost must be strongly negative (wage not recovered)
    product_effect = sum(
        q * ((L - book.bar_buy[i]) - (p0 - book.bar_sell[i]))
        for q, L, p0, prod, i in buys if prod == "ornament")
    assert product_effect < -100  # wage ~800 lost per baht-weight


def test_attribution_reconciles_mixed_path_with_price_moves(book):
    st = PortfolioState("C", 2020, book.dates[0], "t", "PS", "s", "R")
    st.contribute(500_000)
    ig_begin = 0.0
    buys, sales, fees = [], [], 0.0
    rng = np.random.default_rng(7)
    for step in range(6):
        i = int(rng.integers(2, 50))
        prod = "bar" if rng.random() < 0.6 else "ornament"
        q = 0.25 if prod == "ornament" else 1.0
        if rng.random() < 0.65 or not st.qty.get(prod, 0):
            p = book.buy_price(i, prod)
            if st.buy(prod, q, p, 0.0, {"bar": BAR, "ornament": ORNAMENT}[prod])["status"] == "ACCEPTED":
                buys.append((q, book.liquidation_price(i, prod), p, prod, i))
        elif st.qty.get(prod, 0) > 0:
            s = book.sell_price(i, prod)
            if st.sell(prod, q, s, 0.0)["status"] == "ACCEPTED":
                sales.append((q, book.liquidation_price(i, prod), s, prod, i))
    total, comps = decompose(st, book, 50, buys, sales, fees, ig_begin)
    assert abs(total - comps) < 1e-6


def test_engine_attribution_residuals_zero(tmp_path, book):
    from gold_portfolio_simulator.config import SimulationConfig
    from gold_portfolio_simulator.simulation.engine import ReplayEngine
    from gold_portfolio_simulator.population.generator import PortfolioPlan
    cfg = SimulationConfig.from_yaml(
        __import__("pathlib").Path(__file__).parents[1] / "configs/simulation.yaml")
    cfg.cohort_years = [2020]
    cfg.portfolios_per_cohort = 6
    eng = ReplayEngine(cfg, book)
    tx, cf, val, yr, at = [], [], [], [], []
    for k in range(6):
        plan = PortfolioPlan(f"PK{k}", 2020, book.dates[3], "seg",
                             "bar" if k % 2 else "ornament",
                             100_000.0, 30_000.0, 1.0, 70_000.0,
                             ["buy_hold", "dca", "buy_dip", "active_rotation",
                              "liquidity_sale", "partial_profit_taking"][k],
                             "PS", f"seed:{k}", "R_TEST", _rng_seed=1000 + k)
        eng.run_portfolio(plan, tx, cf, val, yr, at, {})
    import pandas as pd
    at_df = pd.DataFrame(at)
    assert (at_df["attribution_quality_flag"] == "RECONCILED").all()
