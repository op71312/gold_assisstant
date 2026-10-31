# Methodology Review (workflow step 6)

This review checks whether the available evidence supports each proposed
parameter distribution **before** the full simulation (spec 18 step 6), and
records where the methodology was adjusted as a result.

## Review table

| Parameter / distribution | Proposed basis | Review outcome | Action taken |
|---|---|---|---|
| Initial capital lognormal (A01) | Wealth skew evidence (S07) only | No direct survey of gold-investor capital → shape is defensible, level is not | Kept as labelled scenario; unit changed to baht-weight affordability so capital scales with observed cohort-year prices; sensitivity 0.5x/2.0x |
| Gold allocation Beta(2,2) (A02) | none (explicit assumption) | No evidence | Kept bounded [0.3, 0.9]; sensitivity via config |
| Product mix 65/35 bar-ornament (A03) | WGC demand mix (bars dominate investment, S01-S03) | Investor-level split unknown | Kept as scenario; affordability fallback documented (realized mix shifts toward ornaments for small portfolios — realistic for small budgets) |
| Ornament buy-back | active feature dataset provides observed `ornament_buy`; raw archive lacks it | Observed in S15; gap in S10 | Active run uses observed quotes; A04 `bar_buy + delta` remains a labelled fallback for raw-source runs |
| Behaviour mix equal weights (A05) | spec 7.5 forbids false weighting | Correct to avoid | Equal weights; configurable; reported per scenario |
| Decision timing monthly (A06) | no evidence on checking frequency | plausible | Sensitivity: weekly/monthly possible via config; monthly default |
| Dip threshold 97%/90d (A07) | S06 dip-buying exists at aggregate level | supports existence, not threshold | Sensitivity 90-99% |
| Momentum MA 20/60 (A08) | standard technical convention | no Thai calibration | documented as convention |
| Liquidity shock λ=0.02/mo (A09) | none | must exist for loss narratives | sensitivity 0-0.05 |
| Explicit fees 0 (A10) | spread already embedded in observed quotes | verified from data | fee=0 baseline; spread handled by timing effect from data |
| Bar unit 1 bw / ornament 0.25 bw (A11/A12) | market convention (S11) | verified (1 salung = 0.25 bw) | minimum-purchase fallback added so decided investors buy ≥ smallest unit when capital allows |
| Initialization contribute_then_buy (A13) | spec 6.4 forbids unobserved cost basis | correct | implemented; no pre-existing gold variant |
| Modified Dietz returns (A14) | spec 9.5 | appropriate to event-level flows | implemented with day-weighted flows |
| Monthly MDD basis (A15) | spec 8.6 output-size control | appropriate | exit-event marks included |

## Findings that changed the design

1. **Affordability floor.** With bars at 1 baht-weight (THB ~65k in 2026), a
   median-sized 2026 portfolio cannot buy a bar. Reviewing against GTA unit
   conventions led to: ornament minimum 0.25 bw, product fallback, and the
   minimum-purchase rule. This is economically meaningful (small investors buy
   ornaments/salung sizes), not a hack.
2. **Spread and ornament buy-back are data, not assumptions in the active
   feature run.** Because the source carries two-sided bar and ornament quotes,
   the replay reads observed spreads and ornament sell-side prices directly
   (~THB 100/baht-weight for most of the sample; wider in volatile periods),
   removing an entire class of assumed costs.
3. **Attribution identity.** The unit-lifecycle decomposition was verified
   algebraically to reconcile exactly (see `docs/accounting_rules.md` §6) and is
   unit-tested on random paths; residuals are floating-point dust.

## Conclusion

No proposed distribution is presented as an empirical fact of Thai investor
behaviour. All behavioural parameters are labelled scenario assumptions with
documented sensitivity ranges; the price and spread layers are observed data.
The methodology is therefore consistent with spec sections 2.1-2.3.
