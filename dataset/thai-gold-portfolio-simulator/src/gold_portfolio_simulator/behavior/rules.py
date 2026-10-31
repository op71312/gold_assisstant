"""Stage D — Transaction behaviour archetypes (spec 7).

Eight configurable, interpretable archetypes. These are candidate scenarios,
not assertions about the prevalence of Thai investor behaviour (spec 7.1).

NO LOOK-AHEAD (spec 7.3): every rule receives a `view` (PriceBook) and a
decision index `i`; the rule may only read quotes at or before `i`. The
PriceBook API exposes no future access, and tests enforce this.
"""
from __future__ import annotations

from ..pricing.quotes import PRODUCTS


def _cash_available(state, params) -> float:
    return state.cash * (1.0 - params.get("min_cash_buffer_fraction", 0.0))


def rule_buy_hold(state, view, i, params, rng, cfg) -> list[dict]:
    """Buy initial allocation at start; hold afterwards."""
    if state.tx_counter == 0 and state.contrib_cum > 0:
        return []  # initial purchase executed by the engine at funding time
    return []


def rule_dca(state, view, i, params, rng, cfg) -> list[dict]:
    """Monthly contribution + purchase of the contributed amount.
    The purchase order is only submitted when the accumulated cash can afford
    the product's smallest tradable unit (an affordability check at decision
    time uses only current quotes - no look-ahead); otherwise the investor
    keeps saving until the next decision date."""
    orders = []
    amt = float(params.get("dca_monthly_contribution_thb", 1000.0))
    if amt > 0:
        orders.append({"kind": "external_contribution", "amount_thb": amt})
        product = state._primary_product
        spec = PRODUCTS[product]
        min_cost = spec.min_qty_bw * view.buy_price(i, product)
        if state.cash + amt >= min_cost:
            orders.append({"kind": "buy", "product": product,
                           "budget_thb": min(state.cash + amt,
                                             max(amt, min_cost))})
    return orders


def rule_buy_dip(state, view, i, params, rng, cfg) -> list[dict]:
    """Buy additional gold after a price decline vs trailing max (A07)."""
    orders = []
    thr = float(params.get("dip_threshold", 0.97))
    lb = int(params.get("dip_lookback_days", 90))
    px = view.bar_sell[i]
    tmax = view.trailing_max_bar_sell(i, lb)
    if tmax > 0 and px <= thr * tmax:
        budget = _cash_available(state, params) * float(
            params.get("dip_buy_fraction_of_cash", 0.5))
        if budget > 0:
            product = state._primary_product
            orders.append({"kind": "buy", "product": product, "budget_thb": budget})
    return orders


def rule_buy_momentum(state, view, i, params, rng, cfg) -> list[dict]:
    """Trend-following: buy when fast MA > slow MA, sell fraction on inversion."""
    orders = []
    f = int(params.get("momentum_fast_days", 20))
    s = int(params.get("momentum_slow_days", 60))
    fast = view.trailing_ma(i, f)
    slow = view.trailing_ma(i, s)
    product = state._primary_product
    if fast > slow:
        budget = _cash_available(state, params) * float(
            params.get("momentum_buy_fraction_of_cash", 0.5))
        if budget > 0:
            orders.append({"kind": "buy", "product": product, "budget_thb": budget})
    elif fast < slow and state.qty.get(product, 0) > 0:
        orders.append({"kind": "sell", "product": product,
                       "fraction": float(params.get("momentum_sell_fraction", 0.5))})
    return orders


def rule_partial_profit_taking(state, view, i, params, rng, cfg) -> list[dict]:
    """Sell a fraction of holdings when unrealized gain exceeds a threshold."""
    orders = []
    thr = float(params.get("profit_gain_threshold", 0.15))
    product = state._primary_product
    q = state.qty.get(product, 0.0)
    if q > 0:
        liq = view.liquidation_price(i, product)
        wac = state.wac.get(product, 0.0)
        if wac > 0 and (liq / wac - 1.0) >= thr:
            orders.append({"kind": "sell", "product": product,
                           "fraction": float(params.get("profit_sell_fraction", 0.25))})
    return orders


def rule_active_rotation(state, view, i, params, rng, cfg) -> list[dict]:
    """Discretionary repeated buying and selling with fixed probabilities."""
    orders = []
    product = state._primary_product
    frac = float(params.get("rotation_trade_fraction", 0.2))
    if rng.random() < float(params.get("rotation_buy_prob", 0.3)):
        budget = _cash_available(state, params) * frac
        if budget > 0:
            orders.append({"kind": "buy", "product": product, "budget_thb": budget})
    if rng.random() < float(params.get("rotation_sell_prob", 0.2)):
        if state.qty.get(product, 0) > 0:
            orders.append({"kind": "sell", "product": product, "fraction": frac})
    return orders


def rule_liquidity_sale(state, view, i, params, rng, cfg) -> list[dict]:
    """Poisson liquidity shock: sell all gold and withdraw the proceeds (A09)."""
    orders = []
    lam = float(params.get("liquidity_shock_lambda_month", 0.02))
    if rng.random() < lam:
        for product, q in list(state.qty.items()):
            if q > 0:
                orders.append({"kind": "sell", "product": product, "fraction": 1.0})
        orders.append({"kind": "external_withdraw_all"})
    return orders


def rule_inactive(state, view, i, params, rng, cfg) -> list[dict]:
    """Initial purchase only; never trades again."""
    return []


RULES = {
    "buy_hold": rule_buy_hold,
    "dca": rule_dca,
    "buy_dip": rule_buy_dip,
    "buy_momentum": rule_buy_momentum,
    "partial_profit_taking": rule_partial_profit_taking,
    "active_rotation": rule_active_rotation,
    "liquidity_sale": rule_liquidity_sale,
    "inactive": rule_inactive,
}
