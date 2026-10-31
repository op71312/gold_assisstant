# Thai Gold Portfolio Synthetic Population & Transaction Simulator

A quantitative research system that builds a **defensible synthetic population of
Thai gold-investment customer portfolios**, replays them against **historical
Thai gold quotes in the processed feature dataset (2006-2026)**, accounts for
every baht with deterministic rules, and produces **ground-truth P&L attribution**
for testing customer-facing loss-explanation systems.

> **What this is not:** the outputs are not observations of Thai investors.
> Behaviour parameters are labelled scenario assumptions. See
> `docs/limitations.md` before using any number.

## Key facts

- **Active input:** the processed `thai_gold_features_v1.csv` dataset, adapted
  into one quote row per date (bar buy/sell, ornament buy/sell, spot, USDTHB), with
  6,261 rows from 1 May 2006 through 13 Oct 2026. Its upstream feature file is
  never modified. The previous raw-announcement output set is retained separately.
- **Quote semantics (verified):** รับซื้อ = dealer buys = customer sells;
  ขายออก = dealer sells = customer buys. Prices are THB per baht-weight
  (15.244 g, 96.5% purity).
- **Engine:** event-driven chronological replay; monthly decision grid; rejected
  orders logged; weighted-average inventory costing; monthly + exit valuations;
  exact P&L attribution (price / timing / product / fees) that reconciles to
  total P&L within 1e-6 relative tolerance.
- **Validation:** 33 automated tests; accounting identity verified on all
  valuation rows; reproducibility verified by hash.

## Quickstart

```bash
# 1) environment
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) run the full pipeline (requires the input CSV; see configs/data.yaml)
export PYTHONPATH=src
python -m gold_portfolio_simulator.cli audit                  # Stage B: data audit
python -m gold_portfolio_simulator.cli research-validate      # Gate 2 check
python -m gold_portfolio_simulator.cli smoke                  # small run + checks
python -m gold_portfolio_simulator.cli full                   # 1,050 portfolios
python -m gold_portfolio_simulator.cli validate-outputs       # Gate 6 check
python -m gold_portfolio_simulator.cli verify-reproducibility # same seed -> same hashes
python -m gold_portfolio_simulator.cli sensitivity            # Stage H sensitivity
python -m gold_portfolio_simulator.cli figures                # Stage J figures
```

The full run executes only after the research-integrity gate passes, refuses to
start without the input file (no fabricated data), and writes
`artifacts/run_manifest.json` + `artifacts/checksums.txt`.

**Input dataset:** regenerate the normalized input and all simulator results
from the feature source with:

```bash
python scripts/recalculate_from_features.py --confirm-overwrite
```

The script defaults to the feature source at
`../datset a gold price/data/processed/thai_gold_features_v1.csv`, writes the
normalized simulator input to `dataset/thai_gold_features_v1_simulator_input.csv`,
and recalculates `outputs/`. It refuses to overwrite a populated output
directory unless `--confirm-overwrite` is specified. `gold_data_raw.csv` remains
untouched as the historical raw-announcement source. To use another compatible
CSV, set `GOLD_DATA_PATH` or pass `--input` to the CLI.

## Configuration (no code edits needed)

- `configs/data.yaml` — active normalized input path, column mapping, daily selection policy.
- `configs/simulation.yaml` — seed, cohorts, population size, behaviour weights,
  behaviour parameters, pricing (ornament buy-back delta, fees), valuation
  frequency, missing-price policy, validation tolerances, sensitivity variants.
- `configs/research_parameters.yaml` — evidence-backed constants and gaps.

## Project layout

```
configs/          data, research parameters, simulation (all editable)
dataset/          raw announcements + derived normalized feature input
docs/             methodology, accounting rules, data dictionary, limitations
reports/          deep research, data audit, validation, methodology review, final summary
src/gold_portfolio_simulator/
    data/         audit + daily price construction
    pricing/      quote semantics, as-of PriceBook (no-look-ahead API)
    accounting/   deterministic portfolio state machine
    population/   cohort/portfolio generator (seeded)
    behavior/     8 configurable archetypes
    simulation/   replay engine + orchestrator
    validation/   population validation, gates, figures
    cli.py        all commands
tests/            pytest suite (accounting, pricing, attribution, lookahead, repro)
outputs/          parquet + csv datasets, diagnostics, sensitivity, figures/
artifacts/        run_manifest.json, checksums.txt
```

## Outputs (outputs/)

| File | Grain |
|---|---|
| daily_market_prices.parquet/csv | one row per valid quote day |
| portfolio_master | one row per synthetic portfolio |
| transaction_ledger | one row per order (accepted + rejected) |
| cashflow_ledger | one row per contribution/withdrawal |
| portfolio_valuation_monthly | one row per portfolio-month (+ exit events) |
| portfolio_yearly | one row per portfolio-year |
| pnl_attribution_yearly | one row per portfolio-year (components) |
| simulation_diagnostics.json | run health and counts |
| sensitivity_analysis.csv | variant comparison |
| figures/*.png | the 13 required figure families |

## Command reference

| Command | Purpose (spec 15) |
|---|---|
| `audit` | Stage B data audit + daily prices + coverage tables |
| `research-validate` | Gate 2: registries complete, statuses explicit |
| `smoke` | 2 cohorts x 8 portfolios + reconciliation checks |
| `full` | configured full simulation after gates |
| `validate-outputs` | Gate 6: files exist, counts match diagnostics |
| `verify-reproducibility` | same seed reproduces identical ledgers |
| `sensitivity` | Stage H parameter ranges |
| `figures` | Stage J visualizations |

## Documentation map

- `reports/deep_research.md` — evidence base (sources S01-S14), explicit gaps
- `reports/data_audit.md` — dataset audit and selection-policy sensitivity
- `docs/methodology.md` — locked population + behaviour models
- `docs/accounting_rules.md` — price semantics, identities, attribution theorem
- `docs/data_dictionary.md` — every column of every output
- `docs/limitations.md` — what may and may not be claimed
- `reports/final_summary.md` — the 12 required answers
