# GAIB-1 Benchmark Build Report

- Build time (UTC): 2026-10-30T08:03:34.342615+00:00
- Overall status: PARTIAL; this is not a benchmark score report.
- Full benchmark API calls: not executed; a separate one-query connectivity smoke test was executed.
- Source files and production notebook were not modified.
- Copied experiment notebook outputs/execution counts were cleared so old 114-query `embedding` Ground Truth output cannot be mistaken for GAIB results.

## Fed track

- Preserved 43 supplied records: 37 map to source documents and exact quotes in the local RAG chunk corpus; 6 remain source gaps.
- Local chunk mapping: 37 of 37 source-present queries; quote mismatches: 0.
- Qdrant and Cloudflare connectivity is checked separately by the one-query smoke test; full-corpus Qdrant coverage remains UNVERIFIED.
- Remote connectivity smoke test: PASS; see `remote_rag_smoke_test.json`.
- The 5-agent notebook generation budget differs from A2 (900/1600 tokens vs A2 1200); this discrepancy is recorded, not silently corrected.
- All records retain their original split and review status. Development is the copied notebook default; validation/test are not mixed into development.
- Fed source classification labels are silver labels, not human gold labels. Human semantic review remains required.

## NaN and relevance-score interpretation

- In the historical 114-query table, `query_type` is text. `describe(include="all")` displays `NaN` for numeric-only statistics (mean/std/min/quantiles) on text columns; these are not missing query types.
- The same historical CSV reports zero retrieval metrics for all queries because the previous scorer compared only candidate `document_id` with Ground Truth IDs. Retrieved corpus chunks also carry `original_id` and source URLs; for example, the connectivity probe found the expected Fed source in Qdrant at rank 6 by its source/original ID.
- The GAIB notebook now scores against document-ID aliases and source URLs, and summarizes numeric metrics separately from categorical counts. Historical CSVs are left untouched and must be rerun before interpreting old zero scores.
- Metric `NaN` is retained only when a query has no usable relevance judgments or a metric is mathematically undefined; it is not replaced with zero.

## Other tracks

- **FED: PARTIAL** — All supplied Fed records are preserved; 6 source-gap cases remain blocked, Qdrant index mapping is unverified, and human semantic review is pending.
- **QUANT: BLOCKED** — No verified production function-calling tool contract was found in the target multi-agent notebook; dataset inspection alone is insufficient to author exact expected tool calls.
- **HMM: BLOCKED** — Model metadata requires bar_buy_log_return and intraday_range_pct; the processed feature dataset contract and training preprocessing have not been independently reconciled. Model bundle is not deserialized by this build.
- **PORTFOLIO: BLOCKED** — Simulator files and outputs exist, but this build does not assert independent ledger formulas or produce synthetic transaction-level reference cases without completing accounting-code validation.
- **MULTI_AGENT: BLOCKED** — Exact required tool-call expectations and human-approved semantic claims are unavailable; E2E ground truth must not be generated from unreviewed model answers.

## Reproduction

From the project root, run `python multi_agent/GAIB-1/build_gaib_benchmark.py`.
Run integrity checks with `python -m unittest discover -s multi_agent/GAIB-1/tests -v`.
Run the read-only one-query Qdrant + Cloudflare connectivity probe with `python multi_agent/GAIB-1/probe_remote_rag.py`.
Open `multi_agent/GAIB-1/Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb` for the opt-in experiment. Set the selected `RUN_*_BENCHMARK=true` to start that remote benchmark and incur API usage. Test split requires `GAIB_ALLOW_TEST_SPLIT=true`.
Per-query outputs and runtime manifests are written under `multi_agent/GAIB-1/runs/`.
