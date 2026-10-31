"""Deterministic portfolio accounting (spec 9.3 / 9.4).

State maintained per portfolio:
  cash, holdings & weighted-average cost by product, cumulative realized P&L,
  cumulative fees, cumulative contributions / withdrawals.

Accounting identities (enforced and unit-tested):
  I1  equity == cash + sum(qty * liquidation_price)
  I2  equity - (contributions - withdrawals)
        == realized_pnl_cum + unrealized_pnl - fees_cum
  I3  external contributions never enter investment P&L; withdrawals never
      leave it as a loss (they are capital flows, tracked separately).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ..pricing.quotes import PriceBook


@dataclass
class PortfolioState:
    portfolio_id: str
    cohort_start_year: int
    start_date: date
    behavior_scenario: str
    parameter_set_id: str
    random_seed_id: str
    simulation_run_id: str
    inventory_costing: str = "weighted_average"

    cash: float = 0.0
    qty: dict = field(default_factory=dict)          # product -> baht-weight
    wac: dict = field(default_factory=dict)          # product -> THB/baht-weight
    realized_pnl_cum: float = 0.0
    fees_cum: float = 0.0
    contrib_cum: float = 0.0
    withdraw_cum: float = 0.0
    gross_purchases_thb: float = 0.0
    gross_sales_thb: float = 0.0
    tx_counter: int = 0
    active: bool = True          # False after full liquidation-with-exit events
    end_date: date | None = None
    initial_bought: bool = False

    # ---------------- capital flows (never P&L) ----------------
    def contribute(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("contribution must be positive")
        self.cash += amount
        self.contrib_cum += amount

    def withdraw(self, amount: float) -> float:
        amt = min(amount, self.cash)
        self.cash -= amt
        self.withdraw_cum += amt
        return amt

    # ---------------- trading ----------------
    def buy(self, product: str, qty_bw: float, exec_price: float, fee: float,
            spec) -> dict:
        """Execute a purchase. Caller must have validated affordability.
        Returns the ledger record payload."""
        if qty_bw <= 0:
            return {"status": "REJECTED", "reason": "NON_POSITIVE_QUANTITY"}
        cost = qty_bw * exec_price
        if cost + fee > self.cash + 1e-9:
            return {"status": "REJECTED", "reason": "INSUFFICIENT_CASH"}
        q = spec.quantize(qty_bw)
        if q <= 0:
            return {"status": "REJECTED", "reason": "BELOW_MIN_TRADE_UNIT"}
        q = min(q, (self.cash - fee) / exec_price)
        cost = q * exec_price
        old_q = self.qty.get(product, 0.0)
        self.wac[product] = ((self.wac.get(product, 0.0) * old_q) + cost) / (old_q + q)
        self.qty[product] = old_q + q
        self.cash -= cost + fee
        self.fees_cum += fee
        self.gross_purchases_thb += cost
        self.tx_counter += 1
        return {"status": "ACCEPTED", "executed_qty": q, "cost": cost,
                "new_wac": self.wac[product]}

    def sell(self, product: str, qty_bw: float, exec_price: float, fee: float) -> dict:
        """Execute a sale; realized P&L follows weighted-average costing."""
        held = self.qty.get(product, 0.0)
        if qty_bw <= 0:
            return {"status": "REJECTED", "reason": "NON_POSITIVE_QUANTITY"}
        if qty_bw > held + 1e-9:
            return {"status": "REJECTED", "reason": "INSUFFICIENT_HOLDINGS"}
        q = qty_bw
        wac = self.wac.get(product, 0.0)
        realized = q * (exec_price - wac)
        proceeds = q * exec_price - fee
        self.qty[product] = held - q
        self.cash += proceeds
        self.realized_pnl_cum += realized
        self.fees_cum += fee
        self.gross_sales_thb += q * exec_price
        self.tx_counter += 1
        if self.qty[product] <= 1e-9:
            self.qty.pop(product, None)
            self.wac.pop(product, None)
        return {"status": "ACCEPTED", "executed_qty": q, "proceeds": proceeds,
                "realized_pnl": realized}

    # ---------------- valuation ----------------
    def liquidation_value(self, book: PriceBook, i: int) -> float:
        v = 0.0
        for p, q in self.qty.items():
            if q > 0:
                v += q * book.liquidation_price(i, p)
        return v

    def cost_basis(self) -> float:
        return sum(q * self.wac[p] for p, q in self.qty.items() if q > 0)

    def unrealized_pnl(self, book: PriceBook, i: int) -> float:
        return self.liquidation_value(book, i) - self.cost_basis()

    def equity(self, book: PriceBook, i: int) -> float:
        return self.cash + self.liquidation_value(book, i)

    def invested_gain_cum(self, book: PriceBook, i: int) -> float:
        """Cumulative investment P&L: realized + unrealized - fees (identity I2)."""
        return (self.realized_pnl_cum + self.unrealized_pnl(book, i) - self.fees_cum)

    def check_identity(self, book: PriceBook, i: int, tol: float = 0.01) -> bool:
        lhs = self.equity(book, i) - (self.contrib_cum - self.withdraw_cum)
        rhs = self.invested_gain_cum(book, i)
        return abs(lhs - rhs) <= max(tol, 1e-9 * max(1.0, abs(lhs)))
