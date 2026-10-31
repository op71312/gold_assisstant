# Limitations

Read this before making any claim from the outputs.

## 1. What the outputs are NOT

- **Not observations of Thai investors.** Every portfolio, transaction and P&L
  record is synthetic. The dataset must never be described as real Thai customer
  data (spec 2.2).
- **Not a representative sample of Thai households.** The population conditions
  on being a gold-investing customer; prevalence (46% of surveyed investors own
  gold, S05) is reference evidence, not a simulated or calibrated output.
- **Not causally proven explanations.** Attribution components are accounting
  decompositions under stated conventions, not econometric causal estimates.

## 2. Empirically supported layers

| Layer | Support |
|---|---|
| Active price history 2006-2026 | 6,261 daily quotes from `thai_gold_features_v1.csv` (S15), derived from GTA market data; the unmodified raw announcement archive remains available as upstream data (S10) |
| Dealer spreads | Directly observed two-sided quotes (data-driven, varies over time) |
| Market demand context | WGC country series (S01-S04) |
| Wealth skew (shape only) | OECD 2025 (S07) |

## 3. Explicit gaps (assumptions, NOT calibration)

| Parameter | Assumption | Impact if wrong |
|---|---|---|
| Transaction frequency | Archetype rules, equal weights (A05) | Changes turnover and cost drag |
| Transaction size | Lognormal baht-weight affordability (A01) | Changes P&L dispersion |
| Initial capital | Same as above | Changes loss/gain magnitude |
| Behaviour mix | Equal weights across 8 archetypes | Changes aggregate outcomes |
| Holding period | Emergent from archetypes | NOT_EMPIRICALLY_VALIDATED |
| Ornament buy-back quote | Active feature dataset provides observed daily `ornament_buy`; fallback `bar_buy + delta` (A04) only for sources without it | Directly shifts ornament realized P&L; A04 remains uncalibrated for legacy raw-source runs |
| Dip/momentum thresholds | 97% / MA 20-60 (A07/A08) | Entry timing quality |
| Liquidity shock rate | λ = 0.02/month (A09) | Forced-loss frequency |

Full register with sensitivity ranges: `outputs/assumptions_register.csv`;
sensitivity results: `outputs/sensitivity_analysis.csv` and figure f13.

## 4. Data coverage limitations

- No imputation is performed; quote gaps in the active feature dataset cause
  trades/valuations to skip or roll according to the configured policy.
- The active feature dataset ends on 13 Oct 2026, so 2026 is partial; the
  upstream raw archive extends later but is not used in the active run.
- Weekend quotes are not published (GTA schedule); decision roll-forward is
  limited to 5 days.
- Quotes are market-wide GTA announcements — individual shop spreads (typically
  wider, especially upcountry) are not represented.
- The user's original `gold_data_cleaned.csv` (Windows path in the spec) was not
  available in this environment; a real dataset of the same announcement family
  was acquired and documented instead (S10). The pipeline accepts the original
  file via `--input`/`GOLD_DATA_PATH` without code changes.

## 5. Modeling limitations

- Ornament wage/premium and customer sell-side quotes are observed in the active
  feature dataset. The modeled buy-back fallback (A04) applies only to legacy
  raw-source runs that lack `ornament_buy`.
- Behaviour rules are deliberately simple and interpretable; they do not model
  multi-product switching, intra-month timing, or taxes (ornament VAT is embedded
  in observed purchase quotes; the active feature dataset has no tax-base field).
- Inventory costing is weighted-average only; FIFO is not implemented (documented
  choice, consistent across realized P&L and attribution).
- Returns use Modified Dietz at annual granularity; intra-month flow timing is
  approximated by day-weighted flows.
- No FX-exposure attribution: V1 products are THB local dealer products; the
  spot/USDTHB columns are reference only.

## 6. Claims that must NOT yet be made

1. "Thai investors typically lose/gain X baht" — the population is a scenario
   population, not a calibrated sample.
2. "Y% of Thai gold customers churn/exit within Z years" — liquidity-shock rate
   is an assumption.
3. Any statement attributing aggregate national demand to the simulated
   population (tonnage comparison is context only).
4. Any causal claim that a specific behaviour caused a specific loss beyond the
   documented accounting decomposition.

## 7. What would most improve validity

1. Customer-level transaction data (anonymized) from a dealer or digital-gold
   platform — calibrates frequency, size, holding period.
2. Historical ornament buy-back quotes from GTA or dealers.
3. A survey of gold-investor entry amounts and contribution behaviour.
4. Monthly behaviour-mix estimates (e.g., platform cohorts) to replace equal
   archetype weights.
