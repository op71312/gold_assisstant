# GAIB-1 token-limit root-cause experiment

- Run: `20261029T110207Z-31b9646e`
- Historical baseline run: `20261028T150635Z-99522ade`
- Phase 0 integrity: **PASS** (25 expected query-agent rows, no duplicate/missing pairs or contradictory success rows).
- Source provenance: historical notebook hash not recorded; historical raw responses not captured.

## Historical failure diagnosis
- Failed historical rows ending exactly at 900 completion tokens: 10.
- Those rows with truncation `finish_reason`: 10.
- Classification: **LIKELY**, not CONFIRMED, because the historical raw response ending was not retained. The API finish reason is strong evidence, but the missing raw response prevents the complete check requested.
- Historical status/validity consistency: passed; no row had `status=success` while JSON parsing or schema validation failed.

## Experiments
- No new LLM requests are made unless `GAIB_RUN_TARGETED_EXPERIMENT=true` is set before running the final experiment cell.
- Remote calls are refused for non-HTTPS ThaiLLM endpoints to prevent sending credentials or prompts over cleartext HTTP.
- Variant A historical baseline, Variant B 1,200-token budget, Variant C compact 900-token contract, targeted recovery, and sequential/concurrent latency comparison are written to the CSV deliverables when enabled.
- Variant 1,500 is only run if the measured 1,200-token output still ends with a truncation finish reason.
- Task correctness is not inferred from JSON validity; it remains unevaluated without a domain oracle or documented human review.

## Preliminary conclusion
- Saved evidence supports output truncation as the leading explanation for 900-token failures with `finish_reason=length`; other failures, including schema violations and slow requests with short outputs, remain separate categories.
- No production default is selected based on the historical run alone. Select a configuration only after the controlled variants complete and compare validity, token overhead, and latency.

See `json_failure_diagnosis.csv`, `agent_request_telemetry.csv`, `token_budget_experiment_results.csv`, `repair_ablation_results.csv`, and `latency_diagnosis.csv` in this run directory.

## Evidence classification
- Confirmed truncation failures with captured raw response and finish reason: 0.
- Likely historical truncation failures without captured raw response: 10.
