# Feature-based simulator recalculation

- Source: `D:\Project_Github\gold assisstant\dataset\datset a gold price\data\processed\thai_gold_features_v1.csv`
- Input records: 6,261
- Daily quotes used: 6,261 (2006-05-01 to 2026-10-13)
- `valid_price_pair` is a price-change computability flag, not a quote quality filter; every row with positive ordered quote prices is retained.
- Ornament tax-base values are unavailable in this source and remain null; the replay does not use this field.
- Observed ornament buy-back quotes: 6,261 of 6,261 daily rows; A04 fallback used for 0 rows. Other simulation parameters remain unchanged.

## Recalculated outputs
- Portfolios: 1,050
- Transaction events: 40,466 (18,885 accepted; 21,581 rejected)
- Monthly valuations: 121,639
- Portfolio-year and attribution records: 10,827
- Accounting reconciliation failures: 0
- Attribution residual failures: 0

## Comparison to prior daily prices
- Status: compared
- Overlapping dates: 5,924
- Same price rows on overlap: 5,267
- Changed price rows on overlap: 657
- Added observed price fields: ornament_buy_thb
- Dates only in previous source: 9
- Dates only in feature source: 337

## Ground Truth impact
- Article-specific Thai PBS/news facts remain unchanged: their evidence is the cited news, not the simulator's numeric outputs. Replacing those answers with feature prices would change the question being evaluated.
- Audit status: news_ground_truth_preserved
- Source-evidence inventory: 264 records; source evidence was not modified.
- Gold price fact queries: 20; 20 refer to dates after the feature dataset ends. See `ground_truth_price_coverage_audit.csv` in the output directory.
- `D:\Project_Github\gold assisstant\multi_agent\gt\ground_truth_fed_v1.jsonl`: 43 queries; 0 news-gold and 0 simulator-output queries.
- `D:\Project_Github\gold assisstant\multi_agent\gt\ground_truth_fed_ready_v1.jsonl`: 37 queries; 0 news-gold and 0 simulator-output queries.
- `D:\Project_Github\gold assisstant\multi_agent\GAIB-1\ground_truth_all_v1.jsonl`: 43 queries; 0 news-gold and 0 simulator-output queries.
- `D:\Project_Github\gold assisstant\embedding\embedding\ground_truth_queries_v2.jsonl`: 114 queries; 29 news-gold and 0 simulator-output queries.
