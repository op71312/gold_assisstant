# Historical Final Summary — R001 (raw-announcement input)

> This report documents the archived R001 run using the raw announcement input.
> It is not the active feature-derived run. See `feature_v1_recalculation.md`
> for the current dataset and recalculated outputs.

Run `R001` (seed 20261022) · 1,050 portfolios · 21 cohorts (2006-2026) ·
generated 2026-10-22 · all six acceptance gates **PASS**.

## Executive summary

The project delivers a complete, tested, reproducible simulation system that
answers its core question — *"why did a gold portfolio lose money, and how much
did each factor contribute?"* — with auditable accounting rather than guessing.
It builds a synthetic population of Thai gold-investment customer portfolios,
replays ~20 years of behaviour against **23,385 real Gold Traders Association
price announcements (May 2006 – Oct 2026)**, and produces deterministic,
reconciling P&L attributions. Every behavioural parameter is a labelled scenario
assumption; every price and spread is observed data. The population is a test
bench for loss-explanation systems — it is **not** a calibrated sample of Thai
investors.

## Answers to the required questions

**1. What evidence about Thai gold portfolios was found?**
Thailand's retail gold investment market is large and active: 39.8 t of bar &
coin demand in 2024 (+17% y/y, 7th globally), 9.0 t jewellery consumption,
10.0 t bar & coin in Q2 2025 alone, and 10.9 t investment demand in Q2 2026
(WGC, S01-S04). WGC survey evidence: 46% of surveyed Thai investors own gold;
motivations are wealth protection (34%), long-term returns (32%), speculation
(17%); dip-buying and hold-through-drawdown behaviour documented at market level
(S05, S06). Full trail: `outputs/source_registry.csv`, `reports/deep_research.md`.

**2. Which parameters are empirically supported?**
Price history (23,385 announcements, sanity-checked against USD spot × USDTHB),
dealer spreads (directly from two-sided quotes), gold conventions (15.244 g,
96.5%), market demand context, and the wealth-concentration shape (top 10% hold
66% of wealth, S07). See `outputs/parameter_evidence.csv`.

**3. Which parameters remain assumptions?**
Transaction frequency and size, initial capital level, behaviour mix weights,
holding periods, the ornament buy-back quote, and all rule thresholds
(dip/momentum/shock). All are in `outputs/assumptions_register.csv` (A01-A15)
with sensitivity ranges; none is presented as fact.

**4. What simulation model was implemented?**
An event-driven Monte Carlo historical replay: 21 annual cohorts → 1,050
seeded portfolios (lognormal baht-weight affordability, Beta allocation, bar/
ornament products with market-convention minimum units) → 8 behaviour
archetypes on a monthly decision grid with no look-ahead → deterministic
weighted-average-cost accounting → monthly and exit-event valuations → exact
unit-lifecycle P&L attribution (`unit_lifecycle_vs_liquidation_quotes_v1`) and a
buy-and-hold bar benchmark (`BH_BAR_SAME_FLOWS`). Docs: `docs/methodology.md`,
`docs/accounting_rules.md`.

**5. How many portfolios and transactions were generated?**
(counts read from the actual outputs)
- Portfolios: **1,050** across **21 cohorts**
- Transaction events: **40,089** (18,337 accepted; 21,752 rejected with logged
  reasons — 19,311 below-minimum-trade-unit, 2,441 no-valid-price)
- Accepted buys: 4,448 (THB 58.8M gross); accepted sells: 13,889 (THB 35.8M)
- Portfolio-year records: **10,845**; monthly valuations: **117,356**
- Cash-flow records and attribution rows: 10,845 attribution rows (plus cashflow
  ledger; see `simulation_diagnostics.json`)

**6. What years and products does the simulator cover?**
Calendar years 2006 (from 1 May) through 2026 (to 22 Oct, partial). Products:
gold bars (1 baht-weight units) and gold ornaments (0.25 baht-weight units),
both quoted per baht-weight at 96.5% purity. ETFs/futures/online gold are
explicitly out of scope for V1 (spec 3.2).

**7. Did all financial accounting checks pass?**
Yes. 33 automated tests pass (the 14 spec-11.1 checks, pricing semantics,
transaction constraints, attribution, no-look-ahead, reproducibility). Across
all 117,356 valuations the equity identity held with max error 2.3e-5 THB;
attribution components reconcile to total P&L with max residual 2.3e-5 THB
(1e-6 relative tolerance); rejected orders are never silently corrected; external
flows are provably separated from investment P&L.

**8. How closely did the synthetic population match available reference evidence?**
Only one valid comparison layer exists: simulated annual outcomes track the
observed market (e.g. 2013 crash: 91.4% of portfolio-years negative; 2024-2025
rally: strongly positive; loss-year share 19.8% overall) because portfolios are
priced with real quotes. Population-level characteristics (prevalence, capital,
frequency) are `NOT_EMPIRICALLY_VALIDATED` — see the table in
`reports/validation_report.md`. Aggregate turnover is reported as order-of-
magnitude context only.

**9. Which outputs are suitable for downstream customer-loss analysis?**
`transaction_ledger`, `cashflow_ledger`, `portfolio_valuation_monthly`,
`portfolio_yearly`, and `pnl_attribution_yearly` — every record is auditable to
the source quote via `source_quote_id`, with realized/unrealized splits, costs,
flows, drawdowns and reconciling attribution components. These are the ground
truth for testing an explanation engine.

**10. Which claims must NOT yet be made about real Thai investors?**
That they trade at particular frequencies or sizes; that they hold particular
initial amounts; that any loss rate here reflects Thailand's actual investor
loss distribution; that the behaviour mix mirrors real behaviour; that ornament
buy-back prices followed the modeled convention. See `docs/limitations.md` §6.

**11. What further real-world data would most improve validity?**
(1) anonymized customer-level transactions from a dealer or digital-gold
platform; (2) historical ornament buy-back quotes; (3) entry-amount and
contribution surveys; (4) behaviour-mix estimates to replace equal weights.

**12. What should be implemented next?**
(1) plug the original `gold_data_cleaned.csv` (2006-2026) into the same pipeline
via `--input`; (2) implement the online-gold / digital-savings extension behind
its own pricing convention; (3) add FIFO costing as a config option;
(4) richer counterfactual benchmarks (monthly DCA benchmark, lump-sum-at-start
benchmark); (5) an explanation generator that consumes
`pnl_attribution_yearly` and emits structured, auditable customer narratives.

## Acceptance gates

| Gate | Result |
|---|---|
| Gate 1: Data integrity | **PASS** |
| Gate 2: Research integrity | **PASS** |
| Gate 3: Accounting correctness | **PASS** |
| Gate 4: Simulation validity | **PASS** |
| Gate 5: Attribution validity | **PASS** |
| Gate 6: Output completeness | **PASS** |

## How to run

```bash
pip install -r requirements.txt
export PYTHONPATH=src
python -m gold_portfolio_simulator.cli audit
python -m gold_portfolio_simulator.cli research-validate
python -m gold_portfolio_simulator.cli smoke
python -m gold_portfolio_simulator.cli full
python -m gold_portfolio_simulator.cli validate-outputs
python -m gold_portfolio_simulator.cli verify-reproducibility
python -m gold_portfolio_simulator.cli sensitivity
python -m gold_portfolio_simulator.cli figures
```

## Limitations table

| # | Limitation | Severity | Mitigation |
|---|---|---|---|
| 1 | Behaviour parameters uncalibrated (frequency, size, mix) | High | Equal-weight scenarios, sensitivity analysis, NOT_EMPIRICALLY_VALIDATED labels |
| 2 | Ornament buy-back quote modeled (A04) | Medium | Anchored to observed bar buy; delta sensitivity run |
| 3 | Source mirror gaps: Mar 2013, Aug-Nov 2016, Aug-Nov 2017, 1-14 Oct 2026 | Medium | No imputation; skip-and-log policy; coverage tables |
| 4 | 2026 partial year | Low | Flagged `is_partial_year` |
| 5 | Market-wide GTA quotes ≠ individual shop spreads | Medium | Documented; spreads vary with data |
| 6 | Weighted-average costing only | Low | Documented choice, consistent with attribution |
| 7 | Affordability fallback shifts product mix from 65/35 | Low | Realistic behaviour, documented in methodology §3 |
| 8 | Original spec dataset not available in this environment | Low | Same-family real dataset acquired (S10); original file drop-in compatible |

## Reproducibility

`artifacts/run_manifest.json` records the input checksum, config checksums,
seed, parameters, counts and validation results; `artifacts/checksums.txt`
covers all major outputs. Re-running `full` with the same config and seed
reproduces identical ledgers (verified by `verify-reproducibility`).
