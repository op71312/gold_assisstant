"""Reproducibility tests (spec 8.5 / 11.1 check 13)."""
import hashlib

import pandas as pd

from gold_portfolio_simulator.config import SimulationConfig
from gold_portfolio_simulator.simulation.engine import ReplayEngine
from gold_portfolio_simulator.population.generator import generate_population
from gold_portfolio_simulator.pricing.quotes import PriceBook
from gold_portfolio_simulator.config import DataConfig
import pathlib

PROJECT = pathlib.Path(__file__).resolve().parents[1]


def _load_book():
    dcfg = DataConfig.from_yaml(PROJECT / "configs/data.yaml")
    from gold_portfolio_simulator.data.audit import load_raw, build_daily_prices
    raw = load_raw(dcfg)
    daily, _ = build_daily_prices(raw, dcfg)
    return PriceBook(daily, 100.0)


def _hash_run(book, seed):
    cfg = SimulationConfig.from_yaml(PROJECT / "configs/simulation.yaml")
    cfg.global_seed = seed
    cfg.cohort_years = [2019, 2020, 2021]
    cfg.portfolios_per_cohort = 5
    plans = generate_population(cfg, book)
    eng = ReplayEngine(cfg, book)
    tx, yr = [], []
    for plan in plans:
        eng.run_portfolio(plan, tx, [], [], yr, [], {})
    h1 = hashlib.sha256(pd.util.hash_pandas_object(
        pd.DataFrame(tx), index=True).values.tobytes()).hexdigest()
    h2 = hashlib.sha256(pd.util.hash_pandas_object(
        pd.DataFrame(yr), index=True).values.tobytes()).hexdigest()
    return h1, h2, len(tx)


def test_same_seed_same_results():
    book = _load_book()
    a = _hash_run(book, 42)
    b = _hash_run(book, 42)
    assert a == b
    assert a[2] > 0


def test_different_seed_different_results():
    book = _load_book()
    a = _hash_run(book, 42)
    b = _hash_run(book, 43)
    assert a[0] != b[0]
