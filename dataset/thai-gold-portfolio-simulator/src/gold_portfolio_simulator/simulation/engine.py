"""Stage E/F — Monte Carlo population + historical replay engine (spec 8, 9).

Chronological, event-driven simulator:
  funding events -> trading decisions -> executed/rejected orders -> valuations.

Monte Carlo only samples inputs and behaviour; every P&L number is produced by
the deterministic accounting engine from holdings, cash flows, observed quotes
and recorded execution prices (spec 2.4). No-look-ahead is enforced by the
PriceBook API (only data <= t is reachable).

Attribution decomposition (per portfolio-year; derived in docs/accounting_rules.md
and proven to reconcile exactly with total investment P&L):
  price_effect            = M_end - M_begin - sum_buys q*L + sum_sales q*L
  timing_effect           = sum_buys q*(L-p) + sum_sales q*(s-L) - product_effect
  product_cost_effect     = sum_ornament_buys q*((L - bar_buy) - (p - bar_sell))
  transaction_cost_effect = -fees
  total                   = invested_gain_end - invested_gain_begin
where L = liquidation quote at event time, p = customer buy price,
s = customer sell price, M = holdings liquidation value.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from ..accounting.portfolio import PortfolioState
from ..behavior.rules import RULES
from ..pricing.quotes import PRODUCTS, PriceBook
from ..population.generator import PortfolioPlan


@dataclass
class YearBucket:
    year: int
    begin_date: object = None          # date or None (new portfolio)
    begin_equity: float = 0.0
    begin_M: float = 0.0
    begin_invested_gain: float = 0.0
    begin_realized_cum: float = 0.0
    begin_fees_cum: float = 0.0
    contrib: float = 0.0
    withdraw: float = 0.0
    flows: list = field(default_factory=list)   # (date, signed_amount)
    buys: list = field(default_factory=list)    # (q, L, p, product, ts)
    sales: list = field(default_factory=list)   # (q, L, s, product, ts)
    fees: float = 0.0
    purchase_count: int = 0
    sale_count: int = 0
    gross_buy: float = 0.0
    gross_sell: float = 0.0
    realized_end_cum: float = 0.0
    fees_end_cum: float = 0.0
    end_equity: float = 0.0
    end_M: float = 0.0
    end_invested_gain: float = 0.0
    end_date: object = None
    val_months: int = 0
    val_ok_months: int = 0
    equity_marks: list = field(default_factory=list)
    exited: bool = False


def _month_end_quote_indices(book: PriceBook) -> list[tuple[date, int]]:
    """Last available quote date of each calendar month present in the data."""
    out = []
    n = len(book.dates)
    i = 0
    while i < n:
        d = book.dates[i]
        y, m = d.year, d.month
        last_i = i
        while last_i + 1 < n and book.dates[last_i + 1].year == y \
                and book.dates[last_i + 1].month == m:
            last_i += 1
        out.append((book.dates[last_i], last_i))
        i = last_i + 1
    return out


class ReplayEngine:
    def __init__(self, cfg, book: PriceBook):
        self.cfg = cfg
        self.book = book
        self.me_idx = _month_end_quote_indices(book)
        self.pricing = cfg.pricing
        self.beh = cfg.behavior
        self._cf_counter = 0

    # ---------------- ledger helpers ----------------
    def _tx_record(self, st, ts, event_type, product, side, req_qty, exec_qty,
                   quote_ts, exec_price, gross, cost, net_cash, realized,
                   status, reason=""):
        return {
            "transaction_id": f"{st.portfolio_id}-T{st.tx_counter:05d}",
            "portfolio_id": st.portfolio_id,
            "event_timestamp": pd.Timestamp(ts),
            "calendar_year": ts.year,
            "event_type": event_type,
            "gold_product_type": product,
            "side": side,
            "requested_quantity_bw": req_qty,
            "executed_quantity_bw": exec_qty,
            "price_quote_timestamp": pd.Timestamp(quote_ts) if quote_ts else pd.NaT,
            "customer_execution_price_thb_per_bw": exec_price,
            "gross_amount_thb": gross,
            "transaction_cost_thb": cost,
            "net_cash_change_thb": net_cash,
            "realized_pnl_thb": realized,
            "execution_status": status,
            "rejection_reason": reason,
            "behavior_scenario": st.behavior_scenario,
            "parameter_set_id": st.parameter_set_id,
            "simulation_run_id": st.simulation_run_id,
            "is_synthetic": True,
            "source_quote_id": f"GTA:{quote_ts.isoformat()}" if quote_ts else "GTA:NONE",
        }

    def _cashflow_record(self, st, ts, ctype, amount, reason):
        self._cf_counter += 1
        return {
            "cashflow_id": f"{st.portfolio_id}-C{self._cf_counter:05d}",
            "portfolio_id": st.portfolio_id,
            "event_timestamp": pd.Timestamp(ts),
            "cashflow_type": ctype,
            "amount_thb": amount,
            "reason_or_scenario": reason,
            "simulation_run_id": st.simulation_run_id,
            "is_synthetic": True,
        }

    # ---------------- order execution ----------------
    def _execute_buy(self, st, bucket, ts, i, product, budget, records):
        book = self.book
        spec = PRODUCTS[product]
        p = book.buy_price(i, product)
        fee = float(self.pricing.get("explicit_fee_thb", 0.0))
        req_qty = budget / p if p > 0 else 0.0
        rec = st.buy(product, req_qty, p, fee, spec)
        if rec["status"] == "ACCEPTED":
            q = rec["executed_qty"]
            L = book.liquidation_price(i, product)
            bucket.buys.append((q, L, p, product, ts))
            bucket.purchase_count += 1
            bucket.gross_buy += q * p
            bucket.fees += fee
            bucket.fees_end_cum = st.fees_cum
            st.initial_bought = True
            records.append(self._tx_record(
                st, ts, "GOLD_PURCHASE", product, "BUY", req_qty, q,
                book.dates[i], p, q * p, fee, -(q * p + fee), 0.0, "ACCEPTED"))
        else:
            records.append(self._tx_record(
                st, ts, "GOLD_PURCHASE", product, "BUY", req_qty, 0.0,
                book.dates[i], p, 0.0, 0.0, 0.0, 0.0, "REJECTED",
                rec.get("reason", "")))

    def _execute_sell(self, st, bucket, ts, i, product, fraction, records):
        book = self.book
        held = st.qty.get(product, 0.0)
        p = book.sell_price(i, product)
        fee = float(self.pricing.get("explicit_fee_thb", 0.0))
        req_qty = held * float(fraction)
        rec = st.sell(product, req_qty, p, fee)
        if rec["status"] == "ACCEPTED":
            q = rec["executed_qty"]
            L = book.liquidation_price(i, product)
            bucket.sales.append((q, L, p, product, ts))
            bucket.sale_count += 1
            bucket.gross_sell += q * p
            bucket.fees += fee
            bucket.fees_end_cum = st.fees_cum
            records.append(self._tx_record(
                st, ts, "GOLD_SALE", product, "SELL", req_qty, q,
                book.dates[i], p, q * p, fee, q * p - fee,
                rec["realized_pnl"], "ACCEPTED"))
        else:
            records.append(self._tx_record(
                st, ts, "GOLD_SALE", product, "SELL", req_qty, 0.0,
                book.dates[i], p, 0.0, 0.0, 0.0, 0.0, "REJECTED",
                rec.get("reason", "")))

    # ---------------- per-portfolio replay ----------------
    def run_portfolio(self, plan: PortfolioPlan, tx_rows: list, cf_rows: list,
                      val_rows: list, year_rows: list, attr_rows: list,
                      diag: dict):
        cfg = self.cfg
        book = self.book
        params = self.beh.params
        st = PortfolioState(
            portfolio_id=plan.portfolio_id,
            cohort_start_year=plan.cohort_start_year,
            start_date=plan.start_date,
            behavior_scenario=plan.behavior_scenario,
            parameter_set_id=plan.parameter_set_id,
            random_seed_id=plan.random_seed_id,
            simulation_run_id=plan.simulation_run_id,
            inventory_costing=cfg.inventory_costing,
        )
        st._primary_product = plan.gold_product_type
        rng = np.random.default_rng(plan._rng_seed)
        rule = RULES[plan.behavior_scenario]
        i0 = book.exact_index(plan.start_date)
        if i0 is None:
            diag["portfolios_skipped_no_start_quote"] = \
                diag.get("portfolios_skipped_no_start_quote", 0) + 1
            return None

        buckets: dict[int, YearBucket] = {}
        prev_bucket: YearBucket | None = None
        last_val = None   # (date, equity, M, invested_gain)
        contributions: list[tuple[date, float]] = []
        withdrawals: list[tuple[date, float]] = []

        def bucket_for(y: int) -> YearBucket:
            nonlocal prev_bucket
            if y not in buckets:
                b = YearBucket(year=y)
                if prev_bucket is None:
                    b.begin_date = None            # new portfolio: zero boundary
                    b.begin_equity = 0.0
                    b.begin_M = 0.0
                    b.begin_invested_gain = 0.0
                else:
                    b.begin_date = date(y, 1, 1)
                    b.begin_equity = prev_bucket.end_equity
                    b.begin_M = prev_bucket.end_M
                    b.begin_invested_gain = prev_bucket.end_invested_gain
                    b.begin_realized_cum = prev_bucket.realized_end_cum
                    b.begin_fees_cum = prev_bucket.fees_end_cum
                    b.equity_marks.append((date(y, 1, 1), b.begin_equity))
                buckets[y] = b
                prev_bucket = b
            return buckets[y]

        # ---- initial funding + purchase (A13: contribute_then_buy) ----
        b0 = bucket_for(plan.start_date.year)
        st.contribute(plan.initial_capital_thb)
        cf_rows.append(self._cashflow_record(
            st, plan.start_date, "initial_contribution",
            plan.initial_capital_thb, "initial funding (synthetic)"))
        b0.contrib += plan.initial_capital_thb
        b0.flows.append((plan.start_date, plan.initial_capital_thb))
        contributions.append((plan.start_date, plan.initial_capital_thb))
        if plan.initial_gold_quantity > 0:
            self._execute_buy(st, b0, plan.start_date, i0,
                              plan.gold_product_type,
                              plan.initial_gold_value_thb, tx_rows)

        # ---- decision dates: one per month (deterministic draw) ----
        decisions = []
        y, m = plan.start_date.year, plan.start_date.month
        while (y, m) <= (book.dates[-1].year, book.dates[-1].month):
            day = int(rng.integers(1, 29))
            d = date(y, m, min(day, calendar.monthrange(y, m)[1]))
            if d > plan.start_date:
                decisions.append(d)
            m += 1
            if m == 13:
                y, m = y + 1, 1

        roll = int(self.beh.decision_roll_forward_days)
        decisions_by_month = {}
        for d in decisions:
            decisions_by_month.setdefault((d.year, d.month), []).append(d)

        # ---- chronological month walk ----
        for me_date, me_i in self.me_idx:
            if me_date < plan.start_date:
                continue
            y = me_date.year
            for dd in decisions_by_month.get((me_date.year, me_date.month), []):
                if not st.active:
                    break
                di = book.next_index(dd, roll)
                b = bucket_for(dd.year)
                if di is None:
                    tx_rows.append(self._tx_record(
                        st, dd, "DECISION_SKIPPED", "", "", np.nan, 0.0,
                        None, np.nan, 0.0, 0.0, 0.0, 0.0, "REJECTED",
                        "NO_VALID_PRICE"))
                    continue
                ts = book.dates[di]
                # Retry the initial allocation buy if it was previously
                # unaffordable (small-capital portfolios save up first).
                if not st.initial_bought and plan.behavior_scenario != "dca":
                    if plan.initial_gold_value_thb > 0:
                        self._execute_buy(st, b, ts, di,
                                          plan.gold_product_type,
                                          plan.initial_gold_value_thb, tx_rows)
                    if st.initial_bought:
                        continue
                orders = rule(st, book, di, params, rng, cfg)
                for od in orders:
                    kind = od["kind"]
                    if kind == "external_contribution":
                        amt = float(od["amount_thb"])
                        st.contribute(amt)
                        cf_rows.append(self._cashflow_record(
                            st, ts, "additional_contribution", amt,
                            f"{plan.behavior_scenario} recurring contribution"))
                        b.contrib += amt
                        b.flows.append((ts, amt))
                        contributions.append((ts, amt))
                    elif kind == "external_withdraw_all":
                        amt = st.withdraw(st.cash)
                        if amt > 0:
                            cf_rows.append(self._cashflow_record(
                                st, ts, "withdrawal", amt,
                                f"{plan.behavior_scenario} liquidity exit"))
                            b.withdraw += amt
                            b.flows.append((ts, -amt))
                            withdrawals.append((ts, amt))
                        st.active = False
                        st.end_date = ts
                        b.exited = True
                        # Final valuation at the exit event so the exit-year
                        # bucket captures the closing sale's P&L (reconciliation).
                        eq = st.equity(book, di)
                        M = st.liquidation_value(book, di)
                        vig = st.invested_gain_cum(book, di)
                        b.end_equity = eq
                        b.end_M = M
                        b.end_invested_gain = vig
                        b.end_date = ts
                        b.realized_end_cum = st.realized_pnl_cum
                        b.fees_end_cum = st.fees_cum
                        b.equity_marks.append((ts, eq))
                        b.val_ok_months += 1
                        val_rows.append({
                            "portfolio_id": st.portfolio_id,
                            "valuation_date": pd.Timestamp(ts),
                            "calendar_year": ts.year,
                            "cash_balance_thb": st.cash,
                            "gold_qty_bar_bw": st.qty.get("bar", 0.0),
                            "gold_qty_ornament_bw": st.qty.get("ornament", 0.0),
                            "gold_cost_basis_thb": st.cost_basis(),
                            "gold_liquidation_value_thb": M,
                            "portfolio_equity_thb": eq,
                            "net_contributed_capital_thb": st.contrib_cum - st.withdraw_cum,
                            "cumulative_realized_pnl_thb": st.realized_pnl_cum,
                            "unrealized_pnl_thb": st.unrealized_pnl(book, di),
                            "cumulative_transaction_cost_thb": st.fees_cum,
                            "cumulative_net_pnl_thb": vig,
                            "valuation_price_timestamp": pd.Timestamp(book.dates[di]),
                            "valuation_quality_flag": "EXIT_EVENT",
                            "simulation_run_id": st.simulation_run_id,
                            "is_synthetic": True,
                        })
                        last_val = (ts, eq, M, vig)
                    elif kind == "buy":
                        budget = float(od["budget_thb"])
                        cap = float(params.get("max_fraction_equity_in_gold", 1.0))
                        eq = st.equity(book, di)
                        gold_val = st.liquidation_value(book, di)
                        budget = min(budget, max(0.0, eq * cap - gold_val))
                        if budget > 0:
                            self._execute_buy(st, b, ts, di, od["product"],
                                              budget, tx_rows)
                    elif kind == "sell":
                        if st.qty.get(od["product"], 0) > 0:
                            self._execute_sell(st, b, ts, di, od["product"],
                                               od["fraction"], tx_rows)
            # ---- month-end valuation ----
            if not st.active and st.end_date is not None and me_date > st.end_date:
                continue
            b = bucket_for(y)
            b.val_months += 1
            eq = st.equity(book, me_i)
            M = st.liquidation_value(book, me_i)
            vig = st.invested_gain_cum(book, me_i)
            b.val_ok_months += 1
            b.equity_marks.append((me_date, eq))
            b.end_equity = eq
            b.end_M = M
            b.end_invested_gain = vig
            b.end_date = me_date
            b.realized_end_cum = st.realized_pnl_cum
            b.fees_end_cum = st.fees_cum
            val_rows.append({
                "portfolio_id": st.portfolio_id,
                "valuation_date": pd.Timestamp(me_date),
                "calendar_year": y,
                "cash_balance_thb": st.cash,
                "gold_qty_bar_bw": st.qty.get("bar", 0.0),
                "gold_qty_ornament_bw": st.qty.get("ornament", 0.0),
                "gold_cost_basis_thb": st.cost_basis(),
                "gold_liquidation_value_thb": M,
                "portfolio_equity_thb": eq,
                "net_contributed_capital_thb": st.contrib_cum - st.withdraw_cum,
                "cumulative_realized_pnl_thb": st.realized_pnl_cum,
                "unrealized_pnl_thb": st.unrealized_pnl(book, me_i),
                "cumulative_transaction_cost_thb": st.fees_cum,
                "cumulative_net_pnl_thb": vig,
                "valuation_price_timestamp": pd.Timestamp(book.dates[me_i]),
                "valuation_quality_flag": "OK",
                "simulation_run_id": st.simulation_run_id,
                "is_synthetic": True,
            })
            last_val = (me_date, eq, M, vig)
            if not st.active:
                break

        # ---- close buckets -> yearly + attribution rows ----
        for y, b in sorted(buckets.items()):
            if b.val_ok_months == 0 and not b.buys:
                continue
            if b.end_date is None:
                continue  # year with no valuation (should not happen after checks)
            total = b.end_invested_gain - b.begin_invested_gain
            sum_buy_L = sum(q * L for q, L, *_ in b.buys)
            sum_sale_L = sum(q * L for q, L, *_ in b.sales)
            sum_buy_timing = sum(q * (L - p) for q, L, p, *_ in b.buys)
            sum_sale_timing = sum(q * (s - L) for q, L, s, *_ in b.sales)
            product_effect = 0.0
            for q, L, p, product, ts in b.buys:
                if product == "ornament":
                    i_ = book.as_of_index(ts)
                    product_effect += q * ((L - book.bar_buy[i_])
                                           - (p - book.bar_sell[i_]))
            price_effect = b.end_M - b.begin_M - sum_buy_L + sum_sale_L
            timing_effect = (sum_buy_timing + sum_sale_timing) - product_effect
            fee_effect = -b.fees
            residual = total - (price_effect + timing_effect + fee_effect
                                + product_effect)
            tol = float(cfg.validation_thresholds["attribution_residual_tol_frac"])
            ok = abs(residual) <= max(0.01, tol * max(1.0, abs(total)))

            is_partial = (plan.start_date.year == y) or \
                (y == book.dates[-1].year) or b.exited

            # Modified Dietz annual return (flows weighted by remaining fraction)
            wsum = 0.0
            for d_, amt in b.flows:
                days_left = (date(y, 12, 31) - d_).days
                wsum += amt * (days_left / 365.0)
            denom = b.begin_equity + wsum
            net_flow = b.contrib - b.withdraw
            annual_return = ((b.end_equity - b.begin_equity - net_flow) / denom
                             if denom > 1e-9 else None)

            mdd = 0.0
            peak = -np.inf
            for _, eq_ in b.equity_marks:
                peak = max(peak, eq_)
                if peak > 0:
                    mdd = max(mdd, (peak - eq_) / peak)

            ann_realized = b.realized_end_cum - b.begin_realized_cum
            ann_unrealized = ((b.end_invested_gain - b.realized_end_cum
                               + b.fees_end_cum)
                              - (b.begin_invested_gain - b.begin_realized_cum
                                 + b.fees_end_cum - b.fees))
            cov_ratio = b.val_ok_months / max(1, b.val_months)
            yr = {
                "portfolio_id": st.portfolio_id,
                "cohort_start_year": plan.cohort_start_year,
                "calendar_year": y,
                "is_partial_year": bool(is_partial),
                "year_start_date": pd.Timestamp(b.begin_date)
                    if b.begin_date else pd.Timestamp(plan.start_date),
                "year_end_date": pd.Timestamp(b.end_date),
                "beginning_equity_thb": b.begin_equity,
                "ending_equity_thb": b.end_equity,
                "external_contributions_thb": b.contrib,
                "external_withdrawals_thb": b.withdraw,
                "purchase_count": b.purchase_count,
                "sale_count": b.sale_count,
                "gross_purchase_value_thb": b.gross_buy,
                "gross_sale_value_thb": b.gross_sell,
                "transaction_cost_thb": b.fees,
                "realized_pnl_thb": ann_realized,
                "unrealized_pnl_thb": ann_unrealized,
                "net_pnl_thb": total,
                "annual_return": annual_return,
                "max_drawdown": mdd,
                "data_coverage_ratio": cov_ratio,
                "calculation_quality_flag": "OK" if ok else "ATTRIB_RESIDUAL_FAIL",
                "benchmark_id": "BH_BAR_SAME_FLOWS",
                "simulation_run_id": st.simulation_run_id,
                "is_synthetic": True,
            }
            # lifetime benchmark comparison (extra column, spec 10.3)
            bi = book.exact_index(plan.start_date)
            ei = book.as_of_index(b.end_date)
            if bi is not None and ei is not None:
                bh_eq = book.benchmark_bh_equity(bi, contributions, ei)
                yr["benchmark_cum_net_pnl_thb"] = bh_eq - sum(a for _, a in contributions)
                yr["cum_net_pnl_thb"] = b.end_invested_gain
            year_rows.append(yr)

            attr_rows.append({
                "portfolio_id": st.portfolio_id,
                "calendar_year": y,
                "pnl_total_thb": total,
                "price_effect_thb": price_effect,
                "trading_timing_effect_thb": timing_effect,
                "transaction_cost_effect_thb": fee_effect,
                "product_cost_effect_thb": product_effect,
                "other_modeled_effect_thb": 0.0,
                "unattributed_residual_thb": residual,
                "benchmark_id": "BH_BAR_SAME_FLOWS",
                "attribution_method": "unit_lifecycle_vs_liquidation_quotes_v1",
                "attribution_quality_flag": "RECONCILED" if ok else "RESIDUAL_FAIL",
                "simulation_run_id": st.simulation_run_id,
                "is_synthetic": True,
            })
        return st
