"""Pricing engine — customer-perspective quote semantics over observed GTA data.

Quote semantics (verified against the published GTA table header, see
reports/deep_research.md section 4):

  bar_buy    = dealer's purchase quote  -> customer's SELL execution price
  bar_sell   = dealer's selling quote   -> customer's BUY execution price
  ornament_sell = customer's BUY price for ornaments (includes wage)
  ornament buy-back (customer SELL for ornaments) uses the observed
  ``ornament_buy`` quote when available; otherwise it is modeled as
  bar_buy + delta (assumption A04, configurable).

The liquidation (mark-to-market) value of a holding uses the customer's
SELL side, i.e. what the customer could actually receive — never the
purchase-side quote (spec 5.2 / 9.4).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

BAHT_WEIGHT_GRAMS = 15.244
GOLD_PURITY = 0.965


@dataclass
class ProductSpec:
    name: str
    increment_bw: float          # tradable quantity increment, baht-weight
    min_qty_bw: float

    def quantize(self, qty_bw: float) -> float:
        """Floor to tradable increments (never round up beyond affordable)."""
        if qty_bw < self.min_qty_bw:
            return 0.0
        steps = np.floor(qty_bw / self.increment_bw + 1e-9)
        return float(max(steps * self.increment_bw, 0.0))


BAR = ProductSpec("bar", increment_bw=1.0, min_qty_bw=1.0)
# Thai ornaments are commonly sold in salung (1 salung = 0.25 baht-weight) sizes;
# documented as market-convention assumption A12.
ORNAMENT = ProductSpec("ornament", increment_bw=0.25, min_qty_bw=0.25)
PRODUCTS = {"bar": BAR, "ornament": ORNAMENT}


class PriceBook:
    """Daily GTA quotes with strict as-of access (no look-ahead possible)."""

    def __init__(self, daily: pd.DataFrame, ornament_buyback_delta_thb: float = 100.0):
        d = daily.sort_values("date").reset_index(drop=True).copy()
        d["date"] = pd.to_datetime(d["date"]).dt.date
        self._dates = np.array(d["date"].tolist())
        self._idx = {d0: i for i, d0 in enumerate(self._dates)}
        self.bar_buy = d["bar_buy_thb"].to_numpy(float)
        self.bar_sell = d["bar_sell_thb"].to_numpy(float)
        self.orn_buy = pd.to_numeric(
            d.get("ornament_buy_thb", pd.Series(np.nan, index=d.index)),
            errors="coerce",
        ).to_numpy(float)
        self.orn_sell = d["ornament_sell_thb"].to_numpy(float)
        self.tax_base = d["ornament_tax_base_thb"].to_numpy(float)
        self.spot_usd = d["gold_spot_usd"].to_numpy(float)
        self.usd_thb = d["usd_thb"].to_numpy(float)
        self.delta = float(ornament_buyback_delta_thb)
        self.dates = self._dates  # sorted array of date objects

    # ---------- lookups ----------
    def exact_index(self, d: date):
        return self._idx.get(d)

    def as_of_index(self, d: date):
        """Index of the last available quote day <= d, or None."""
        i = np.searchsorted(self._dates, d, side="right") - 1
        return int(i) if i >= 0 else None

    def as_of(self, d: date):
        i = self.as_of_index(d)
        if i is None:
            return None
        return {
            "date": self._dates[i], "bar_buy": self.bar_buy[i],
            "bar_sell": self.bar_sell[i], "orn_sell": self.orn_sell[i],
            "orn_buy": self.sell_price(i, "ornament"), "tax_base": self.tax_base[i],
            "spot_usd": self.spot_usd[i], "usd_thb": self.usd_thb[i],
        }

    def next_index(self, d: date, max_roll_days: int):
        """First available quote day in [d, d + max_roll_days] (execution policy)."""
        hi = np.searchsorted(self._dates, d + timedelta(days=max_roll_days), side="right")
        lo = np.searchsorted(self._dates, d, side="left")
        return int(lo) if lo < hi else None

    # ---------- execution and valuation prices ----------
    def buy_price(self, i: int, product: str) -> float:
        return self.bar_sell[i] if product == "bar" else self.orn_sell[i]

    def sell_price(self, i: int, product: str) -> float:
        if product == "bar":
            return self.bar_buy[i]
        observed = self.orn_buy[i]
        if np.isfinite(observed) and observed > 0:
            return observed
        return self.bar_buy[i] + self.delta

    def liquidation_price(self, i: int, product: str) -> float:
        """Conservative mark: the price the customer could receive today."""
        return self.sell_price(i, product)

    # ---------- trailing statistics (information set = data <= t only) ----------
    def trailing_max_bar_sell(self, i: int, lookback_days: int) -> float:
        lo = np.searchsorted(self._dates, self._dates[i] - timedelta(days=lookback_days))
        return float(self.bar_sell[lo:i + 1].max())

    def trailing_min_bar_sell(self, i: int, lookback_days: int) -> float:
        lo = np.searchsorted(self._dates, self._dates[i] - timedelta(days=lookback_days))
        return float(self.bar_sell[lo:i + 1].min())

    def trailing_ma(self, i: int, window_days: int) -> float:
        """Mean of bar_sell over the last `window_days` calendar days, as of i."""
        lo = np.searchsorted(self._dates, self._dates[i] - timedelta(days=window_days))
        return float(self.bar_sell[lo:i + 1].mean())

    def benchmark_bh_equity(self, start_i: int, contributions: list[tuple[date, float]],
                            end_i: int) -> float:
        """Buy-and-hold bar benchmark: each contribution buys bar gold at that
        day's bar_sell quote (rolled to next valid day) and is never sold.
        Returns THB liquidation value at end_i. Used only for comparison."""
        qty = 0.0
        for d, amount in contributions:
            j = self.next_index(d, 7)
            if j is None or j > end_i:
                continue
            qty += amount / self.bar_sell[j]
        return qty * self.bar_buy[end_i]
