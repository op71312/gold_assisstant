# Data Dictionary

All monetary values in THB; gold quantities in baht-weight (bw; 1 bw = 15.244 g
of 96.5% gold). `is_synthetic = True` on every simulated record.

## Upstream source — `dataset/gold_data_raw.csv`

The raw announcement archive is retained and is not modified by the feature-based
recalculation. Active simulator outputs are now rebuilt from
`dataset/thai_gold_features_v1_simulator_input.csv`, generated from
`thai_gold_features_v1.csv` by `scripts/recalculate_from_features.py`.

The feature source's `valid_price_pair` field is a price-change computability
flag: it is false for a first observation without a previous same-day quote.
It is not a test of whether the quote prices are valid, so the adapter keeps
these rows when the actual buy/sell prices are positive and ordered.
The feature source includes `ornament_buy`, used as the observed customer SELL
quote for ornaments. `ornament_tax_base_thb` is not present and is retained as
null in the adapted input; it is not used by the portfolio replay. Assumption
A04 is only a fallback for input sources without an observed ornament buy quote.

## Legacy raw-announcement schema — `dataset/gold_data_raw.csv`

| Column | Type | Meaning |
|---|---|---|
| timestamp | datetime | announcement date/time (converted from Thai Buddhist era) |
| announce_seq | int | sequence of the announcement within the day |
| bar_buy_thb | float | GTA bar purchase quote (customer SELL side) |
| bar_sell_thb | float | GTA bar selling quote (customer BUY side) |
| ornament_buy_thb | float | Ornament dealer purchase quote (customer SELL side) when available |
| ornament_tax_base_thb | float | GTA ornament tax-base reference |
| ornament_sell_thb | float | GTA ornament selling quote (customer BUY side) |
| gold_spot_usd | float | gold spot, USD/oz (reference) |
| usd_thb | float | THB per USD (reference) |
| change_thb | float | announced change vs previous quote |
| source_url | str | archive page of the announcement |

## `daily_market_prices` (outputs/, parquet + csv)

One row per calendar date with a valid bar quote pair; selection policy
`last_valid_of_day` (last announcement of the day); **no imputation** across days.
For the active feature-derived run, the feature source already has one row per
date, so the policy selects that daily quote. The quote timestamp and available
price/FX fields are carried through; unavailable ornament tax base values remain
null.

| Column | Meaning |
|---|---|
| date, price_quote_timestamp | selected quote day and exact timestamp |
| bar_buy_thb, bar_sell_thb | two-sided bar quote |
| ornament_buy_thb, ornament_sell_thb, ornament_tax_base_thb | observed ornament buy/sell quotes and optional tax-base reference |
| gold_spot_usd, usd_thb, change_thb | reference series |
| announce_seq, selection_policy, quality_flag | provenance |

## `portfolio_master`

| Column | Meaning |
|---|---|
| portfolio_id | `P{cohort_year}{index:04d}` |
| cohort_start_year | original cohort |
| start_timestamp, end_timestamp | inception; last valuation or exit event |
| portfolio_segment | scenario label (`mass_retail`/`affluent_retail`) — not evidence-based |
| gold_product_type | `bar` or `ornament` (post-fallback) |
| initial_capital_thb | first contribution (external funding) |
| initial_cash_thb / initial_gold_quantity / initial_gold_value_thb | split at inception |
| behavior_scenario | one of the 8 archetypes |
| parameter_set_id, random_seed_id, simulation_run_id | reproducibility |
| is_synthetic (always True), calibration_status | `SCENARIO_ASSUMPTION` |

## `transaction_ledger`

Grain: one row per simulated order, including rejected orders.

| Column | Meaning |
|---|---|
| transaction_id | `{portfolio_id}-T{seq}` |
| event_timestamp, calendar_year | execution date (rolled quote day) |
| event_type | GOLD_PURCHASE / GOLD_SALE / DECISION_SKIPPED |
| gold_product_type, side | bar/ornament; BUY/SELL |
| requested_quantity_bw, executed_quantity_bw | baht-weight (bar: 1.0 steps; ornament: 0.25 steps) |
| price_quote_timestamp, customer_execution_price_thb_per_bw | the quote used and the customer-side price |
| gross_amount_thb, transaction_cost_thb, net_cash_change_thb | amounts |
| realized_pnl_thb | WAC-based, sales only |
| execution_status, rejection_reason | ACCEPTED / REJECTED + reason |
| behavior_scenario, parameter_set_id, simulation_run_id, is_synthetic | provenance |
| source_quote_id | join key `GTA:{quote timestamp}` back to the announcement |

Quantity × price units: THB per baht-weight × baht-weight = THB. Never ambiguous.

## `cashflow_ledger`

Grain: one row per external funding/withdrawal event. `cashflow_type` ∈
{initial_contribution, additional_contribution, withdrawal}. Kept separate from
the transaction ledger so capital flows cannot be mistaken for performance.

## `portfolio_valuation_monthly`

Grain: one row per portfolio per month-end quote day (plus `EXIT_EVENT` rows).
Multi-product holdings are stored as separate quantity columns
(`gold_qty_bar_bw`, `gold_qty_ornament_bw`) — never a mixed single quantity.
Includes cash, cost basis, liquidation value, equity, net contributed capital,
cumulative realized / unrealized / fees / net P&L, valuation price timestamp and
quality flag.

## `portfolio_yearly`

Grain: one row per portfolio per active calendar year. `net_pnl_thb` is the
**annual** investment P&L (Δ invested gain); `realized_pnl_thb` and
`unrealized_pnl_thb` are annual deltas (not cumulative). `annual_return` is
Modified Dietz (None when the denominator is non-positive). `max_drawdown` uses
monthly equity marks within the year. `is_partial_year` flags inception/exit/final
years. Extra columns `cum_net_pnl_thb` and `benchmark_cum_net_pnl_thb` support the
lifetime benchmark comparison (BH_BAR_SAME_FLOWS).

## `pnl_attribution_yearly`

Grain: one row per portfolio per calendar year. Components (see
`docs/accounting_rules.md` §6): `price_effect_thb`, `trading_timing_effect_thb`,
`transaction_cost_effect_thb`, `product_cost_effect_thb`,
`other_modeled_effect_thb` (0; FX is N/A for V1 products),
`unattributed_residual_thb` (≈ 0; enforced), `attribution_method` =
`unit_lifecycle_vs_liquidation_quotes_v1`, `attribution_quality_flag` =
RECONCILED / RESIDUAL_FAIL.

## `simulation_diagnostics.json`

Machine-readable run summary: counts, acceptance/rejection breakdown,
reconciliation results, reproducibility metadata, calibration gaps, warnings,
and validation failures (never reports success if a required check failed).
