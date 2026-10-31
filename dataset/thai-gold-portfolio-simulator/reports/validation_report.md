# Validation Report

Run `R001` generated 1050 portfolios, 40089 transaction events, 10845 portfolio-year records and 117356 monthly valuations.

## Accounting correctness
- Accounting reconciliation failures across all valuation rows: **0** (max error 2.28e-05 THB)
- Attribution reconciliation failures: **0** (max residual 2.28e-05 THB)
- Rejected orders: 21752 ({'BELOW_MIN_TRADE_UNIT': 19311, '': 18337, 'NO_VALID_PRICE': 2441})
- Unit tests: 33 tests covering the 14 accounting checks of spec 11.1, pricing semantics, transaction constraints, no-look-ahead and reproducibility (`pytest tests/`).

## Population validation vs reference evidence
| Metric | Reference | Simulated | Method | Valid? | Limitations |
|---|---|---|---|---|---|
| gold_ownership_prevalence | 46% of surveyed investors (S05) | 100% by construction (customer-portfolio population) | not comparable (different populations) | NO | Simulated population conditions on being a gold customer |
| aggregate_net_gold_purchased_lifetime | 39.8 t national bar & coin demand 2024 (S01) | 0.01 t across 1050 synthetic portfolios (20 years) | order-of-magnitude context only | NO | Simulation is a sample of scenarios, not a census; not a calibration target |
| bar_product_share_at_construction | 65% (assumption A03) | 31.0% after affordability fallback | config vs realized | yes | Affordability fallback moves small portfolios to ornaments (documented) |
| initial_capital_distribution | no reference observation | median 23,564 THB; p10 6,789; p90 82,265 | NOT_EMPIRICALLY_VALIDATED | NO | Scenario assumption A01 informed by S07 skew only |
| transaction_size | no reference observation | median 7,575 THB per buy | NOT_EMPIRICALLY_VALIDATED | NO | Spec 4.3 forbids fabricated calibration |
| transaction_frequency | no reference observation | 17.5 accepted transactions per portfolio (lifetime mean) | NOT_EMPIRICALLY_VALIDATED | NO | Scenario parameter A05-A09 |
| median_annual_return_vs_market_direction | observed bar price annual change (corr computed over 21 years) | Pearson r = 0.99 | sign/level association check | yes | Simulated returns include spread drag and behaviour, so levels differ |

Metrics marked NOT_EMPIRICALLY_VALIDATED have no reference observation; they are scenario parameters (see outputs/assumptions_register.csv).

## Market-period context
Simulated annual loss concentration follows the observed quote history: the 2013 gold crash (91% of portfolio-years negative), the 2014-2015 and 2018 bear phases, and strong positive years 2020/2024/2025. These are outcomes of modeled behaviour under real historical prices, NOT actual losses reported by Thai households (spec 11.5).

## Warnings
- None.