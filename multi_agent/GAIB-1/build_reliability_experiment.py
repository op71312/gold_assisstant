#!/usr/bin/env python
"""Build a separate GAIB reliability experiment notebook from the A2 baseline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
GAIB_DIR = Path(__file__).resolve().parent
SOURCE_NOTEBOOK = GAIB_DIR / "Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb"
OUTPUT_NOTEBOOK = GAIB_DIR / "Gold_Assistant_GAIB1_Reliability_Experiment_Phase1_2.ipynb"


def source(cell: dict[str, Any]) -> str:
    return "".join(cell.get("source", []))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected exactly one matching source block, found {count}")
    return text.replace(old, new, 1)


def set_source(cell: dict[str, Any], value: str) -> None:
    cell["source"] = value.splitlines(keepends=True)


AUDIT_CELL = r'''def _normalized_alias(value):
    if value is None:
        return None
    result = str(value).strip().rstrip("/").casefold()
    return result or None

def _record_aliases(record):
    fields = ("document_id", "doc_id", "original_id", "source_document_id",
              "source_document_id_in_uploaded_corpus", "url", "source_url")
    return {_normalized_alias(record.get(field)) for field in fields if _normalized_alias(record.get(field))}

def _expected_groups(gt):
    groups = []
    judgments = gt.get("relevance_judgments") or []
    evidence = gt.get("evidence") or []
    for judgment in judgments:
        aliases = _record_aliases(judgment)
        if not aliases:
            continue
        matching = [item for item in evidence if aliases & _record_aliases(item)]
        for item in matching:
            aliases.update(_record_aliases(item))
        groups.append({
            "aliases": aliases,
            "expected_document_id": str(judgment.get("document_id") or judgment.get("doc_id") or ""),
            "document_aliases": {
                alias for alias in aliases
                if not alias.startswith(("http://", "https://"))
            },
            "url_aliases": {
                alias for alias in aliases
                if alias.startswith(("http://", "https://"))
            },
        })
    return groups

def _source_file_names():
    fed_root = DATASET_ROOT / "news" / "fed"
    if not fed_root.is_dir():
        return set()
    return {path.name.casefold() for path in fed_root.rglob("*") if path.is_file()}

def audit_ground_truth_coverage(all_ready_rows):
    if assistant is None or assistant.evidence.backend_name != "qdrant_cloudflare_hybrid":
        raise RuntimeError("Index audit requires the initialized Qdrant + Cloudflare A2 backend.")
    retriever = assistant.evidence.backend
    chunks = retriever.chunks
    local_aliases = set().union(*(_record_aliases(chunk) for chunk in chunks)) if chunks else set()
    expected_source_names = _source_file_names()
    qdrant_aliases = set()
    scanned_points = 0
    offset = None
    while True:
        current_offset = offset
        (points, next_offset), _attempts = QDRANT_GATE.call(
            lambda current_offset=current_offset: retriever.qdrant.scroll(
                collection_name=QDRANT_COLLECTION,
                limit=256,
                with_payload=True,
                with_vectors=False,
                offset=current_offset,
            )
        )
        for point in points:
            payload = point.payload or {}
            payload["qdrant_point_id"] = str(point.id)
            qdrant_aliases.update(_record_aliases(payload))
            scanned_points += 1
        if next_offset is None:
            break
        if next_offset == offset:
            raise RuntimeError("Qdrant scroll pagination did not advance during index audit.")
        offset = next_offset

    audit_rows = []
    for gt in all_ready_rows:
        evidence = gt.get("evidence") or []
        expected = _expected_groups(gt)
        expected_aliases = set().union(*(group["aliases"] for group in expected)) if expected else set()
        expected_doc_aliases = set().union(*(group["document_aliases"] for group in expected)) if expected else set()
        expected_url_aliases = set().union(*(group["url_aliases"] for group in expected)) if expected else set()
        group_checks = []
        for index, group in enumerate(expected, 1):
            local_match = bool(group["aliases"] & local_aliases)
            qdrant_match = bool(group["aliases"] & qdrant_aliases)
            group_checks.append({
                "group_index": index,
                "expected_document_id": group["expected_document_id"],
                "bm25_corpus_match": local_match,
                "qdrant_index_match": qdrant_match,
            })
        source_file_exists = bool(evidence) and all(
            Path(str(item.get("source_file") or "")).name.casefold() in expected_source_names
            for item in evidence
            if item.get("source_file")
        )
        if any(not item.get("source_file") for item in evidence):
            source_file_exists = False
        bm25_match = bool(group_checks) and all(item["bm25_corpus_match"] for item in group_checks)
        qdrant_match = bool(group_checks) and all(item["qdrant_index_match"] for item in group_checks)
        document_id_match = bool(expected_doc_aliases & local_aliases)
        url_match = bool(expected_url_aliases & (local_aliases | qdrant_aliases))
        if not evidence:
            coverage_status, block_reason = "SOURCE_GAP", "Ground Truth has no source evidence."
        elif not expected:
            coverage_status, block_reason = "NO_EXPECTED_DOCUMENT_GROUPS", "Ground Truth has no judged expected document groups."
        elif not source_file_exists:
            coverage_status, block_reason = "SOURCE_FILE_MISSING", "At least one evidence source file is not present in the local Fed source tree."
        elif not bm25_match:
            coverage_status, block_reason = "CORPUS_ID_MISMATCH", "One or more expected document groups do not match the BM25 corpus."
        elif not qdrant_match:
            coverage_status, block_reason = "INDEX_MISSING", "One or more expected document groups were not found in the Qdrant payload index."
        else:
            coverage_status, block_reason = "COVERED", ""
        audit_rows.append({
            "query_id": gt.get("query_id"),
            "split": gt.get("split"),
            "query_type": gt.get("query_type"),
            "query_language": gt.get("query_language"),
            "expected_document_ids": json.dumps(sorted(expected_doc_aliases), ensure_ascii=False),
            "expected_source_urls": json.dumps(sorted(expected_url_aliases), ensure_ascii=False),
            "expected_document_group_coverage": json.dumps(group_checks, ensure_ascii=False),
            "ground_truth_qdrant_index_coverage_verified": bool(gt.get("qdrant_index_coverage_verified", False)),
            "runtime_qdrant_index_coverage_verified": qdrant_match,
            "source_file_exists": source_file_exists,
            "bm25_corpus_match": bm25_match,
            "qdrant_index_match": qdrant_match,
            "document_id_match": document_id_match,
            "url_match": url_match,
            "judgment_count": len(expected),
            "review_status": gt.get("review_status"),
            "coverage_status": coverage_status,
            "block_reason": block_reason,
        })
    audit = pd.DataFrame(audit_rows)
    audit_path = OUTPUT_DIR / "ground_truth_audit.csv"
    audit.to_csv(audit_path, index=False, encoding="utf-8-sig")
    audit.attrs["qdrant_points_scanned"] = scanned_points
    audit.attrs["qdrant_collection"] = QDRANT_COLLECTION
    print(f"Ground Truth audit saved: {audit_path}; Qdrant points scanned={scanned_points:,}")
    display(audit.groupby(["split", "coverage_status"], dropna=False).size().rename("queries").to_frame())
    return audit

ALL_READY_GROUND_TRUTH = read_jsonl(GAIB_GT_READY_PATH)
ground_truth_audit_df = audit_ground_truth_coverage(ALL_READY_GROUND_TRUTH)
'''


RELIABILITY_METRICS_CELL = r'''def bootstrap_mean_interval(values, confidence=0.95, iterations=2000, minimum_queries=10):
    numeric = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if len(numeric) < minimum_queries:
        return {
            "sample_count": len(numeric),
            "status": "INSUFFICIENT_SAMPLE",
            "ci_low": "NOT_ESTIMATED",
            "ci_high": "NOT_ESTIMATED",
        }
    rng = np.random.default_rng(20261028)
    samples = rng.choice(numeric, size=(iterations, len(numeric)), replace=True).mean(axis=1)
    alpha = (1 - confidence) / 2
    return {
        "sample_count": len(numeric),
        "status": "ESTIMATED",
        "ci_low": float(np.quantile(samples, alpha)),
        "ci_high": float(np.quantile(samples, 1 - alpha)),
    }

def _stage_match_flags(gt, candidate):
    groups = _expected_groups(gt)
    candidate_aliases = _record_aliases(candidate)
    matched_groups = [group for group in groups if group["aliases"] & candidate_aliases]
    return {
        "relevance_match": bool(matched_groups),
        "document_id_match": any(group["document_aliases"] & candidate_aliases for group in groups),
        "url_match": any(group["url_aliases"] & candidate_aliases for group in groups),
    }

def _candidate_output_row(query_id, stage, rank, candidate, gt):
    flags = _stage_match_flags(gt, candidate)
    return {
        "query_id": query_id,
        "stage": stage,
        "rank": rank,
        "qdrant_point_id": candidate.get("qdrant_point_id"),
        "chunk_id": candidate.get("chunk_id"),
        "document_id": candidate.get("document_id"),
        "original_id": candidate.get("original_id"),
        "url": candidate.get("url") or candidate.get("source_url"),
        "source": candidate.get("source"),
        "source_file": candidate.get("source_file"),
        "title": candidate.get("title"),
        "publication_date": candidate.get("publication_date"),
        "score": candidate.get("reranker_score", candidate.get("rrf_score",
                 candidate.get("dense_score", candidate.get("bm25_score")))),
        **flags,
    }

def run_retrieval_benchmark(ground_truth, limit=None):
    if assistant is None or not assistant.evidence.ready:
        raise RuntimeError("Initialize the remote assistant before the retrieval benchmark.")
    if assistant.evidence.backend_name != "qdrant_cloudflare_hybrid":
        raise RuntimeError("This experiment requires Qdrant + Cloudflare hybrid retrieval.")
    rows, stage_rows, errors = [], [], []
    selected = (
        [row for row in ground_truth if str(row.get("query_id")) in set(BENCHMARK_QUERY_IDS)]
        if BENCHMARK_QUERY_IDS else (ground_truth[:limit] if limit else ground_truth)
    )
    coverage_by_query = {
        row["query_id"]: row for row in ground_truth_audit_df.to_dict("records")
    }
    for index, gt in enumerate(selected, 1):
        query = str(gt.get("query") or "").strip()
        if not query:
            errors.append({"query_id": gt.get("query_id"), "error_type": "empty_query", "error": "Ground Truth query is empty."})
            continue
        try:
            result = assistant.evidence.retrieve(query, FINAL_K)
            stage_candidates = result["metrics"].get("stage_candidates", {})
            stages = {
                "dense": stage_candidates.get("dense", []),
                "bm25": stage_candidates.get("bm25", []),
                "hybrid": stage_candidates.get("hybrid", result["raw_candidates"]),
                "reranked": result["ranked_candidates"],
            }
            context, context_sources = prepare_cited_context(result["ranked_candidates"])
            stages["evidence_context"] = context_sources
            audit_record = coverage_by_query.get(gt.get("query_id"), {})
            coverage_status = audit_record.get("coverage_status", "NOT_AUDITED")
            evaluation_eligible = coverage_status == "COVERED"
            row = {
                "run_id": GAIB_RUN_ID,
                "query_id": gt.get("query_id"),
                "query": query,
                "query_type": gt.get("query_type"),
                "query_language": gt.get("query_language"),
                "split": gt.get("split"),
                "review_status": gt.get("review_status"),
                "judgment_set_exhaustive": gt.get("judgment_set_exhaustive", False),
                "ground_truth_qdrant_index_coverage_verified": gt.get("qdrant_index_coverage_verified", False),
                "runtime_qdrant_index_coverage_verified": audit_record.get("runtime_qdrant_index_coverage_verified", False),
                "coverage_status": coverage_status,
                "evaluation_eligible": evaluation_eligible,
                "evaluation_block_reason": audit_record.get("block_reason", "Ground Truth index coverage was not audited."),
                "retrieval_backend": result.get("backend"),
                "dense_latency_ms": result["metrics"].get("dense_wall_ms"),
                "bm25_latency_ms": result["metrics"].get("bm25_wall_ms"),
                "embedding_latency_ms": result["metrics"].get("embedding_ms"),
                "qdrant_latency_ms": result["metrics"].get("qdrant_ms"),
                "hybrid_latency_ms": result["metrics"].get("retrieval_wall_ms"),
                "jina_latency_ms": result["metrics"].get("rerank_ms"),
                "jina_status": result["metrics"].get("rerank_status"),
                "input_tokens": "NOT_AVAILABLE_FOR_RETRIEVAL",
                "output_tokens": "NOT_AVAILABLE_FOR_RETRIEVAL",
            }
            for stage, candidates in stages.items():
                candidate_aliases = [_record_aliases(candidate) for candidate in candidates]
                matched_ids = [
                    group["expected_document_id"]
                    for group in _expected_groups(gt)
                    if group["expected_document_id"]
                    and any(group["aliases"] & aliases for aliases in candidate_aliases)
                ]
                expected_ids = [
                    group["expected_document_id"]
                    for group in _expected_groups(gt)
                    if group["expected_document_id"]
                ]
                row[f"{stage}_matched_document_ids"] = json.dumps(sorted(set(matched_ids)), ensure_ascii=False)
                row[f"{stage}_unmatched_expected_document_ids"] = json.dumps(
                    sorted(set(expected_ids) - set(matched_ids)), ensure_ascii=False
                )
                identities = [
                    _normalized_alias(candidate.get("chunk_id") or candidate.get("qdrant_point_id"))
                    for candidate in candidates
                ]
                identities = [identity for identity in identities if identity]
                row[f"{stage}_duplicate_chunk_rate"] = (
                    1 - len(set(identities)) / len(identities) if identities else "NO_CANDIDATES"
                )
            for stage in ("dense", "bm25", "hybrid"):
                candidates = stages[stage]
                for rank, candidate in enumerate(candidates, 1):
                    stage_rows.append(_candidate_output_row(gt.get("query_id"), stage, rank, candidate, gt))
                for k in (10, 40):
                    if evaluation_eligible:
                        metrics = rank_metrics(gt, candidates, k=k)
                        row[f"{stage}_known_relevant_recall@{k}"] = metrics[f"known_relevant_recall@{k}"]
                        if k == 10:
                            row[f"{stage}_mrr@10"] = metrics["mrr@10"]
                            row[f"{stage}_ndcg@10"] = metrics["ndcg@10"]
                        row[f"{stage}_judged_relevant_count"] = metrics["judged_relevant_count"]
                    else:
                        row[f"{stage}_known_relevant_recall@{k}"] = "BLOCKED_COVERAGE"
                        if k == 10:
                            row[f"{stage}_mrr@10"] = "BLOCKED_COVERAGE"
                            row[f"{stage}_ndcg@10"] = "BLOCKED_COVERAGE"
                        row[f"{stage}_judged_relevant_count"] = len(_expected_groups(gt))
            for stage in ("reranked", "evidence_context"):
                candidates = stages[stage]
                for rank, candidate in enumerate(candidates, 1):
                    stage_rows.append(_candidate_output_row(gt.get("query_id"), stage, rank, candidate, gt))
                if evaluation_eligible:
                    metrics = rank_metrics(gt, candidates, k=10)
                    row[f"{stage}_known_relevant_recall@10"] = metrics["known_relevant_recall@10"]
                    row[f"{stage}_mrr@10"] = metrics["mrr@10"]
                    row[f"{stage}_ndcg@10"] = metrics["ndcg@10"]
                    row[f"{stage}_judged_relevant_count"] = metrics["judged_relevant_count"]
                else:
                    row[f"{stage}_known_relevant_recall@10"] = "BLOCKED_COVERAGE"
                    row[f"{stage}_mrr@10"] = "BLOCKED_COVERAGE"
                    row[f"{stage}_ndcg@10"] = "BLOCKED_COVERAGE"
                    row[f"{stage}_judged_relevant_count"] = len(_expected_groups(gt))
            row["expected_doc_candidate_recall@40"] = (
                row["hybrid_known_relevant_recall@40"] if evaluation_eligible else "BLOCKED_COVERAGE"
            )
            expected_groups = _expected_groups(gt)
            row["document_id_match_rate"] = (
                sum(any(group["document_aliases"] & _record_aliases(item) for item in stages["hybrid"])
                    for group in expected_groups) / len(expected_groups)
                if expected_groups else "NO_JUDGMENTS"
            )
            row["url_match_rate"] = (
                sum(any(group["url_aliases"] & _record_aliases(item) for item in stages["hybrid"])
                    for group in expected_groups) / len(expected_groups)
                if expected_groups else "NO_JUDGMENTS"
            )
            row["stage_context_ids"] = json.dumps(
                [{"citation_id": item.get("citation_id"), "document_id": item.get("document_id"),
                  "chunk_id": item.get("chunk_id"), "url": item.get("url")} for item in context_sources],
                ensure_ascii=False,
            )
            rows.append(row)
        except Exception as error:
            errors.append({
                "query_id": gt.get("query_id"),
                "error_type": type(error).__name__,
                "error": str(error)[:800],
            })
        if index % 10 == 0:
            print(f"Processed {index}/{len(selected)} retrieval queries.")

    result_df = pd.DataFrame(rows)
    stage_df = pd.DataFrame(stage_rows)
    error_df = pd.DataFrame(errors)
    result_df.to_csv(OUTPUT_DIR / "retrieval_stage_metrics.csv", index=False, encoding="utf-8-sig")
    stage_df.to_csv(OUTPUT_DIR / "retrieval_stage_candidates.csv", index=False, encoding="utf-8-sig")
    error_df.to_csv(OUTPUT_DIR / "retrieval_errors.csv", index=False, encoding="utf-8-sig")
    miss_columns = [
        "query_id", "coverage_status", "dense_known_relevant_recall@10",
        "bm25_known_relevant_recall@10", "hybrid_known_relevant_recall@10",
        "hybrid_known_relevant_recall@40", "reranked_known_relevant_recall@10",
        "dense_matched_document_ids", "bm25_matched_document_ids",
        "hybrid_matched_document_ids", "reranked_matched_document_ids",
    ]
    if not result_df.empty and "reranked_known_relevant_recall@10" in result_df:
        reranked_recall = pd.to_numeric(result_df["reranked_known_relevant_recall@10"], errors="coerce")
        miss_df = result_df.loc[reranked_recall.eq(0), [column for column in miss_columns if column in result_df]]
    else:
        miss_df = pd.DataFrame(columns=miss_columns)
    miss_df.to_csv(OUTPUT_DIR / "retrieval_miss_diagnosis.csv", index=False, encoding="utf-8-sig")
    if not miss_df.empty:
        display(miss_df)
    interval_rows = []
    if not result_df.empty:
        for metric in [column for column in result_df if "recall@" in column or "mrr@" in column or "ndcg@" in column]:
            interval_rows.append({"metric": metric, **bootstrap_mean_interval(result_df[metric])})
    pd.DataFrame(interval_rows).to_csv(OUTPUT_DIR / "retrieval_bootstrap_intervals.csv", index=False, encoding="utf-8-sig")
    baseline_path = BASELINE_RUN_DIR / "retrieval_reranking_benchmark.csv"
    if baseline_path.is_file() and not result_df.empty:
        baseline = pd.read_csv(baseline_path)
        comparison = result_df.merge(baseline, on="query_id", how="left", suffixes=("_experiment", "_baseline"))
        comparison.to_csv(OUTPUT_DIR / "baseline_comparison_retrieval.csv", index=False, encoding="utf-8-sig")
    return result_df, stage_df, error_df

retrieval_benchmark_df = pd.DataFrame()
retrieval_stage_candidates_df = pd.DataFrame()
retrieval_errors_df = pd.DataFrame()
if RUN_RETRIEVAL_BENCHMARK and GROUND_TRUTH:
    retrieval_benchmark_df, retrieval_stage_candidates_df, retrieval_errors_df = run_retrieval_benchmark(
        GROUND_TRUTH, limit=BENCHMARK_LIMIT
    )
    display(retrieval_benchmark_df.head())
    print(f"Retrieval sample size={len(retrieval_benchmark_df)}; errors={len(retrieval_errors_df)}.")
else:
    print("Retrieval experiment is disabled or selected Ground Truth split is empty.")
'''


def main() -> None:
    notebook = json.loads(SOURCE_NOTEBOOK.read_text(encoding="utf-8"))
    cells = notebook.get("cells", [])
    by_id = {cell.get("id"): cell for cell in cells}
    required_ids = {
        "eab45473", "8b105991", "6c41d141", "677be107", "5cce7a2e",
        "4284e50e", "a3a65109", "6059c30d",
    }
    missing = required_ids - by_id.keys()
    if missing:
        raise ValueError(f"Source notebook is missing expected cells: {sorted(missing)}")

    title = source(by_id["eab45473"])
    title = replace_once(
        title,
        "# Gold Assistant — 5-Agent Collaborative Research Pipeline (7-Key)",
        "# GAIB-1 Reliability Experiment — Phase 1–2",
        "experiment title",
    )
    title += (
        "\n\nThis is a new, separate experiment notebook cloned from the existing GAIB-1 A2 pipeline. "
        "It keeps the A2 retrieval/generation configuration fixed and focuses on benchmark integrity, "
        "strict agent contracts, claim-level evidence rendering, and auditability. It does not change "
        "the embedding model, candidate counts, RRF, Jina model, LLM model, or generation parameters. "
        "Outputs are isolated under `runs/reliability_phase1_2/`; earlier run files are never overwritten.\n"
    )
    set_source(by_id["eab45473"], title)

    config = source(by_id["8b105991"])
    config = replace_once(
        config,
        "import threading\n",
        "import threading\nimport traceback\n",
        "traceback diagnostics import",
    )
    config = replace_once(
        config,
        'THAILLM_BASE_URL = os.getenv("THAILLM_BASE_URL", "http://thaillm.or.th/api/v1").strip().rstrip("/")',
        'THAILLM_BASE_URL = os.getenv("THAILLM_BASE_URL", "https://thaillm.or.th/api/v1").strip().rstrip("/")\n'
        'if not THAILLM_BASE_URL.lower().startswith("https://"):\n'
        '    raise ValueError("ThaiLLM API credentials must only be sent over HTTPS.")',
        "require HTTPS for ThaiLLM credentials",
    )
    config = replace_once(
        config,
        "RUN_RETRIEVAL_BENCHMARK = True",
        'RUN_RETRIEVAL_BENCHMARK = os.getenv("GAIB_RUN_RETRIEVAL_BENCHMARK", "false").strip().lower() in {"1", "true", "yes"}',
        "make retrieval benchmark an explicit environment opt-in",
    )
    config = replace_once(
        config,
        "RUN_AGENT_BENCHMARK = True",
        'RUN_AGENT_BENCHMARK = os.getenv("GAIB_RUN_AGENT_BENCHMARK", "false").strip().lower() in {"1", "true", "yes"}',
        "make multi-agent benchmark an explicit environment opt-in",
    )
    config = replace_once(
        config,
        'BENCHMARK_LIMIT = 5',
        'BENCHMARK_LIMIT = 5\nBENCHMARK_QUERY_IDS = []  # Optional: rerun only named failed query IDs.',
        "benchmark limit",
    )
    config = replace_once(
        config,
        'OUTPUT_DIR = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs"\nif not PROJECT_ROOT.exists() and Path.cwd().exists():',
        'GAIB_RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:8]\nOUTPUT_DIR = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs" / "reliability_phase1_2" / GAIB_RUN_ID\nBASELINE_RUN_DIR = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs"\nif not PROJECT_ROOT.exists() and Path.cwd().exists():',
        "isolated output directory",
    )
    config = replace_once(
        config,
        'OUTPUT_DIR = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs"\nOUTPUT_DIR.mkdir(parents=True, exist_ok=True)',
        'OUTPUT_DIR = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs" / "reliability_phase1_2" / GAIB_RUN_ID\nOUTPUT_DIR.mkdir(parents=True, exist_ok=True)',
        "isolated output fallback",
    )
    config = replace_once(
        config,
        '(OUTPUT_DIR / "benchmark_run_manifest.json").write_text(json.dumps(GAIB_RUNTIME_MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")',
        '''corpus_path = next((candidate for candidate in CHUNKS_CANDIDATES if candidate.is_file()), None)
GAIB_RUNTIME_MANIFEST.update({
    "run_id": GAIB_RUN_ID,
    "experiment": "GAIB-1 reliability phase 1-2",
    "prompt_version": "claim-evidence-v1",
    "schema_version": "agent-contract-v1",
    "corpus_sha256": None,
    "baseline_comparison_note": "Historical run comparison is diagnostic only; API timing/model service conditions may differ.",
})
if corpus_path is not None:
    corpus_digest = hashlib.sha256()
    with corpus_path.open("rb") as corpus_stream:
        for corpus_block in iter(lambda: corpus_stream.read(1024 * 1024), b""):
            corpus_digest.update(corpus_block)
    GAIB_RUNTIME_MANIFEST["corpus_sha256"] = corpus_digest.hexdigest()
(OUTPUT_DIR / "benchmark_run_manifest.json").write_text(json.dumps(GAIB_RUNTIME_MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")''',
        "run provenance manifest",
    )
    set_source(by_id["8b105991"], config)

    retrieval_engine = source(by_id["6c41d141"])
    retrieval_engine = replace_once(
        retrieval_engine,
        "class QdrantHybridRetriever:",
        '''def _stage_candidate_metadata(candidate):
    return {
        key: candidate.get(key)
        for key in ("qdrant_point_id", "chunk_id", "document_id", "original_id",
                    "source_document_id", "source_document_id_in_uploaded_corpus",
                    "url", "source_url", "source", "source_file", "title", "publication_date",
                    "dense_score", "bm25_score", "rrf_score")
        if candidate.get(key) is not None
    }

class QdrantHybridRetriever:''',
        "retrieval stage instrumentation helper",
    )
    retrieval_engine = replace_once(
        retrieval_engine,
        '''metrics.update({"retrieval_wall_ms":(time.perf_counter()-wall)*1000,"dense_result_count":len(dense),"bm25_result_count":len(bm),
                        "hybrid_candidate_count":len(ranked),"retrieval_status":"success" if ranked else "no_results",
                        "retrieval_errors":";".join(errors) or None,"corpus_source":self.corpus_source,"corpus_chunk_count":len(self.chunks)})''',
        '''metrics["stage_candidates"] = {
            "dense": [_stage_candidate_metadata(candidate) for candidate in dense],
            "bm25": [_stage_candidate_metadata(candidate) for candidate in bm],
            "hybrid": [_stage_candidate_metadata(candidate) for candidate in ranked],
        }
        metrics.update({"retrieval_wall_ms":(time.perf_counter()-wall)*1000,"dense_result_count":len(dense),"bm25_result_count":len(bm),
                        "hybrid_candidate_count":len(ranked),"retrieval_status":"success" if ranked else "no_results",
                        "retrieval_errors":";".join(errors) or None,"corpus_source":self.corpus_source,"corpus_chunk_count":len(self.chunks)})''',
        "retrieval stage candidate capture",
    )
    set_source(by_id["6c41d141"], retrieval_engine)

    agent_source = source(by_id["f5926591"])
    agent_contract_changes = [
        (
            "Return JSON keys: status, concise_summary, relevant_events (list of {{event,date,reported_fact,possible_market_channel,evidence_ids}}), price_bias (bullish/bearish/mixed/unknown), evidence_strength (high/medium/low), missing_evidence, cautions. Each event must include evidence_ids chosen only from provided [S#]. If no relevant evidence, use status='insufficient_evidence' and empty events.",
            "Return JSON keys: status, reported_fact, event_date, possible_market_channel, evidence_ids, relevant_events (list of {{event,date,reported_fact,possible_market_channel,evidence_ids}}), concise_summary, price_bias (bullish/bearish/mixed/unknown), evidence_strength (high/medium/low), missing_evidence, cautions. Use empty strings/lists and null dates when evidence is insufficient. Every factual item must cite only provided [S#] IDs.",
        ),
        (
            "Return JSON keys: status, as_of, observed_market_facts (list of {{fact,evidence_ids}}), macro_channels (list of {{factor,observed_evidence,interpretation,evidence_ids}}), macro_bias (bullish/bearish/mixed/unknown), confidence (low/medium/high), data_gaps, non_causal_caveat. Use only supplied evidence IDs. If a macro variable is absent, say so; do not infer its current value.",
            "Return JSON keys: status, as_of, observed_market_facts (list of {{fact,evidence_ids}}), macro_channels (list of {{factor,observed_evidence,interpretation,evidence_ids}}), evidence_ids, macro_bias (bullish/bearish/mixed/unknown), confidence (low/medium/high), data_gaps, non_causal_caveat. Use only supplied evidence IDs. If a macro variable is absent, say so; do not infer its current value.",
        ),
        (
            "Return JSON keys: status, as_of, quantified_findings (list of {{finding,evidence_ids}}), hmm_interpretation, regime_state_id, regime_confidence, robustness_notes, limitations, recommendation_for_next_test. Do not invent regime labels; describe the state using supplied state-feature means. State IDs have no inherent bullish/bearish meaning unless observed feature summaries support a cautious interpretation. If HMM unavailable, report it transparently.",
            "Return JSON keys: status, as_of, statistics (list of {{name,value,unit,period,evidence_ids}}), regime_state (object with state_id, as_of, confidence, interpretation, or null), feature_inputs (list of {{name,value,as_of,source}}), tool_result_ids (list of valid [Q#] or [H#] IDs), quantified_findings (list of {{finding,evidence_ids}}), hmm_interpretation, regime_state_id, regime_confidence, robustness_notes, limitations, recommendation_for_next_test. Do not invent regime labels or feature values. If the HMM feature contract is unverified or unavailable, state that in limitations and do not imply a verified state.",
        ),
        (
            "Return JSON keys: status, critical_risks (list of {{risk,severity,measured_evidence,evidence_ids,mitigation}}), accounting_assessment, data_provenance, synthetic_data_caveat, go_no_go (go/conditional/no_go), required_checks_before_external_claims. Severity values: low/medium/high. Do not turn missing data into a zero.",
            "Return JSON keys: status, checks (list of {{check,observed_value,expected_invariant,status,evidence_ids}}), observed_value, expected_invariant, pnl_reconciliation, risk_flags, critical_risks (list of {{risk,severity,measured_evidence,evidence_ids,mitigation}}), accounting_assessment, data_provenance, synthetic_data_caveat, go_no_go (go/conditional/no_go), required_checks_before_external_claims. Severity values: low/medium/high. Use only supplied Python audit results; do not calculate new values in prose or turn missing data into zero.",
        ),
    ]
    for old_contract, new_contract in agent_contract_changes:
        agent_source = replace_once(agent_source, old_contract, new_contract, "specialist JSON contract prompt")
    set_source(by_id["f5926591"], agent_source)

    llm_source = source(by_id["677be107"])
    parser_start = llm_source.index("def parse_json_object(text):")
    parser_end = llm_source.index("AGENT_SYSTEM_BASE =", parser_start)
    llm_replacement = r'''def parse_json_object(text):
    raw = str(text or "").strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", raw, flags=re.I | re.S)
    if fenced:
        raw = fenced.group(1).strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        return {}, False, f"invalid_json:{error.msg}"
    if not isinstance(value, dict):
        return {}, False, "JSON root is not an object"
    return value, True, None

AGENT_SCHEMAS = {
    "AI1_News_Analyst": {
        "required": {"status": str, "reported_fact": str, "event_date": (str, type(None)),
                     "possible_market_channel": str, "evidence_ids": list,
                     "concise_summary": str, "relevant_events": list,
                     "price_bias": str, "evidence_strength": str, "missing_evidence": list, "cautions": list},
        "list_items": {"relevant_events": ("event", "date", "reported_fact", "possible_market_channel", "evidence_ids")},
    },
    "AI2_Macro_Analyst": {
        "required": {"status": str, "as_of": (str, type(None)), "observed_market_facts": list,
                     "macro_channels": list, "evidence_ids": list, "macro_bias": str, "confidence": str,
                     "data_gaps": list, "non_causal_caveat": str},
        "list_items": {"observed_market_facts": ("fact", "evidence_ids"),
                       "macro_channels": ("factor", "observed_evidence", "interpretation", "evidence_ids")},
    },
    "AI3_Quant_Regime_Analyst": {
        "required": {"status": str, "as_of": (str, type(None)), "statistics": list,
                     "regime_state": (dict, type(None)), "feature_inputs": list, "tool_result_ids": list,
                     "quantified_findings": list,
                     "hmm_interpretation": (str, type(None)), "regime_state_id": (str, int, type(None)),
                     "regime_confidence": (str, int, float, type(None)), "robustness_notes": list,
                     "limitations": list, "recommendation_for_next_test": (str, type(None))},
        "list_items": {"statistics": ("name", "value", "unit", "period", "evidence_ids"),
                       "feature_inputs": ("name", "value", "as_of", "source"),
                       "quantified_findings": ("finding", "evidence_ids")},
    },
    "AI4_Risk_Data_Auditor": {
        "required": {"status": str, "checks": list, "observed_value": (str, int, float, dict, type(None)),
                     "expected_invariant": (str, dict, type(None)), "pnl_reconciliation": (str, dict, type(None)),
                     "risk_flags": list, "critical_risks": list, "accounting_assessment": (str, dict, type(None)),
                     "data_provenance": (str, dict, type(None)), "synthetic_data_caveat": str,
                     "go_no_go": str, "required_checks_before_external_claims": list},
        "list_items": {"checks": ("check", "observed_value", "expected_invariant", "status", "evidence_ids"),
                       "critical_risks": ("risk", "severity", "measured_evidence", "evidence_ids", "mitigation")},
    },
    "AI5_Lead_Researcher": {
        "required": {"status": str, "executive_summary": str, "evidence_based_findings": list,
                     "agent_agreement": list, "agent_disagreements": list, "risk_flags": list,
                     "confidence": str, "limitations": list, "next_research_steps": list, "abstention_reason": str},
        "list_items": {"evidence_based_findings": ("claim", "claim_type", "evidence_ids", "confidence", "limitations")},
    },
}

def validate_agent_schema(agent_name, value):
    contract = AGENT_SCHEMAS.get(agent_name)
    if contract is None:
        return [f"no_schema_registered:{agent_name}"]
    errors = []
    for key, expected_type in contract["required"].items():
        if key not in value:
            errors.append(f"missing_required_field:{key}")
        elif not isinstance(value[key], expected_type):
            errors.append(f"invalid_type:{key}:expected_{getattr(expected_type, '__name__', 'union')}")
    for field, required_keys in contract.get("list_items", {}).items():
        items = value.get(field)
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"invalid_item_type:{field}[{index}]")
                continue
            for key in required_keys:
                if key not in item:
                    errors.append(f"missing_nested_field:{field}[{index}].{key}")
            if "evidence_ids" in item and not isinstance(item["evidence_ids"], list):
                errors.append(f"invalid_type:{field}[{index}].evidence_ids")
    for key, allowed in (("price_bias", {"bullish", "bearish", "mixed", "unknown"}),
                         ("macro_bias", {"bullish", "bearish", "mixed", "unknown"}),
                         ("confidence", {"low", "medium", "high"}),
                         ("evidence_strength", {"low", "medium", "high"}),
                         ("go_no_go", {"go", "conditional", "no_go"})):
        if key in value and isinstance(value[key], str) and value[key].strip().lower() not in allowed:
            errors.append(f"invalid_enum:{key}")
    for index, finding in enumerate(value.get("evidence_based_findings", []) if isinstance(value.get("evidence_based_findings"), list) else []):
        if isinstance(finding, dict):
            if finding.get("claim_type") not in {"fact", "interpretation", "hypothesis"}:
                errors.append(f"invalid_enum:evidence_based_findings[{index}].claim_type")
            if finding.get("confidence") not in {"low", "medium", "high"}:
                errors.append(f"invalid_enum:evidence_based_findings[{index}].confidence")
    return errors

def _collect_evidence_ids(value):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"evidence_ids", "tool_result_ids"} and isinstance(item, list):
                found.extend(str(identifier) for identifier in item)
            else:
                found.extend(_collect_evidence_ids(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_collect_evidence_ids(item))
    return found

def call_agent_json(llm, agent_name, role_instruction, user_payload, max_tokens=None, allowed_ids=None):
    started = time.perf_counter()
    effective_max_tokens = max_tokens if max_tokens is not None else THAILLM_MAX_TOKENS_AGENT
    system_prompt = AGENT_SYSTEM_BASE + "\nROLE: " + role_instruction
    available_ids = set(allowed_ids or re.findall(r"\[((?:S|Q|H|R)\d+)\]", user_payload))
    raw_responses = []
    responses = []
    parsed = {}
    parse_error = None
    parse_success = False
    schema_errors = []
    status = "api_error"
    api_success = False
    exception_traceback = None
    for attempt in range(2):
        request_payload = user_payload
        if attempt:
            request_payload = (
                "Repair the prior response to satisfy this JSON contract. Return one JSON object only. "
                "Do not add unsupported factual claims. Validation errors: "
                + json.dumps(schema_errors or [parse_error], ensure_ascii=False)
                + "\nOriginal response:\n"
                + raw_responses[-1]
                + "\nOriginal task:\n"
                + user_payload
            )
        try:
            response = llm.generate(system_prompt, request_payload, max_tokens=effective_max_tokens)
            api_success = True
            responses.append(response)
            raw_responses.append(response.get("text", ""))
        except Exception as error:
            status = "api_error"
            parse_error = f"{type(error).__name__}:{error}"
            exception_traceback = traceback.format_exc()
            break
        finish_reason = str(response.get("finish_reason") or "").casefold()
        if finish_reason in {"length", "max_tokens", "max_output_tokens"}:
            status = "truncated_output"
            parse_error = "finish_reason_indicates_output_truncation"
            break
        parsed, parse_ok, parse_error = parse_json_object(response.get("text"))
        parse_success = parse_ok
        if not parse_ok:
            status = "invalid_json"
            if attempt == 0:
                continue
            break
        schema_errors = validate_agent_schema(agent_name, parsed)
        output_ids = _collect_evidence_ids(parsed)
        invalid_ids = sorted(set(output_ids) - available_ids) if available_ids else []
        if invalid_ids:
            schema_errors.append("unknown_evidence_ids:" + ",".join(invalid_ids))
        if schema_errors:
            status = "schema_violation"
            if attempt == 0:
                continue
            break
        status = "success"
        break

    def total_usage(key):
        values = [item.get(key) for item in responses if item.get(key) is not None]
        return sum(values) if values else None

    def usage_for(items, key):
        values = [item.get(key) for item in items if item.get(key) is not None]
        return sum(values) if values else None

    final_response = responses[-1] if responses else {}
    parse_valid = parse_success
    schema_valid = status == "success"
    evidence_ids = _collect_evidence_ids(parsed) if schema_valid else []
    invalid_ids = sorted(set(evidence_ids) - available_ids) if available_ids else []
    metrics = {
        "latency_ms": (time.perf_counter() - started) * 1000,
        "attempts": len(responses),
        "repair_attempts": max(0, len(responses) - 1),
        "attempt_count": len(responses),
        "initial_tokens": usage_for(responses[:1], "total_tokens"),
        "repair_tokens": usage_for(responses[1:], "total_tokens"),
        "initial_prompt_tokens": usage_for(responses[:1], "prompt_tokens"),
        "initial_completion_tokens": usage_for(responses[:1], "completion_tokens"),
        "repair_prompt_tokens": usage_for(responses[1:], "prompt_tokens"),
        "repair_completion_tokens": usage_for(responses[1:], "completion_tokens"),
        "finish_reason": final_response.get("finish_reason"),
        "prompt_tokens": total_usage("prompt_tokens"),
        "completion_tokens": total_usage("completion_tokens"),
        "total_tokens": total_usage("total_tokens"),
        "model": final_response.get("model", THAILLM_MODEL),
        "provider": final_response.get("provider", "ThaiLLM"),
        "api_success": api_success,
        "json_parse": parse_valid,
        "schema_valid": schema_valid,
        "task_success": None,
        "task_validation_status": "NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE",
        "invalid_evidence_ids": invalid_ids,
        "error_type": None if status == "success" else status,
        "traceback": exception_traceback,
    }
    return {
        "agent": agent_name,
        "status": status,
        "data": parsed if schema_valid else {},
        "raw_text": raw_responses[0] if raw_responses else "",
        "repair_raw_text": raw_responses[1] if len(raw_responses) > 1 else None,
        "json_valid": parse_valid,
        "schema_valid": schema_valid,
        "schema_errors": schema_errors,
        "json_error": parse_error,
        "metrics": metrics,
    }

'''
    llm_source = llm_source[:parser_start] + llm_replacement + llm_source[parser_end:]
    legacy_call = llm_source.rindex("def call_agent_json(llm, agent_name, role_instruction, user_payload, max_tokens=None):")
    legacy_call_end = llm_source.index('print("ThaiLLM JSON agent helpers ready.")', legacy_call)
    llm_source = llm_source[:legacy_call] + llm_source[legacy_call_end:]
    set_source(by_id["677be107"], llm_source)

    citation_source = source(by_id["5cce7a2e"])
    citation_source = replace_once(
        citation_source,
        '''        reduced={}
        for name,res in agent_results.items():
            data=res.get("data",{})
            reduced[name]={"status":res.get("status"),"json_valid":res.get("json_valid"),"findings":data,"raw_text_excerpt":res.get("raw_text","")[:4500] if not res.get("json_valid") else None}''',
        '''        reduced={}
        for name,res in agent_results.items():
            schema_valid=bool(res.get("schema_valid"))
            if schema_valid:
                reduced[name]={"status":"schema_valid","findings":res.get("data",{})}
            else:
                reduced[name]={"status":"schema_invalid","schema_errors":res.get("schema_errors",[]),
                               "json_error":res.get("json_error"),"findings":None}''',
        "exclude invalid raw specialist outputs",
    )
    citation_source = replace_once(
        citation_source,
        '''    def _run_specialists(self,query,sources,market,hmm,risk):
        tasks={
            "AI1_News_Analyst":lambda:agent1.run(self.llm,query,sources,market),
            "AI2_Macro_Analyst":lambda:agent2.run(self.llm,query,sources,market),
            "AI3_Quant_Regime_Analyst":lambda:agent3.run(self.llm,query,market,hmm),
            "AI4_Risk_Data_Auditor":lambda:agent4.run(self.llm,query,market,risk),
        }
        results={}
        if RUN_AGENTS_CONCURRENTLY:
            with ThreadPoolExecutor(max_workers=4) as pool:
                fs={pool.submit(fn):name for name,fn in tasks.items()}
                for future in as_completed(fs):
                    name=fs[future]
                    try: results[name]=future.result()
                    except Exception as e: results[name]={"agent":name,"status":"error","data":{"error":str(e)},"raw_text":"","json_valid":False,"metrics":{"error_type":type(e).__name__}}
        else:
            for name,fn in tasks.items():
                try: results[name]=fn()
                except Exception as e: results[name]={"agent":name,"status":"error","data":{"error":str(e)},"raw_text":"","json_valid":False,"metrics":{"error_type":type(e).__name__}}
        return results''',
        '''    def _run_specialists(self,query,sources,market,hmm,risk,telemetry_callback=None):
        tasks={
            "AI1_News_Analyst":lambda:agent1.run(self.llm,query,sources,market),
            "AI2_Macro_Analyst":lambda:agent2.run(self.llm,query,sources,market),
            "AI3_Quant_Regime_Analyst":lambda:agent3.run(self.llm,query,market,hmm),
            "AI4_Risk_Data_Auditor":lambda:agent4.run(self.llm,query,market,risk),
        }
        results={}
        def record(name,result):
            results[name]=result
            if telemetry_callback is not None:
                telemetry_callback(name,result)
        if RUN_AGENTS_CONCURRENTLY:
            with ThreadPoolExecutor(max_workers=4) as pool:
                fs={pool.submit(fn):name for name,fn in tasks.items()}
                for future in as_completed(fs):
                    name=fs[future]
                    try:
                        result=future.result()
                    except Exception as error:
                        result={"agent":name,"status":"error","data":{"error":str(error)},"raw_text":"",
                                "json_valid":False,"schema_valid":False,
                                "metrics":{"error_type":type(error).__name__,"api_success":False,
                                           "json_parse":False,"schema_valid":False,
                                           "traceback":traceback.format_exc()}}
                    record(name,result)
        else:
            for name,fn in tasks.items():
                try:
                    result=fn()
                except Exception as error:
                    result={"agent":name,"status":"error","data":{"error":str(error)},"raw_text":"",
                            "json_valid":False,"schema_valid":False,
                            "metrics":{"error_type":type(error).__name__,"api_success":False,
                                       "json_parse":False,"schema_valid":False,
                                       "traceback":traceback.format_exc()}}
                record(name,result)
        return results''',
        "capture specialist telemetry as calls complete",
    )
    citation_source = replace_once(
        citation_source,
        '''    def run(self,query):
        if not isinstance(query,str) or not query.strip(): raise ValueError("query must be non-empty")''',
        '''    def run(self,query,telemetry_callback=None):
        if not isinstance(query,str) or not query.strip(): raise ValueError("query must be non-empty")''',
        "allow immediate benchmark telemetry",
    )
    citation_source = replace_once(
        citation_source,
        '''        specialist_results=self._run_specialists(query,source_manifest,market,hmm,risk)''',
        '''        specialist_results=self._run_specialists(query,source_manifest,market,hmm,risk,telemetry_callback)''',
        "forward specialist telemetry callback",
    )
    citation_source = replace_once(
        citation_source,
        '''        final=agent5.run(self.llm,query,specialist_results,manifest,market,hmm,risk,prechecks)
        final_data=final.get("data",{})''',
        '''        ai5_started=time.perf_counter()
        try:
            final=agent5.run(self.llm,query,specialist_results,manifest,market,hmm,risk,prechecks)
        except Exception as error:
            final={"agent":"AI5_Lead_Researcher","status":"error","data":{},"raw_text":"",
                   "schema_valid":False,"metrics":{"error_type":type(error).__name__,
                   "api_success":False,"json_parse":False,"schema_valid":False,
                   "traceback":traceback.format_exc()}}
        if telemetry_callback is not None:
            telemetry_callback("AI5_Lead_Researcher",final)
        ai5_synthesis_ms=(time.perf_counter()-ai5_started)*1000
        citation_validation_started=time.perf_counter()
        final_data=final.get("data",{})''',
        "capture lead researcher telemetry and traceback",
    )
    citation_source = replace_once(
        citation_source,
        '''    paragraphs=[p.strip() for p in re.split(r"\\n+",str(text or "")) if len(p.strip())>=25]
    cited_paragraphs=sum(any(tok in p for tok in valid_unique) for p in paragraphs)
    return {"citation_count":len(found),"unique_citation_count":len(unique),"invalid_citation_ids":invalid,
            "all_citation_ids_valid":bool(found) and not invalid,"citation_paragraph_coverage":cited_paragraphs/len(paragraphs) if paragraphs else 0.0,
            "paragraphs_checked":len(paragraphs),"cited_paragraphs":cited_paragraphs}''',
        '''    paragraphs=[p.strip() for p in re.split(r"\\n+",str(text or "")) if len(p.strip())>=25]
    cited_paragraphs=sum(any(tok in p for tok in valid_unique) for p in paragraphs)
    return {"citation_count":len(found),"unique_citation_count":len(unique),"invalid_citation_ids":invalid,
            "all_citation_ids_valid":bool(found) and not invalid,
            "citation_id_valid_rate":len(valid_unique)/len(unique) if unique else "NO_CITATIONS",
            "report_has_citations":bool(found),
            "citation_id_valid_rate_when_present":len(valid_unique)/len(unique) if unique else "NO_CITATIONS",
            "citation_paragraph_coverage":cited_paragraphs/len(paragraphs) if paragraphs else "NO_PARAGRAPHS",
            "paragraphs_checked":len(paragraphs),"cited_paragraphs":cited_paragraphs}

def claim_evidence_audit(findings, allowed_ids):
    claims = findings if isinstance(findings, list) else []
    cited_claims = 0
    unsupported_claims = 0
    all_refs, valid_refs = [], []
    for finding in claims:
        if not isinstance(finding, dict):
            unsupported_claims += 1
            continue
        ids = finding.get("evidence_ids")
        ids = ids if isinstance(ids, list) else []
        valid = [str(identifier) for identifier in ids if str(identifier) in allowed_ids]
        all_refs.extend(str(identifier) for identifier in ids)
        valid_refs.extend(valid)
        if valid:
            cited_claims += 1
        else:
            unsupported_claims += 1
    return {
        "claim_count": len(claims),
        "claim_citation_coverage": cited_claims / len(claims) if claims else "NO_CLAIMS",
        "claim_citation_id_valid_rate": len(valid_refs) / len(all_refs) if all_refs else "NO_CITATIONS",
        "citation_support_rate": "NOT_HUMAN_REVIEWED",
        "unsupported_claim_rate": unsupported_claims / len(claims) if claims else "NO_CLAIMS",
        "unsupported_claim_count": unsupported_claims,
        "human_semantic_review_status": "REQUIRED",
    }

def render_evidence_report(final_data, allowed_ids):
    findings = final_data.get("evidence_based_findings", [])
    if not isinstance(findings, list):
        findings = []
    lines = ["## Evidence-based findings"]
    for finding in findings:
        if not isinstance(finding, dict) or not str(finding.get("claim") or "").strip():
            continue
        claim = str(finding["claim"]).strip()
        identifiers = finding.get("evidence_ids")
        identifiers = identifiers if isinstance(identifiers, list) else []
        valid = sorted({str(identifier) for identifier in identifiers if str(identifier) in allowed_ids},
                       key=lambda identifier: (identifier[0], int(identifier[1:])))
        invalid = sorted({str(identifier) for identifier in identifiers} - set(valid))
        if valid:
            lines.append("- " + claim + " " + " ".join(f"[{identifier}]" for identifier in valid))
        else:
            lines.append("- **Needs evidence review:** " + claim + " (no valid supporting source ID)")
        if invalid:
            lines.append("  - Rejected unknown source IDs: " + ", ".join(invalid))
    if len(lines) == 1:
        lines.append("No schema-valid evidence-based findings were produced.")
    return "\\n".join(lines), claim_evidence_audit(findings, allowed_ids)''',
        "claim-level citation audit and renderer",
    )
    old_prompt = '''        payload=f"USER QUESTION:\\n{query}\\n\\nEVIDENCE MANIFEST (valid IDs only):\\n{json.dumps(manifest,ensure_ascii=False,default=str)[:8000]}\\n\\nSPECIALIST OUTPUTS (untrusted drafts; validate them against evidence IDs and values):\\n{json.dumps(reduced,ensure_ascii=False,default=str)[:19000]}\\n\\nAS-OF DATES / DETERMINISTIC CHECKS:\\n{json.dumps(prechecks,ensure_ascii=False,default=str)}\\n\\nReturn JSON keys: status, final_report_markdown, executive_summary, evidence_based_findings (list of {{claim,evidence_ids}}), agent_agreement, agent_disagreements, risk_flags, confidence (low/medium/high), limitations, next_research_steps, abstention_reason. Write Thai. Every material claim should cite valid [S#], [Q#], [H#], or [R#] IDs from manifest. Do not invent claims, values, dates, citations, or causal statements. If specialist findings conflict, explain the conflict instead of choosing one without evidence. If evidence is insufficient, abstain on that conclusion."
        return call_agent_json(llm,self.name,self.role,payload,max_tokens=THAILLM_MAX_TOKENS_FINAL)'''
    new_prompt = '''        allowed_ids={source.get("citation_id") for source in manifest.get("rag_sources",[]) if source.get("citation_id")}
        for section in ("market_records","hmm_records","risk_records"):
            allowed_ids.update(record.get("evidence_id") for record in manifest.get(section,[]) if record.get("evidence_id"))
        payload=f"USER QUESTION:\\n{query}\\n\\nEVIDENCE MANIFEST (valid IDs only):\\n{json.dumps(manifest,ensure_ascii=False,default=str)[:8000]}\\n\\nSPECIALIST OUTPUTS (untrusted drafts; use schema-valid structured outputs only):\\n{json.dumps(reduced,ensure_ascii=False,default=str)[:19000]}\\n\\nAS-OF DATES / DETERMINISTIC CHECKS:\\n{json.dumps(prechecks,ensure_ascii=False,default=str)}\\n\\nReturn one JSON object with keys: status, executive_summary, evidence_based_findings (list of {{claim,claim_type,evidence_ids,confidence,limitations}}), agent_agreement, agent_disagreements, risk_flags, confidence (low/medium/high), limitations, next_research_steps, abstention_reason. Each finding must have claim_type fact/interpretation/hypothesis, confidence low/medium/high, and evidence_ids selected only from the manifest. Do not include an uncited factual summary or final markdown. A valid ID does not prove semantic support; uncertain claims must be marked for human review or omitted. Do not invent claims, values, dates, citations, or causal statements. If evidence is insufficient, state that explicitly."
        return call_agent_json(llm,self.name,self.role,payload,max_tokens=THAILLM_MAX_TOKENS_FINAL,allowed_ids=allowed_ids)'''
    citation_source = replace_once(citation_source, old_prompt, new_prompt, "structured lead researcher claim contract")
    citation_source = replace_once(
        citation_source,
        '''        final_data=final.get("data",{})
        final_text=final_data.get("final_report_markdown") or final_data.get("executive_summary") or final.get("raw_text") or "Final report unavailable."
        audit=citation_audit(final_text,allowed)
        # deterministic fallback if ThaiLLM final synthesis failed; retain specialist outputs without manufacturing conclusions.
        if final.get("status")!="success":
            sections=["## รายงานวิจัยเบื้องต้น (fallback; AI 5 ไม่สำเร็จ)","ระบบไม่สามารถสังเคราะห์ด้วย ThaiLLM ได้ในรอบนี้ จึงแสดงผลจาก specialist agents โดยไม่เติมข้อสรุปใหม่."]
            for name,res in specialist_results.items():
                sections.append(f"### {name}\\n"+(res.get("raw_text") or json.dumps(res.get("data",{}),ensure_ascii=False,default=str)))
            final_text="\\n\\n".join(sections); audit=citation_audit(final_text,allowed)''',
        '''        final_data=final.get("data",{})
        final_text,claim_audit_result=render_evidence_report(final_data,allowed)
        audit=citation_audit(final_text,allowed)
        audit.update(claim_audit_result)
        if final.get("status")!="success":
            final_text="## Evidence-based findings\\nAI5 did not produce a schema-valid claim set. No unsupported draft was promoted to the final report."
            audit=citation_audit(final_text,allowed)
            audit.update(claim_evidence_audit([],allowed))''',
        "validated deterministic report rendering",
    )
    citation_source = replace_once(
        citation_source,
        '''        market=build_market_snapshot(query,df_features)
        hmm=run_hmm_snapshot(query,df_features,HMM_PATH)
        risk=risk_snapshot_global''',
        '''        quant_started=time.perf_counter()
        market=build_market_snapshot(query,df_features)
        quant_snapshot_ms=(time.perf_counter()-quant_started)*1000
        hmm_started=time.perf_counter()
        hmm=run_hmm_snapshot(query,df_features,HMM_PATH)
        hmm_inference_ms=(time.perf_counter()-hmm_started)*1000
        risk=risk_snapshot_global
        risk_snapshot_ms=0.0
        risk_snapshot_precomputed=True''',
        "deterministic stage timings",
    )
    citation_source = replace_once(
        citation_source,
        '''        agent_rows.append({"agent":name,"status":res.get("status"),"json_valid":res.get("json_valid"),"latency_ms":mm.get("latency_ms"),
                "prompt_tokens":mm.get("prompt_tokens"),"completion_tokens":mm.get("completion_tokens"),"total_tokens":mm.get("total_tokens"),
                "error_type":mm.get("error_type") or res.get("data",{}).get("error_type")})''',
        '''        agent_rows.append({"agent":name,"status":res.get("status"),"api_success":mm.get("api_success",False),
                "json_parse":mm.get("json_parse",False),"schema_valid":mm.get("schema_valid",False),
                "task_success":mm.get("task_success"),"task_validation_status":mm.get("task_validation_status"),
                "repair_attempts":mm.get("repair_attempts",0),"finish_reason":mm.get("finish_reason"),
                "attempt_count":mm.get("attempt_count",mm.get("attempts",0)),
                "latency_ms":mm.get("latency_ms"),"prompt_tokens":mm.get("prompt_tokens"),
                "completion_tokens":mm.get("completion_tokens"),"total_tokens":mm.get("total_tokens"),
                "initial_tokens":mm.get("initial_tokens"),"repair_tokens":mm.get("repair_tokens"),
                "schema_errors":json.dumps(res.get("schema_errors",[]),ensure_ascii=False),
                "error_type":mm.get("error_type") or res.get("data",{}).get("error_type")})''',
        "layered agent metrics",
    )
    citation_source = replace_once(
        citation_source,
        '''            "agent_count":len(agent_rows),"agents_success":int((agent_df["status"]=="success").sum()),"agent_success_rate":float((agent_df["status"]=="success").mean()),
            "agent_json_valid_rate":float(pd.to_numeric(agent_df["json_valid"],errors="coerce").fillna(False).mean()),
            "total_tokens":float(token_total) if pd.notna(token_total) else None,"mean_agent_latency_ms":float(pd.to_numeric(agent_df["latency_ms"],errors="coerce").mean()),''',
        '''            "agent_count":len(agent_rows),
            "api_success_rate":float(agent_df["api_success"].mean()) if len(agent_df) else "NO_AGENT_CALLS",
            "json_parse_rate":float(agent_df["json_parse"].mean()) if len(agent_df) else "NO_AGENT_CALLS",
            "schema_valid_rate":float(agent_df["schema_valid"].mean()) if len(agent_df) else "NO_AGENT_CALLS",
            "task_success_rate":"NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE",
            "quant_snapshot_ms":quant_snapshot_ms,"hmm_inference_ms":hmm_inference_ms,
            "risk_snapshot_ms":risk_snapshot_ms,"risk_snapshot_precomputed":risk_snapshot_precomputed,
            "ai5_synthesis_ms":ai5_synthesis_ms,
            "citation_validation_ms":(time.perf_counter()-citation_validation_started)*1000,
            "total_tokens":float(token_total) if pd.notna(token_total) else "NOT_REPORTED",
            "mean_agent_latency_ms":float(pd.to_numeric(agent_df["latency_ms"],errors="coerce").mean()),''',
        "non-conflated run metrics",
    )
    set_source(by_id["5cce7a2e"], citation_source)

    gt_title_index = next(index for index, cell in enumerate(cells) if cell.get("id") == "4284e50e")
    audit_cell = {
        "cell_type": "code",
        "execution_count": None,
        "id": "gaib_coverage_audit_v1",
        "metadata": {},
        "outputs": [],
        "source": AUDIT_CELL.splitlines(keepends=True),
    }
    cells.insert(gt_title_index + 1, audit_cell)

    retrieval_cell = by_id["a3a65109"]
    retrieval_source = source(retrieval_cell)
    retrieval_start = retrieval_source.index("def write_latency_percentiles(")
    retrieval_end = retrieval_source.index("##__RETRIEVAL_CELL_END__", retrieval_start) if "##__RETRIEVAL_CELL_END__" in retrieval_source else -1
    if retrieval_end >= 0:
        raise ValueError("Unexpected retrieval cell marker.")
    run_start = retrieval_source.index("def run_retrieval_benchmark(")
    run_end = retrieval_source.index("retrieval_benchmark_df=pd.DataFrame()", run_start)
    # Keep the existing identity/metric helpers and replace only the benchmark runner.
    retrieval_source = retrieval_source[:run_start] + RELIABILITY_METRICS_CELL + "\n"
    set_source(retrieval_cell, retrieval_source)

    benchmark_source = source(by_id["6059c30d"])
    benchmark_source = replace_once(
        benchmark_source,
        '''    selected=ground_truth[:limit] if limit else ground_truth''',
        '''    selected=(
        [row for row in ground_truth if str(row.get("query_id")) in set(BENCHMARK_QUERY_IDS)]
        if BENCHMARK_QUERY_IDS else (ground_truth[:limit] if limit else ground_truth)
    )''',
        "support targeted failed-query reruns",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''    for i,gt in enumerate(selected,1):
        q=str(gt.get("query") or "").strip()
        if not q: continue
        try:''',
        '''    coverage_by_query={row["query_id"]:row for row in ground_truth_audit_df.to_dict("records")}
    for i,gt in enumerate(selected,1):
        q=str(gt.get("query") or "").strip()
        if not q: continue
        audit_row=coverage_by_query.get(gt.get("query_id"),{})
        coverage_status=audit_row.get("coverage_status","NOT_AUDITED")
        if coverage_status!="COVERED":
            error_rows.append({"query_id":gt.get("query_id"),"query":q,"stage":"coverage_audit","error_type":coverage_status,
                               "error":audit_row.get("block_reason") or "Ground Truth index coverage was not verified."})
            continue
        try:''',
        "block unverified end-to-end cases",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''        q=str(gt.get("query") or "").strip()
        if not q: continue
        audit_row=coverage_by_query.get(gt.get("query_id"),{})''',
        '''        q=str(gt.get("query") or "").strip()
        if not q:
            error_rows.append({"query_id":gt.get("query_id"),"query":q,"stage":"input_validation",
                               "error_type":"empty_query","error":"Ground Truth query is empty."})
            continue
        audit_row=coverage_by_query.get(gt.get("query_id"),{})''',
        "record empty benchmark queries",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''        try:
            res=assistant.run(q)
            m=res["metrics"]''',
        '''        try:
            def record_agent_telemetry(agent_name,agent_result):
                mm=agent_result.get("metrics",{}) or {}
                record={"query_id":gt.get("query_id"),"agent":agent_name,"status":agent_result.get("status"),
                        "api_success":mm.get("api_success",False),"json_parse":mm.get("json_parse",False),
                        "schema_valid":mm.get("schema_valid",False),"task_success":mm.get("task_success"),
                        "task_validation_status":mm.get("task_validation_status"),
                        "schema_errors":json.dumps(agent_result.get("schema_errors",[]),ensure_ascii=False),
                        "repair_attempts":mm.get("repair_attempts",0),"attempt_count":mm.get("attempt_count",mm.get("attempts",0)),
                        "finish_reason":mm.get("finish_reason"),"latency_ms":mm.get("latency_ms"),
                        "prompt_tokens":mm.get("prompt_tokens"),"completion_tokens":mm.get("completion_tokens"),
                        "total_tokens":mm.get("total_tokens"),"initial_tokens":mm.get("initial_tokens"),
                        "repair_tokens":mm.get("repair_tokens"),"error_type":mm.get("error_type"),
                        "error":agent_result.get("json_error") or agent_result.get("data",{}).get("error"),
                        "traceback":mm.get("traceback","")}
                with agent_rows_lock:
                    agent_rows.append(record)
                    pd.DataFrame(agent_rows).to_csv(
                        OUTPUT_DIR/"agent_quality_and_latency_checkpoint.csv",index=False,encoding="utf-8-sig"
                    )
            res=assistant.run(q,telemetry_callback=record_agent_telemetry)
            m=res["metrics"]''',
        "persist per-agent telemetry before query completion",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''    run_rows=[]; agent_rows=[]; review_rows=[]; error_rows=[]
    coverage_by_query=''',
        '''    run_rows=[]; agent_rows=[]; review_rows=[]; error_rows=[]
    agent_rows_lock=threading.Lock()
    coverage_by_query=''',
        "synchronize telemetry checkpoints",
    )
    run_row_start = benchmark_source.index('"status":"success" if m.get("agents_success",0)==5')
    run_row_end = benchmark_source.index('}\n            run_rows.append(one)', run_row_start) + 1
    benchmark_source = (
        benchmark_source[:run_row_start]
        + '''"execution_status":"schema_valid" if m.get("schema_valid_rate")==1.0 else "partial_schema_failure","retrieval_backend":m.get("retrieval_backend"),
                 "source_count":m.get("source_count"),"total_wall_ms":m.get("total_wall_ms"),
                 "embedding_ms":m.get("embedding_ms"),"qdrant_ms":m.get("qdrant_ms"),
                 "dense_wall_ms":m.get("dense_wall_ms"),"bm25_wall_ms":m.get("bm25_wall_ms"),
                 "retrieval_wall_ms":m.get("retrieval_wall_ms"),"rerank_ms":m.get("rerank_ms"),
                 "quant_snapshot_ms":m.get("quant_snapshot_ms"),"hmm_inference_ms":m.get("hmm_inference_ms"),
                 "risk_snapshot_ms":m.get("risk_snapshot_ms"),"ai5_synthesis_ms":m.get("ai5_synthesis_ms"),
                 "citation_validation_ms":m.get("citation_validation_ms"),
                 "api_success_rate":m.get("api_success_rate"),"json_parse_rate":m.get("json_parse_rate"),
                 "schema_valid_rate":m.get("schema_valid_rate"),"task_success_rate":m.get("task_success_rate"),
                 "total_tokens":m.get("total_tokens"),"citation_count":m.get("citation_audit",{}).get("citation_count"),
                 "report_has_citations":m.get("citation_audit",{}).get("report_has_citations",False),
                 "all_citation_ids_valid":m.get("citation_audit",{}).get("all_citation_ids_valid"),
                 "citation_id_valid_rate":m.get("citation_audit",{}).get("citation_id_valid_rate"),
                 "citation_id_valid_rate_when_present":m.get("citation_audit",{}).get("citation_id_valid_rate_when_present"),
                 "claim_citation_coverage":m.get("citation_audit",{}).get("claim_citation_coverage"),
                 "citation_support_rate":m.get("citation_audit",{}).get("citation_support_rate"),
                 "citation_paragraph_coverage":m.get("citation_audit",{}).get("citation_paragraph_coverage"),
                 "unsupported_claim_rate":m.get("citation_audit",{}).get("unsupported_claim_rate"),
                 "human_semantic_review_status":m.get("citation_audit",{}).get("human_semantic_review_status"),
                 "hmm_status":m.get("hmm_status"),"market_as_of":m.get("market_as_of"),
                 "run_id":GAIB_RUN_ID,"final_report":res.get("final_text","")}'''
        + benchmark_source[run_row_end:]
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''                 "qdrant_index_coverage_verified":gt.get("qdrant_index_coverage_verified",False),
                 "execution_status"''',
        '''                 "ground_truth_qdrant_index_coverage_verified":gt.get("qdrant_index_coverage_verified",False),
                 "runtime_qdrant_index_coverage_verified":audit_row.get("runtime_qdrant_index_coverage_verified",False),
                 "coverage_status":coverage_status,"evaluation_eligible":coverage_status=="COVERED",
                 "execution_status"''',
        "record verified coverage state",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''            for _,row in res["agent_metrics"].iterrows(): agent_rows.append({"query_id":gt.get("query_id"),**row.to_dict()})''',
        "",
        "avoid duplicate per-agent telemetry",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''        except Exception as e:
            error_rows.append({"query_id":gt.get("query_id"),"query":q,"error_type":type(e).__name__,"error":str(e)[:800]})
            print(f"[{i}/{len(selected)}] failed {gt.get('query_id')}: {type(e).__name__}")''',
        '''        except Exception as e:
            error_rows.append({"query_id":gt.get("query_id"),"query":q,"stage":"assistant.run_or_metrics",
                               "error_type":type(e).__name__,"error":str(e),"traceback":traceback.format_exc()})
            print(f"[{i}/{len(selected)}] failed {gt.get('query_id')}: {type(e).__name__}: {e}")
            print(traceback.format_exc())''',
        "retain detailed query failure diagnostics",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''                                "review_status":gt.get("review_status"),"expected_fact_coverage":"","human_correctness":"",
                                "citation_supported":"","citation_support_rate":"","reviewer_notes":""})''',
        '''                                "review_status":gt.get("review_status"),"expected_fact_coverage":"","human_correctness":"",
                                "citation_supported":"","citation_support_rate":"NOT_HUMAN_REVIEWED",
                                "citation_id_valid_rate":m.get("citation_audit",{}).get("citation_id_valid_rate"),
                                "claim_citation_coverage":m.get("citation_audit",{}).get("claim_citation_coverage"),
                                "unsupported_claim_rate":m.get("citation_audit",{}).get("unsupported_claim_rate"),
                                "reviewer_notes":""})''',
        "human review evidence metrics",
    )
    benchmark_source = benchmark_source.replace(
        '''print(f"[{i}/{len(selected)}] {gt.get('query_id')} | total_ms={m.get('total_wall_ms',np.nan):.0f} | agents={m.get('agents_success')}/5")''',
        '''print(f"[{i}/{len(selected)}] {gt.get('query_id')} | total_ms={m.get('total_wall_ms',0):.0f} | schema_valid={m.get('schema_valid_rate')}")''',
        1,
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''            pd.DataFrame(run_rows).to_csv(OUTPUT_DIR/"multiagent_benchmark_results_checkpoint.csv",index=False,encoding="utf-8-sig")
''',
        "",
        "remove duplicate checkpoint output",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''    write_latency_percentiles(run_df,"total_wall_ms",OUTPUT_DIR/"multiagent_latency_percentiles.csv")
    for metric in [column for column in agents_df.columns if "ms" in str(column).lower()]:
        write_latency_percentiles(agents_df,metric,OUTPUT_DIR/f"agent_{metric}_percentiles.csv",group_by="agent")''',
        '''    write_latency_percentiles(run_df,"total_wall_ms",OUTPUT_DIR/"multiagent_latency_percentiles.csv")
    for metric in [column for column in agents_df.columns if "ms" in str(column).lower()]:
        write_latency_percentiles(agents_df,metric,OUTPUT_DIR/f"agent_{metric}_percentiles.csv",group_by="agent")
    agents_df.to_csv(OUTPUT_DIR/"agent_quality_and_latency.csv",index=False,encoding="utf-8-sig")''',
        "save per-agent validity and timing",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''    display(multiagent_benchmark_df.head())''',
        '''    display(multiagent_benchmark_df.head())
    if not multiagent_errors_df.empty:
        display(multiagent_errors_df[["query_id","error_type","error"]])''',
        "display detailed query failures",
    )
    benchmark_source = replace_once(
        benchmark_source,
        '''    errors_df.to_csv(OUTPUT_DIR/"multiagent_benchmark_errors.csv",index=False,encoding="utf-8-sig")
    return run_df,agents_df,review_df,errors_df''',
        '''    errors_df.to_csv(OUTPUT_DIR/"multiagent_benchmark_errors.csv",index=False,encoding="utf-8-sig")
    attempted_count=len(run_df)+len(errors_df)
    completion_summary=pd.DataFrame([{
        "attempted_queries":attempted_count,
        "completed_queries":len(run_df),
        "failed_or_blocked_queries":len(errors_df),
        "completion_rate":len(run_df)/attempted_count if attempted_count else "NO_QUERIES",
        "fully_schema_valid_queries":int((run_df.get("schema_valid_rate",pd.Series(dtype=float))==1.0).sum()),
        "schema_complete_rate":float((run_df.get("schema_valid_rate",pd.Series(dtype=float))==1.0).mean()) if not run_df.empty else "NO_COMPLETED_QUERIES",
    }])
    completion_summary.to_csv(OUTPUT_DIR/"multiagent_benchmark_summary.csv",index=False,encoding="utf-8-sig")
    baseline_path=BASELINE_RUN_DIR/"multiagent_benchmark_results.csv"
    if baseline_path.is_file() and not run_df.empty:
        baseline=pd.read_csv(baseline_path)
        comparison=baseline.merge(run_df,on="query_id",how="outer",suffixes=("_baseline","_experiment"))
        comparison["comparison_note"]="Historical baseline; API/service conditions may differ and metrics are not causal."
        comparison.to_csv(OUTPUT_DIR/"baseline_comparison_multiagent.csv",index=False,encoding="utf-8-sig")
    return run_df,agents_df,review_df,errors_df''',
        "write diagnostic multi-agent baseline comparison",
    )
    set_source(by_id["6059c30d"], benchmark_source)

    summary_source = source(by_id["93fae555"])
    summary_source = summary_source.replace(
        '''    summary_rows.append({"scope":"single_live_run","queries":1,"agent_success_rate":m.get("agent_success_rate"),
        "json_valid_rate":m.get("agent_json_valid_rate"),"total_latency_ms":m.get("total_wall_ms"),"tokens":m.get("total_tokens"),
        "valid_citations":m.get("citation_audit",{}).get("all_citation_ids_valid"),
        "citation_paragraph_coverage":m.get("citation_audit",{}).get("citation_paragraph_coverage")})''',
        '''    summary_rows.append({"scope":"single_live_run","queries":1,"api_success_rate":m.get("api_success_rate"),
        "json_parse_rate":m.get("json_parse_rate"),"schema_valid_rate":m.get("schema_valid_rate"),
        "task_success_rate":m.get("task_success_rate"),"total_latency_ms":m.get("total_wall_ms"),"tokens":m.get("total_tokens"),
        "report_has_citations":m.get("citation_audit",{}).get("report_has_citations",False),
        "citation_id_valid_rate_when_present":m.get("citation_audit",{}).get("citation_id_valid_rate_when_present"),
        "claim_citation_coverage":m.get("citation_audit",{}).get("claim_citation_coverage"),
        "citation_paragraph_coverage":m.get("citation_audit",{}).get("citation_paragraph_coverage"),
        "citation_support_rate":m.get("citation_audit",{}).get("citation_support_rate")})''',
        1,
    )
    summary_source = summary_source.replace(
        '''    summary_rows.append({"scope":"multiagent_benchmark","queries":len(multiagent_benchmark_df),
        "agent_success_rate":pd.to_numeric(multiagent_benchmark_df.get("agent_success_rate"),errors="coerce").mean(),''',
        '''    attempted_queries=len(multiagent_benchmark_df)+len(multiagent_errors_df)
    summary_rows.append({"scope":"multiagent_benchmark","queries":len(multiagent_benchmark_df),
        "attempted_queries":attempted_queries,
        "completion_rate":len(multiagent_benchmark_df)/attempted_queries if attempted_queries else "NO_QUERIES",
        "api_success_rate":pd.to_numeric(multiagent_benchmark_df.get("api_success_rate"),errors="coerce").mean(),
        "json_parse_rate":pd.to_numeric(multiagent_benchmark_df.get("json_parse_rate"),errors="coerce").mean(),
        "schema_valid_rate":pd.to_numeric(multiagent_benchmark_df.get("schema_valid_rate"),errors="coerce").mean(),
        "task_success_rate":"NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE",''',
        1,
    )
    summary_source = summary_source.replace(
        '''                summary_rows.append({"scope":f"retrieval_{prefix}{metric}","queries":int(retrieval_benchmark_df[col].notna().sum()),"mean":retrieval_benchmark_df[col].mean(),"median":retrieval_benchmark_df[col].median()})''',
        '''                values=pd.to_numeric(retrieval_benchmark_df[col],errors="coerce")
                summary_rows.append({"scope":f"retrieval_{prefix}{metric}","queries":int(values.notna().sum()),
                    "coverage_eligible_queries":int(retrieval_benchmark_df["evaluation_eligible"].sum()),
                    "mean":values.mean() if values.notna().any() else "NOT_EVALUATED",
                    "median":values.median() if values.notna().any() else "NOT_EVALUATED"})''',
        1,
    )
    summary_source = summary_source.replace(
        '''        "valid_citation_run_rate":pd.to_numeric(multiagent_benchmark_df.get("valid_citations"),errors="coerce").fillna(0).mean(),
        "mean_citation_paragraph_coverage":pd.to_numeric(multiagent_benchmark_df.get("citation_paragraph_coverage"),errors="coerce").mean()})''',
        '''        "report_has_citations_rate":float(multiagent_benchmark_df["report_has_citations"].fillna(False).astype(bool).mean()),
        "citation_id_valid_rate_when_present":pd.to_numeric(
            multiagent_benchmark_df.loc[multiagent_benchmark_df["report_has_citations"].fillna(False).astype(bool),
                                        "citation_id_valid_rate_when_present"],errors="coerce").mean(),
        "mean_claim_citation_coverage":pd.to_numeric(multiagent_benchmark_df.get("claim_citation_coverage"),errors="coerce").mean(),
        "mean_citation_paragraph_coverage":pd.to_numeric(multiagent_benchmark_df.get("citation_paragraph_coverage"),errors="coerce").mean(),
        "citation_support_rate":"NOT_HUMAN_REVIEWED"})''',
        1,
    )
    set_source(by_id["93fae555"], summary_source)

    # Add a new experiment heading and change the last summary to describe the two-phase scope.
    for cell in cells:
        if cell.get("cell_type") == "markdown" and cell.get("id") == "518212c2":
            set_source(cell, source(cell) + (
                "\n\n## Experiment controls and interpretation\n"
                "- This is a Phase 1–2 reliability experiment; it does not change A2 retrieval parameters or model settings.\n"
                "- Ground Truth index coverage must be `COVERED` before a query is treated as retrieval-ready; failed audits are retained with explicit block reasons.\n"
                "- Coverage is checked for every expected document group, and Ground Truth's prior coverage flag is kept separate from runtime Qdrant verification.\n"
                "- `citation_support_rate` is not automatically inferred from valid IDs. It remains `NOT_HUMAN_REVIEWED` until claim-source alignment is reviewed.\n"
                "- Citation presence, ID validity when present, claim coverage, and paragraph coverage are reported as separate measures.\n"
                "- Agent telemetry is checkpointed after each result; failed queries include exception type, message, and traceback.\n"
                "- Task correctness is `NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE` unless a deterministic or human-reviewed oracle exists.\n"
                "- The selected development sample and small-n latency summaries are provisional. The held-out test split remains gated.\n"
                "- Historical results are read-only and are not overwritten. New per-query output is stored in the experiment-specific run directory.\n"
            ))
            break

    # Ensure no output from any earlier baseline run is copied into the new artifact.
    for cell in cells:
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            cell["outputs"] = []

    notebook["metadata"].setdefault("kernelspec", {
        "display_name": "Python 3", "language": "python", "name": "python3"
    })
    OUTPUT_NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Created {OUTPUT_NOTEBOOK}")


if __name__ == "__main__":
    main()
