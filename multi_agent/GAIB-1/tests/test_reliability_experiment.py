import ast
import json
import math
import re
import tempfile
import time
import traceback
import unicodedata
from datetime import datetime
from types import SimpleNamespace
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


GAIB_DIR = Path(__file__).resolve().parents[1]
BASE_NOTEBOOK = GAIB_DIR / "Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb"
EXPERIMENT_NOTEBOOK = GAIB_DIR / "Gold_Assistant_GAIB1_Reliability_Experiment_Phase1_2.ipynb"
ROOT_CAUSE_NOTEBOOK = GAIB_DIR / "Gold_Assistant_GAIB1_Token_Root_Cause_Experiment_v1.ipynb"
EXIT_CRITERIA_NOTEBOOK = GAIB_DIR / "Gold_Assistant_GAIB1_Exit_Criteria_v2.ipynb"


def load_notebook(path):
    return json.loads(path.read_text(encoding="utf-8"))


def cell_by_id(notebook, cell_id):
    return next(cell for cell in notebook["cells"] if cell.get("id") == cell_id)


def exec_selected(source, names, namespace):
    tree = ast.parse(source)
    selected = [
        node for node in tree.body
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in names)
        or (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Name) and target.id in names
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            )
        )
    ]
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, "selected_notebook_helpers", "exec"), namespace)


class ReliabilityExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exit_criteria = load_notebook(EXIT_CRITERIA_NOTEBOOK)
        cls.base = load_notebook(BASE_NOTEBOOK) if BASE_NOTEBOOK.exists() else cls.exit_criteria
        cls.experiment = load_notebook(EXPERIMENT_NOTEBOOK) if EXPERIMENT_NOTEBOOK.exists() else cls.exit_criteria
        cls.root_cause = load_notebook(ROOT_CAUSE_NOTEBOOK) if ROOT_CAUSE_NOTEBOOK.exists() else cls.exit_criteria
        cls.sources = {
            cell.get("id"): "".join(cell.get("source", []))
            for cell in cls.exit_criteria["cells"]
        }

    def test_notebook_is_clean_and_all_python_cells_parse(self):
        self.assertEqual(
            self.exit_criteria.get("metadata", {}).get("kernelspec", {}).get("name"),
            "gold-assistant-embedding",
        )
        self.assertTrue(any(
            cell.get("id") == "gaib-exit-criteria-v2-instrumentation"
            for cell in self.exit_criteria["cells"]
        ))
        judge_cell = cell_by_id(self.exit_criteria, "gaib-ai-judge-policy")
        judge_source = "".join(judge_cell.get("source", []))
        judge_module_source = (GAIB_DIR / "gaib1_ai_judge.py").read_text(encoding="utf-8")
        instrumentation_source = "".join(
            cell_by_id(self.exit_criteria, "gaib-exit-criteria-v2-instrumentation")["source"]
        )
        live_source = "".join(
            cell_by_id(self.exit_criteria, "gaib-live-acceptance-run")["source"]
        )
        config_source = "".join(cell_by_id(self.exit_criteria, "8b105991")["source"])
        self.assertIn("GAIB_JUDGE_MODEL", judge_source)
        self.assertIn("blind_evidence", judge_module_source)
        self.assertIn("expected_fact_fields", judge_module_source)
        self.assertIn("run_gaib_ai_judge_acceptance", live_source)
        self.assertNotIn("GAIB_SECOND_JUDGE_MODEL", live_source)
        self.assertIn("frame[column] = frame[column].astype(object)", instrumentation_source)
        self.assertIn('configured_path("GAIB_GT_READY_PATH"', config_source)
        self.assertIn("GAIB_ALLOW_HELD_OUT_SPLIT", config_source)
        self.assertIn("GAIB_RUN_LIVE_ACCEPTANCE", live_source)
        for cell in self.exit_criteria["cells"]:
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            self.assertIsNone(cell.get("execution_count"))
            self.assertEqual(cell.get("outputs"), [])
            if not source.lstrip().startswith("%"):
                ast.parse(source)

    def test_v2_span_and_expected_fact_metrics_use_exact_evidence(self):
        source = "".join(
            cell_by_id(self.exit_criteria, "gaib-exit-criteria-v2-instrumentation")["source"]
        )
        namespace = {
            "re": re,
            "unicodedata": unicodedata,
            "datetime": datetime,
            "json": json,
        }
        numeric_source = "".join(
            cell_by_id(self.exit_criteria, "6059c30d")["source"]
        )
        exec_selected(
            numeric_source,
            {"expected_answer_review_fields", "_numeric_answer_facts",
             "deterministic_numeric_answer_check"},
            namespace,
        )
        exec_selected(
            source,
            {"_exit_normalize", "_exit_exact_quotes", "_exit_quote_present",
             "_exit_expected_values", "_exit_fact_coverage"},
            namespace,
        )
        gt = {
            "evidence": [{"exact_quote": "target range at 3‑1/2 to 3‑3/4 percent"}],
            "expected_answer": {
                "facts": [{
                    "value_text": "3‑1/2 to 3‑3/4 percent",
                    "decision_action": "maintain",
                    "publication_date": "2026-01-28",
                }],
            },
        }
        self.assertEqual(
            namespace["_exit_exact_quotes"](gt),
            ["target range at 3‑1/2 to 3‑3/4 percent"],
        )
        self.assertTrue(namespace["_exit_quote_present"](
            gt["evidence"][0]["exact_quote"],
            [{"text_excerpt": "target range at 3-1/2 to 3-3/4 percent"}],
        ))
        self.assertFalse(namespace["_exit_quote_present"](
            gt["evidence"][0]["exact_quote"],
            [{"text_excerpt": "target range at 2-1/2 to 2-3/4 percent"}],
        ))
        metrics = namespace["_exit_fact_coverage"](
            gt,
            "The Committee decided to maintain the target range at 3-1/2 to 3-3/4 percent on 2026-01-28.",
        )
        self.assertEqual(metrics["expected_fact_coverage"], 1.0)
        self.assertEqual(
            namespace["_exit_fact_coverage"](gt, "No supported findings were produced.")[
                "expected_fact_coverage"
            ],
            0.0,
        )
        strict_metrics = namespace["_exit_fact_coverage"](
            {"expected_answer": "ลดลง 1,000 บาท และเพิ่มขึ้น 1,000 บาท"},
            "เพิ่มขึ้น 1,000 บาท เพิ่มขึ้น 1,000 บาท",
        )
        self.assertEqual(strict_metrics["expected_fact_coverage"], 0.5)
        self.assertEqual(strict_metrics["expected_fact_count"], 2)
        self.assertEqual(strict_metrics["matched_expected_fact_count"], 1)
        self.assertEqual(
            strict_metrics["missing_expected_numeric_facts"],
            [{"value": "1000", "direction": "down"}],
        )
        self.assertIsNone(namespace["_exit_fact_coverage"](
            {"expected_answer": {"text": "A prose answer without structured facts.", "facts": []}},
            "A paraphrased prose answer.",
        )["expected_fact_coverage"])

    def test_v2_instruments_protected_traces_and_keeps_unmet_gates_no_go(self):
        joined = "\n".join(self.sources.values())
        self.assertIn("unsupported_critical_numeric_claim_count", joined)
        self.assertIn("critical_truncation_count", joined)
        self.assertIn("NOT_HUMAN_REVIEWED", joined)
        self.assertIn("The source set is not human-reviewed", joined)
        self.assertNotIn("held_out_sample_minimum_100", joined)

    def test_live_benchmark_uses_bounded_truncation_recovery(self):
        source = "".join(
            cell_by_id(self.exit_criteria, "gaib-live-acceptance-run")["source"]
        )
        agent_source = "".join(
            cell_by_id(self.exit_criteria, "677be107")["source"]
        )
        self.assertIn("GAIB_LIVE_TRUNCATION_RECOVERY_MODE = os.getenv(", source)
        self.assertIn(
            '"GAIB_LIVE_TRUNCATION_RECOVERY_MODE", "increased"',
            source,
        )
        self.assertIn("GAIB_TRUNCATION_RECOVERY_MODE = GAIB_LIVE_TRUNCATION_RECOVERY_MODE", source)
        self.assertIn("GAIB_RECOVERY_MAX_TOKENS", source)
        self.assertIn("GAIB_RECOVERY_ESCALATION_MAX_TOKENS", source)
        self.assertIn("str(user_payload)", agent_source)
        self.assertIn("original question, task, and evidence above remain authoritative", agent_source)

    def test_v2_citation_coverage_excludes_markdown_headings(self):
        source = "".join(
            cell_by_id(self.exit_criteria, "gaib-exit-criteria-v2-instrumentation")["source"]
        )
        namespace = {
            "re": re,
            "CITATION_TOKEN_RE": re.compile(r"\[(S\d+)\]"),
            "_GAIB_ORIGINAL_CITATION_AUDIT": lambda _text, _allowed: {},
        }
        exec_selected(source, {"citation_audit_v2"}, namespace)
        audit = namespace["citation_audit_v2"](
            "## A markdown heading that must not count as a claim\n"
            "- A factual claim with a valid source citation [S1]",
            {"S1"},
        )
        self.assertEqual(audit["citation_claim_count"], 1)
        self.assertEqual(audit["citation_paragraph_coverage"], 1.0)
        self.assertEqual(
            namespace["citation_audit_v2"]("## Heading only, no factual claim here", {"S1"})[
                "citation_paragraph_coverage"
            ],
            "NO_CLAIMS",
        )

    def test_v2_preserves_prepared_context_excerpts_for_span_metrics(self):
        source = "".join(
            cell_by_id(self.exit_criteria, "gaib-exit-criteria-v2-instrumentation")["source"]
        )
        namespace = {
            "_GAIB_ORIGINAL_CANDIDATE_OUTPUT_ROW": lambda *_args: {},
            "_exit_exact_quotes": lambda _gt: ["maintain the target range at 5-1/4 to 5-1/2 percent"],
            "_exit_quote_present": lambda quote, items: any(
                quote in (item.get("text_excerpt") or item.get("text") or "")
                for item in items
            ),
        }
        exec_selected(source, {"_candidate_output_row_v2"}, namespace)
        candidate = {
            "citation_id": "S1",
            "text_excerpt": "The FOMC decided to maintain the target range at 5-1/4 to 5-1/2 percent.",
        }
        row = namespace["_candidate_output_row_v2"](
            "gtv2_000070",
            "evidence_context",
            1,
            candidate,
            {"query_id": "gtv2_000070"},
        )
        self.assertIn(candidate["text_excerpt"], row["text_excerpt"])
        self.assertTrue(row["answer_bearing_span_match"])

    def test_v2_emits_error_csv_header_and_recomputes_fact_coverage(self):
        source = "".join(
            cell_by_id(self.exit_criteria, "gaib-exit-criteria-v2-instrumentation")["source"]
        )
        run_df = pd.DataFrame([{
            "query_id": "q1",
            "query_type": "numeric_fact",
            "final_report": "- ราคาทองลดลง 100 บาท และเพิ่มขึ้น 100 บาท ทองคำแท่งขายออก 65,600 บาท [S1].",
            "citation_count": 1,
            "all_citation_ids_valid": True,
        }])
        agents_df = pd.DataFrame([
            {"query_id": "q1", "agent": f"AI{index}"}
            for index in range(1, 6)
        ])
        review_df = pd.DataFrame([{
            "query_id": "q1",
            "generated_answer": "No supported evidence.",
            "human_correctness": "",
            "citation_supported": "",
        }])
        errors_df = pd.DataFrame()
        ground_truth = [{
            "query_id": "q1",
            "query_type": "numeric_fact",
            "expected_answer": "ราคาทองลดลง 100 บาท เพิ่มขึ้น 100 บาท และทองคำแท่งขายออก 65,600 บาท",
        }]
        with tempfile.TemporaryDirectory() as output_dir:
            namespace = {
                "pd": pd,
                "json": json,
                "re": re,
                "Path": Path,
                "CITATION_TOKEN_RE": re.compile(r"\[([A-Z]\d+)\]"),
                "OUTPUT_DIR": Path(output_dir),
                "GAIB_EXIT_RUN_DETAILS": {
                    "q1": {
                        "answer_status": "ANSWERED_FROM_DATE_MATCHED_EVIDENCE",
                        "answer_attempted": True,
                        "abstention_reason": "",
                        "abstention_correctness": "NOT_AN_ABSTENTION",
                        "fact_coverage": {"expected_fact_coverage": 0.75},
                        "evidence_span_in_final_context": True,
                    }
                },
                "GAIB_REQUEST_TELEMETRY_ROWS": [],
                "GAIB_RUN_ID": "unit-test-run",
                "GAIB_BENCHMARK_SPLIT": "development",
                "BENCHMARK_LIMIT": 1,
                "_GAIB_ORIGINAL_MULTIAGENT_BENCHMARK": lambda _gt, limit=None: (
                    run_df.copy(), agents_df.copy(), review_df.copy(), errors_df.copy()
                ),
            }
            numeric_source = "".join(
                cell_by_id(self.exit_criteria, "6059c30d")["source"]
            )
            exec_selected(
                numeric_source,
                {"expected_answer_review_fields", "_numeric_answer_facts",
                 "deterministic_numeric_answer_check"},
                namespace,
            )
            exec_selected(
                source,
                {"_exit_normalize", "_exit_expected_values", "_exit_fact_coverage",
                 "run_multiagent_benchmark_exit_v2"},
                namespace,
            )
            result = namespace["run_multiagent_benchmark_exit_v2"](ground_truth, limit=1)
            self.assertEqual(len(result[0]), 1)
            self.assertEqual(result[0].loc[0, "expected_fact_coverage"], 1.0)
            self.assertEqual(result[0].loc[0, "expected_fact_count"], 3)
            self.assertEqual(result[0].loc[0, "matched_expected_fact_count"], 3)
            self.assertEqual(json.loads(result[0].loc[0, "missing_expected_numeric_facts"]), [])
            self.assertEqual(result[2]["review_type"].tolist(), ["factual_claim", "factual_claim"])
            self.assertEqual(result[2]["reviewer_slot"].tolist(), ["A", "B"])
            error_header = (
                Path(output_dir) / "multiagent_benchmark_errors.csv"
            ).read_text(encoding="utf-8-sig").splitlines()[0]
            self.assertEqual(error_header, "query_id,query,stage,error_type,error,traceback")
            namespace["GAIB_EXIT_RUN_DETAILS"]["q1"].update({
                "answer_status": "EXPLICIT_ABSTENTION",
                "abstention_correctness": "CORRECT",
                "fact_coverage": {"expected_fact_coverage": 0.0},
                "evidence_span_in_final_context": False,
            })
            run_df.loc[0, "final_report"] = "No supported evidence."
            abstention_result = namespace["run_multiagent_benchmark_exit_v2"](
                ground_truth, limit=1
            )
            self.assertEqual(abstention_result[0].loc[0, "expected_fact_coverage"], 0.0)
            namespace["GAIB_EXIT_RUN_DETAILS"]["q1"].update({
                "answer_status": "ANSWERED_FROM_DATE_MATCHED_EVIDENCE",
                "abstention_correctness": "NOT_AN_ABSTENTION",
                "evidence_span_in_final_context": True,
            })
            namespace["GAIB_EXIT_RUN_DETAILS"]["q1"]["fact_coverage"] = {
                "expected_fact_coverage": 1.0
            }
            run_df.loc[0, "final_report"] = "- ราคาทองลดลง 100 บาท [S1]"
            partial_result = namespace["run_multiagent_benchmark_exit_v2"](
                ground_truth, limit=1
            )
            self.assertAlmostEqual(partial_result[0].loc[0, "expected_fact_coverage"], 1 / 3)
            self.assertEqual(partial_result[0].loc[0, "matched_expected_fact_count"], 1)

    def test_agent_context_compaction_preserves_citable_measurements(self):
        source = "".join(cell_by_id(self.exit_criteria, "f5926591")["source"])
        namespace = {"json": json}
        exec_selected(source, {"hmm_context", "risk_context"}, namespace)
        hmm_text = namespace["hmm_context"]({
            "status": "available",
            "model_name": "GaussianHMM",
            "as_of": "2026-10-13",
            "latest_state": 2,
            "latest_state_confidence": 0.91,
            "n_observations": 500,
            "state_counts": {"0": 200, "1": 180, "2": 120},
            "feature_cols": ["large", "unneeded", "feature", "list"],
            "state_feature_summary": {"verbose": "x" * 10000},
            "warnings": [],
            "retrospective_only": True,
            "records": [
                {"evidence_id": "H1", "name": "state", "value": 2,
                 "unit": "", "status": "PASS", "payload": "x" * 10000}
            ],
        })
        hmm_payload = json.loads(hmm_text)
        self.assertEqual(hmm_payload["records"][0]["evidence_id"], "H1")
        self.assertEqual(hmm_payload["records"][0]["value"], 2)
        self.assertNotIn("feature_cols", hmm_payload)
        self.assertNotIn("state_feature_summary", hmm_payload)
        self.assertNotIn("payload", hmm_payload["records"][0])

        risk_text = namespace["risk_context"]({
            "summary": "x" * 10000,
            "records": [
                {"evidence_id": "R1", "name": "duplicate_ids", "value": 0,
                 "unit": "rows", "status": "PASS", "note": "routine"},
                {"evidence_id": "R2", "name": "feature_lag", "value": 5,
                 "unit": "days", "status": "WARN", "note": "Rebuild feature parquet."},
            ],
        })
        risk_payload = json.loads(risk_text)
        self.assertEqual([record["evidence_id"] for record in risk_payload], ["R1", "R2"])
        self.assertNotIn("note", risk_payload[0])
        self.assertEqual(risk_payload[1]["note"], "Rebuild feature parquet.")
        self.assertNotIn("summary", risk_text)

    def test_fomc_retrieval_expansion_is_date_aware_and_limited_to_fomc(self):
        source = "".join(cell_by_id(self.root_cause, "6c41d141").get("source", []))
        tree = ast.parse(source)
        helper = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "expand_retrieval_query"
        )
        namespace = {"re": re, "datetime": datetime}
        exec(compile(ast.Module(body=[helper], type_ignores=[]), "retrieval_query_helper", "exec"), namespace)
        expand = namespace["expand_retrieval_query"]
        expanded = expand("FOMC statement on 2023-11-01")
        self.assertIn("Federal Open Market Committee", expanded)
        self.assertIn("November 01, 2023", expanded)
        self.assertEqual(expand("What is the price of gold?"), "What is the price of gold?")

    @unittest.skipUnless(ROOT_CAUSE_NOTEBOOK.exists(), "legacy root-cause notebook fixture is not present")
    def test_root_cause_notebook_is_versioned_opt_in_and_instruments_requests(self):
        source_by_id = {
            cell.get("id"): "".join(cell.get("source", []))
            for cell in self.root_cause["cells"]
        }
        config = source_by_id["8b105991"]
        generation = source_by_id["677be107"]
        agents = source_by_id["f5926591"]
        live_acceptance = source_by_id["gaib-live-acceptance-run"]
        self.assertIn(
            'RUN_RETRIEVAL_BENCHMARK = os.getenv("GAIB_RUN_RETRIEVAL_BENCHMARK", "false")',
            config,
        )
        self.assertIn(
            'RUN_AGENT_BENCHMARK = os.getenv("GAIB_RUN_AGENT_BENCHMARK", "false")',
            config,
        )
        self.assertIn('"https://thaillm.or.th/api/v1"', config)
        self.assertIn("ThaiLLM API credentials must only be sent over HTTPS.", config)
        self.assertIn(
            'GAIB_AI3_COMPACT_OUTPUT = os.getenv("GAIB_AI3_COMPACT_OUTPUT", "true")',
            config,
        )
        self.assertIn(
            'GAIB_COMPACT_OUTPUT_DEFAULT = os.getenv("GAIB_COMPACT_OUTPUT_DEFAULT", "true")',
            config,
        )
        self.assertIn(
            'GAIB_AI1_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI1_LIVE_MAX_TOKENS", "1500"))',
            config,
        )
        self.assertIn(
            'GAIB_AI2_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI2_LIVE_MAX_TOKENS", "1500"))',
            config,
        )
        self.assertIn(
            'GAIB_AI4_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI4_LIVE_MAX_TOKENS", "1500"))',
            config,
        )
        self.assertIn(
            'GAIB_AI5_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI5_LIVE_MAX_TOKENS", "2400"))',
            config,
        )
        self.assertIn('"live_agent_token_budgets"', config)
        exit_config = next(
            "".join(cell.get("source", []))
            for cell in self.exit_criteria["cells"]
            if cell.get("id") == "8b105991"
        )
        self.assertIn(
            'GAIB_RUN_ALL_EXPERIMENTS = os.getenv("GAIB_RUN_ALL_EXPERIMENTS", "false")',
            exit_config,
        )
        self.assertIn(
            'GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK = os.getenv("GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK", "false")',
            exit_config,
        )
        self.assertIn("DENSE_CANDIDATES = 40", config)
        self.assertIn("BM25_CANDIDATES = 40", config)
        self.assertIn("HYBRID_CANDIDATES = 40", config)
        self.assertIn("RRF_BM25_WEIGHT = 2.0", config)
        self.assertIn('"retrieval_query_expansion": "fomc_acronym_date_v1"', config)
        retrieval = source_by_id["6c41d141"]
        self.assertIn("def bm25_index_text(chunk):", retrieval)
        self.assertIn('"publication_date", "report_period", "url"', retrieval)
        self.assertEqual(retrieval.count("tokenize(bm25_index_text(c))"), 2)
        self.assertIn("def expand_retrieval_query(query):", retrieval)
        self.assertIn("Federal Open Market Committee Federal Reserve monetary policy statement", retrieval)
        self.assertIn("def reranker_document(candidate):", retrieval)
        self.assertIn("reranker_document(c) for c in candidates", retrieval)
        self.assertIn("weight/(RRF_K+rank)", retrieval)
        self.assertIn("metrics[\"query_expansion\"]", retrieval)
        self.assertIn('"retrieval_query_expansion": result["metrics"].get("query_expansion")', source_by_id["a3a65109"])
        self.assertIn('"agent_prompt_versions"', config)
        self.assertIn('"claim-evidence-ai1-compact-v1"', config)
        self.assertIn('"claim-evidence-ai3-compact-v1"', config)
        self.assertIn('"claim-evidence-ai5-compact-v1"', config)
        self.assertIn('"token_root_cause"', config)
        self.assertIn("GAIB_RUN_TARGETED_EXPERIMENT", source_by_id["token-root-cause-experiments"])
        self.assertIn("or GAIB_RUN_ALL_EXPERIMENTS", source_by_id["token-root-cause-experiments"])
        self.assertIn('GAIB_BENCHMARK_SPLIT != "development"', source_by_id["token-root-cause-experiments"])
        self.assertIn("or GAIB_RUN_ALL_EXPERIMENTS", live_acceptance)
        exit_live_acceptance = next(
            "".join(cell.get("source", []))
            for cell in self.exit_criteria["cells"]
            if cell.get("id") == "gaib-live-acceptance-run"
        )
        self.assertIn("GAIB_RUN_FULL_DEVELOPMENT_BENCHMARK", exit_live_acceptance)
        self.assertIn("Full GAIB experiment/benchmark switches only run on the development split", exit_live_acceptance)
        self.assertIn('GAIB_BENCHMARK_SPLIT != "development"', live_acceptance)
        self.assertIn("len(GROUND_TRUTH) if GAIB_RUN_ALL_EXPERIMENTS", live_acceptance)
        self.assertIn("request_duration_ms", generation)
        self.assertIn("gate_wait_ms", generation)
        self.assertIn("api_attempt_count", generation)
        self.assertIn("finish_reason_indicates_output_truncation", generation)
        self.assertIn("GAIB_TRUNCATION_RECOVERY_MODE == \"increased\"", generation)
        self.assertIn("available_ids = set(allowed_ids) if allowed_ids is not None", generation)
        self.assertIn("contract_hint = {\"required\": required_types", generation)
        self.assertIn("Limit narrative lists to at most 3 relevant items", generation)
        self.assertIn("AI4 concise-output rule", generation)
        self.assertIn("AI3 concise-output rule", generation)
        self.assertIn("AI1 concise-output rule", generation)
        self.assertIn("AI5 concise-output rule", generation)
        self.assertIn("Every list-typed field must be a JSON array", generation)
        self.assertIn("under 450 output tokens", generation)
        self.assertIn("under 400 output tokens", generation)
        self.assertIn("prompt_manifest", source_by_id["5cce7a2e"])
        self.assertIn('if key != "rag_sources"', source_by_id["5cce7a2e"])
        exit_lead = "".join(
            cell_by_id(self.exit_criteria, "5cce7a2e")["source"]
        )
        self.assertIn(
            "Treat dated primary-source text in rag_sources as direct evidence",
            exit_lead,
        )
        self.assertIn("answer every part supported by the evidence", exit_lead)
        self.assertIn("and GAIB_AI3_COMPACT_OUTPUT", generation)
        self.assertIn("quantified_findings", generation)
        self.assertIn("one item per list", generation)
        quant_agent = agents.split("class QuantRegimeAgent:", 1)[1].split("class RiskAuditorAgent:", 1)[0]
        self.assertIn('for evidence_pack in (market, hmm)', quant_agent)
        self.assertIn("allowed_ids=allowed_ids", quant_agent)
        self.assertNotIn("Document ID:", agents.split("def query_evidence_context(sources):", 1)[1].split("def quant_context", 1)[0])
        context_namespace = {}
        exec_selected(agents, {"query_evidence_context"}, context_namespace)
        context = context_namespace["query_evidence_context"]([{
            "citation_id": "S1", "document_id": "internal-document-hash",
            "chunk_id": "internal-chunk-hash", "title": "FOMC statement",
            "text_excerpt": "Evidence excerpt",
        }])
        self.assertIn("[S1]", context)
        self.assertIn("FOMC statement", context)
        self.assertNotIn("internal-document-hash", context)
        self.assertNotIn("internal-chunk-hash", context)
        news_agent = agents.split("class NewsAnalystAgent:", 1)[1].split("class MacroAnalystAgent:", 1)[0]
        self.assertIn("def run(self,llm,query,sources,market,max_tokens=None):", news_agent)
        self.assertIn("payload,max_tokens=max_tokens)", news_agent)
        self.assertIn("max_tokens=GAIB_AI1_LIVE_MAX_TOKENS", source_by_id["5cce7a2e"])
        macro_agent = agents.split("class MacroAnalystAgent:", 1)[1].split("class QuantRegimeAgent:", 1)[0]
        self.assertIn("def run(self,llm,query,sources,market,max_tokens=None):", macro_agent)
        self.assertIn("max_tokens=GAIB_AI2_LIVE_MAX_TOKENS", source_by_id["5cce7a2e"])
        risk_agent = agents.split("class RiskAuditorAgent:", 1)[1].split("agent1=NewsAnalystAgent()", 1)[0]
        self.assertIn("def run(self,llm,query,market,risk,max_tokens=None):", risk_agent)
        self.assertIn("max_tokens=GAIB_AI4_LIVE_MAX_TOKENS", source_by_id["5cce7a2e"])
        lead_agent = source_by_id["5cce7a2e"].split("class LeadResearcherAgent:", 1)[1]
        self.assertIn("max_tokens=None):", lead_agent)
        self.assertIn("answer every part supported by the evidence", lead_agent)
        self.assertIn("max_tokens=GAIB_AI5_LIVE_MAX_TOKENS", source_by_id["5cce7a2e"])
        self.assertIn("status == \"success\" and not (parse_valid and schema_valid)", generation)
        self.assertIn("record_request_diagnostic", generation)
        self.assertIn("icacls", source_by_id["token-root-cause-preflight"])
        self.assertIn('Path.home() / ".copilot" / "session-state"', source_by_id["token-root-cause-preflight"])
        self.assertIn("Diagnostic ACL verification failed", source_by_id["token-root-cause-preflight"])
        self.assertIn('"schema_valid": record.get("schema_valid")', source_by_id["token-root-cause-preflight"])
        self.assertIn('"claim-evidence-ai3-compact-v1"', source_by_id["token-root-cause-preflight"])
        self.assertIn('"claim-evidence-ai1-compact-v1"', source_by_id["token-root-cause-preflight"])
        self.assertIn('"claim-evidence-ai5-compact-v1"', source_by_id["token-root-cause-preflight"])
        self.assertIn("GAIB_COMPACT_OUTPUT = GAIB_COMPACT_OUTPUT_DEFAULT", source_by_id["token-root-cause-preflight"])
        self.assertIn('"schema_valid": outcome["schema_valid"]', generation)
        self.assertIn("raw_response", source_by_id["token-root-cause-preflight"])
        self.assertIn("B_budget_1200", source_by_id["token-root-cause-experiments"])
        self.assertIn("C_compact_900", source_by_id["token-root-cause-experiments"])
        self.assertIn("B2_budget_1500_conditional", source_by_id["token-root-cause-experiments"])
        self.assertIn('f"E_latency_{mode}"', source_by_id["token-root-cause-experiments"])
        self.assertIn("execution_mode=mode", source_by_id["token-root-cause-experiments"])
        live_run = source_by_id["gaib-live-acceptance-run"]
        self.assertIn('"GAIB_RUN_LIVE_ACCEPTANCE"', live_run)
        self.assertIn('THAILLM_BASE_URL.lower().startswith("https://")', live_run)
        self.assertIn('assistant.evidence.backend_name != "qdrant_cloudflare_hybrid"', live_run)
        self.assertIn("run_retrieval_benchmark(GROUND_TRUTH", live_run)
        self.assertIn("run_multiagent_benchmark(GROUND_TRUTH", live_run)
        self.assertIn('GAIB_RUNTIME_MANIFEST["remote_api_opt_in"] = True', live_run)
        self.assertIn('"live_acceptance_enabled": True', live_run)

    def test_retrieval_eligibility_requires_verified_coverage(self):
        source_by_id = {
            cell.get("id"): "".join(cell.get("source", []))
            for cell in self.root_cause["cells"]
        }
        retrieval_source = source_by_id["a3a65109"]
        self.assertIn('evaluation_eligible = coverage_status == "COVERED"', retrieval_source)
        self.assertIn('"evaluation_eligible": evaluation_eligible', retrieval_source)

        benchmark_source = source_by_id["6059c30d"]
        self.assertIn('if coverage_status!="COVERED":', benchmark_source)
        self.assertIn('"evaluation_eligible":coverage_status=="COVERED"', benchmark_source)

        builder_source = (GAIB_DIR / "build_reliability_experiment.py").read_text(encoding="utf-8")
        self.assertIn(
            '"coverage_status":coverage_status,"evaluation_eligible":coverage_status=="COVERED"',
            builder_source,
        )
        self.assertNotIn(
            '"coverage_status":coverage_status,"evaluation_eligible":True',
            builder_source,
        )

    @unittest.skipUnless(ROOT_CAUSE_NOTEBOOK.exists(), "legacy root-cause notebook fixture is not present")
    def test_root_cause_diagnostic_redaction_handles_api_key_slots(self):
        source_by_id = {
            cell.get("id"): "".join(cell.get("source", []))
            for cell in self.root_cause["cells"]
        }
        namespace = {
            "THAILLM_API_KEYS": [("THAILLM_API_KEY1", "thai-secret")],
            "CF_API_TOKEN": "cloudflare-secret",
            "QDRANT_API_KEY": "qdrant-secret",
            "JINA_API_KEYS": [("JINA_API_KEY1", "jina-secret")],
        }
        exec_selected(
            source_by_id["token-root-cause-preflight"],
            {"_sanitize_sensitive"},
            namespace,
        )

        sanitized = namespace["_sanitize_sensitive"](
            "thai-secret cloudflare-secret qdrant-secret jina-secret"
        )

        self.assertEqual(sanitized, "[REDACTED] [REDACTED] [REDACTED] [REDACTED]")

    def test_directional_schema_accepts_neutral_and_prompts_it(self):
        source_by_id = {
            cell.get("id"): "".join(cell.get("source", []))
            for cell in self.root_cause["cells"]
        }
        namespace = {}
        exec_selected(
            source_by_id["677be107"],
            {"AGENT_SCHEMAS", "validate_agent_schema"},
            namespace,
        )

        news_result = {
            "status": "success",
            "reported_fact": "",
            "event_date": None,
            "possible_market_channel": "",
            "evidence_ids": [],
            "concise_summary": "",
            "relevant_events": [],
            "price_bias": "neutral",
            "evidence_strength": "low",
            "missing_evidence": [],
            "cautions": [],
        }
        macro_result = {
            "status": "success",
            "as_of": None,
            "observed_market_facts": [],
            "macro_channels": [],
            "evidence_ids": [],
            "macro_bias": "neutral",
            "confidence": "medium",
            "data_gaps": [],
            "non_causal_caveat": "",
        }

        self.assertEqual(
            namespace["validate_agent_schema"]("AI1_News_Analyst", news_result), []
        )
        self.assertEqual(
            namespace["validate_agent_schema"]("AI2_Macro_Analyst", macro_result), []
        )
        self.assertIn(
            "price_bias (bullish/bearish/mixed/neutral/unknown)",
            source_by_id["f5926591"],
        )
        self.assertIn(
            "macro_bias (bullish/bearish/mixed/neutral/unknown)",
            source_by_id["f5926591"],
        )

    def test_quant_agent_passes_market_and_hmm_evidence_ids_to_validator(self):
        source_by_id = {
            cell.get("id"): "".join(cell.get("source", []))
            for cell in self.root_cause["cells"]
        }
        captured = {}

        def capture_call(*args, **kwargs):
            captured.update(kwargs)
            return {"status": "captured"}

        namespace = {
            "call_agent_json": capture_call,
            "quant_context": lambda snapshot: "market",
            "hmm_context": lambda snapshot: "hmm",
        }
        exec_selected(
            source_by_id["f5926591"],
            {"QuantRegimeAgent"},
            namespace,
        )
        market = {"records": [{"evidence_id": "Q1"}]}
        hmm = {"records": [{"evidence_id": "H1"}]}

        result = namespace["QuantRegimeAgent"]().run(None, "query", market, hmm)

        self.assertEqual(result, {"status": "captured"})
        self.assertEqual(captured["allowed_ids"], {"Q1", "H1"})

    def test_risk_agent_passes_only_risk_evidence_ids_to_validator(self):
        source_by_id = {
            cell.get("id"): "".join(cell.get("source", []))
            for cell in self.root_cause["cells"]
        }
        captured = {}

        def capture_call(*args, **kwargs):
            captured.update(kwargs)
            return {"status": "captured"}

        namespace = {
            "call_agent_json": capture_call,
            "quant_context": lambda snapshot: "market",
            "risk_context": lambda snapshot: "risk",
        }
        exec_selected(
            source_by_id["f5926591"],
            {"RiskAuditorAgent"},
            namespace,
        )
        risk = {"records": [{"evidence_id": "R1"}, {"evidence_id": "R3"}]}

        result = namespace["RiskAuditorAgent"]().run(
            None, "query", {"records": [{"evidence_id": "Q1"}]}, risk, max_tokens=1500
        )

        self.assertEqual(result, {"status": "captured"})
        self.assertEqual(captured["allowed_ids"], {"R1", "R3"})
        self.assertEqual(captured["max_tokens"], 1500)

    def test_a2_model_and_retrieval_parameters_are_unchanged(self):
        protected = {
            "THAILLM_MODEL", "THAILLM_TEMPERATURE", "THAILLM_MAX_TOKENS_AGENT",
            "THAILLM_MAX_TOKENS_FINAL", "DENSE_CANDIDATES", "BM25_CANDIDATES",
            "HYBRID_CANDIDATES", "FINAL_K", "RRF_K", "JINA_MODEL", "EMBEDDING_MODEL",
        }

        def assignments(notebook):
            result = {}
            for cell in notebook["cells"]:
                if cell.get("cell_type") != "code":
                    continue
                source = "".join(cell.get("source", []))
                if source.lstrip().startswith("%"):
                    continue
                for node in ast.walk(ast.parse(source)):
                    if not isinstance(node, ast.Assign):
                        continue
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id in protected:
                            result[target.id] = ast.dump(node.value, include_attributes=False)
            return result

        self.assertEqual(assignments(self.base), assignments(self.experiment))
        config = self.sources["8b105991"]
        self.assertIn("BENCHMARK_QUERY_IDS = []", config)
        self.assertIn('"thai_gold_development"', config)
        self.assertIn(' / GAIB_RUN_ID', config)
        live_source = "".join(
            cell_by_id(self.exit_criteria, "gaib-live-acceptance-run")["source"]
        )
        self.assertIn("GAIB_RUN_LIVE_ACCEPTANCE", live_source)
        self.assertIn("GAIB_RUN_ID = datetime.now(timezone.utc)", config)
        candidate_config = "".join(cell_by_id(self.exit_criteria, "8b105991")["source"])
        self.assertIn(
            'for slot in ("JINA_API_KEY4", "JINA_API_KEY", "JINA_API_KEY2", "JINA_API_KEY3")',
            candidate_config,
        )

    def test_live_acceptance_outputs_are_present_without_historical_baseline(self):
        joined = "\n".join(self.sources.values())
        self.assertIn("ground_truth_audit.csv", joined)
        self.assertIn("retrieval_stage_candidates.csv", joined)
        self.assertIn("retrieval_stage_metrics.csv", joined)
        self.assertIn("retrieval_miss_diagnosis.csv", joined)
        self.assertIn("agent_quality_and_latency.csv", joined)
        self.assertIn("agent_quality_and_latency_checkpoint.csv", joined)
        self.assertIn("multiagent_benchmark_summary.csv", joined)
        self.assertNotIn("BASELINE_RUN_DIR", joined)
        self.assertNotIn("BASELINE_METRICS_PATH", joined)
        self.assertIn("BLOCKED_COVERAGE", joined)
        self.assertIn("matched_document_ids", joined)
        self.assertIn("unmatched_expected_document_ids", joined)
        self.assertIn("task_success_rate", joined)
        self.assertIn("NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE", joined)
        self.assertIn("NOT_HUMAN_REVIEWED", joined)
        self.assertIn("report_has_citations_rate", joined)
        self.assertIn("citation_id_valid_rate_when_present", joined)
        self.assertIn("traceback.format_exc()", joined)
        self.assertIn("final_text,claim_audit_result=render_evidence_report(final_data,allowed)", joined)
        self.assertIn("audit.update(claim_evidence_audit([],allowed))", joined)
        self.assertNotIn("audit.update(claim_audit([],allowed))", joined)
        self.assertIn("initial_tokens", joined)
        self.assertIn("repair_tokens", joined)
        self.assertNotIn("raw_text_excerpt", joined)
        self.assertIn('"reported_fact": str', joined)
        self.assertIn('"tool_result_ids": list', joined)
        self.assertIn('"pnl_reconciliation": (str, dict, type(None))', joined)
        self.assertNotIn("multiagent_benchmark_results_checkpoint.csv", joined)
        self.assertIn("SOURCE_GAP", self.sources["gaib_coverage_audit_v1"])
        self.assertIn("source_spans_verified", self.sources["gaib_coverage_audit_v1"])
        self.assertIn("bm25_corpus_match", self.sources["gaib_coverage_audit_v1"])
        self.assertIn("runtime_qdrant_index_coverage_verified", self.sources["gaib_coverage_audit_v1"])

    def test_jina_key_slots_include_fourth_fallback(self):
        config = self.sources["8b105991"]
        namespace = {
            "os": SimpleNamespace(getenv=lambda name, default="": {
                "JINA_API_KEY2": "key-two",
                "JINA_API_KEY3": "key-three",
                "JINA_API_KEY4": "key-four",
            }.get(name, default))
        }
        exec_selected(config, {"JINA_API_KEYS"}, namespace)
        self.assertEqual(
            namespace["JINA_API_KEYS"],
            [
                ("JINA_API_KEY4", "key-four"),
                ("JINA_API_KEY2", "key-two"),
                ("JINA_API_KEY3", "key-three"),
            ],
        )

    def test_agent_repair_detects_truncation_and_separates_validity_layers(self):
        namespace = {
            "json": json,
            "re": re,
            "time": time,
            "THAILLM_MODEL": "test-model",
            "THAILLM_MAX_TOKENS_AGENT": 900,
            "GAIB_COMPACT_OUTPUT": False,
            "GAIB_AI3_COMPACT_OUTPUT": False,
            "GAIB_TRUNCATION_RECOVERY_MODE": "none",
            "GAIB_RECOVERY_MAX_TOKENS": 1200,
            "GAIB_RECOVERY_ESCALATION_MAX_TOKENS": 1500,
            "GAIB_REQUEST_DIAGNOSTICS_ENABLED": False,
        }
        llm_source = "".join(
            cell_by_id(self.exit_criteria, "677be107")["source"]
        )
        exec_selected(
            llm_source,
            {"AGENT_SCHEMAS", "AGENT_ENUMS", "parse_json_object", "validate_agent_schema",
             "_collect_evidence_ids", "call_agent_json"},
            namespace,
        )
        namespace["AGENT_SYSTEM_BASE"] = "system"
        valid_agent = {
            "status": "success",
            "reported_fact": "fact",
            "event_date": None,
            "possible_market_channel": "unknown",
            "evidence_ids": ["S1"],
            "concise_summary": "Summary",
            "relevant_events": [{"event": "event", "date": "2020-01-01",
                                 "reported_fact": "fact", "possible_market_channel": "unknown",
                                 "evidence_ids": ["S1"]}],
            "price_bias": "unknown",
            "evidence_strength": "low",
            "missing_evidence": [],
            "cautions": [],
        }

        class FakeLLM:
            def __init__(self, responses):
                self.responses = list(responses)
                self.calls = 0
                self.request_budgets = []

            def generate(self, *_args, **kwargs):
                self.calls += 1
                self.request_budgets.append(kwargs.get("max_tokens"))
                return self.responses.pop(0)

        def response(text, finish_reason="stop"):
            return {
                "text": text, "finish_reason": finish_reason, "latency_ms": 1,
                "attempts": 1, "prompt_tokens": 2, "completion_tokens": 3,
                "total_tokens": 5, "model": "test-model", "provider": "test",
            }

        llm = FakeLLM([response('{"status":"incomplete"}'), response(json.dumps(valid_agent))])
        repaired = namespace["call_agent_json"](llm, "AI1_News_Analyst", "role", "Use [S1]", allowed_ids={"S1"})
        self.assertEqual(repaired["status"], "success")
        self.assertTrue(repaired["metrics"]["api_success"])
        self.assertTrue(repaired["metrics"]["json_parse"])
        self.assertTrue(repaired["metrics"]["schema_valid"])
        self.assertEqual(repaired["metrics"]["repair_attempts"], 1)
        self.assertEqual(repaired["metrics"]["attempt_count"], 2)
        self.assertEqual(repaired["metrics"]["initial_tokens"], 5)
        self.assertEqual(repaired["metrics"]["repair_tokens"], 5)
        self.assertEqual(llm.request_budgets, [900, 900])
        self.assertIsNone(repaired["metrics"]["task_success"])

        truncated_llm = FakeLLM([response('{"broken":', finish_reason="length")])
        truncated = namespace["call_agent_json"](
            truncated_llm, "AI1_News_Analyst", "role", "Use [S1]", allowed_ids={"S1"}
        )
        self.assertEqual(truncated["status"], "truncated_output")
        self.assertEqual(truncated_llm.calls, 1)
        self.assertFalse(truncated["metrics"]["json_parse"])

        namespace["GAIB_TRUNCATION_RECOVERY_MODE"] = "increased"
        recovered_llm = FakeLLM([
            response('{"broken":', finish_reason="length"),
            response(json.dumps(valid_agent)),
        ])
        recovered = namespace["call_agent_json"](
            recovered_llm,
            "AI1_News_Analyst",
            "role",
            "Use [S1]",
            max_tokens=900,
            allowed_ids={"S1"},
        )
        self.assertEqual(recovered["status"], "success")
        self.assertEqual(recovered_llm.request_budgets, [900, 1200])
        self.assertEqual(recovered["metrics"]["request_budgets"], [900, 1200])

        still_truncated_llm = FakeLLM([
            response('{"broken":', finish_reason="length"),
            response('{"still_broken":', finish_reason="length"),
        ])
        still_truncated = namespace["call_agent_json"](
            still_truncated_llm,
            "AI1_News_Analyst",
            "role",
            "Use [S1]",
            max_tokens=900,
            allowed_ids={"S1"},
        )
        self.assertEqual(still_truncated["status"], "truncated_output")
        self.assertEqual(still_truncated_llm.request_budgets, [900, 1200])
        self.assertEqual(still_truncated["metrics"]["request_budgets"], [900, 1200])

    def test_exit_criteria_agent_repair_uses_compact_schema_only(self):
        config = "".join(cell_by_id(self.exit_criteria, "8b105991")["source"])
        self.assertIn(
            'GAIB_AI3_LIVE_MAX_TOKENS = int(os.getenv("GAIB_AI3_LIVE_MAX_TOKENS", "3000"))',
            config,
        )
        source = "".join(cell_by_id(self.exit_criteria, "677be107")["source"])
        namespace = {
            "json": json,
            "re": re,
            "time": time,
            "traceback": traceback,
            "THAILLM_MODEL": "test-model",
            "THAILLM_MAX_TOKENS_AGENT": 900,
            "GAIB_COMPACT_OUTPUT": True,
            "GAIB_AI3_COMPACT_OUTPUT": True,
            "AGENT_SYSTEM_BASE": "test system prompt",
        }
        exec_selected(
            source,
            {"AGENT_SCHEMAS", "AGENT_ENUMS", "parse_json_object", "validate_agent_schema",
             "_collect_evidence_ids", "call_agent_json"},
            namespace,
        )
        valid_agent = {
            "status": "insufficient_evidence",
            "as_of": None,
            "statistics": [],
            "regime_state": None,
            "feature_inputs": [],
            "tool_result_ids": [],
            "quantified_findings": [],
            "hmm_interpretation": None,
            "regime_state_id": None,
            "regime_confidence": None,
            "robustness_notes": [],
            "limitations": [],
            "recommendation_for_next_test": None,
        }

        class FakeLLM:
            def __init__(self):
                self.calls = []

            def generate(self, system, payload, max_tokens):
                self.calls.append((system, payload, max_tokens))
                text = "malformed response" if len(self.calls) == 1 else json.dumps(valid_agent)
                return {
                    "text": text,
                    "finish_reason": "stop",
                    "model": "test-model",
                    "provider": "fake",
                    "prompt_tokens": 2,
                    "completion_tokens": 3,
                    "total_tokens": 5,
                }

        llm = FakeLLM()
        result = namespace["call_agent_json"](
            llm,
            "AI3_Quant_Regime_Analyst",
            "quant role",
            "ORIGINAL_TASK_SENTINEL [Q1]",
            max_tokens=1500,
            allowed_ids={"Q1"},
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("COMPACT JSON CONTRACT", llm.calls[0][0])
        self.assertIn("AI3 concise-output rule", llm.calls[0][0])
        self.assertIn("Previous response (reference only", llm.calls[1][1])
        self.assertIn("ORIGINAL_TASK_SENTINEL", llm.calls[1][1])
        self.assertEqual([call[2] for call in llm.calls], [1500, 1500])

    def test_exit_criteria_schema_repair_includes_allowed_enum_values(self):
        source = "".join(cell_by_id(self.exit_criteria, "677be107")["source"])
        namespace = {
            "json": json,
            "re": re,
            "time": time,
            "traceback": traceback,
            "THAILLM_MODEL": "test-model",
            "THAILLM_MAX_TOKENS_AGENT": 900,
            "GAIB_COMPACT_OUTPUT": True,
            "GAIB_AI3_COMPACT_OUTPUT": True,
            "AGENT_SYSTEM_BASE": "test system prompt",
        }
        exec_selected(
            source,
            {"AGENT_SCHEMAS", "AGENT_ENUMS", "parse_json_object",
             "validate_agent_schema", "_collect_evidence_ids", "call_agent_json"},
            namespace,
        )
        valid_agent = {
            "status": "insufficient_evidence",
            "reported_fact": "",
            "event_date": None,
            "possible_market_channel": "unknown",
            "evidence_ids": [],
            "concise_summary": "",
            "relevant_events": [],
            "price_bias": "unknown",
            "evidence_strength": "low",
            "missing_evidence": [],
            "cautions": [],
        }

        class FakeLLM:
            def __init__(self):
                self.prompts = []

            def generate(self, _system, prompt, **_kwargs):
                self.prompts.append(prompt)
                response = dict(valid_agent)
                if len(self.prompts) == 1:
                    response["evidence_strength"] = "medium-high"
                return {
                    "text": json.dumps(response),
                    "finish_reason": "stop",
                    "model": "test-model",
                    "provider": "fake",
                }

        llm = FakeLLM()
        result = namespace["call_agent_json"](
            llm, "AI1_News_Analyst", "news role", "Return a news analysis."
        )
        self.assertEqual(result["status"], "success")
        self.assertIn('"evidence_strength": ["low", "medium", "high"]', llm.prompts[1])

    def test_exit_criteria_expected_answer_review_supports_string_and_object(self):
        source = "".join(cell_by_id(self.exit_criteria, "6059c30d")["source"])
        namespace = {"re": re}
        exec_selected(
            source,
            {"expected_answer_review_fields", "_numeric_answer_facts",
             "deterministic_numeric_answer_check"},
            namespace,
        )
        normalize = namespace["expected_answer_review_fields"]
        expected_text = "ทองคำแท่งขายออก 65,600 บาท"
        self.assertEqual(normalize(expected_text), (expected_text, []))
        self.assertEqual(
            normalize({"text": expected_text, "facts": [{"value_text": "65,600"}]}),
            (expected_text, [{"value_text": "65,600"}]),
        )
        self.assertEqual(normalize({"facts": "invalid-shape"}), ("", []))

    def test_numeric_answer_check_requires_values_and_directions(self):
        source = "".join(cell_by_id(self.exit_criteria, "6059c30d")["source"])
        self.assertIn("gt.get(\"expected_numeric_facts\")", source)
        namespace = {"re": re}
        exec_selected(
            source,
            {"expected_answer_review_fields", "_numeric_answer_facts",
             "deterministic_numeric_answer_check"},
            namespace,
        )
        check = namespace["deterministic_numeric_answer_check"]
        expected = "ลดลง 1,000 บาท และเพิ่มขึ้น 1,000 บาท; ทองคำแท่งขายออก 65,600 บาท"
        self.assertEqual(
            check(expected, "ลดลง 1,000 บาท เพิ่มขึ้น 1,000 บาท ทองคำแท่งขายออก 65,600 บาท")["coverage"],
            1.0,
        )
        wrong_direction = check(expected, "เพิ่มขึ้น 1,000 บาท เพิ่มขึ้น 1,000 บาท ทองคำแท่งขายออก 65,600 บาท")
        self.assertLess(wrong_direction["coverage"], 1.0)
        missing_value = check(expected, "ลดลง 1,000 บาท เพิ่มขึ้น 1,000 บาท")
        self.assertLess(missing_value["coverage"], 1.0)
        neutral_count = check(
            "ราคาทองเปลี่ยนแปลง 24 ครั้ง",
            "ราคาทองมีการเปลี่ยนแปลง 24 ครั้ง",
        )
        self.assertEqual(neutral_count["coverage"], 1.0)
        normalized_unit = check(
            "World Bank ใช้งบ 1.9 หมื่นล้านดอลลาร์",
            "World Bank allocated $19 billion.",
            [{"value_text": "19", "direction": "neutral"}],
        )
        self.assertEqual(normalized_unit["coverage"], 1.0)
        wrong_direction = check(
            "ราคาทองบวก 150 บาท",
            "ราคาทองเปลี่ยนแปลง 150 บาท",
            [{"value_text": "150", "direction": "up"}],
        )
        self.assertLess(wrong_direction["coverage"], 1.0)
        english_down = check(
            "ราคาทองลดลง 1,000 บาท",
            "Gold prices decreased by 1,000 baht.",
            [{"value_text": "1000", "direction": "down"}],
        )
        self.assertEqual(english_down["coverage"], 1.0)
        english_wrong_direction = check(
            "ราคาทองลดลง 1,000 บาท",
            "Gold prices increased by 1,000 baht.",
            [{"value_text": "1000", "direction": "down"}],
        )
        self.assertEqual(english_wrong_direction["coverage"], 0.0)

    def test_lead_research_manifest_preserves_primary_source_text_first(self):
        source = "".join(cell_by_id(self.exit_criteria, "5cce7a2e")["source"])
        evidence_source = "".join(cell_by_id(self.exit_criteria, "f5926591")["source"])
        namespace = {"re": re}
        exec_selected(evidence_source, {"_unique_article_sources"}, namespace)
        exec_selected(source, {"lead_research_prompt_manifest"}, namespace)
        manifest = {
            "rag_sources": [{
                "citation_id": "S1",
                "title": "Dated primary source",
                "publication_date": "2026-10-20",
                "text_excerpt": "The closing gold price changed by 650 baht.",
            }],
            "market_records": [{"evidence_id": "Q1", "large_unneeded_payload": "x" * 10000}],
            "hmm_records": [{"evidence_id": "H1"}],
            "risk_records": [{"evidence_id": "R1"}],
        }
        compact = namespace["lead_research_prompt_manifest"](manifest)
        self.assertEqual(compact["rag_sources"][0]["citation_id"], "S1")
        self.assertIn("650 baht", compact["rag_sources"][0]["text_excerpt"])
        self.assertEqual(compact["market_evidence_ids"], ["Q1"])
        self.assertNotIn("large_unneeded_payload", json.dumps(compact))

    def test_lead_manifest_deduplicates_chunks_from_the_same_article(self):
        source = "".join(cell_by_id(self.exit_criteria, "5cce7a2e")["source"])
        evidence_source = "".join(cell_by_id(self.exit_criteria, "f5926591")["source"])
        namespace = {"re": re}
        exec_selected(evidence_source, {"_unique_article_sources"}, namespace)
        exec_selected(source, {"lead_research_prompt_manifest"}, namespace)
        compact = namespace["lead_research_prompt_manifest"]({
            "rag_sources": [
                {"citation_id": "S1", "url": "https://example.test/article?chunk=1", "text_excerpt": "Closing price."},
                {"citation_id": "S2", "url": "https://example.test/article?chunk=2", "text_excerpt": "Earlier price."},
                {"citation_id": "S3", "url": "https://example.test/other", "text_excerpt": "Separate source."},
            ]
        })
        self.assertEqual([row["citation_id"] for row in compact["rag_sources"]], ["S1", "S3"])

    def test_date_matched_lead_manifest_excludes_wrong_day_and_phase_evidence(self):
        source = "".join(cell_by_id(self.exit_criteria, "5cce7a2e")["source"])
        namespace = {"re": re}
        exec_selected(
            source,
            {
                "_lead_query_dates",
                "_lead_source_matches_phase",
                "date_matched_lead_manifest",
            },
            namespace,
        )
        manifest = {
            "rag_sources": [
                {
                    "citation_id": "S1",
                    "title": "สรุปราคาทองคำ 14 ต.ค.2569 ปิดตลาด",
                    "publication_date": "2026-10-14T18:12:15+07:00",
                    "text_excerpt": "ปิดตลาด ทองแท่งขายออก 65,950 บาท อ่านข่าวเปิดตลาด -300 บาท",
                },
                {
                    "citation_id": "S5",
                    "title": "ราคา 'ทองคำ' เช้านี้",
                    "publication_date": "2026-10-14T10:17:36+07:00",
                    "text_excerpt": "เปิดตลาด -300 บาท รูปพรรณขายออก 67,000 บาท",
                },
                {
                    "citation_id": "S6",
                    "title": "ราคาทองคำ 15 ต.ค.2569",
                    "publication_date": "2026-10-15T09:00:00+07:00",
                    "text_excerpt": "เปิดตลาด -100 บาท",
                },
            ],
            "market_records": [{"evidence_id": "Q1"}],
            "hmm_records": [{"evidence_id": "H1"}],
            "risk_records": [{"evidence_id": "R1"}],
        }
        filter_manifest = namespace["date_matched_lead_manifest"]
        morning = filter_manifest(
            "เช้าวันที่ 14 ต.ค. 2569 ทองรูปพรรณขายออกเท่าไร?",
            manifest,
            {"feature_as_of": "2026-10-14", "hmm_as_of": "2026-10-13"},
        )
        self.assertEqual(
            [source["citation_id"] for source in morning["rag_sources"]],
            ["S5"],
        )
        self.assertEqual(morning["market_records"], [])
        self.assertEqual(morning["hmm_records"], [])
        self.assertEqual(morning["risk_records"], [])

        closing = filter_manifest(
            "ข่าวปิดตลาดวันที่ 14 ต.ค. 2569",
            manifest,
            {"feature_as_of": "2026-10-13", "hmm_as_of": "2026-10-14"},
        )
        self.assertEqual(
            [source["citation_id"] for source in closing["rag_sources"]],
            ["S1"],
        )
        self.assertEqual(closing["market_records"], [])
        self.assertEqual(closing["hmm_records"], [])

        manifest["rag_sources"].append({
            "citation_id": "S7",
            "title": "สรุปราคาทองคำ 23 ต.ค.2569 ปิดตลาด",
            "publication_date": "2026-10-23T18:00:00+07:00",
            "text_excerpt": "ปิดตลาด ทองแท่งขายออก 64,350 บาท",
        })
        comparison = filter_manifest(
            "เปรียบเทียบราคาปิดตลาดวันที่ 14 ต.ค. กับ 23 ต.ค. 2569",
            manifest,
            {"feature_as_of": "2026-10-23", "hmm_as_of": "2026-10-13"},
        )
        self.assertEqual(
            [source["citation_id"] for source in comparison["rag_sources"]],
            ["S1", "S7"],
        )
        self.assertEqual(comparison["market_records"], [])
        self.assertEqual(comparison["hmm_records"], [])

        feature_comparison = filter_manifest(
            "ข่าววันที่ 14 ต.ค. และข้อมูล feature ล่าสุด 13 ต.ค. 2569; HMM latent state",
            manifest,
            {"feature_as_of": "2026-10-13", "hmm_as_of": "2026-10-13"},
        )
        self.assertEqual(
            [source["citation_id"] for source in feature_comparison["rag_sources"]],
            ["S1", "S5"],
        )
        self.assertEqual([row["evidence_id"] for row in feature_comparison["market_records"]], ["Q1"])
        self.assertEqual([row["evidence_id"] for row in feature_comparison["hmm_records"]], ["H1"])

    def test_latest_feature_and_hmm_evidence_are_kept_when_news_date_differs(self):
        source = "".join(cell_by_id(self.exit_criteria, "5cce7a2e")["source"])
        namespace = {"re": re}
        exec_selected(
            source,
            {
                "_lead_query_dates",
                "_lead_source_matches_phase",
                "date_matched_lead_manifest",
            },
            namespace,
        )
        manifest = {
            "rag_sources": [],
            "market_records": [{"evidence_id": "Q1"}],
            "hmm_records": [{"evidence_id": "H1"}],
            "risk_records": [{"evidence_id": "R1"}],
        }
        filtered = namespace["date_matched_lead_manifest"](
            "ข่าววันที่ 14 ต.ค. 2569 และข้อมูล feature ล่าสุดกับ HMM state",
            manifest,
            {"feature_as_of": "2026-10-13", "hmm_as_of": "2026-10-13"},
        )
        self.assertEqual(filtered["market_records"], manifest["market_records"])
        self.assertEqual(filtered["hmm_records"], manifest["hmm_records"])

    def test_judge_invocation_uses_json_mode_and_thaillm_retry_gate(self):
        source = next(
            "".join(cell.get("source", []))
            for cell in self.exit_criteria["cells"]
            if "def _gaib_judge_invoke(" in "".join(cell.get("source", []))
        )
        observed = {}

        class FakeCompletions:
            def create(self, **kwargs):
                observed["request"] = kwargs
                return SimpleNamespace(
                    choices=[SimpleNamespace(
                        message=SimpleNamespace(
                            content='<think>discarded</think>{"result":"valid"}'
                        ),
                        finish_reason="stop",
                    )],
                    model="fake-judge",
                    usage=SimpleNamespace(
                        prompt_tokens=12,
                        completion_tokens=8,
                    ),
                )

        class FakeGate:
            def call(self, operation, max_retries=None):
                observed["max_retries"] = max_retries
                return operation(), 2

            @staticmethod
            def _status_code(_error):
                return None

        client = SimpleNamespace(
            chat=SimpleNamespace(completions=FakeCompletions())
        )
        namespace = {
            "THAILLM_CLIENTS": {"slot": client},
            "next_thaillm_client": lambda: ("slot", client),
            "THAILLM_GATE": FakeGate(),
            "API_MAX_RETRIES": 3,
            "GAIB_AI_JUDGE_SYSTEM_PROMPT": "judge system",
            "json": json,
            "re": re,
            "time": time,
        }
        exec_selected(source, {"_gaib_judge_invoke"}, namespace)
        result = namespace["_gaib_judge_invoke"](
            "judge-model", "blind_evidence", {"claim": "example"}
        )
        self.assertEqual(observed["max_retries"], 3)
        self.assertEqual(
            observed["request"]["response_format"],
            {"type": "json_object"},
        )
        self.assertEqual(observed["request"]["max_tokens"], 2400)
        self.assertEqual(result["content"], '{"result":"valid"}')
        self.assertEqual(result["api_attempt_count"], 2)
        self.assertTrue(result["json_mode"])

    def test_ai3_compact_contract_is_sent_and_schema_valid(self):
        source = "".join(cell_by_id(self.exit_criteria, "677be107")["source"])
        namespace = {"json": json, "re": re, "time": time, "THAILLM_MODEL": "test-model"}
        exec_selected(
            source,
            {"AGENT_SCHEMAS", "AGENT_ENUMS", "parse_json_object", "validate_agent_schema",
             "_collect_evidence_ids", "call_agent_json"},
            namespace,
        )
        namespace.update({
            "AGENT_SYSTEM_BASE": "system",
            "GAIB_COMPACT_OUTPUT": False,
            "GAIB_AI3_COMPACT_OUTPUT": True,
            "GAIB_TRUNCATION_RECOVERY_MODE": "none",
            "GAIB_REQUEST_DIAGNOSTICS_ENABLED": False,
            "THAILLM_MAX_TOKENS_AGENT": 900,
        })
        ai3_result = {
            "status": "insufficient_evidence",
            "as_of": None,
            "statistics": [],
            "regime_state": None,
            "feature_inputs": [],
            "tool_result_ids": [],
            "quantified_findings": [],
            "hmm_interpretation": None,
            "regime_state_id": None,
            "regime_confidence": None,
            "robustness_notes": [],
            "limitations": [],
            "recommendation_for_next_test": None,
        }

        class CapturingLLM:
            system_prompt = None

            def generate(self, system_prompt, _user_prompt, max_tokens=None):
                self.system_prompt = system_prompt
                self.max_tokens = max_tokens
                return {
                    "text": json.dumps(ai3_result),
                    "finish_reason": "stop",
                    "latency_ms": 1,
                    "attempts": 1,
                    "prompt_tokens": 2,
                    "completion_tokens": 3,
                    "total_tokens": 5,
                    "model": "test-model",
                }

        llm = CapturingLLM()
        result = namespace["call_agent_json"](
            llm,
            "AI3_Quant_Regime_Analyst",
            "quant analyst",
            "Use only provided evidence.",
        )

        self.assertTrue(result["json_valid"])
        self.assertTrue(result["schema_valid"])
        self.assertIn("AI3 concise-output rule", llm.system_prompt)
        self.assertIn("under 450 output tokens", llm.system_prompt)
        self.assertEqual(llm.max_tokens, 900)

    def test_report_renderer_adds_only_registered_citations(self):
        namespace = {"re": re}
        citation_source = "".join(
            cell_by_id(self.root_cause, "5cce7a2e").get("source", [])
        )
        exec_selected(
            citation_source,
            {"CITATION_TOKEN_RE", "citation_audit", "claim_evidence_audit", "render_evidence_report"},
            namespace,
        )
        findings = [
            {"claim": "Supported claim", "evidence_ids": ["S1"]},
            {"claim": "Missing source claim", "evidence_ids": []},
            {"claim": "Unknown source claim", "evidence_ids": ["S99", "doc1"]},
        ]
        report, audit = namespace["render_evidence_report"](
            {"evidence_based_findings": findings}, {"S1"}
        )
        self.assertIn("Supported claim [S1]", report)
        self.assertNotIn("Unknown source claim [S99]", report)
        self.assertNotIn("Missing source claim", report)
        self.assertNotIn("Unknown source claim", report)
        self.assertEqual(audit["claim_citation_coverage"], 1 / 3)
        self.assertEqual(audit["unsupported_claim_rate"], 2 / 3)
        self.assertEqual(audit["invalid_claim_evidence_ids"], ["S99", "doc1"])
        self.assertEqual(audit["citation_support_rate"], "NOT_HUMAN_REVIEWED")
        citation_audit = namespace["citation_audit"](report, {"S1"})
        self.assertEqual(citation_audit["invalid_citation_ids"], [])
        self.assertTrue(citation_audit["report_has_citations"])
        self.assertEqual(citation_audit["citation_id_valid_rate_when_present"], 1.0)
        empty_citation_audit = namespace["citation_audit"]("Claim without a citation.", {"S1"})
        self.assertFalse(empty_citation_audit["report_has_citations"])
        self.assertEqual(empty_citation_audit["citation_id_valid_rate_when_present"], "NO_CITATIONS")
        abstention_report, _ = namespace["render_evidence_report"](
            {"evidence_based_findings": [{"claim": "Unsupported claim", "evidence_ids": []}]},
            {"S1"},
        )
        self.assertIn("No cited, schema-valid evidence-based findings were produced", abstention_report)
        self.assertNotIn("Unsupported claim", abstention_report)

    def test_runtime_coverage_requires_verified_source_and_local_corpus(self):
        source = self.sources["gaib_coverage_audit_v1"]
        namespace = {
            "json": json,
            "Path": Path,
            "pd": pd,
            "display": lambda *_args, **_kwargs: None,
        }
        exec_selected(
            source,
            {"_normalized_alias", "_record_aliases", "_expected_groups",
             "_source_file_names", "audit_ground_truth_coverage"},
            namespace,
        )

        class Gate:
            def call(self, operation):
                return operation(), 1

        class FakeQdrant:
            def __init__(self, points):
                self.points = points

            def scroll(self, **_kwargs):
                return self.points, None

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / "dataset" / "news" / "fed"
            source_dir.mkdir(parents=True)
            (source_dir / "a.txt").write_text("a", encoding="utf-8")
            (source_dir / "b.txt").write_text("b", encoding="utf-8")
            output_dir = root / "output"
            output_dir.mkdir()
            retriever = SimpleNamespace(
                chunks=[{"document_id": "doc-a"}, {"document_id": "doc-b"}],
            )
            namespace.update({
                "assistant": SimpleNamespace(
                    evidence=SimpleNamespace(
                        backend_name="qdrant_cloudflare_hybrid",
                        backend=retriever,
                    )
                ),
                "QDRANT_GATE": Gate(),
                "QDRANT_COLLECTION": "test",
                "DATASET_ROOT": root / "dataset",
                "OUTPUT_DIR": output_dir,
            })
            gt = {
                "query_id": "q1",
                "split": "development",
                "query_type": "multi_evidence",
                "qdrant_index_coverage_verified": False,
                "relevance_judgments": [
                    {"document_id": "doc-a"},
                    {"document_id": "doc-b"},
                ],
                "evidence": [
                    {"document_id": "doc-a", "source_file": "a.txt"},
                    {"document_id": "doc-b", "source_file": "b.txt"},
                ],
            }
            missing = namespace["audit_ground_truth_coverage"]([gt]).iloc[0]
            self.assertEqual(missing["coverage_status"], "SOURCE_GAP")
            self.assertFalse(missing["runtime_qdrant_index_coverage_verified"])
            self.assertFalse(missing["source_spans_verified"])
            self.assertTrue(missing["source_files_present"])
            self.assertTrue(missing["bm25_corpus_match"])

            gt["evidence"] = [
                {**item, "source_span_validated_against_uploaded_corpus": True}
                for item in gt["evidence"]
            ]
            covered = namespace["audit_ground_truth_coverage"]([gt]).iloc[0]
            self.assertEqual(covered["coverage_status"], "COVERED")
            self.assertTrue(covered["source_spans_verified"])
            self.assertTrue(covered["source_files_present"])
            self.assertTrue(covered["bm25_corpus_match"])
            self.assertFalse(covered["runtime_qdrant_index_coverage_verified"])

    def test_retrieval_stage_recall_does_not_double_count_chunks(self):
        namespace = {"math": math, "np": np}
        retrieval_source = self.sources["a3a65109"]
        exec_selected(
            retrieval_source,
            {"normalized_document_alias", "candidate_document_aliases",
             "get_relevant_document_groups", "get_relevance_map", "rank_metrics"},
            namespace,
        )
        gt = {
            "relevance_judgments": [{"document_id": "doc-1", "relevance_grade": 3}],
            "evidence": [{"document_id": "doc-1", "source_url": "https://example.test/a"}],
        }
        candidates = [
            {"chunk_id": "c1", "original_id": "doc-1"},
            {"chunk_id": "c2", "url": "https://example.test/a/"},
        ]
        metrics = namespace["rank_metrics"](gt, candidates, k=40)
        self.assertEqual(metrics["known_relevant_recall@40"], 1.0)
        self.assertEqual(metrics["mrr@40"], 1.0)


if __name__ == "__main__":
    unittest.main()
