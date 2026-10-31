# Data Audit Report

Input file: `D:\Project_Github\gold assisstant\dataset\thai-gold-portfolio-simulator\dataset\thai_gold_features_v1_simulator_input.csv` (sha256 `f1314f1f011ca52b...`) - original preserved unmodified.

- Input rows: **6,261** (valid two-sided bar quote rows: 6,261)
- Period: **2006-05-01 09:30:00 .. 2026-10-13 12:09:00**
- Daily rows after selection policy `last_valid_of_day`: **6,261**
- Calendar days with a valid quote: 6,261 of 7,471 (missing 1,210 days; weekends and GTA non-publication days are expected)

## Price semantics
Columns follow the published GTA convention: `รับซื้อ` (bar_buy) = dealer buys = customer SELL price; `ขายออก` (bar_sell / ornament_sell) = dealer sells = customer BUY price. `ornament_buy`, when present, is the observed ornament customer SELL price; otherwise A04 is used as fallback. Liquidation valuation uses the customer SELL side. Units: THB per baht-weight (15.244 g, 96.5% purity). The historical ornament buy-back quote is not present in the raw archive and is modeled only for sources without an observed quote.

## Quality checks
- Invalid/nonpositive bar buy: 0, bar sell: 0, ornament sell: 0
- Invalid/missing ornament buy quotes: 0/0; above ornament sell: 0
- Exact duplicate (timestamp,seq) rows: 0 (none removed; daily selection policy picks the authoritative quote per day)
- Input rows sharing a timestamp: 0
- Input rows per date: mean 1.00, max 1
- Share of input rows with nonzero change: 89.4%
- Bar buy-sell spread (THB/baht-weight): mean 105, p5 100, p95 100
- Ornament sell minus bar sell (wage proxy): mean 477 THB/baht-weight
- Negative bar spreads: 0 (flagged, not removed)

## Selection-policy sensitivity
- Alternative policy `first_valid_of_day`: correlation of daily bar returns 1.0000; annualized vol 13.0% (primary) vs 13.0% (alt).

## Coverage by year
|   year |   valid_quote_days | first_quote_date    | last_quote_date     |   bar_sell_min |   bar_sell_max |   bar_sell_year_end |   bar_spread_mean | is_partial_year   |
|-------:|-------------------:|:--------------------|:--------------------|---------------:|---------------:|--------------------:|------------------:|:------------------|
|   2006 |                201 | 2006-05-01 00:00:00 | 2006-12-30 00:00:00 |          10150 |          12900 |               10850 |           100     | True              |
|   2007 |                299 | 2007-01-03 00:00:00 | 2007-12-29 00:00:00 |          10450 |          13400 |               13300 |           100     | False             |
|   2008 |                298 | 2008-01-03 00:00:00 | 2008-12-30 00:00:00 |          12200 |          15450 |               14000 |           100     | False             |
|   2009 |                297 | 2009-01-03 00:00:00 | 2009-12-30 00:00:00 |          13550 |          19150 |               17350 |           100     | False             |
|   2010 |                299 | 2010-01-04 00:00:00 | 2010-12-30 00:00:00 |          16850 |          20150 |               20150 |           100     | False             |
|   2011 |                301 | 2011-01-03 00:00:00 | 2011-12-30 00:00:00 |          19500 |          26850 |               23500 |           100     | False             |
|   2012 |                297 | 2012-01-03 00:00:00 | 2012-12-29 00:00:00 |          22950 |          25900 |               24100 |           100     | False             |
|   2013 |                299 | 2013-01-02 00:00:00 | 2013-12-30 00:00:00 |          17850 |          24300 |               18800 |           100     | False             |
|   2014 |                300 | 2014-01-02 00:00:00 | 2014-12-30 00:00:00 |          17850 |          21100 |               18550 |           100     | False             |
|   2015 |                299 | 2015-01-02 00:00:00 | 2015-12-30 00:00:00 |          17950 |          20100 |               18300 |           100     | False             |
|   2016 |                302 | 2016-01-02 00:00:00 | 2016-12-30 00:00:00 |          18200 |          22800 |               19750 |           100     | False             |
|   2017 |                306 | 2017-01-03 00:00:00 | 2017-12-30 00:00:00 |          19250 |          21150 |               20100 |           100     | False             |
|   2018 |                313 | 2018-01-01 00:00:00 | 2018-12-31 00:00:00 |          18150 |          20300 |               19700 |           100     | False             |
|   2019 |                313 | 2019-01-01 00:00:00 | 2019-12-31 00:00:00 |          19250 |          22350 |               21550 |           100     | False             |
|   2020 |                314 | 2020-01-01 00:00:00 | 2020-12-31 00:00:00 |          21450 |          30300 |               26850 |           119.427 | False             |
|   2021 |                313 | 2021-01-01 00:00:00 | 2021-12-31 00:00:00 |          24500 |          28950 |               28650 |           100     | False             |
|   2022 |                313 | 2022-01-01 00:00:00 | 2022-12-31 00:00:00 |          28300 |          31700 |               29850 |           100     | False             |
|   2023 |                312 | 2023-01-02 00:00:00 | 2023-12-30 00:00:00 |          29650 |          34250 |               33650 |           100     | False             |
|   2024 |                314 | 2024-01-01 00:00:00 | 2024-12-31 00:00:00 |          33450 |          44400 |               42400 |           100     | False             |
|   2025 |                314 | 2025-01-01 00:00:00 | 2025-12-31 00:00:00 |          42650 |          67200 |               64950 |           100     | False             |
|   2026 |                257 | 2026-01-01 00:00:00 | 2026-10-13 00:00:00 |          63050 |          81500 |               66700 |           189.494 | True              |

## Anomalies and limitations
- No imputation is performed; trading and valuation skip unavailable quote dates (policy `skip_and_log`).
- Input coverage ends at **2026-10-13 12:09:00**; the final calendar year is partial when the input ends before December.
- Quotes are market-wide GTA prices, not individual shop transactions.

## Feature dataset provenance
- Source: `D:\Project_Github\gold assisstant\dataset\datset a gold price\data\processed\thai_gold_features_v1.csv` (SHA-256 recorded in the run manifest).
- `valid_price_pair` is not used to filter rows; it describes price-change computability against a prior same-day observation.
- `ornament_buy` is used as the observed customer sell quote for ornaments.
- Ornament tax-base values are unavailable in the feature source and remain null; portfolio replay does not use this field.
