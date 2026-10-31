# Methodology

This document locks the portfolio population model (Stage C) and the transaction
behaviour model (Stage D) before the Monte Carlo run, per spec sections 6-8.

## 1. Two complementary views (spec 6.1)

**View 1 — Annual investment cohorts.** One cohort per calendar year from 2006
through 2026 (the observed data span). Each cohort holds `portfolios_per_cohort`
synthetic portfolios (default 50). A portfolio's holdings, cost basis and cash
carry forward from its start date until the end of the data or a defined exit
event (liquidity shock). Cohort 2006 starts after 1 May 2006 (first observed
quote); cohort 2026 is flagged as a partial year.

**View 2 — Annual portfolio snapshots.** `portfolio_yearly.parquet` contains one
row per portfolio per calendar year in which the portfolio was active. A
continuing portfolio appears in multiple annual snapshots; `cohort_start_year`
identifies the original cohort and `is_partial_year` flags first/last years.
No snapshot row is ever a "new population".

Every record identifies: calendar year, original cohort, portfolio identity,
and whether the portfolio is newly started (`year_start_date == start_timestamp`)
or continuing.

## 2. Initial capital (spec 6.2)

**Status: scenario assumption A01 — NOT empirically calibrated.**

- Distribution: lognormal over *baht-weight affordability units*,
  median 1.0 baht-weight, sigma 0.9, floored at THB 6,000.
- Because the unit is baht-weight, nominal capital scales automatically with the
  observed price level of the cohort year (e.g. median ≈ THB 11,800 in 2006,
  ≈ THB 65,000 in 2026).
- Rationale: (i) wealth concentration evidence (S07: top 10% hold 66% of wealth)
  motivates a right-skewed shape; (ii) retail gold purchases are quoted per
  baht-weight with minimum unit sizes, so affordability is the natural scale;
  (iii) no survey of gold-investor capital was found (explicit gap, see
  `reports/deep_research.md` section 5).
- Sensitivity range: median_bw ∈ [0.5, 2.0], sigma ∈ [0.6, 1.2]
  (executed by the `sensitivity` command).

Each portfolio records: initial capital, initial cash, initial gold quantity and
value, product type, start date, segment label (scenario label only), behaviour
scenario, parameter-set id, and a reproducibility seed id (spec 6.2 list).

**Households with no gold are out of scope by construction**: the population is a
*customer-portfolio population* (gold-investing customers), which is the target
of the downstream loss-explanation system. Prevalence of gold ownership among all
Thai households is therefore reported as reference evidence only (S05), never as
a simulated output (spec 6.3).

## 3. Initial gold allocation (spec 6.3)

The five concepts are kept separate:

1. *Probability of holding gold*: 100% conditional on being in the population
   (customer portfolios). Not a household prevalence claim.
2. *Share of capital allocated to gold*: Beta(2,2) scaled to [0.3, 0.9]
   (assumption A02); DCA portfolios start at 10% and accumulate.
3. *Amount and form*: product type bar (65% target, A03) or ornament (35%);
   minimum tradable units: bar = 1 baht-weight, ornament = 0.25 baht-weight
   (1 salung, A12). If the target product is unaffordable with the sampled
   capital, the portfolio falls back to the other product's smallest unit
   (documented affordability fallback); if even that fails, the portfolio starts
   in cash and retries at monthly decisions ("saving up").
4. *Cash buffer*: remainder of initial capital stays in cash.
5. *External capital*: only DCA portfolios receive recurring contributions
   (THB 1,000/month, A05-family parameter); all contributions are recorded in
   the cash-flow ledger and never counted as investment profit.

## 4. Initialization and cost basis (spec 6.4)

Rule `contribute_then_buy` (A13): the portfolio is established on its start date
with an external contribution followed by an immediate purchase at that day's
observed customer price. **No pre-existing gold and no unobserved historical cost
basis is ever assigned.** The alternative initialization (pre-existing gold) is
explicitly not implemented because the historical acquisition price would be
unknowable; its impact is confined to first-year attribution and is avoided by
construction.

## 5. Behaviour archetypes (spec 7.1-7.2)

Eight configurable archetypes (weights = scenario assumption A05; equal by
default). Rules, triggers, and information sets:

| Scenario | Trigger (information available at decision time only) | Action | Size rule |
|---|---|---|---|
| buy_hold | none after initial purchase | hold | - |
| dca | monthly decision | contribute THB 1,000 + buy | budget = contribution (when affordable) |
| buy_dip | bar_sell ≤ 97% of trailing 90-day max (A07) | buy | 50% of available cash |
| buy_momentum | 20-day MA > 60-day MA (A08); inverted → sell | buy / sell | 50% of cash / 50% of holdings |
| partial_profit_taking | unrealized gain ≥ 15% over WAC | sell | 25% of holdings |
| active_rotation | p(buy)=0.30, p(sell)=0.20 per month (A06 family) | buy / sell | 20% fractions |
| liquidity_sale | Poisson shock λ=0.02/month (A09) | sell all + withdraw all | full exit |
| inactive | none | hold forever | - |

Common constraints: minimum cash buffer 5% of equity, gold exposure cap
(≤ 100% of equity, configurable), product quantity increments, minimum trade
units, and stop-after-exit. When a decision date has no valid quote (missing
months, GTA non-publication days), the decision rolls forward up to 5 days and
is otherwise logged as `REJECTED / NO_VALID_PRICE` (policy `skip_and_log`).

## 6. No look-ahead (spec 7.3)

Decision rules receive a `PriceBook` view and a decision index; the API exposes
only quotes at or before the decision index (`as_of`, `trailing_*`). Decision
dates are drawn from a per-portfolio RNG independent of future prices. A
transaction on date t uses the customer-side quote of the *execution* date
(rolled forward ≤ 5 days). Future prices are used only for subsequent
valuations, which is permitted by spec 7.3. Tests (`tests/test_no_lookahead.py`)
verify that a dip rule is silent before a late crash on a monotone path and that
every accepted execution price equals the quote of its own timestamp.

## 7. Behaviour vs capital-flow separation (spec 7.4)

Separate records: initial funding, additional contributions and withdrawals live
in `cashflow_ledger.parquet`; purchases, sales and their P&L live in
`transaction_ledger.parquet`. Contributions never enter investment P&L and
withdrawals never automatically become losses (identity I2 in
`docs/accounting_rules.md`, tested).

## 8. Monte Carlo design (spec 8)

- Sampling unit: the synthetic portfolio. Sampled: start date, capital, product,
  allocation share, behaviour scenario, decision-day offsets, rule randomness.
- Hierarchy: cohort year → portfolio → behaviour → transactions → valuation.
  Year-specific parameters: none beyond the price level (documented; annual
  behaviour distributions would be manufactured precision — spec 8.2).
- Correlations: capital, allocation and product are sampled independently
  (baseline) because no dependence evidence exists (spec 8.3); dependence
  structures are configurable but not asserted.
- Time sampling: decisions on a monthly grid (random day 1-28), executed on the
  next valid quote day within 5 days (spec 8.4).
- Reproducibility: `numpy.SeedSequence(global_seed).spawn()` per cohort, per
  portfolio; identical config + seed reproduces identical outputs (tested,
  spec 8.5).
- Scale: default 50 portfolios/cohort × 21 cohorts = 1,050 portfolios (config);
  smoke scale 8×2 for development (spec 8.6).
