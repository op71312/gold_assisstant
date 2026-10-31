"""Stage C — Synthetic portfolio population generator (spec 6).

Generates the initial characteristics of synthetic gold-investment customer
portfolios. All distributions are labelled scenario assumptions
(outputs/assumptions_register.csv A01–A03, A13); none is presented as an
empirical measurement of Thai households or investors.

Reproducibility (spec 8.5): a global seed is expanded deterministically via
numpy SeedSequence: cohort seed = spawn(global), portfolio seed = spawn(cohort).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from ..pricing.quotes import PriceBook, PRODUCTS


@dataclass
class PortfolioPlan:
    portfolio_id: str
    cohort_start_year: int
    start_date: date
    portfolio_segment: str
    gold_product_type: str
    initial_capital_thb: float
    initial_cash_thb: float
    initial_gold_quantity: float
    initial_gold_value_thb: float
    behavior_scenario: str
    parameter_set_id: str
    random_seed_id: str
    simulation_run_id: str
    is_synthetic: bool = True
    calibration_status: str = "SCENARIO_ASSUMPTION"
    # internal fields (not exported to portfolio_master)
    _initial_buy_product: str = "bar"
    _rng_seed: int = 0


def _cohort_start_dates(year: int, book: PriceBook, n: int, rng: np.random.Generator) -> list[date]:
    """Random start dates within the cohort year, restricted to available quote days."""
    y = pd.Timestamp(year, 1, 1).date()
    y_end = pd.Timestamp(year, 12, 31).date()
    lo = book.next_index(y, 400)
    if lo is None:
        return [None] * n
    hi_i = book.as_of_index(y_end)
    # restrict to quote days within the year
    valid = [i for i in range(lo, hi_i + 1)
             if book.dates[i].year == year]
    if not valid:
        return [None] * n
    picks = rng.choice(valid, size=n, replace=True)
    return [book.dates[int(i)] for i in picks]


def generate_population(cfg, book: PriceBook) -> list[PortfolioPlan]:
    ss = np.random.SeedSequence(cfg.global_seed)
    cohort_seeds = ss.spawn(len(cfg.cohort_years))
    plans: list[PortfolioPlan] = []
    seg_names = ["mass_retail", "affluent_retail"]
    pop = cfg.population
    for ci, year in enumerate(cfg.cohort_years):
        cs = np.random.default_rng(cohort_seeds[ci])
        # split cohort portfolios across behavior scenarios by configured weights
        scen_names = list(cfg.behavior.weights.keys())
        w = np.array([cfg.behavior.weights[s] for s in scen_names], dtype=float)
        w = w / w.sum()
        scenarios = cs.choice(scen_names, size=cfg.portfolios_per_cohort, p=w)
        # segment label (documented as a scenario label only)
        segments = cs.choice(seg_names, size=cfg.portfolios_per_cohort, p=[0.8, 0.2])
        start_dates = _cohort_start_dates(year, book, cfg.portfolios_per_cohort, cs)
        for pi in range(cfg.portfolios_per_cohort):
            ps = cs.integers(0, 2**63 - 1)
            rng = np.random.default_rng(ps)
            d0 = start_dates[pi]
            if d0 is None:
                continue  # no quotes in that year at all
            i0 = book.exact_index(d0)
            # --- initial capital (A01): lognormal in baht-weight affordability ---
            ic = pop.initial_capital
            n_bw = float(rng.lognormal(np.log(ic["median_bw"]), ic["sigma"]))
            bar_price = book.bar_sell[i0]
            capital = max(n_bw * bar_price, ic["min_capital_thb"])
            # --- product type (A03) ---
            mix = pop.product_mix
            product = "bar" if rng.random() < mix["bar"] else "ornament"
            # --- gold allocation share (A02) ---
            ga = pop.gold_allocation
            share = float(ga["low"] + (ga["high"] - ga["low"])
                          * rng.beta(ga["a"], ga["b"]))
            gold_budget = capital * share
            if scenarios[pi] == "dca":
                gold_budget = capital * float(
                    cfg.behavior.params["dca_initial_fraction"])
            # Product fallback (documented in methodology): if the sampled
            # product is unaffordable with the sampled capital, fall back to
            # the other product's smallest tradable unit before giving up.
            def affordable(prod, budget):
                sp = PRODUCTS[prod]
                return budget >= sp.min_qty_bw * book.buy_price(i0, prod)
            if not affordable(product, gold_budget):
                other = "ornament" if product == "bar" else "bar"
                if affordable(other, gold_budget):
                    product = other
            # Minimum-purchase rule: an investor who decided to hold gold buys
            # at least the smallest tradable unit if total capital allows it
            # (keeps a 5% cash buffer). Documented in methodology 6.2.
            spec0 = PRODUCTS[product]
            min_cost = spec0.min_qty_bw * book.buy_price(i0, product)
            if gold_budget < min_cost and capital * 0.95 >= min_cost:
                gold_budget = min_cost
            price0 = book.buy_price(i0, product)
            spec = PRODUCTS[product]
            qty = spec.quantize(gold_budget / price0)
            gold_value = qty * price0
            cash = capital - gold_value
            pid = f"P{year}{'%04d' % (pi + 1)}"
            plans.append(PortfolioPlan(
                portfolio_id=pid,
                cohort_start_year=year,
                start_date=d0,
                portfolio_segment=str(segments[pi]),
                gold_product_type=product,
                initial_capital_thb=round(capital, 2),
                initial_cash_thb=round(cash, 2),
                initial_gold_quantity=qty,
                initial_gold_value_thb=round(gold_value, 2),
                behavior_scenario=str(scenarios[pi]),
                parameter_set_id=f"PS_{cfg.run_id}",
                random_seed_id=f"seed:{cfg.global_seed}:{year}:{pid}",
                simulation_run_id=cfg.run_id,
                _rng_seed=int(ps),
                _initial_buy_product=product,
            ))
    return plans


def population_frame(plans: list[PortfolioPlan]) -> pd.DataFrame:
    rows = []
    for p in plans:
        rows.append({
            "portfolio_id": p.portfolio_id,
            "cohort_start_year": p.cohort_start_year,
            "start_timestamp": pd.Timestamp(p.start_date),
            "end_timestamp": pd.NaT,
            "portfolio_segment": p.portfolio_segment,
            "gold_product_type": p.gold_product_type,
            "initial_capital_thb": p.initial_capital_thb,
            "initial_cash_thb": p.initial_cash_thb,
            "initial_gold_quantity": p.initial_gold_quantity,
            "initial_gold_value_thb": p.initial_gold_value_thb,
            "behavior_scenario": p.behavior_scenario,
            "parameter_set_id": p.parameter_set_id,
            "random_seed_id": p.random_seed_id,
            "simulation_run_id": p.simulation_run_id,
            "is_synthetic": p.is_synthetic,
            "calibration_status": p.calibration_status,
        })
    return pd.DataFrame(rows)
