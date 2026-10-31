# GAIB-1 Progress Handoff — 2026-10-29

## Current decision

**Code and schema fix is complete; release gating remains NO-GO.** The root cause behind the live judge failure was that the judge model returned prose instead of a valid JSON object. That issue has now been fixed by enforcing JSON-only judge output and adding a fail-closed fallback parser that extracts structured fields from narrative responses before validation.

The frozen test split was not used for this experiment. The project remains in a policy NO-GO state until the required human calibration and paired three-variant baseline evidence are completed and all mandatory gates pass.

## Work completed

- Built a separate 100-query `held_out` Ground Truth candidate from Federal Reserve source documents. It has 100 unique source documents and publication dates, verified exact quote spans, and no source-group overlap with existing development, validation, or test data. All queries are `numeric_fact`; machine construction is **not** human semantic review.
- Updated the exit-criteria notebook builder to recognize `JINA_API_KEY3` after the first two key slots, regenerated the notebook, and verified that `JINA_API_KEY3` succeeds with HTTP 200 without printing the key.
- Fixed the live AI judge failure: the judge invocation now uses a JSON-only prompt and `response_format` fallback, and the parser can recover valid structured fields from verbose model output instead of treating the whole response as invalid.
- Fixed the fail-closed expected-fact logic and preserved schema validation semantics for missing/malformed expected-fact judgments.
- Ran the full GAIB-1 regression suite after the judge fix: **47 tests passed**.

## Latest live run

Run ID: `20261029T085922Z-0a3d4e87`

Evidence directory: `runs/token_root_cause/20261029T085922Z-0a3d4e87/`

The notebook execution was interrupted before completion. There is no final execution status file or completed AI-judge result for this run. The latest saved multi-agent checkpoint is at 16:27 local time.

| Measure | Latest recorded result |
|---|---:|
| Held-out queries in retrieval run | 100 |
| Runtime BM25/Qdrant coverage | 87/100 |
| Queries blocked by corpus-ID mismatch | 13 |
| Jina rerank status | `jina_success`, 100/100 |
| Eligible reranked known-relevant Recall@10 | 0.920 (87 eligible queries) |
| Eligible reranked MRR@10 | 0.914 (87 eligible queries) |
| Eligible reranked nDCG@10 | 0.915 (87 eligible queries) |
| Eligible answer-bearing span recall@10 after reranking | 0.943 (87 eligible queries) |
| Multi-agent queries with any checkpointed records | 23 |
| Checkpointed specialist records | 114: 110 successes, 4 API errors |
| Schema-valid successful specialist records | 110/110 |
| AI judge / human calibration | No completed result / no human labels |

Retrieval values above are measured only on the 87 eligible cases. They do not erase the 13 coverage failures or satisfy the policy's 100% index-coverage requirement.

## Evidence and implementation files

- Candidate notebook: [Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb](./Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb)  
  SHA-256: `b4d19a7cebc030206c19b684e5ea63b0af367dc9021d03b12f4363201323af6f`
- Notebook builder: [build_token_root_cause_experiment.py](./build_token_root_cause_experiment.py)
- AI judge and metrics: [gaib1_ai_judge.py](./gaib1_ai_judge.py)
- Held-out data: [ground_truth_fed_numeric_acceptance_v2.jsonl](./ground_truth_fed_numeric_acceptance_v2.jsonl)
- Held-out provenance: [ground_truth_fed_numeric_acceptance_v2_manifest.json](./ground_truth_fed_numeric_acceptance_v2_manifest.json)
- Run coverage audit: [ground_truth_audit.csv](./runs/token_root_cause/20261029T085922Z-0a3d4e87/ground_truth_audit.csv)
- Run retrieval metrics: [retrieval_stage_metrics.csv](./runs/token_root_cause/20261029T085922Z-0a3d4e87/retrieval_stage_metrics.csv)
- Run generation checkpoint: [agent_quality_and_latency_checkpoint.csv](./runs/token_root_cause/20261029T085922Z-0a3d4e87/agent_quality_and_latency_checkpoint.csv)
- Earlier failed run and judge-metric crash: [20261029T081959Z-6909f183](./runs/token_root_cause/20261029T081959Z-6909f183/)
- Acceptance criteria and recorded evidence: [GAIB1_RELEASE_GATES_AND_ACCEPTANCE_CRITERIA.md](../GAIB1_RELEASE_GATES_AND_ACCEPTANCE_CRITERIA.md)

No credential values should be copied into notebooks, logs, markdown, or chat. Keep them in the local `.env`.

## What to do next

1. **Diagnose the 13 coverage failures before spending on another full run.** Compare their expected source document IDs with the local BM25 chunk corpus and the Qdrant payloads. Determine whether the correct remedy is a corpus-ID/alias mapping fix or an explicitly approved ingestion of the missing eligible source documents. Preserve the current source-disjoint dataset and frozen test split.
   - Confirmed root cause from the current evidence: the 13 problematic document IDs are present in the raw FED source tree at `dataset/news/fed/fed_press_releases_cleaned/fed_press_releases_clean.jsonl`, but none of those 13 document IDs or expected URLs appear in the live chunk corpus at `embedding/artifacts/chunking_real/structure_aware/chunks_structure_aware_real.jsonl`. This is why the live audit marks them as `CORPUS_ID_MISMATCH` even though source-grounded GT rows were generated from the official Fed document set.
2. **Inspect the four ThaiLLM API errors** in this run's checkpoint/telemetry and protected diagnostics. Record only sanitized error types, status codes, and query IDs in any shared report. Fix a confirmed systemic cause before retrying.
3. **Choose the rerun scope deliberately.** A short smoke test on affected held-out cases can validate coverage and API fixes, but it is diagnostic only. Once coverage and the error cause are resolved, run all 100 held-out cases to create a complete acceptance record. Do not resume by treating the 23-query checkpoint as a finished benchmark.
4. **Complete judge evaluation** for the fully generated run. Confirm every claim and abstention is evaluated, expected-fact comparisons are present, judge models are distinct from the answer generator, and all policy gates are computed. If the run stops, investigate the saved error before retrying.
5. **Obtain real independent human review.** Review the required stratified claims and double-review sample; do not generate or infer human labels. Recompute calibration agreement and kappa from reviewer-supplied labels.
6. **Run the policy-required paired three-variant comparison** on identical query IDs and comparable conditions: single-agent + RAG, multi-agent + RAG, and multi-agent + RAG + judge. The existing historical multi-agent comparison is not a substitute.
7. **Record final metrics and gate status** in the release criteria document. Declare GO only if every mandatory gate passes; otherwise retain NO-GO and document blockers.

## Evidence update from the 13-case coverage audit

Executed on 2026-10-29 and validated against the latest run directory `runs/token_root_cause/20261029T085922Z-0a3d4e87/`.

- Audit result: `coverage_status == "CORPUS_ID_MISMATCH"` for 13 of 100 held-out queries.
- Exact command run: `python -c "import pandas as pd; p=r'D:\Project_Github\gold assisstant\multi_agent\GAIB-1\runs\token_root_cause\20261029T085922Z-0a3d4e87\ground_truth_audit.csv'; df=pd.read_csv(p); m=df[df['coverage_status']=='CORPUS_ID_MISMATCH']; print('mismatch_count', len(m)); ..."`
- Observed output: `mismatch_count 13`.
- Follow-up verification: a Python check that iterated the 13 mismatched document IDs against the live corpus found `found_in_corpus 0`.
- Independent source verification: the same 13 document IDs were present in `dataset/news/fed/fed_press_releases_cleaned/fed_press_releases_clean.jsonl` with source URLs such as `https://www.federalreserve.gov/newsevents/pressreleases/monetary20060920a.htm`.

This narrows the remaining blocker to the runtime corpus/index synchronization layer, not to the held-out ground-truth construction itself. The GT is source-disjoint and valid; the live retrieval corpus still lacks those 13 eligible documents.

## Recommended run configuration

The following non-secret settings were used for the held-out run and can be reused after fixing coverage and API errors:

```text
GAIB_GT_READY_PATH=multi_agent/GAIB-1/ground_truth_fed_numeric_acceptance_v2.jsonl
GAIB_BENCHMARK_SPLIT=held_out
GAIB_ALLOW_HELD_OUT_SPLIT=true
GAIB_RUN_FULL_HELD_OUT_ACCEPTANCE=true
GAIB_RUN_LIVE_ACCEPTANCE=true
GAIB_JUDGE_MODEL=qwen3.6-35b-a3b
GAIB_SECOND_JUDGE_MODEL=Typhoon-S-ThaiLLM-8B-Instruct
GAIB_JUDGE_ENABLED=true
```

Load the project `.env` locally and keep secrets out of the notebook and run manifest.

## Continuation checklist after this handoff

Status update: still NO-GO. The root blockers are unchanged and remain policy-blocking, even though the run is now much closer to a complete evidence flow.

1. Fix corpus alignment before the next full run.
   - The 13 blocked cases are not random failures: they are source-brand mismatches between the GT source IDs and the live chunk corpus IDs.
   - The immediate check is to compare every `document_id` in `ground_truth_fed_numeric_acceptance_v2.jsonl` against the indexed corpus, then reconcile the canonical IDs or approved ingest mapping.
   - Goal: all 100 held-out cases are `COVERED` before the run is counted as a valid acceptance trial.

2. Finish the full 100-query held-out run without partial checkpoints being treated as a release result.
   - The current run terminated before a final status file and before the AI judge output completed.
   - A 23-query checkpoint is not evidence for GO; it is only a diagnostic milestone.

3. Complete AI-judge and calibration evidence.
   - Produce a completed judge result on the full run.
   - Confirm all claims and abstentions are evaluated and all expected-fact comparisons are present.
   - Generate human calibration labels for the required subset and record the review coverage and double-review sample explicitly.

4. Run the paired baseline comparison required by policy.
   - Same query IDs, same held-out corpus.
   - Compare single-agent + RAG, multi-agent + RAG, and multi-agent + RAG + judge.
   - Do not substitute historical or partial runs for this requirement.

5. Only declare GO after all mandatory gates pass.
   - Service reliability, retrieval coverage, judge quality, calibration agreement, and paired baseline evidence all have to clear the acceptance policy.
   - Until all of these are present and signed off, the project remains `NO-GO`.

These are the exact tasks to continue from the current state; do not skip them or treat partial evidence as a pass.
