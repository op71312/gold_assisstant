"""Shared pytest fixtures. The price fixture is a small SYNTHETIC TEST FIXTURE
used only for unit tests of the accounting/pricing engines. It is NOT real
market data and is never used for empirical claims."""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from gold_portfolio_simulator.pricing.quotes import PriceBook  # noqa: E402


def make_daily_frame(start=date(2020, 1, 1), days=90, p0=40000.0):
    """Deterministic synthetic daily prices (test fixture only)."""
    rows = []
    p = p0
    d = start
    for k in range(days):
        if d.weekday() < 5:  # business days only
            # gentle deterministic path: +0.1%/day with a dip in days 20-25
            drift = 1.001
            if 20 <= k <= 25:
                drift = 0.988
            p = p * drift
            spread = 100.0
            rows.append({
                "date": d,
                "price_quote_timestamp": pd.Timestamp(d) + pd.Timedelta(hours=15),
                "bar_buy_thb": round(p - spread / 2, 2),
                "bar_sell_thb": round(p + spread / 2, 2),
                "ornament_sell_thb": round(p + spread / 2 + 800, 2),
                "ornament_tax_base_thb": round(p * 0.98, 2),
                "gold_spot_usd": 2000.0, "usd_thb": 33.0, "change_thb": 0.0,
                "announce_seq": 1, "selection_policy": "fixture",
                "quality_flag": "OK",
            })
        d += timedelta(days=1)
    return pd.DataFrame(rows)


@pytest.fixture(scope="session")
def daily():
    return make_daily_frame()


@pytest.fixture(scope="session")
def book(daily):
    return PriceBook(daily, ornament_buyback_delta_thb=100.0)
