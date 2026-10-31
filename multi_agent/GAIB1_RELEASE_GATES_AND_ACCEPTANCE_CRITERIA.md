# Gold Assistant GAIB-1 — Release Gates & Acceptance Criteria

Version: 1.0  
Purpose: Define measurable criteria for deciding when the Gold Assistant is ready for internal research use, supervised pilot, and broader release.

> **Important:** All numeric thresholds in this document are proposed product/engineering acceptance criteria for this project, not universal thresholds prescribed by the cited research papers. They should be reviewed against risk tolerance, user workflow, and actual operating cost.

## 1. Current evidence and decision

The supplied telemetry file is the historical baseline run `20261028T150635Z-99522ade`, not the newer root-cause run `20261028T170803Z-5822241b`. It contains 25 agent records: five queries × five agents.

| Historical final status | Count | Rate |
|---|---:|---:|
| `truncated_output` with `finish_reason=length` | 10/25 | 40% |
| `schema_violation` | 6/25 | 24% |
| `success` (JSON and schema valid) | 9/25 | 36% |
| JSON parseable (success + schema violation) | 15/25 | 60% |

### Failure concentration by agent

| Agent | Truncated | Schema violation | Valid success | Final schema pass |
|---|---:|---:|---:|---:|
| AI1 News Analyst | 2/5 | 3/5 | 0/5 | 0% |
| AI2 Macro Analyst | 2/5 | 0/5 | 3/5 | 60% |
| AI3 Quant Regime Analyst | 5/5 | 0/5 | 0/5 | 0% |
| AI4 Risk Data Auditor | 1/5 | 1/5 | 3/5 | 60% |
| AI5 Lead Researcher | 0/5 | 2/5 | 3/5 | 60% |

AI3's five outputs all end with `finish_reason=length` at 900 completion tokens. This is strong evidence that the current output budget is inadequate for those outputs, but the historical raw response and source hash were not captured; retain the historical classification as `LIKELY`, not fully confirmed. AI1 has two truncations and three schema violations, so its problems need separate token-budget and schema-contract experiments. Other schema failures include `missing_evidence`/`cautions` expected lists, AI4 `go_no_go` invalid enum, and AI5 `agent_agreement`/`limitations` expected lists.

**Current release decision: PRELIMINARY / NOT READY for a supervised pilot, unsupervised research outputs, or external release.** It is suitable for continued development and controlled experiments.

### Latest live development checkpoint

The final candidate was exercised against the real ThaiLLM, Qdrant/Cloudflare hybrid retrieval, and Jina reranker in run `20261029T034146Z-994d858a`. The run used five development queries and completed all 25 specialist calls:

| Observed measure | Result |
|---|---:|
| Specialist JSON parses | 25/25 (100%) |
| Specialist schema-valid outputs | 25/25 (100%) |
| Fully schema-valid queries | 5/5 (100%) |
| Reranked known-relevant Recall@10 | 5/5 (1.00) |
| Reranked MRR@10 / nDCG@10 | 1.00 / 1.00 |
| Retrieval/API orchestration errors | 0 |
| Human semantic reviews completed | 0/5 |

This is a **five-query development diagnostic, not release evidence**: it is below the 100-case held-out minimum, the Ground Truth judgments are not exhaustive, and every answer remains `NOT_HUMAN_REVIEWED`. The available Ground Truth has 43 rows (37 source-present); only six are development queries. Automated retrieval and schema results do not establish claim support, domain correctness, latency qualification, or readiness. Keep the release decision `PRELIMINARY / NOT READY` until every mandatory gate is independently satisfied.

Run artifacts: [benchmark manifest](./GAIB-1/runs/token_root_cause/20261029T034146Z-994d858a/benchmark_run_manifest.json), [agent metrics](./GAIB-1/runs/token_root_cause/20261029T034146Z-994d858a/multiagent_per_agent_metrics.csv), [retrieval metrics](./GAIB-1/runs/token_root_cause/20261029T034146Z-994d858a/retrieval_stage_metrics.csv), and [human-review template](./GAIB-1/runs/token_root_cause/20261029T034146Z-994d858a/answer_human_review_template.csv).

### One-time frozen held-out test checkpoint

The frozen candidate was evaluated once on all 25 available test queries using the real ThaiLLM, Qdrant/Cloudflare hybrid retrieval, and Jina reranker in run `20261029T035022Z-2490575e`. No prompts, retrieval settings, or candidate code were changed based on this test run.

| Observed measure | Result |
|---|---:|
| Test queries attempted / completed | 25/25 |
| Retrieval/API orchestration errors | 0 |
| Covered, evaluation-eligible retrieval queries | 25/25 |
| Reranked known-relevant Recall@10 / MRR@10 / nDCG@10 | 0.96 / 0.96 / 0.96 |
| Queries with all five specialist outputs schema-valid | 22/25 (88%) |
| Specialist JSON parses / schema-valid outputs | 124/125 / 122/125 |
| Human semantic reviews completed | 0/25 |

This is **preliminary test evidence, not a release pass**. Retrieval missed the expected document for numeric-fact query `gtv2_000066`. The three invalid specialist outputs were AI3 truncation on `gtv2_000063`, an AI2 missing-required-fields schema violation on `fedv1_0003`, and an AI4 invalid `go_no_go` enum on `fedv1_0005`. All 25 generated answers still require human semantic review. The available Ground Truth has 43 rows (37 source-present), including only 25 test cases; this does not meet the minimum 100 held-out cases. Do not tune against or re-run this test split as a development set. Keep the release decision `PRELIMINARY / NOT READY`.

Evaluated candidate SHA-256: notebook `a8b2967e17218551564d7e69ffd7288fda7dd4a108e4d0aa2fd1fc55500d5d7d`; builder `bd0c46997517039068ba7fb75258fa4c0230f767dbc0bd594bbaa39e393a556b`.

Run artifacts: [benchmark manifest](./GAIB-1/runs/token_root_cause/20261029T035022Z-2490575e/benchmark_run_manifest.json), [agent metrics](./GAIB-1/runs/token_root_cause/20261029T035022Z-2490575e/multiagent_per_agent_metrics.csv), [agent query summary](./GAIB-1/runs/token_root_cause/20261029T035022Z-2490575e/multiagent_benchmark_summary.csv), [retrieval metrics](./GAIB-1/runs/token_root_cause/20261029T035022Z-2490575e/retrieval_stage_metrics.csv), and [human-review template](./GAIB-1/runs/token_root_cause/20261029T035022Z-2490575e/answer_human_review_template.csv).

### Post-test development checkpoint — new candidate, not held-out validated

After recording the one-time test result, a development-only change stopped rendering claims that have no valid evidence IDs, retained rejected IDs and claim-coverage counts in the deterministic audit, and made AI5's JSON-array requirements more explicit. The test split was not used for this change. The updated candidate was exercised against the real services on five development queries in run `20261029T041850Z-9070e471`:

| Observed measure | Result |
|---|---:|
| Development queries completed | 5/5 |
| Retrieval/API orchestration errors | 0 |
| Covered retrieval queries / mean reranked known-relevant Recall@10 | 5/5 / 1.00 |
| Specialist JSON parses / schema-valid outputs | 24/25 / 24/25 |
| Fully schema-valid queries | 4/5 |
| Development reports with valid citations | 4/4 reports containing claims |
| Safe abstentions with no valid claim | 1 |
| Human semantic reviews completed | 0/5 |

One specialist call returned an API error. The updated renderer withheld unsupported claim text and returned an explicit abstention rather than presenting uncited factual content. These results are a small development diagnostic, not release evidence. This candidate has **not** been evaluated on an independent held-out set; the preceding 25-query test metrics apply only to the earlier candidate hash and must not be attributed to this one. Do not re-use the consumed test split for tuning or certification.

After this live development run, a small audit-only hardening made sorting of rejected evidence IDs safe for malformed IDs; the regression suite passed, but the live run above predates this hardening. Current working candidate SHA-256: notebook `653083ea48243d69f4620cdf95a77973210332b100f53a94702340ae807ec148`; builder `9f0cd2ffce61bf6fa2d065aabac9867a87c99785f8a3abc8572c69630d1788f7`.

Run artifacts: [benchmark manifest](./GAIB-1/runs/token_root_cause/20261029T041850Z-9070e471/benchmark_run_manifest.json), [agent metrics](./GAIB-1/runs/token_root_cause/20261029T041850Z-9070e471/multiagent_per_agent_metrics.csv), [retrieval metrics](./GAIB-1/runs/token_root_cause/20261029T041850Z-9070e471/retrieval_stage_metrics.csv), [multi-agent results](./GAIB-1/runs/token_root_cause/20261029T041850Z-9070e471/multiagent_benchmark_results.csv), and [human-review template](./GAIB-1/runs/token_root_cause/20261029T041850Z-9070e471/answer_human_review_template.csv).

### Current candidate verification after audit hardening

The current notebook and builder hashes above were then exercised together on the same five development-only queries, again using the real ThaiLLM, Qdrant/Cloudflare hybrid retrieval, and Jina reranker. Run `20261029T042713Z-d415fd91` completed all retrieval and multi-agent cases without API/orchestration errors:

| Observed measure | Result |
|---|---:|
| Covered, evaluation-eligible retrieval queries / mean reranked known-relevant Recall@10 | 5/5 / 1.00 |
| Specialist JSON parses / schema-valid outputs | 25/25 / 25/25 |
| Fully schema-valid queries | 5/5 |
| Reports with valid cited findings | 4/5 |
| Explicit safe abstentions with no cited finding | 1/5 |
| Human semantic reviews completed | 0/5 |

This confirms the audit-hardening code runs on the configured services and preserves the safe-abstention behavior. It remains a five-case development diagnostic, not independent test evidence. All answers still need human semantic review; no release gate is inferred from this run. The decision remains `PRELIMINARY / NOT READY`.

Run artifacts: [benchmark manifest](./GAIB-1/runs/token_root_cause/20261029T042713Z-d415fd91/benchmark_run_manifest.json), [agent metrics](./GAIB-1/runs/token_root_cause/20261029T042713Z-d415fd91/multiagent_per_agent_metrics.csv), [retrieval metrics](./GAIB-1/runs/token_root_cause/20261029T042713Z-d415fd91/retrieval_stage_metrics.csv), [multi-agent results](./GAIB-1/runs/token_root_cause/20261029T042713Z-d415fd91/multiagent_benchmark_results.csv), and [human-review template](./GAIB-1/runs/token_root_cause/20261029T042713Z-d415fd91/answer_human_review_template.csv).

### Complete development experiment suite

The notebook now has a master opt-in, `GAIB_RUN_ALL_EXPERIMENTS=true`. It runs the targeted token-budget, compact-output, conditional-budget, truncation-recovery, and sequential/concurrent latency comparisons, then evaluates every query in the development split. The master switch refuses non-development splits; the existing test split remains untouched. Remote API calls incur provider usage, so ordinary notebook execution remains opt-in.

The full suite was run once against the real ThaiLLM, Qdrant/Cloudflare hybrid retrieval, and Jina services in run `20261029T043729Z-2d81cad3` on the exact candidate hashes below. Historical baseline rows are reported separately from newly generated calls:

| Experiment / measurement | Results |
|---|---:|
| Phase 0 historical telemetry integrity | PASS; 25/25 expected records |
| New targeted request telemetry | 84 request records |
| Fresh 900-token baseline | 2/9 schema-valid |
| 1200-token budget | 4/9 schema-valid |
| Conditional 1500-token budget | 0/4 schema-valid |
| Compact 900-token output | 8/9 schema-valid |
| Same-budget truncation repair | 0/3 schema-valid |
| Increased-budget truncation repair | 1/3 schema-valid |
| Sequential / concurrent latency comparison | 4 calls per mode; 2/4 schema-valid per mode |
| Full live development benchmark | 6/6 queries completed; no retrieval or benchmark-level orchestration errors |
| Covered retrieval queries / mean reranked known-relevant Recall@10 | 6/6 / 1.00 |
| Live specialist outputs | 29/30 JSON-parseable and schema-valid; one AI3 truncation |
| Fully schema-valid queries | 5/6 |
| Final reports with cited findings / explicit safe abstentions | 5/6 / 1/6 |
| Human semantic reviews completed | 0/6 |

These are small, diagnostic development samples, not release estimates. In particular, the budget and latency arms have small, conditional sample sizes and do not establish that one configuration is generally superior. The one AI3 truncation and the unreviewed claims remain unresolved acceptance issues. No conclusions from this run certify the consumed 25-case test split or satisfy the 100-case held-out minimum.

To run the suite from PowerShell before starting the notebook kernel, set `$env:GAIB_RUN_ALL_EXPERIMENTS='true'` and `$env:GAIB_BENCHMARK_SPLIT='development'`; keep `$env:GAIB_ALLOW_TEST_SPLIT='false'`. Alternatively configure the same environment variables before launching Jupyter. The switch is deliberately opt-in to prevent unexpected API charges.

Candidate hashes: notebook `caa1378fd2f416ea40d5d2b74f96e0859dd446aa189ecd137cd6a78be2918e71`; builder `ca0b5824c62c65f9229e04a77eaa9fd41b653bd501f1930a816c9c181034de71`.

Run artifacts: [experiment manifest](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/experiment_manifest.json), [root-cause report](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/root_cause_report.md), [token-budget results](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/token_budget_experiment_results.csv), [repair ablation results](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/repair_ablation_results.csv), [latency results](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/latency_diagnosis.csv), [live benchmark manifest](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/benchmark_run_manifest.json), [retrieval metrics](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/retrieval_stage_metrics.csv), [agent metrics](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/multiagent_per_agent_metrics.csv), and [human-review template](./GAIB-1/runs/token_root_cause/20261029T043729Z-2d81cad3/answer_human_review_template.csv).

## 2. Release levels

### Level 0 — Developer experimentation

Allowed now, with outputs treated as debugging artifacts only.

Requirements:
- Secrets are not stored in notebooks or logs.
- No direct trading/order execution or autonomous investment decisions.
- Experimental runs are versioned and failures are preserved rather than silently discarded.

### Level 1 — Supervised internal research pilot

Use only with a human reviewing outputs before relying on them. All mandatory gates below must pass.

### Level 2 — Limited team release

Require all Level 1 gates plus a larger held-out test, maintained human calibration of the judge, operational monitoring, and the paired three-variant comparison.

### Level 3 — Broader/production use

Require Level 2 gates plus reliability qualification on a larger test set, runbook/incident handling, repeatability tests, and explicit disclosure that market analysis is not a guaranteed forecast or personalized investment advice. No trading execution based solely on an LLM-generated report.

## 3. Mandatory release gates

### Gate A — Evaluation and run integrity

| Criterion | Level 1 pilot | Level 2+ |
|---|---|---|
| Expected query/agent records | 100% accounted for; failures represented explicitly | Same |
| Duplicate `(run_id, query_id, agent, attempt)` keys | 0 | 0 |
| Contradictory final status and validity flags | 0 | 0 |
| Run manifest | 100% of runs include model, config, prompt/schema versions, source/index version, timestamp and code hash | Same |
| Failed requests | Preserve error class, attempts, finish reason and timing; never silently drop | Same |
| Historical versus fresh runs | Never mix in one estimate without a `run_id`/variant filter | Same |
| Benchmark split | Development and holdout sets separated; holdout not used to tune prompts/config | Same |

A run with incomplete telemetry is `INVALID_FOR_COMPARISON`; it may still be useful for debugging but cannot establish that a change improved the system.

### Gate B — JSON/schema and safe degradation

| Metric / rule | Level 1 pilot | Level 2+ |
|---|---:|---:|
| JSON parse rate after permitted recovery | ≥99% over evaluation calls | ≥99.5% |
| Schema-valid rate after permitted recovery | ≥98% over evaluation calls | ≥99.5% |
| Downstream payloads accepted without schema validation | 0 | 0 |
| Final report renderer/schema validity | 100% | 100% |
| Missing/failed specialist handling | Explicit `unavailable`/`partial` state; no raw invalid JSON passed as trusted evidence | Same |
| Retries/repairs | Logged per attempt; bounded; no unlogged retry | Same |

A query may complete in a controlled `partial` or `insufficient_evidence` state even when one specialist fails. It must not be labelled `complete` if required specialist evidence is missing. For a stricter reliability claim, collect at least 300 outputs per agent with zero failures; under an independence assumption, the rough rule-of-three puts the 95% upper bound near 1%. Since outputs within a query may be correlated, also report query-clustered confidence intervals or bootstrap intervals; do not treat the rule-of-three as proof by itself.

### Gate C — Retrieval

First verify that the expected source document is actually present and searchable. `index_coverage=100%` for eligible expected documents is a prerequisite to interpreting a miss as retrieval-model failure.

| Metric | Level 1 pilot | Level 2+ target |
|---|---:|---:|
| Eligible expected-document index coverage | 100% of cases included in scored retrieval evaluation | 100% |
| Known-relevant Recall@10 (overall) | ≥0.85 | ≥0.90 |
| MRR@10 | ≥0.60 | ≥0.70 |
| nDCG@10 | ≥0.70 | ≥0.80 |
| Worst major query category Recall@10 | ≥0.75 | ≥0.85 |
| Stage diagnostics | Dense, BM25, hybrid/RRF and reranked candidates saved for every miss | Same |
| Ground-truth review | Judgments checked for correctness; non-exhaustive judgments explicitly labelled | Broader and adjudicated holdout |

These are proposed targets, not published universal standards. If the benchmark's relevance judgments are non-exhaustive, call the metric `known_relevant_recall@10`, not absolute recall. Do not optimize only on a five-query sample; use at least 100 held-out queries across task families for a pilot-quality estimate, preferably 20 or more per major category. If the actual source-ready set is smaller, report the test as preliminary and do not claim the gate is statistically established.

### Gate D — Evidence, citations and faithfulness

| Metric / rule | Level 1 pilot | Level 2+ target |
|---|---:|---:|
| Citation ID validity in final rendered report | 100% | 100% |
| External-source factual reports with citations | 100%, unless an explicit no-source/abstention state is shown | 100% |
| Coverage of material factual claims with evidence IDs | ≥95% | ≥98% |
| AI-judge citation support / entailment | ≥95% | ≥98% |
| Judge output schema validity | ≥99% | ≥99% |
| Support for high-impact numeric, date, policy or P&L claims | 100%, with deterministic checks applied first where available | 100% |
| Unsupported high-impact claim | 0 in release evaluation | 0 |
| Citation support status | `NOT_CALIBRATED` until the human calibration gates pass | Same |
| `NO_CLAIMS` / no citation | Report separately; do not silently drop from summaries | Same |

Track the raw citations proposed by the LLM separately from IDs that survive deterministic rendering. An ID-validity rate calculated only after filtering invalid IDs can appear perfect while the original output is poor. Distinguish `report_has_citations_rate`, raw proposed ID validity, rendered ID validity, claim citation coverage, and semantic support.

For the pilot, AI-judge every factual claim and abstention on the held-out set. Separately calibrate the judge against at least 50 stratified human-reviewed claims, with at least 10 claims independently double-reviewed. Require supported/unsupported agreement ≥90%, Cohen's kappa ≥0.70, citation agreement ≥90%, completeness agreement ≥85%, and 100% detection recall on sampled critical unsupported claims. Until calibration passes, judge results are not release evidence.

### Gate E — Domain correctness and tool contracts

| Component | Required acceptance |
|---|---|
| Quant/statistical tools | 100% of deterministic unit tests pass; compare to independently calculated expected values and tolerances |
| Portfolio accounting / P&L | 100% ledger invariants reconcile; fees/costs and realized/unrealized values explicitly specified; no silent discrepancy |
| HMM | 100% contract tests pass for feature order, preprocessing/scaler version, as-of timestamp and output schema; do not confuse contract correctness with predictive accuracy |
| Dates/periods/source attribution | 100% of critical test cases correct in the deterministic oracle set |
| Answer correctness | Blind AI-judge correctness ≥90% overall and per query type, then compare expected facts separately; never infer from API success or valid JSON |
| Answer completeness | AI-judge completeness ≥90% |
| Critical numeric facts | 100% of available deterministic checks pass; unsupported critical numeric/policy claims = 0 |
| Abstention | On cases intentionally lacking evidence, the system should abstain or explicitly state insufficient evidence rather than invent a fact |
| Abstention metrics | Precision and recall reported separately; `NO_CLAIMS` is not automatically a success |

A single critical numerical/accounting error blocks release until root-caused and regression-tested. AI judge correctness, evidence support, citation entailment, and completeness remain separate measurements; uncertain or disputed judgments cannot be counted as passes.

### Gate F — Latency, reliability and token budget

Separate simple factual mode from full research mode; their latency budgets should not be pooled.

| Metric | Level 1 pilot target | Level 2+ target |
|---|---:|---:|
| API/run completion rate after bounded retry or explicit fallback | ≥99% | ≥99.5% |
| Simple lookup end-to-end latency P95 | ≤15 s | ≤10 s |
| Full research mode end-to-end latency P95 | ≤60 s | ≤45 s |
| Full research mode mean total tokens/query | ≤30,000 soft target | ≤25,000 target, unless quality evidence justifies extra cost |
| Per-query hard cost/token cap | Configured, documented and enforced | Same |
| Latency measurement size | At least 100 full end-to-end runs for preliminary P95; report n and max | ≥200 runs, repeated at representative load |
| Error/timeout/retry rates | Report separately by stage and agent | Same |

Report end-to-end latency before and after the offline judge overhead separately. The offline acceptance judge must not be counted as user-facing latency. These are initial operational targets and should be adjusted if the product deliberately offers a slower, deeper research mode. Current five-query P95 and mean token estimates are too small to certify the targets. The historical per-agent latency and newer end-to-end latency are different measurements and must not be compared as if they were from one identical run/configuration.

### Gate G — Does the five-agent architecture add value?

Compare the same held-out query IDs across all three variants: single-agent + RAG, multi-agent + RAG, and multi-agent + RAG + AI-judge evaluation. Use the same evidence, model family where feasible, and evaluation rubric. Report paired correctness, completeness, citation support, latency, and tokens, with per-query results and uncertainty where estimable. Document whether the additional architecture improves quality rather than only producing longer answers or adding cost. The AI-as-a-judge policy does not prescribe a universal numeric improvement threshold; do not invent one after reviewing results. If routing only the necessary specialists produces equivalent quality more cheaply, prefer routing over always calling all five agents.

## 4. Minimum benchmark design

Before Level 1 pilot:
- At least 100 independent held-out query cases, stratified across news, macro, document facts, quant statistics, HMM, portfolio/risk and insufficient-evidence cases; use at least 20 cases per major category when practical. Keep source/document groups separated between development and held-out splits.
- Include difficult dates/numeric facts, source conflicts, missing evidence, ambiguous asks, unsupported causal claims and cases where the correct action is abstention.
- Keep source/document families together when splitting train/development/test to reduce leakage from near-duplicate statements.
- AI-judge every claim and abstention; run all three variants on the same eligible cases and report per-query results and failure counts, not only means.
- Complete the stratified human calibration sample of at least 50 claims, including at least 10 independent double reviews, and meet the agreement thresholds in Gate D.
- Complete at least 100 end-to-end latency runs on the frozen configuration.

Before Level 2+:
- Expand to at least 200–300 held-out queries across the domains actually supported by the product.
- Collect at least 300 outputs per active agent for a preliminary sub-1% failure-rate claim only when zero failures are seen; use exact/binomial or query-clustered intervals and document assumptions.
- Maintain independent human calibration and compare automatic judges to human labels before relying on judge scores.
- Freeze the final test set; use it once for release evaluation, not iterative prompt tuning.

If these sample sizes cannot be reached yet, the correct conclusion is `PRELIMINARY / LIMITED INTERNAL USE`, not that the system passed.

## 5. Variant selection protocol

1. Preserve the old baseline and its run ID unchanged.
2. Diagnose historical failures as `LIKELY` if raw responses/source provenance are missing; do not retroactively mark them confirmed.
3. Test targeted cases first: AI3 token budget 900 vs 1,200; AI1 token budget and schema contract separately; AI4 enum contract; AI5 list-field contract.
4. Compare compact-output 900 against higher-budget output using the exact same query/context where possible.
5. Only test 1,500 tokens if 1,200 tokens still produces a documented truncation finish reason or cannot fit a valid required schema.
6. Test repair separately from initial generation. Log every HTTP attempt, finish reason, output token count, error, cost and result.
7. Accept a variant only if schema validity improves, all critical fields remain present, evidence quality does not regress, and token/latency overhead is justified.
8. Re-run regression cases and the frozen holdout after selecting the candidate configuration.

## 6. Overall go/no-go rule

### NO-GO
Any of the following is enough to block unsupervised or external release:
- Incomplete/contradictory telemetry or inability to reproduce the run.
- Unvalidated JSON/schema payload reaches AI5 or any downstream consumer as trusted data.
- Retrieval benchmark includes cases whose expected sources are missing from the index without flagging them.
- A factual report lacks citations and does not explicitly state insufficient evidence.
- Unsupported high-impact numeric, policy, HMM or portfolio claim in release evaluation.
- Deterministic P&L/quant invariant fails.
- Task correctness is still `NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE` while marketing or UI implies answers are verified.

### GO — supervised internal pilot
All Level 1 gates pass; invalid specialist data is blocked; outputs can abstain safely; the AI judge is calibrated against the required human sample; no automatic trading/order execution occurs.

### GO — limited release
All Level 2 gates pass on a frozen held-out set; monitoring and rollback are available; the paired three-variant comparison documents the value of the multi-agent architecture; unresolved limitations are disclosed.

## 7. Research rationale

The literature supports evaluating separate components and using human review, but does not supply universal product-release thresholds such as Recall@10 ≥0.90 or schema validity ≥99.5%. Those numerical cutoffs above are this project's proposed engineering policy.

- **BEIR** evaluates lexical, dense and reranking retrieval approaches across varied tasks and reports that BM25 remains a robust baseline while reranking can improve quality at higher compute cost. This supports keeping BM25, dense retrieval, hybrid fusion and reranking as separate ablation stages: https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html
- **RAGChecker** proposes fine-grained diagnostic metrics for retrieval and generation and compares them with human judgments. This supports component-level failure analysis rather than a single aggregate RAG score: https://proceedings.neurips.cc/paper_files/paper/2024/hash/27245589131d17368cccdfa990cbf16e-Abstract.html
- **ARES** evaluates context relevance, answer faithfulness and answer relevance, and uses human-annotated data to address automated-judge errors: https://aclanthology.org/2024.naacl-long.20/
- **ALCE** separately measures answer correctness and citation quality, demonstrating that citation presence alone is not sufficient: https://aclanthology.org/2023.emnlp-main.398/

## Final recommendation

Do not promote the current baseline to use. First run the controlled variants and fix the agent-specific failures, then build an eligible, held-out evaluation set. Treat the release decision as a gate-by-gate safety case: all mandatory gates must pass, and any metric not actually measured must remain `NOT_EVALUATED` rather than being filled with an optimistic proxy.

## Prior v2 candidate and live development evidence (pre-judge)

The v2 candidate was exercised against the configured live ThaiLLM, Qdrant/Cloudflare hybrid retrieval, and Jina reranker in development run `20261029T071757Z-556f9a64`. It completed all six development queries and all 30 specialist records with valid JSON and schemas. Numeric fact coverage was 3/3; final-context evidence spans were present for all six queries. Across the six cases, reranked known-relevant Recall@10, MRR@10, nDCG@10, reranked answer-bearing-span recall, and final-context span recall were each 1.00. All six protected traces were recorded.

The run's 32 attempt records passed telemetry-integrity checks: no missing required fields, duplicate attempt keys, contradictory statuses, missing/duplicate query IDs, or benchmark-level errors. Seven factual claims were prepared for review; 0/7 have human review and 0/7 double review. The run is a six-query development diagnostic, not a held-out evaluation or a release pass.

Run artifacts: [benchmark manifest](./GAIB-1/runs/token_root_cause/20261029T071757Z-556f9a64/benchmark_run_manifest.json), [gate status](./GAIB-1/runs/token_root_cause/20261029T071757Z-556f9a64/exit_criteria_gate_status.json), [agent metrics](./GAIB-1/runs/token_root_cause/20261029T071757Z-556f9a64/multiagent_per_agent_metrics.csv), [retrieval metrics](./GAIB-1/runs/token_root_cause/20261029T071757Z-556f9a64/retrieval_stage_metrics.csv), [claim-review template](./GAIB-1/runs/token_root_cause/20261029T071757Z-556f9a64/answer_human_review_template.csv), and [HTTP attempt telemetry](./GAIB-1/runs/token_root_cause/20261029T071757Z-556f9a64/live_http_attempts.csv).

The reproducible notebook is [Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb](./GAIB-1/Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb), SHA-256 `fe3e33e53a2714d7fb5e154602ca1a3de4c3d0f89de325d05535907cc33e6250`. Its current builder SHA-256 is `9befb280481d937d0f9c8a4c6e342d28cf28490632d260178e9f1f757994ea14`. The current builder adds machine gates for accounting for each critical query's answer/abstention status and for numeric facts requiring complete fact coverage with valid citations and a retrieved evidence span, or a correct explicit abstention. The saved live run's gate JSON predates these two fields; their PASS and FAIL paths, including correct-abstention handling, are covered by regression tests rather than represented as fields in that historical JSON.

## AI-as-a-judge policy integration — initial candidate checkpoint

The candidate notebook now integrates the AI-as-a-judge policy in [GAIB1_AI_AS_JUDGE_ACCEPTANCE_POLICY.md](./GAIB1_AI_AS_JUDGE_ACCEPTANCE_POLICY.md). The implementation performs blind claim/evidence review before a separate expected-fact comparison, validates citation and evidence-span references, escalates critical/uncertain/disputed judgments to a distinct second model, preserves disagreements, and fails closed on missing or invalid evidence. It generates claim-level judgments, judge-call metrics, a stratified human-calibration template, labels/metrics, a policy gate report, and an updated run manifest. Expected-fact matching and deterministic numeric checks do not substitute for evidence support.

The regenerated candidate is [Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb](./GAIB-1/Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb), SHA-256 `6aab61cffb355a4fd7c102f570646b713d7f72a97d72b0eecad9c07178ac4fb8`. It is generated from [build_token_root_cause_experiment.py](./GAIB-1/build_token_root_cause_experiment.py) and uses [gaib1_ai_judge.py](./GAIB-1/gaib1_ai_judge.py).

**Verification at this checkpoint:** 39 regression tests passed; the Python modules and test files compiled; the notebook was regenerated from the builder and its code cells were checked for clean outputs and valid Python syntax by the regression suite. No live AI-judge acceptance run had yet been made; this status is superseded by the latest live held-out attempt below.

**Decision at this checkpoint: NO-GO.** These were the blockers at that point in time, not the current blocker list:

- The available Ground Truth file contains 43 records (37 source-present and 6 source-gap records), with only 6 development queries and 25 frozen test queries. There is no independent, source-separated held-out set of at least 100 queries. The frozen test set must not be used for tuning or represented as a 100-query set.
- `GAIB_JUDGE_MODEL` and `GAIB_SECOND_JUDGE_MODEL` are not configured. A live run requires two available, distinct judge models, both distinct from the answer generator.
- A completed, independent human calibration set is not present. Acceptance requires at least 50 stratified reviewed claims, at least 10 claims double-reviewed by independent reviewers, and all policy agreement thresholds.
- The policy's 100 end-to-end latency runs and paired three-variant comparison (single-agent + RAG, multi-agent + RAG, and multi-agent + RAG + judge) are not evidenced.

Do not treat the notebook's generated templates or the earlier development run as acceptance evidence. The current decision and blockers are recorded in the latest live held-out checkpoint below.

## Initial Exit-criteria v2 candidate checkpoint (superseded)

A separate, reproducible candidate notebook is generated by `GAIB-1/build_gaib1_exit_criteria_v2.py` and written to `GAIB-1/Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb`; the v1 notebook remains untouched. The candidate adds protected traces for `gtv2_000055`, `gtv2_000070`, and `gtv2_000078`, source-text excerpts and exact-quote span metrics at retrieval stages, raw-versus-rendered citation IDs, explicit answer/abstention fields, and a machine-readable `exit_criteria_gate_status.json`. Numeric target-range extraction is constrained to an allowed citation from a retrieved source whose publication date matches the date asked; it does not use Ground Truth values to produce answers.

Candidate notebook SHA-256: `34369d340d1cac7b19eda5094844c1d7b7f9ee72e4cf323c1ccf80dfcf4d4f0b`. The builder was run twice with identical output hashes. The focused regression suite passed **19 tests**; Python compilation and Pylance syntax checks reported no errors.

The gate design described here was intentionally fail-closed. At this initial checkpoint no live run had been started; the credential probe used then-current environment variable aliases and did not find the Cloudflare values. That blocker was later resolved using the configured `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` names, followed by the live development run documented above. This initial candidate hash and credential status are historical and superseded; the current decision remains **NO-GO / NOT READY** until all mandatory acceptance evidence is available.

## Latest live held-out acceptance attempt — partial, NO-GO

The candidate was run against the separately constructed 100-query `held_out` set in run `20261029T081959Z-6909f183`. The frozen test split was not used or modified. The Ground Truth contains 100 unique source documents and publication dates, all exact quote spans were verified against the local Federal Reserve source corpus, and source-group overlap with the existing development, validation, and test splits is zero. It is a machine-constructed `numeric_fact`-only set and still requires human semantic review.

| Measure | Observed result |
|---|---:|
| Held-out queries in the source dataset / retrieval audit | 100 / 100 |
| Source documents present in the local corpus | 100 / 100 |
| Runtime Qdrant and BM25 coverage / evaluation-eligible queries | 87 / 100 |
| Queries blocked by source/corpus ID mismatch | 13 |
| Eligible reranked known-relevant Recall@10 / MRR@10 / nDCG@10 | 0.920 / 0.914 / 0.915 (n=87) |
| Eligible reranked answer-bearing span recall@10 | 0.943 (n=87) |
| Multi-agent queries completed / attempted | 18 / 100 |
| Specialist records schema-valid | 90 / 90 completed records |
| Multi-agent queries failed or blocked | 82 / 100 |
| Human-reviewed / double-reviewed claims | 0 / 0 |

The 13 corpus-coverage failures independently block the 100% index-coverage gate. Of the remaining failed/blocked queries, 69 failed because strict A2 retrieval could not obtain a successful Jina rerank; the run reports `JINA_API_KEY2` HTTP 403. A post-run, minimal probe returned HTTP 403 for both configured Jina key slots. No credentials were printed or added to the notebook. The candidate must not fall back to non-Jina ranking to make this gate pass.

The AI-judge metrics stage also stopped on a missing `expected_fact_judgment` (`None`) before producing the complete judge summary. This was fixed in [gaib1_ai_judge.py](./GAIB-1/gaib1_ai_judge.py): missing or malformed expected-fact judgments now count as unevaluated and cannot be counted as matches. A regression test covers this fail-closed behavior. Validation after the fix: **44 GAIB-1 tests passed**, Python compilation passed, and Pylance reported no syntax errors for the changed module and test.

Run evidence: [execution status](./GAIB-1/runs/token_root_cause/20261029T081959Z-6909f183/notebook_execution_status.json), [gate status](./GAIB-1/runs/token_root_cause/20261029T081959Z-6909f183/exit_criteria_gate_status.json), [Ground Truth coverage audit](./GAIB-1/runs/token_root_cause/20261029T081959Z-6909f183/ground_truth_audit.csv), [retrieval metrics](./GAIB-1/runs/token_root_cause/20261029T081959Z-6909f183/retrieval_stage_metrics.csv), [multi-agent results](./GAIB-1/runs/token_root_cause/20261029T081959Z-6909f183/multiagent_benchmark_results.csv), [multi-agent errors](./GAIB-1/runs/token_root_cause/20261029T081959Z-6909f183/multiagent_benchmark_errors.csv), and [human calibration template](./GAIB-1/runs/token_root_cause/20261029T081959Z-6909f183/ai_judge_human_calibration_template.csv).

**Decision remains NO-GO.** The next live attempt requires working Jina credentials and a source/index-covered 100-query set (or an explicitly approved, isolated Qdrant ingestion of the missing eligible source documents). It must then complete all 100 end-to-end runs and the judge gates. Human calibration requires independent reviewer labels; the system must not invent them. The paired three-variant comparison—single-agent + RAG, multi-agent + RAG, and multi-agent + RAG + judge—remains unmeasured.
