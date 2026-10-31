# Accounting Rules

Deterministic accounting for physical gold portfolios (spec 9.3-9.5, Stage G).
Monte Carlo never generates P&L directly; every number below is derived from
holdings, cash flows, observed quotes and recorded execution prices.

## 1. Price semantics (verified, spec 5.2)

From the published GTA table (source S10):

| Column | Dealer action | Customer action | Used as |
|---|---|---|---|
| `bar_buy` (รับซื้อ) | buys bar from customer | customer SELLS bar | sale execution price; **liquidation value of bars** |
| `bar_sell` (ขายออก) | sells bar to customer | customer BUYS bar | purchase execution price (bars) |
| `ornament_sell` (ขายออก) | sells ornament to customer | customer BUYS ornament | purchase execution price (ornaments, incl. wage) |
| ornament buy-back | observed `ornament_buy` when present; otherwise unavailable in raw archive | customer SELLS ornament | use observed quote; otherwise fallback `bar_buy + delta` (A04; default delta=THB 100) |
| `ornament_tax_base` (ฐานภาษี) | reference | reference | carried through, never used for execution |

Units: THB per 1 baht-weight (15.244 g) of 96.5% gold. Quantities in baht-weight.

## 2. State (per portfolio)

cash; quantity and weighted-average cost (WAC) per product; cumulative realized
P&L; cumulative fees; cumulative contributions; cumulative withdrawals.

## 3. Transaction rules

**Buy** (customer pays): validate cash ≥ cost + fee and quantity ≥ product
minimum; WAC update: `wac' = (wac·q_old + p·q) / (q_old + q)`; cash decreases by
`p·q + fee`. Fees are expensed to `fees_cum`, not capitalized into WAC.

**Sell** (customer receives): validate holdings ≥ quantity; realized P&L per
weighted-average costing: `realized = q·(s − wac)`; cash increases by
`s·q − fee`; WAC unchanged for remaining units.

**Rejected orders** are recorded with a reason (`INSUFFICIENT_CASH`,
`INSUFFICIENT_HOLDINGS`, `BELOW_MIN_TRADE_UNIT`, `NON_POSITIVE_QUANTITY`,
`NO_VALID_PRICE`) and never silently corrected (spec 9.1).

## 4. Valuation

- **Liquidation value** `M = Σ q·L` where `L` is the customer's *receivable*
  price (dealer buy side): `bar_buy` for bars, modeled buy-back for ornaments.
  The purchase-side quote is never used for valuation (spec 9.4).
- **Unrealized P&L** = `M − Σ q·wac`.
- **Equity** = cash + M.
- **Net contributed capital** = contributions − withdrawals.
- Monthly valuations at each month's last valid quote day; an exit event adds a
  final valuation flagged `EXIT_EVENT`.

## 5. Accounting identities (enforced and tested)

- **I1** `equity == cash + Σ q·L`
- **I2** `equity − (contributions − withdrawals) == realized_cum + unrealized − fees_cum`
- Contributions never create investment profit; withdrawals never create
  investment loss (spec 11.1 checks 6-7).
- Verified across all 117,356 valuations of the full run: max error 2.3e-5 THB
  (floating-point dust).

## 6. P&L attribution (spec 10.3, 12.6)

Definitions: `L(t)` = liquidation quote at t; `p` = customer buy price;
`s` = customer sell price; `M` = holdings liquidation value. For a year window
beginning before all events (new portfolios) or at the prior year-end valuation:

- **price_effect** `= M_end − M_begin − Σ_buys q·L + Σ_sales q·L`
  (market movement on every unit lifecycle within the year)
- **product_cost_effect** `= Σ_ornament_buys q·[(L − bar_buy) − (p − bar_sell)]`
  (wage/premium paid vs recovery; 0 for bars)
- **trading_timing_effect** `= Σ_buys q·(L − p) + Σ_sales q·(s − L) − product_cost_effect`
  (dealer spread paid at execution; sale side is 0 by construction because sales
  execute at the receivable quote)
- **transaction_cost_effect** `= −fees` (explicit fees; 0 in baseline)
- **pnl_total** `= invested_gain_end − invested_gain_begin`
  where `invested_gain = realized_cum + unrealized − fees_cum = equity − net_contributed`

**Reconciliation theorem** (derived algebraically; enforced within 1e-6 relative
tolerance and tested on random paths):

```
price_effect + trading_timing_effect + product_cost_effect + transaction_cost_effect
    == pnl_total
```

The spread paid on each purchase telescopes against the L-terms, making the
identity exact. The unattributed residual is 0 up to floating point.

**FX exposure**: bars and ornaments are THB-denominated local dealer products.
The THB/USD and gold-spot columns are reference data only; no instrument in V1
has a directly modeled FX exposure, so the FX effect is reported as N/A rather
than fabricated (spec 10.3). Explanations such as "the customer bought at
relatively high prices" are grounded in per-purchase `price_effect` and the
benchmark comparison, not in correlation guesses.

## 7. Returns (spec 9.5)

- **Annual return** = Modified Dietz over the calendar year:
  `r = (E_end − E_begin − net_flows) / (E_begin + Σ flow_i·w_i)`, with `w_i` the
  remaining fraction of the year at each flow. External flows are flow-adjusted,
  never treated as performance. Partial years are flagged `is_partial_year`.
- **max_drawdown** = max peak-to-trough of monthly (plus exit-event) equity
  marks within the year (A15; daily marks configurable).
- Lifetime-to-date attribution uses the same formulas with the window from
  portfolio inception.

## 8. Benchmark

`BH_BAR_SAME_FLOWS`: buy-and-hold bar gold where every cash contribution buys
bar gold at that day's `bar_sell` quote (rolled ≤ 7 days) and is never sold.
Lifetime benchmark P&L = benchmark liquidation value − total contributions.
Stored per portfolio-year as `benchmark_cum_net_pnl_thb` and
`cum_net_pnl_thb` for comparison (spec 10.2-10.3); it is a *comparison*, not an
additive attribution component.
