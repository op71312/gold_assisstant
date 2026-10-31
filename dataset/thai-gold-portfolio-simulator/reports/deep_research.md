# Deep Research: Thai Gold Portfolio Evidence Base

Stage A deliverable. Every empirical claim below links to `outputs/source_registry.csv`
(S01–S14) and `outputs/parameter_evidence.csv`. Parameters that could not be supported by
evidence are explicitly listed as gaps in Section 5.

## 1. Research question A — What assets do Thai households hold?

**Finding (medium confidence):** Thai household assets are dominated by real estate, with
financial assets concentrated in bank deposits. The OECD Capital Market Review of Thailand
(2025) [S07] states that household assets are "heavily concentrated in real estate, with
limited investment in financial assets," and reports that 66% of total household wealth is
held by the richest 10% of households (39% by the top 1%). The Bank of Thailand's Financial
Access Survey series [S09] documents near-universal deposit access but does not publish
household-level gold holdings. Krungsri Research (using BOT data) reports household debt of
THB 16.35 trillion, 87.4% of GDP, in 2025 Q1 [S08, S12], indicating constrained household
financial capacity.

**Implication for the population model:** the initial-capital distribution must be
right-skewed and modest relative to total household wealth. A lognormal distribution
informed by the wealth-concentration shape [S07] is used as a **labelled scenario
assumption (A01)**, not as an empirical measurement of Thai gold investors. Total household
wealth must NOT be equated with money available for gold investment.

**What was NOT found:** no official survey publishing the *value share* of gold within Thai
household balance sheets at national level was located. The NSO Household Socio-Economic
Survey reports income/expenditure and some durable ownership, but a gold-holding value
series usable for calibration was not accessible in this environment.

## 2. Research question B — How much gold do Thai investors hold?

**Finding (high confidence, market-level):** Thailand is a top-tier retail gold investment
market. WGC Gold Demand Trends data [S01, S02]:

| Metric | Value | Period |
|---|---|---|
| Bar & coin investment demand | 39.8 t (+17% y/y), rank 7 globally | 2024 |
| Bar & coin, Q4 2024 | 14.6 t (+20% y/y) | Q4 2024 |
| Jewellery consumption | 9.0 t (−2% y/y vs global −11%) | 2024 |
| Bar & coin, Q2 2025 | 10.0 t (+38% y/y), strongest ASEAN growth | Q2 2025 [S03] |
| Investment demand, Q2 2026 | 10.9 t (+10% y/y) | Q2 2026 [S04] |
| Global bar & coin (context) | 1,186.3 t | 2024 [S14] |

**Survey-level prevalence (medium confidence):** WGC Retail Insights Thailand [S05] reports
46% of surveyed Thai investors own gold in some form; 77% have bought gold in the past;
20% of non-owners would consider buying. **This survey population is investors, not all
households**, so it is NOT used to calibrate portfolio prevalence. It is reported as
reference only, per spec 2.1/4.2.

**Implication:** aggregate tonnage exists, but **no distribution of holdings per person or
per household is available**. Per spec 4.2, we do not fabricate one. The simulated
population is therefore a *scenario population of gold-investment customer portfolios*
(useful for testing a loss-explanation system), explicitly not a calibrated sample of all
Thai households. Aggregate simulated turnover can be *compared* to the tonnage above as a
plausibility check at scenario level.

## 3. Research question C — How do Thai customers transact in gold?

**Empirically supported behaviour signals:**
- **Dip buying exists.** WGC GDT Q3 2021 [S06]: Thai retail investment swung from net
  disinvestment (−4.5 t H1 2021) to +7 t in Q3 2021 as "Thai investors seem to have taken
  advantage of an 8% drop in the local gold price." This supports the existence of a
  buy-the-dip archetype — at the aggregate level only; it does NOT quantify individual
  propensity.
- **Holding orientation with opportunistic trading.** WGC Retail Insights [S05]:
  motivations are wealth protection (34%), long-term returns above inflation (32%),
  speculation (17%); Thai investors "are confident using gold for shorter-term goals,
  responding to price moves."
- **Hold-through-drawdown behaviour.** WGC Q2 2025 [S03]: recycled supply "dropped
  sharply," interpreted by WGC as investors holding onto gold.
- **Digital gold savings platforms growing** [S02, S13], relevant to future extensions,
  not to the V1 physical-gold engine.

**Transaction-level gap (critical):** no public source of customer-level transaction size,
frequency, or holding-period statistics for Thai gold was found. Aggregate annual tonnage
cannot be converted into transaction counts without an arbitrary average trade size —
explicitly forbidden by spec 4.3. Therefore:
- Transaction frequency and size are **scenario parameters** (assumption register A01,
  A05–A09) with sensitivity ranges, reported as `NOT_EMPIRICALLY_VALIDATED`.
- The transaction-cost model is NOT assumed: dealer spreads are computed **directly from
  observed GTA two-sided quotes** (bar buy vs bar sell per announcement, S10), which
  embeds the historical spread variation.

## 4. Price semantics and product conventions (observed)

From the GTA announcement structure mirrored in the scraped dataset [S10]:
- Quotes are per **1 baht-weight = 15.244 g** of **96.5% (23K)** gold [S11].
- `bar_buy` (รับซื้อ) = dealer's purchase price → **the customer receives this when
  selling**. `bar_sell` (ขายออก) = dealer's selling price → **the customer pays this when
  buying**. Verified against the published header (รับซื้อ/ขายออก) and sanity-checked
  against USD spot × USDTHB × purity (e.g., May 2006: $652.8/oz × 38.22 → ≈11.8k THB per
  baht-weight matches bar quotes).
- `ornament_sell` (ขายออกทองรูปพรรณ) = customer's purchase price for ornaments, including
  the wage (historically ~400 THB/baht-weight above bar sell in 2006; rising later).
- **Gap:** the archive does not include the ornament buy-back quote (รับซื้อทองรูปพรรณ).
  Ornament liquidation value is therefore modelled under a labelled assumption (A04):
  default `ornament_buy = bar_buy + delta`, delta ∈ [0, 200] THB, with an alternative
  convention (pay tax-base value) available in configuration.
- `ornament_tax_base` (ฐานภาษี) is a GTA-published reference price used for VAT bases; it
  is carried through as a reference column, not as an execution price.

## 5. Evidence gaps (explicit)

| Parameter | Status | Consequence |
|---|---|---|
| Customer transaction frequency | GAP | Scenario assumption + sensitivity analysis |
| Customer transaction size | GAP | Scenario assumption + sensitivity analysis |
| Initial capital of gold investors | GAP | Lognormal scenario (A01) informed by S07 shape |
| Holding period distribution | GAP | Emergent from behaviour scenarios; flagged |
| Household-level gold value share | GAP | Population model = customer portfolios, not households |
| Ornament buy-back quote (historical) | GAP | A04 labelled assumption |
| Behaviour mix weights | GAP | Equal-weight baseline (A05); configurable |

## 6. Consequence for the simulation design

1. The simulator generates a **defensible synthetic population of gold-investment customer
   portfolios** under named scenarios — it does not claim to be a statistically
   representative sample of Thai households or investors.
2. All behaviour parameters are configurable and reported with sensitivity ranges; results
   are reported conditionally per scenario, never as population-wide estimates of Thailand.
3. Price and spread inputs are **real observed GTA quotes**; only the ornament buy-back
   side and behavioural parameters are modelled, and both are labelled.
4. Aggregate plausibility check: simulated aggregate net purchases per year are compared to
   WGC bar & coin tonnage as an order-of-magnitude context check (units converted), not as
   a calibration target.
