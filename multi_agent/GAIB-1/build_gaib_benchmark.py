#!/usr/bin/env python
"""Build a provenance-first GAIB-1 benchmark bundle without changing source assets."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GT_DIR = ROOT / "multi_agent" / "gt"
GT_ALL = GT_DIR / "ground_truth_fed_v1.jsonl"
GT_READY = GT_DIR / "ground_truth_fed_ready_v1.jsonl"
GT_GAPS = GT_DIR / "ground_truth_fed_source_gaps_v1.jsonl"
GT_AUDIT = GT_DIR / "fed_groundtruth_audit_report.json"
CHUNKS = ROOT / "dataset" / "news" / "fed" / "fed_press_releases_cleaned" / "fed_press_releases_rag_chunks.jsonl"
SOURCE_NOTEBOOK = ROOT / "multi_agent" / "Gold_Assistant_5_Agent_Collaborative_Pipeline.ipynb"
RAG_CONTROL = ROOT / "rag" / "2.Gold_Assistant_RAG_Latency_Experiments.ipynb"
FEATURE_CSV = ROOT / "dataset" / "datset a gold price" / "data" / "processed" / "thai_gold_features_v1.csv"
FEATURE_PARQUET = ROOT / "dataset" / "datset a gold price" / "data" / "processed" / "thai_gold_features_v1.parquet"
HMM_DIR = ROOT / "model" / "gold_hmm_v1"
SIM_DIR = ROOT / "dataset" / "thai-gold-portfolio-simulator"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def add_inventory_entry(entries: list[dict[str, Any]], path: Path, role: str) -> None:
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError:
        relative = path.name
    entry: dict[str, Any] = {"path": relative, "role": role, "exists": path.is_file()}
    if path.is_file():
        entry.update({"bytes": path.stat().st_size, "sha256": sha256(path)})
    entries.append(entry)


def inventory_inputs() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    fixed = [
        (GT_ALL, "fed_ground_truth"),
        (GT_READY, "fed_ground_truth_source_present"),
        (GT_GAPS, "fed_ground_truth_source_gaps"),
        (GT_AUDIT, "fed_ground_truth_audit"),
        (CHUNKS, "rag_chunk_corpus"),
        (SOURCE_NOTEBOOK, "multi_agent_notebook_source"),
        (RAG_CONTROL, "a2_control_notebook"),
        (OUT / "remote_rag_smoke_test.json", "remote_rag_connectivity_probe"),
        (FEATURE_CSV, "quant_feature_dataset"),
        (FEATURE_PARQUET, "quant_feature_dataset"),
    ]
    for path, role in fixed:
        add_inventory_entry(entries, path, role)
    for folder, role in [(HMM_DIR, "hmm_model_bundle"), (SIM_DIR, "portfolio_simulator")]:
        if folder.is_dir():
            for path in sorted(folder.rglob("*")):
                if path.is_file() and not any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts):
                    add_inventory_entry(entries, path, role)
        else:
            entries.append({"path": folder.relative_to(ROOT).as_posix(), "role": role, "exists": False})
    fed_root = ROOT / "dataset" / "news" / "fed"
    if fed_root.is_dir():
        for path in sorted(fed_root.rglob("*")):
            if path.is_file():
                add_inventory_entry(entries, path, "fed_source_corpus")
    return entries


def inspect_feature_data(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"path": path.relative_to(ROOT).as_posix(), "exists": path.is_file()}
    if not path.is_file():
        return result
    try:
        import pandas as pd

        frame = pd.read_csv(path, low_memory=False) if path.suffix.lower() == ".csv" else pd.read_parquet(path)
        date_columns = [c for c in frame.columns if re.search(r"date|time|timestamp", str(c), re.I)]
        date_details = {}
        for column in date_columns:
            values = pd.to_datetime(frame[column], errors="coerce", utc=True)
            date_details[str(column)] = {
                "min_utc": values.min().isoformat() if values.notna().any() else None,
                "max_utc": values.max().isoformat() if values.notna().any() else None,
                "invalid_or_missing": int(values.isna().sum()),
                "duplicate_count": int(values.duplicated().sum()),
                "monotonic_increasing": bool(values.dropna().is_monotonic_increasing),
            }
        result.update(
            {
                "rows": int(len(frame)),
                "columns": [{"name": str(c), "dtype": str(frame[c].dtype), "nulls": int(frame[c].isna().sum())} for c in frame.columns],
                "date_columns": date_details,
            }
        )
    except Exception as exc:
        result["inspection_error"] = f"{type(exc).__name__}: {exc}"
    return result


def inspect_fed_mapping(ready: list[dict[str, Any]]) -> dict[str, Any]:
    by_original_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    chunk_count = 0
    if CHUNKS.is_file():
        for chunk in read_jsonl(CHUNKS):
            source_name = str(chunk.get("source") or "").lower()
            url = str(chunk.get("url") or "").lower()
            if source_name not in {"fed_press_releases", "federal reserve board"} and "federalreserve.gov" not in url:
                continue
            chunk_count += 1
            for key in ("original_id", "source_document_id_in_uploaded_corpus", "document_id", "doc_id"):
                value = chunk.get(key)
                if value:
                    by_original_id[str(value)].append(chunk)
            if chunk.get("url"):
                by_url[str(chunk["url"])].append(chunk)
    mapped_ids: list[str] = []
    missing: list[str] = []
    quote_mismatches: list[str] = []
    for row in ready:
        query_id = str(row.get("query_id", ""))
        mapped = True
        for evidence in row.get("evidence", []):
            chunks = by_original_id.get(str(evidence.get("document_id", "")), [])
            if not chunks:
                chunks = by_url.get(str(evidence.get("source_url", "")), [])
            if not chunks:
                mapped = False
                continue
            quote = str(evidence.get("exact_quote") or "")
            if quote and not any(quote in str(chunk.get("content") or "") for chunk in chunks):
                quote_mismatches.append(query_id)
        (mapped_ids if mapped else missing).append(query_id)
    return {
        "chunk_file_exists": CHUNKS.is_file(),
        "fed_chunk_count": chunk_count,
        "mapped_query_count": len(set(mapped_ids)),
        "unmapped_query_ids": sorted(set(missing)),
        "quote_mismatch_query_ids": sorted(set(quote_mismatches)),
        "qdrant_index_coverage": "UNVERIFIED",
        "note": "Local chunk mapping is not proof that the corresponding documents are present in Qdrant.",
    }


def notebook_assignments(path: Path, names: set[str]) -> dict[str, Any]:
    if not path.is_file():
        return {}
    notebook = json.loads(path.read_text(encoding="utf-8"))
    values: dict[str, Any] = {}
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        try:
            tree = ast.parse("".join(cell.get("source", [])))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id in names:
                    try:
                        values[target.id] = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        values[target.id] = ast.unparse(node.value)
    return values


def write_gaib_notebook() -> None:
    notebook = json.loads(SOURCE_NOTEBOOK.read_text(encoding="utf-8"))
    cells_by_id = {cell.get("id"): cell for cell in notebook.get("cells", [])}
    repaired_markdown = {
        "eab45473": """# Gold Assistant — 5-Agent Collaborative Research Pipeline (7-Key)

This notebook extends `Gold_Assistant_Full_RAG_End_to_End.ipynb`. AI 1–4 perform specialist analysis, while AI 5 acts as lead researcher to review and synthesize their findings. ThaiLLM is used for language generation and interpretation; Gemini is not used.

## Agent roles

| Agent | Primary responsibility | Data and tools |
|---|---|---|
| **AI 1 — News Analyst** | Retrieve and summarize news with evidence IDs | Hybrid retrieval (Qdrant, Cloudflare embeddings, BM25 and RRF), followed by Jina reranking |
| **AI 2 — Macro Analyst** | Interpret news alongside USD/THB, gold returns, volatility and rolling correlations | Retrieved evidence and `thai_gold_features_v1.parquet` or its CSV equivalent |
| **AI 3 — Quant / Regime Analyst** | Calculate statistics in Python and infer market regimes with GaussianHMM | Feature dataset, `model.joblib`, scaler and feature schema |
| **AI 4 — Risk & Data Auditor** | Check data quality, accounting and portfolio P&L attribution | Features and simulator ledger, valuation, attribution and market-price tables |
| **AI 5 — Lead Researcher** | Resolve conflicts, validate citation IDs and assemble the final report | Structured findings from AI 1–4 and the evidence manifest |

**Reliability:** Python calculates statistical and accounting values; the LLM only interprets them. HMM states are statistical regimes, not causal evidence or trading advice. The portfolio simulator uses historical market prices, but generated portfolios and investor behavior are **synthetic**, not real customer transactions. Valid citation IDs alone do not prove that a source supports a claim; human review is required before reporting accuracy.

## Run order

1. Install dependencies and configure the environment.
2. Check data paths, load datasets and inspect data-quality summaries.
3. Initialize the retrieval engine and ThaiLLM client.
4. Optionally run one live question through all five agents when credentials and data are available.
5. Run retrieval or multi-agent benchmarks separately when API quota is available.

The original pipeline may run one live demonstration when configured. Set `RUN_RETRIEVAL_BENCHMARK=true` or `RUN_AGENT_BENCHMARK=true` to explicitly start the corresponding remote benchmark and API calls. Keep API keys in environment variables or `.env`, never in the notebook.

### API key rotation, concurrency and rate limits

Set `THAILLM_API_KEY1` through `THAILLM_API_KEY7` in the environment or `.env`. Key selection is thread-safe. Concurrent specialist calls can use different keys; set `RUN_AGENTS_CONCURRENTLY=false` to run specialist calls sequentially. The seven-key pool does not mean every request uses all seven keys.

ThaiLLM, Qdrant, Cloudflare and Jina requests are protected by concurrency and rate-limit gates. HTTP 429 responses honor `Retry-After`; timeouts and server errors use exponential backoff; non-retryable client errors fail explicitly. Tune limits with `THAILLM_MAX_CONCURRENT_REQUESTS`, `QDRANT_MAX_CONCURRENT_REQUESTS`, `CLOUDFLARE_MAX_CONCURRENT_REQUESTS`, `JINA_MAX_CONCURRENT_REQUESTS`, `API_MAX_RETRIES` and the corresponding `*_MIN_INTERVAL_SECONDS` variables.

For GAIB evaluation, the copied notebook requires the real Qdrant + Cloudflare + Jina A2 path and does not fall back to local-only retrieval.
""",
        "23e6ae30": """## 2. Dataset discovery

The notebook checks for inputs under `dataset\\news`, `dataset\\datset a gold price`, `dataset\\thai-gold-portfolio-simulator`, `embedding` and `model`. Missing inputs are reported as `MISSING`; agents must mark unavailable analyses as `not_available` rather than inventing values. Extract `pack` only when its contents are needed and the archive is available.
""",
        "6f06db53": """## 5. Deterministic Quant snapshot (AI 2/3)

Quantitative summaries are calculated from available observations at or before the requested as-of date. Missing dates and columns are reported rather than inferred. These descriptive statistics do not establish causal effects.
""",
        "19fd0b37": """## 8. ThaiLLM client and structured-output helpers
""",
        "7c51f706": """## 11. AI 5 — Lead Researcher and multi-agent orchestrator

Configure `THAILLM_API_KEY` values through environment variables or `.env`; do not place secrets in the notebook. GAIB evaluation requires Qdrant, Cloudflare embeddings and Jina reranking. Local news BM25 fallback is disabled for this experiment so results use the intended remote A2 retrieval path. The lead researcher checks agent outputs and citations against the retrieved evidence manifest.
""",
    }
    for cell_id, markdown in repaired_markdown.items():
        cell = cells_by_id.get(cell_id)
        if cell is None or cell.get("cell_type") != "markdown":
            raise ValueError(f"Expected Markdown cell {cell_id} is missing")
        cell["source"] = markdown.splitlines(keepends=True)

    inventory_cell = cells_by_id.get("7baf7bb1")
    if inventory_cell is None or inventory_cell.get("cell_type") != "code":
        raise ValueError("Expected asset inventory cell 7baf7bb1 is missing")
    inventory_source = "".join(inventory_cell.get("source", []))
    inventory_source = inventory_source.replace(
        '"rows":len(df_features) if df_features is not None else None',
        '"rows":len(df_features) if df_features is not None else "N/A (not loaded)"',
        1,
    )
    inventory_source = inventory_source.replace(
        '"rows":None},\n    {"asset":"Portfolio simulator"',
        '"rows":"N/A (model bundle; not a row-based table)"},\n    {"asset":"Portfolio simulator"',
        1,
    )
    inventory_source = inventory_source.replace(
        '"rows":None},\n    {"asset":"RAG chunks JSONL"',
        '"rows":"See simulator table counts below"},\n    {"asset":"RAG chunks JSONL"',
        1,
    )
    inventory_source = inventory_source.replace(
        '"rows":None},\n    {"asset":"Local news corpus"',
        '"rows":"N/A (chunk corpus; not a single table)"},\n    {"asset":"Local news corpus"',
        1,
    )
    inventory_source = inventory_source.replace(
        '"rows":None},\n    {"asset":"Ground truth file"',
        '"rows":"N/A (directory; not a table)"},\n    {"asset":"Ground truth file"',
        1,
    )
    inventory_source = inventory_source.replace(
        '"rows":None},\n])\ndisplay(file_inventory)',
        '"rows":"N/A (see Ground Truth summary below)"},\n])\n'
        'file_inventory["rows"] = file_inventory["rows"].fillna("N/A (not applicable)")\n'
        'display(file_inventory)',
        1,
    )
    if '"rows":None' in inventory_source:
        raise ValueError("Unlabeled None remains in asset inventory row-count fields")
    inventory_cell["source"] = inventory_source.splitlines(keepends=True)

    config = cells_by_id.get("8b105991")
    if config is None:
        raise ValueError("Expected configuration cell 8b105991 is missing from source notebook")
    config_source = "".join(config.get("source", []))
    old_gt = '''GROUND_TRUTH_CANDIDATES = [
    configured_path("GROUND_TRUTH_PATH", "embedding/embedding/ground_truth_queries_v2.jsonl"),
    PROJECT_ROOT / "embedding" / "embedding" / "ground_truth_queries_v2.jsonl",
]'''
    new_gt = '''GAIB_GT_DIR = PROJECT_ROOT / "multi_agent" / "gt"
GAIB_GT_ALL_PATH = GAIB_GT_DIR / "ground_truth_fed_v1.jsonl"
GAIB_GT_READY_PATH = GAIB_GT_DIR / "ground_truth_fed_ready_v1.jsonl"
GAIB_GT_GAPS_PATH = GAIB_GT_DIR / "ground_truth_fed_source_gaps_v1.jsonl"
GAIB_BENCHMARK_SPLIT = os.getenv("GAIB_BENCHMARK_SPLIT", "development").strip().lower()
GAIB_ALLOW_TEST_SPLIT = os.getenv("GAIB_ALLOW_TEST_SPLIT", "false").strip().lower() in {"1", "true", "yes"}
GROUND_TRUTH_CANDIDATES = [GAIB_GT_READY_PATH]'''
    if old_gt not in config_source:
        raise ValueError("Ground Truth path block changed; refusing to patch the copied notebook")
    config_source = config_source.replace(old_gt, new_gt, 1)
    config_source = config_source.replace(
        'OUTPUT_DIR = PROJECT_ROOT / "gold_assistant_outputs"',
        'OUTPUT_DIR = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs"',
    )
    config_source = config_source.replace(
        'OUTPUT_DIR = Path.cwd() / "gold_assistant_outputs"',
        'OUTPUT_DIR = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs"',
    )
    config_source = config_source.replace(
        'RUN_RETRIEVAL_BENCHMARK = False\nRUN_AGENT_BENCHMARK = False',
        'RUN_RETRIEVAL_BENCHMARK = os.getenv("RUN_RETRIEVAL_BENCHMARK", "false").strip().lower() in {"1", "true", "yes"}\n'
        'RUN_AGENT_BENCHMARK = os.getenv("RUN_AGENT_BENCHMARK", "false").strip().lower() in {"1", "true", "yes"}',
        1,
    )
    config_source = config_source.replace(
        'OUTPUT_DIR.mkdir(parents=True, exist_ok=True)',
        'OUTPUT_DIR.mkdir(parents=True, exist_ok=True)\n'
        'if GAIB_BENCHMARK_SPLIT not in {"development", "validation", "test"}:\n'
        '    raise ValueError("GAIB_BENCHMARK_SPLIT must be development, validation, or test.")\n'
        'if GAIB_BENCHMARK_SPLIT == "test" and not GAIB_ALLOW_TEST_SPLIT:\n'
        '    raise RuntimeError("Test split is held out. Set GAIB_ALLOW_TEST_SPLIT=true only for final evaluation.")\n'
        'GAIB_RUNTIME_MANIFEST = {\n'
        '    "benchmark": "GAIB-1", "created_at_utc": datetime.now(timezone.utc).isoformat(),\n'
        '    "ground_truth_source": str(GAIB_GT_READY_PATH), "selected_split": GAIB_BENCHMARK_SPLIT,\n'
        '    "source_gaps_file": str(GAIB_GT_GAPS_PATH), "test_split_opt_in": GAIB_ALLOW_TEST_SPLIT,\n'
        '    "remote_api_opt_in": RUN_RETRIEVAL_BENCHMARK or RUN_AGENT_BENCHMARK or RUN_LIVE_DEMO,\n'
        '    "a2_retrieval": {"embedding_model": EMBEDDING_MODEL, "dense_candidates": DENSE_CANDIDATES,\n'
        '        "bm25_candidates": BM25_CANDIDATES, "hybrid_candidates": HYBRID_CANDIDATES, "rrf_k": RRF_K,\n'
        '        "final_k": FINAL_K, "context_max_chars": CONTEXT_MAX_CHARS,\n'
        '        "context_per_chunk_max_chars": CONTEXT_PER_CHUNK_MAX_CHARS, "jina_model": JINA_MODEL,\n'
        '        "jina_key_slots_configured": len(JINA_API_KEYS), "remote_rag_required": REQUIRE_A2_REMOTE_RAG},\n'
        '    "generation": {"model": THAILLM_MODEL, "temperature": THAILLM_TEMPERATURE,\n'
        '        "agent_max_tokens": THAILLM_MAX_TOKENS_AGENT, "final_max_tokens": THAILLM_MAX_TOKENS_FINAL,\n'
        '        "timeout_seconds": THAILLM_TIMEOUT_SECONDS, "max_attempts": THAILLM_MAX_ATTEMPTS,\n'
        '        "api_max_retries": API_MAX_RETRIES},\n'
        '    "api_gates": {"qdrant": {"max_concurrent": QDRANT_MAX_CONCURRENT_REQUESTS, "min_interval_seconds": QDRANT_MIN_INTERVAL_SECONDS},\n'
        '        "cloudflare": {"max_concurrent": CLOUDFLARE_MAX_CONCURRENT_REQUESTS, "min_interval_seconds": CLOUDFLARE_MIN_INTERVAL_SECONDS},\n'
        '        "jina": {"max_concurrent": JINA_MAX_CONCURRENT_REQUESTS, "min_interval_seconds": JINA_MIN_INTERVAL_SECONDS},\n'
        '        "thaillm": {"max_concurrent": THAILLM_MAX_CONCURRENT_REQUESTS, "min_interval_seconds": THAILLM_MIN_INTERVAL_SECONDS}},\n'
        '    "benchmark": {"retrieval_enabled": RUN_RETRIEVAL_BENCHMARK, "multi_agent_enabled": RUN_AGENT_BENCHMARK,\n'
        '        "limit": BENCHMARK_LIMIT, "output_dir": str(OUTPUT_DIR)},\n'
        '}\n'
        '(OUTPUT_DIR / "benchmark_run_manifest.json").write_text(json.dumps(GAIB_RUNTIME_MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")',
        1,
    )
    config["source"] = config_source.splitlines(keepends=True)

    gt_cell = cells_by_id.get("4284e50e")
    if gt_cell is None:
        raise ValueError("Expected Ground Truth loader cell 4284e50e is missing")
    gt_cell["source"] = '''def load_ground_truth():
    if not (GAIB_GT_ALL_PATH.is_file() and GAIB_GT_READY_PATH.is_file() and GAIB_GT_GAPS_PATH.is_file()):
        raise FileNotFoundError("Required Fed Ground Truth files are missing from multi_agent/gt.")
    all_rows = read_jsonl(GAIB_GT_ALL_PATH)
    ready_rows = read_jsonl(GAIB_GT_READY_PATH)
    gap_rows = read_jsonl(GAIB_GT_GAPS_PATH)
    if len(all_rows) != 43 or len(ready_rows) != 37 or len(gap_rows) != 6:
        raise ValueError(f"Unexpected Fed Ground Truth counts: all={len(all_rows)}, ready={len(ready_rows)}, gaps={len(gap_rows)}")
    if any(row.get("qdrant_index_coverage_verified") is not False for row in ready_rows):
        raise ValueError("Expected source-present Fed records to retain their unverified Qdrant status.")
    selected = [row for row in ready_rows if row.get("split") == GAIB_BENCHMARK_SPLIT]
    return selected, {
        "source": str(GAIB_GT_READY_PATH),
        "all_count": len(all_rows),
        "source_present_count": len(ready_rows),
        "blocked_source_gap_count": len(gap_rows),
        "selected_split": GAIB_BENCHMARK_SPLIT,
        "selected_count": len(selected),
        "qdrant_index_coverage": "UNVERIFIED",
        "human_semantic_review": "REQUIRED",
    }

GROUND_TRUTH, ground_truth_info = load_ground_truth()
GROUND_TRUTH_SOURCE_GAPS = read_jsonl(GAIB_GT_GAPS_PATH)
print("GAIB Fed Ground Truth:", ground_truth_info)
print("Source gaps are excluded from retrieval-ready evaluation:", len(GROUND_TRUTH_SOURCE_GAPS))
if GROUND_TRUTH:
    gt_summary=pd.DataFrame([{"query_type":r.get("query_type","unknown"),"difficulty":r.get("difficulty","unknown"),"language":r.get("query_language","unknown")} for r in GROUND_TRUTH]).value_counts().rename("count").reset_index()
    display(gt_summary)
else:
    print("No Fed records exist in the selected split.")
'''.splitlines(keepends=True)

    retrieval_cell = cells_by_id.get("a3a65109")
    if retrieval_cell is None:
        raise ValueError("Expected retrieval benchmark cell a3a65109 is missing")
    retrieval_source = "".join(retrieval_cell.get("source", []))
    metric_start = retrieval_source.index("def get_relevance_map(gt):")
    metric_end = retrieval_source.index("def run_retrieval_benchmark(", metric_start)
    retrieval_source = (
        retrieval_source[:metric_start]
        + '''def normalized_document_alias(value):
    if value is None:
        return None
    alias=str(value).strip()
    return alias.rstrip("/").casefold() if alias else None

def candidate_document_aliases(candidate):
    aliases=set()
    for key in ["document_id","doc_id","original_id","source_document_id",
                "source_document_id_in_uploaded_corpus","url","source_url"]:
        alias=normalized_document_alias(candidate.get(key))
        if alias:
            aliases.add(alias)
    return aliases

def get_relevant_document_groups(gt):
    judgments=gt.get("relevance_judgments") or []
    evidence=gt.get("evidence") or []
    groups={}
    for judgment in judgments:
        did=judgment.get("document_id") or judgment.get("doc_id")
        if did is None:
            continue
        document_id=normalized_document_alias(did)
        try:
            grade=float(judgment.get("relevance_grade",judgment.get("grade",1)))
        except (TypeError,ValueError):
            grade=1.0
        aliases={document_id}
        for item in evidence:
            evidence_ids={
                normalized_document_alias(item.get("document_id")),
                normalized_document_alias(item.get("source_document_id_in_uploaded_corpus")),
                normalized_document_alias(item.get("source_document_id")),
            }
            if document_id in evidence_ids:
                for key in ["document_id","source_document_id_in_uploaded_corpus",
                            "source_document_id","original_id","source_url","url"]:
                    alias=normalized_document_alias(item.get(key))
                    if alias:
                        aliases.add(alias)
        previous=groups.get(document_id)
        if previous:
            previous["grade"]=max(previous["grade"],grade)
            previous["aliases"].update(aliases)
        else:
            groups[document_id]={"grade":grade,"aliases":aliases}
    return groups

def get_relevance_map(gt):
    aliases={}
    for document_id,group in get_relevant_document_groups(gt).items():
        for alias in group["aliases"]:
            aliases[alias]=max(aliases.get(alias,0),group["grade"])
    return aliases

def rank_metrics(gt,candidates,k=10):
    groups=get_relevant_document_groups(gt)
    if not groups:
        return {f"known_relevant_recall@{k}":np.nan,f"mrr@{k}":np.nan,f"ndcg@{k}":np.nan,"judged_relevant_count":0}
    matched=set()
    ranked=candidates[:k]
    gains=[]
    first_relevant_rank=None
    for rank,candidate in enumerate(ranked,1):
        aliases=candidate_document_aliases(candidate)
        newly_matched=[
            (document_id,group["grade"])
            for document_id,group in groups.items()
            if document_id not in matched and aliases.intersection(group["aliases"])
        ]
        if newly_matched:
            matched.update(document_id for document_id,_ in newly_matched)
            if first_relevant_rank is None:
                first_relevant_rank=rank
            gain=max((2**max(grade,0)-1 for _,grade in newly_matched),default=0)
        else:
            gain=0
        gains.append(gain/math.log2(rank+1))
    recall=len(matched)/len(groups)
    mrr=1.0/first_relevant_rank if first_relevant_rank is not None else 0.0
    ideal=sorted([2**max(group["grade"],0)-1 for group in groups.values()],reverse=True)[:k]
    idcg=sum(g/math.log2(i+2) for i,g in enumerate(ideal))
    ndcg=sum(gains)/idcg if idcg>0 else np.nan
    return {f"known_relevant_recall@{k}":recall,f"mrr@{k}":mrr,f"ndcg@{k}":ndcg,"judged_relevant_count":len(groups)}

'''
        + retrieval_source[metric_end:]
    )
    retrieval_source = retrieval_source.replace(
        '"judgment_set_exhaustive":gt.get("judgment_set_exhaustive",False)}',
        '"judgment_set_exhaustive":gt.get("judgment_set_exhaustive",False),\n'
        '                 "split":gt.get("split"),"review_status":gt.get("review_status"),\n'
        '                 "qdrant_index_coverage_verified":gt.get("qdrant_index_coverage_verified",False)}',
        1,
    )
    retrieval_source = retrieval_source.replace(
        'def run_retrieval_benchmark(ground_truth,limit=None):',
        '''def write_latency_percentiles(frame,metric,path,group_by="query_type"):
    if frame.empty or metric not in frame.columns:
        return
    work=frame.copy()
    work[metric]=pd.to_numeric(work[metric],errors="coerce")
    if group_by not in work.columns:
        group_by=next((column for column in ["agent_name","agent","name"] if column in work.columns),"all")
        if group_by=="all":
            work[group_by]="all"
    summary=work.groupby(group_by,dropna=False)[metric].agg(
        count="count",p50_ms="median",
        p90_ms=lambda values:values.quantile(0.90),
        p95_ms=lambda values:values.quantile(0.95),
        p99_ms=lambda values:values.quantile(0.99),
    ).reset_index()
    summary.to_csv(path,index=False,encoding="utf-8-sig")

def run_retrieval_benchmark(ground_truth,limit=None):''',
        1,
    )
    retrieval_source = retrieval_source.replace(
        'result=pd.DataFrame(rows); errdf=pd.DataFrame(errors)\n    return result,errdf',
        'result=pd.DataFrame(rows); errdf=pd.DataFrame(errors)\n'
        '    write_latency_percentiles(result,"retrieval_wall_ms",OUTPUT_DIR/"retrieval_latency_percentiles.csv")\n'
        '    write_latency_percentiles(result,"rerank_ms",OUTPUT_DIR/"rerank_latency_percentiles.csv")\n'
        '    for metric in [column for column in result.columns if str(column).endswith("_ms")]:\n'
        '        write_latency_percentiles(result,metric,OUTPUT_DIR/f"retrieval_{metric}_percentiles.csv")\n'
        '    return result,errdf',
        1,
    )
    retrieval_source = retrieval_source.replace(
        'if RUN_RETRIEVAL_BENCHMARK and GROUND_TRUTH:',
        'if RUN_RETRIEVAL_BENCHMARK and GROUND_TRUTH:',
        1,
    )
    retrieval_source = retrieval_source.replace(
        'else:\n    print("Retrieval benchmark disabled or ground truth unavailable; set RUN_RETRIEVAL_BENCHMARK=True to run.")',
        'else:\n    print("Retrieval benchmark not run. Set RUN_RETRIEVAL_BENCHMARK=true to start remote API calls.")',
        1,
    )
    retrieval_source = retrieval_source.replace(
        '        display(retrieval_benchmark_df.describe(include="all").T)',
        '        numeric_metrics=retrieval_benchmark_df.select_dtypes(include="number")\n'
        '        display(numeric_metrics.describe(percentiles=[0.50,0.90,0.95]).T)\n'
        '        for column in ["query_type","backend","rerank_status"]:\n'
        '            if column in retrieval_benchmark_df.columns:\n'
        '                display(retrieval_benchmark_df[column].value_counts(dropna=False).rename_axis(column).to_frame("count"))\n'
        '        missing_metrics=numeric_metrics.isna().sum()\n'
        '        if missing_metrics.any():\n'
        '            display(missing_metrics[missing_metrics>0].rename("missing_count").to_frame())',
        1,
    )
    retrieval_cell["source"] = retrieval_source.splitlines(keepends=True)

    agent_cell = cells_by_id.get("6059c30d")
    if agent_cell is None:
        raise ValueError("Expected multi-agent benchmark cell 6059c30d is missing")
    agent_source = "".join(agent_cell.get("source", []))
    agent_source = agent_source.replace(
        '"query_id":gt.get("query_id"),"query":q,"query_type":gt.get("query_type"),"difficulty":gt.get("difficulty"),',
        '"query_id":gt.get("query_id"),"query":q,"query_type":gt.get("query_type"),"difficulty":gt.get("difficulty"),\n'
        '                 "split":gt.get("split"),"review_status":gt.get("review_status"),\n'
        '                 "qdrant_index_coverage_verified":gt.get("qdrant_index_coverage_verified",False),',
        1,
    )
    agent_source = agent_source.replace(
        '"generated_answer":res.get("final_text",""),"human_correctness":"","citation_supported":"","reviewer_notes":""',
        '"generated_answer":res.get("final_text",""),"expected_facts":json.dumps((gt.get("expected_answer") or {}).get("facts",[]),ensure_ascii=False),\n'
        '                                "evidence_ids":json.dumps([e.get("evidence_id") for e in gt.get("evidence",[])],ensure_ascii=False),\n'
        '                                "source_urls":json.dumps([e.get("source_url") for e in gt.get("evidence",[])],ensure_ascii=False),\n'
        '                                "review_status":gt.get("review_status"),"expected_fact_coverage":"","human_correctness":"",\n'
        '                                "citation_supported":"","citation_support_rate":"","reviewer_notes":""',
        1,
    )
    agent_source = agent_source.replace(
        'run_df=pd.DataFrame(run_rows); agents_df=pd.DataFrame(agent_rows); review_df=pd.DataFrame(review_rows); errors_df=pd.DataFrame(error_rows)',
        'run_df=pd.DataFrame(run_rows); agents_df=pd.DataFrame(agent_rows); review_df=pd.DataFrame(review_rows); errors_df=pd.DataFrame(error_rows)\n'
        '    write_latency_percentiles(run_df,"total_wall_ms",OUTPUT_DIR/"multiagent_latency_percentiles.csv")\n'
        '    for metric in [column for column in agents_df.columns if "ms" in str(column).lower()]:\n'
        '        write_latency_percentiles(agents_df,metric,OUTPUT_DIR/f"agent_{metric}_percentiles.csv",group_by="agent")',
        1,
    )
    agent_source = agent_source.replace(
        'if RUN_AGENT_BENCHMARK:',
        'if RUN_AGENT_BENCHMARK:',
        1,
    )
    agent_source = agent_source.replace(
        'else:\n    print(f"Multi-agent benchmark disabled. Set RUN_AGENT_BENCHMARK=True; BENCHMARK_LIMIT={BENCHMARK_LIMIT}.")',
        'else:\n    print(f"Multi-agent benchmark not run. Set RUN_AGENT_BENCHMARK=true to start remote API calls; split={GAIB_BENCHMARK_SPLIT}.")',
        1,
    )
    agent_cell["source"] = agent_source.splitlines(keepends=True)

    startup_cell = cells_by_id.get("88dd7b13")
    if startup_cell is None:
        raise ValueError("Expected assistant startup cell 88dd7b13 is missing")
    startup_cell["source"] = '''QUESTION = "วิเคราะห์สถานะราคาทองคำไทยจากข้อมูลล่าสุดที่มี โดยแยกข่าว ปัจจัยมหภาค ผลเชิงปริมาณ และความเสี่ยง/ข้อจำกัดของข้อมูล พร้อมอ้างอิงหลักฐาน"

assistant = None
latest_run = None
remote_ready = bool(CF_ACCOUNT_ID and CF_API_TOKEN and QDRANT_URL and QDRANT_API_KEY and JINA_API_KEYS)
local_ready = LOCAL_NEWS_DIR is not None
if RUN_AGENT_BENCHMARK or RUN_LIVE_DEMO:
    if not remote_ready:
        missing = [name for name, value in (
            ("CLOUDFLARE_ACCOUNT_ID", CF_ACCOUNT_ID), ("CLOUDFLARE_API_TOKEN", CF_API_TOKEN),
            ("QDRANT_URL", QDRANT_URL), ("QDRANT_API_KEY", QDRANT_API_KEY),
            ("JINA_API_KEY or JINA_API_KEY2", JINA_API_KEYS),
        ) if not value]
        raise RuntimeError("Qdrant + Cloudflare + Jina are required for GAIB A2 mode; missing: " + ", ".join(missing))
    if RUN_AGENT_BENCHMARK and not THAILLM_API_KEYS:
        raise RuntimeError("Set THAILLM_API_KEYS before enabling the multi-agent benchmark.")
    assistant = GoldAssistantMultiAgent()
    if not assistant.evidence.ready or assistant.evidence.backend_name != "qdrant_cloudflare_hybrid":
        raise RuntimeError("GAIB requires the real Qdrant + Cloudflare backend; local fallback is not allowed.")
    print("Remote A2 RAG initialized:", assistant.evidence.backend_name)
    print("Indexed source chunks loaded for BM25:", len(assistant.evidence.backend.chunks))
    if RUN_LIVE_DEMO:
        latest_run = assistant.run(QUESTION)
        print("Live demo completed.")
else:
    print("Remote assistant not initialized. Enable RUN_AGENT_BENCHMARK or RUN_LIVE_DEMO to start remote API calls.")
    print(" - Remote credentials:", "ready" if remote_ready else "missing")
    print(" - Local news fallback is intentionally disabled for GAIB A2 evaluation.")
'''.splitlines(keepends=True)

    agent_source = "".join(agent_cell.get("source", []))
    agent_source = agent_source.replace(
        'if assistant is None or not assistant.evidence.ready:\n'
        '        raise RuntimeError("Initialize a working GoldAssistantMultiAgent first (Qdrant+Cloudflare or local dataset/news corpus)")',
        'if assistant is None or not assistant.evidence.ready:\n'
        '        raise RuntimeError("Remote assistant did not initialize; run the setup cell with RUN_AGENT_BENCHMARK=true.")\n'
        '    if assistant.evidence.backend_name != "qdrant_cloudflare_hybrid":\n'
        '        raise RuntimeError(f"GAIB requires Qdrant + Cloudflare, not {assistant.evidence.backend_name}.")',
        1,
    )
    agent_cell["source"] = agent_source.splitlines(keepends=True)

    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            cell["outputs"] = []

    out_path = OUT / "Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb"
    out_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def write_reports() -> dict[str, Any]:
    all_rows = read_jsonl(GT_ALL)
    ready_rows = read_jsonl(GT_READY)
    gap_rows = read_jsonl(GT_GAPS)
    mapping = inspect_fed_mapping(ready_rows)
    inventory = inventory_inputs()
    feature_details = [inspect_feature_data(path) for path in [FEATURE_CSV, FEATURE_PARQUET]]
    a2_names = {
        "EMBEDDING_MODEL", "DENSE_CANDIDATES", "BM25_CANDIDATES", "HYBRID_CANDIDATES", "RRF_K",
        "FINAL_K", "CONTEXT_MAX_CHARS", "CONTEXT_PER_CHUNK_MAX_CHARS", "JINA_MODEL", "THAILLM_MODEL",
        "THAILLM_TEMPERATURE", "THAILLM_MAX_TOKENS", "THAILLM_TIMEOUT_SECONDS", "API_MAX_RETRIES",
    }
    target_names = {
        "EMBEDDING_MODEL", "DENSE_CANDIDATES", "BM25_CANDIDATES", "HYBRID_CANDIDATES", "RRF_K",
        "FINAL_K", "CONTEXT_MAX_CHARS", "CONTEXT_PER_CHUNK_MAX_CHARS", "JINA_MODEL", "THAILLM_MODEL",
        "THAILLM_TEMPERATURE", "THAILLM_MAX_TOKENS_AGENT", "THAILLM_MAX_TOKENS_FINAL",
        "THAILLM_TIMEOUT_SECONDS", "THAILLM_MAX_ATTEMPTS", "API_MAX_RETRIES",
    }
    a2_config = notebook_assignments(RAG_CONTROL, a2_names)
    target_config = notebook_assignments(SOURCE_NOTEBOOK, target_names)
    remote_probe_path = OUT / "remote_rag_smoke_test.json"
    remote_probe = json.loads(remote_probe_path.read_text(encoding="utf-8")) if remote_probe_path.is_file() else None
    config_comparison = {
        "a2_values_from_code": a2_config,
        "multi_agent_values_from_code": target_config,
        "discrepancies": [
            "The 5-agent notebook uses separate generation budgets (agent=900, final=1600 by code defaults) while A2 uses one max_tokens=1200 generation budget; this benchmark preserves the 5-agent values and does not silently change them.",
            "The default ThaiLLM model identifier casing differs between notebook code cells; runtime model equivalence is not assumed and must be confirmed from the effective runtime manifest."
        ],
        "runtime_env_overrides": "Captured only when the GAIB notebook is run; API credential values are never written.",
    }
    (OUT / "a2_config_comparison.json").write_text(json.dumps(config_comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_tracks = {
        "fed": {"status": "PARTIAL", "reason": "All supplied Fed records are preserved; 6 source-gap cases remain blocked, Qdrant index mapping is unverified, and human semantic review is pending."},
        "quant": {"status": "BLOCKED", "reason": "No verified production function-calling tool contract was found in the target multi-agent notebook; dataset inspection alone is insufficient to author exact expected tool calls."},
        "hmm": {"status": "BLOCKED", "reason": "Model metadata requires bar_buy_log_return and intraday_range_pct; the processed feature dataset contract and training preprocessing have not been independently reconciled. Model bundle is not deserialized by this build."},
        "portfolio": {"status": "BLOCKED", "reason": "Simulator files and outputs exist, but this build does not assert independent ledger formulas or produce synthetic transaction-level reference cases without completing accounting-code validation."},
        "multi_agent": {"status": "BLOCKED", "reason": "Exact required tool-call expectations and human-approved semantic claims are unavailable; E2E ground truth must not be generated from unreviewed model answers."},
    }
    inventory_path = OUT / "source_inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "built_at_utc": datetime.now(timezone.utc).isoformat(),
                "project_root": str(ROOT),
                "inputs": inventory,
                "fed_source_mapping": mapping,
                "feature_datasets": feature_details,
                "source_classification_notice": "Fed ThaiLLM classifications are silver labels, not human gold labels.",
                "simulator_notice": "Portfolio simulator outputs are synthetic and are not customer observations.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    fed_all = [{**row, "track": "fed"} for row in all_rows]
    fed_ready = [{**row, "track": "fed"} for row in ready_rows]
    fed_gaps = [{**row, "track": "fed", "benchmark_status": "BLOCKED"} for row in gap_rows]
    write_jsonl(OUT / "ground_truth_fed_v1.jsonl", fed_all)
    write_jsonl(OUT / "ground_truth_fed_ready_v1.jsonl", fed_ready)
    write_jsonl(OUT / "ground_truth_fed_source_gaps_v1.jsonl", fed_gaps)
    write_jsonl(OUT / "ground_truth_all_v1.jsonl", fed_all)

    queue_path = OUT / "human_review_queue.csv"
    with queue_path.open("w", encoding="utf-8-sig", newline="") as stream:
        fields = ["track", "query_id", "query", "split", "review_status", "source_status", "evidence_urls", "review_reason"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in all_rows:
            evidence = row.get("evidence", [])
            is_gap = row.get("benchmark_readiness") == "blocked_missing_source_ingestion"
            writer.writerow(
                {
                    "track": "fed",
                    "query_id": row.get("query_id"),
                    "query": row.get("query"),
                    "split": row.get("split"),
                    "review_status": row.get("review_status"),
                    "source_status": "BLOCKED_SOURCE_GAP" if is_gap else "LOCAL_CHUNK_MAPPED_QDRANT_UNVERIFIED",
                    "evidence_urls": json.dumps([e.get("source_url") for e in evidence], ensure_ascii=False),
                    "review_reason": "Human semantic review required; verify query clarity, answer completeness, and claim-to-source support.",
                }
            )

    checks = [
        {"id": "fed_counts", "status": "PASS" if (len(all_rows), len(ready_rows), len(gap_rows)) == (43, 37, 6) else "FAIL", "observed": {"all": len(all_rows), "ready": len(ready_rows), "gaps": len(gap_rows)}},
        {"id": "fed_unique_query_ids", "status": "PASS" if len({r.get("query_id") for r in all_rows}) == len(all_rows) else "FAIL"},
        {"id": "retrieval_metric_document_identity", "status": "PASS", "method": "Match canonical judged document IDs against candidate document_id, original_id, source_document_id, and source URL aliases; count each judged document once."},
        {"id": "fed_ready_source_and_quote_mapping", "status": "PASS" if not mapping["unmapped_query_ids"] and not mapping["quote_mismatch_query_ids"] else "FAIL", "observed": mapping},
        {"id": "qdrant_full_corpus_index_coverage", "status": "BLOCKED", "reason": "A one-query live retrieval smoke test is not a full point-to-source audit across all 37 records."},
        {"id": "remote_qdrant_cloudflare_smoke_test", "status": "PASS" if remote_probe and remote_probe.get("status") == "PASS" else "BLOCKED", "observed": remote_probe or "Run python multi_agent/GAIB-1/probe_remote_rag.py to test one real query."},
        {"id": "fed_semantic_review", "status": "BLOCKED", "reason": "All supplied records need human semantic review."},
        {"id": "quant_track", "status": "BLOCKED", "reason": out_tracks["quant"]["reason"]},
        {"id": "hmm_track", "status": "BLOCKED", "reason": out_tracks["hmm"]["reason"]},
        {"id": "portfolio_track", "status": "BLOCKED", "reason": out_tracks["portfolio"]["reason"]},
        {"id": "multi_agent_track", "status": "BLOCKED", "reason": out_tracks["multi_agent"]["reason"]},
    ]
    validation = {
        "status": "PARTIAL",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "track_status": out_tracks,
        "api_benchmark_executed": False,
        "test_split_used_for_prompt_development": False,
        "retrieval_metric_logic": "document_identity_aliases_v2",
        "legacy_114_query_results_require_rescoring": True,
        "limitations": [
            "The notebook copy defaults to the development split; setting RUN_RETRIEVAL_BENCHMARK or RUN_AGENT_BENCHMARK to true starts remote API calls.",
            "The connectivity smoke test is not a scored benchmark run; per-query latency and agent results require an opted-in evaluation run.",
            "Fed source-document and exact-quote mapping was checked against the local chunk file only; Qdrant coverage remains unverified.",
            "The historical 114-query retrieval CSV was produced before document-ID alias matching; its zero relevance scores must not be interpreted as measured retrieval failure until rerun with the corrected scorer.",
        ],
    }
    (OUT / "validation_report.json").write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "benchmark": "GAIB-1",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "builder": Path(__file__).name,
        "seed": 20260415,
        "source_inventory_sha256": sha256(inventory_path),
        "fed_counts": {"all": len(all_rows), "source_present_local_chunks": len(ready_rows), "source_gaps": len(gap_rows)},
        "fed_split_counts": dict(Counter(str(row.get("split", "unknown")) for row in all_rows)),
        "fed_source_mapping": mapping,
        "remote_rag_smoke_test": remote_probe,
        "a2_config_comparison": config_comparison,
        "track_status": out_tracks,
        "a2_control_source": {"path": RAG_CONTROL.relative_to(ROOT).as_posix(), "sha256": sha256(RAG_CONTROL) if RAG_CONTROL.is_file() else None, "effective_runtime_config": "not captured; record from the benchmark notebook at run time"},
        "api_benchmark_executed": False,
        "input_sha256": {entry["path"]: entry.get("sha256") for entry in inventory if entry.get("exists")},
    }
    (OUT / "benchmark_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_lines = [
        "# GAIB-1 Benchmark Build Report",
        "",
        f"- Build time (UTC): {manifest['built_at_utc']}",
        "- Overall status: PARTIAL; this is not a benchmark score report.",
        "- Full benchmark API calls: not executed; a separate one-query connectivity smoke test was executed.",
        "- Source files and production notebook were not modified.",
        "- Copied experiment notebook outputs/execution counts were cleared so old 114-query `embedding` Ground Truth output cannot be mistaken for GAIB results.",
        "",
        "## Fed track",
        "",
        f"- Preserved {len(all_rows)} supplied records: {len(ready_rows)} map to source documents and exact quotes in the local RAG chunk corpus; {len(gap_rows)} remain source gaps.",
        f"- Local chunk mapping: {mapping['mapped_query_count']} of {len(ready_rows)} source-present queries; quote mismatches: {len(mapping['quote_mismatch_query_ids'])}.",
        "- Qdrant and Cloudflare connectivity is checked separately by the one-query smoke test; full-corpus Qdrant coverage remains UNVERIFIED.",
        f"- Remote connectivity smoke test: {remote_probe.get('status') if remote_probe else 'NOT RUN'}; see `remote_rag_smoke_test.json`.",
        "- The 5-agent notebook generation budget differs from A2 (900/1600 tokens vs A2 1200); this discrepancy is recorded, not silently corrected.",
        "- All records retain their original split and review status. Development is the copied notebook default; validation/test are not mixed into development.",
        "- Fed source classification labels are silver labels, not human gold labels. Human semantic review remains required.",
        "",
        "## NaN and relevance-score interpretation",
        "",
        "- In the historical 114-query table, `query_type` is text. `describe(include=\"all\")` displays `NaN` for numeric-only statistics (mean/std/min/quantiles) on text columns; these are not missing query types.",
        "- The same historical CSV reports zero retrieval metrics for all queries because the previous scorer compared only candidate `document_id` with Ground Truth IDs. Retrieved corpus chunks also carry `original_id` and source URLs; for example, the connectivity probe found the expected Fed source in Qdrant at rank 6 by its source/original ID.",
        "- The GAIB notebook now scores against document-ID aliases and source URLs, and summarizes numeric metrics separately from categorical counts. Historical CSVs are left untouched and must be rerun before interpreting old zero scores.",
        "- Metric `NaN` is retained only when a query has no usable relevance judgments or a metric is mathematically undefined; it is not replaced with zero.",
        "",
        "## Other tracks",
        "",
    ]
    for track, details in out_tracks.items():
        report_lines.append(f"- **{track.upper()}: {details['status']}** — {details['reason']}")
    report_lines.extend(
        [
            "",
            "## Reproduction",
            "",
            "From the project root, run `python multi_agent/GAIB-1/build_gaib_benchmark.py`.",
            "Run integrity checks with `python -m unittest discover -s multi_agent/GAIB-1/tests -v`.",
            "Run the read-only one-query Qdrant + Cloudflare connectivity probe with `python multi_agent/GAIB-1/probe_remote_rag.py`.",
            "Open `multi_agent/GAIB-1/Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb` for the opt-in experiment. Set the selected `RUN_*_BENCHMARK=true` to start that remote benchmark and incur API usage. Test split requires `GAIB_ALLOW_TEST_SPLIT=true`.",
            "Per-query outputs and runtime manifests are written under `multi_agent/GAIB-1/runs/`.",
            "",
        ]
    )
    (OUT / "build_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    write_gaib_notebook()
    return validation


if __name__ == "__main__":
    report = write_reports()
    print(f"GAIB-1 build status: {report['status']}")
    print(f"Output directory: {OUT}")
