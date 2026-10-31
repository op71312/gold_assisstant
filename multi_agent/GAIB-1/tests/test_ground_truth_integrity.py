import json
import math
import sys
import unittest
from pathlib import Path

import pandas as pd
import numpy as np


GAIB_DIR = Path(__file__).resolve().parents[1]
ROOT = GAIB_DIR.parents[1]
sys.path.insert(0, str(GAIB_DIR))

import build_gaib_benchmark as builder


def load_jsonl(path):
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


class GroundTruthIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.write_reports()

    def test_fed_counts_ids_and_original_splits_are_preserved(self):
        source = load_jsonl(ROOT / "multi_agent" / "gt" / "ground_truth_fed_v1.jsonl")
        built = load_jsonl(GAIB_DIR / "ground_truth_fed_v1.jsonl")
        self.assertEqual(len(source), 43)
        self.assertEqual(len(built), 43)
        self.assertEqual(len({row["query_id"] for row in built}), 43)
        self.assertEqual(
            {row["query_id"]: row["split"] for row in source},
            {row["query_id"]: row["split"] for row in built},
        )
        self.assertTrue(all(row["track"] == "fed" for row in built))

    def test_source_ready_quotes_map_to_local_chunks_without_claiming_qdrant(self):
        ready = load_jsonl(GAIB_DIR / "ground_truth_fed_ready_v1.jsonl")
        self.assertEqual(len(ready), 37)
        mapping = builder.inspect_fed_mapping(ready)
        self.assertEqual(mapping["mapped_query_count"], 37)
        self.assertEqual(mapping["unmapped_query_ids"], [])
        self.assertEqual(mapping["quote_mismatch_query_ids"], [])
        self.assertEqual(mapping["qdrant_index_coverage"], "UNVERIFIED")
        self.assertTrue(all(row.get("qdrant_index_coverage_verified") is False for row in ready))

    def test_source_gaps_are_isolated_and_blocked(self):
        gaps = load_jsonl(GAIB_DIR / "ground_truth_fed_source_gaps_v1.jsonl")
        ready = load_jsonl(GAIB_DIR / "ground_truth_fed_ready_v1.jsonl")
        self.assertEqual(len(gaps), 6)
        self.assertTrue(all(row["benchmark_status"] == "BLOCKED" for row in gaps))
        self.assertFalse({row["query_id"] for row in gaps} & {row["query_id"] for row in ready})

    def test_unbuilt_tracks_are_explicitly_blocked(self):
        validation = json.loads((GAIB_DIR / "validation_report.json").read_text(encoding="utf-8"))
        self.assertEqual(validation["retrieval_metric_logic"], "document_identity_aliases_v2")
        self.assertTrue(validation["legacy_114_query_results_require_rescoring"])
        self.assertTrue(
            any(check["id"] == "retrieval_metric_document_identity" and check["status"] == "PASS"
                for check in validation["checks"])
        )
        for track in ("quant", "hmm", "portfolio", "multi_agent"):
            self.assertEqual(validation["track_status"][track]["status"], "BLOCKED")
            self.assertFalse((GAIB_DIR / f"ground_truth_{track}_v1.jsonl").exists())

    def test_experiment_notebook_is_gated_and_uses_development_split(self):
        notebook = json.loads(
            (GAIB_DIR / "Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb").read_text(
                encoding="utf-8"
            )
        )
        sources = ["".join(cell.get("source", [])) for cell in notebook["cells"]]
        joined = "\n".join(sources)
        markdown = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook["cells"]
            if cell.get("cell_type") == "markdown"
        )
        self.assertIn('os.getenv("GAIB_BENCHMARK_SPLIT", "development")', joined)
        self.assertNotIn("GAIB_ALLOW_API_BENCHMARKS", joined)
        self.assertIn('if RUN_RETRIEVAL_BENCHMARK and GROUND_TRUTH:', sources[29])
        self.assertIn('if RUN_AGENT_BENCHMARK:', sources[31])
        self.assertIn("GAIB_ALLOW_TEST_SPLIT", joined)
        self.assertIn("ground_truth_fed_ready_v1.jsonl", joined)
        self.assertIn('OUTPUT_DIR = PROJECT_ROOT / "multi_agent" / "GAIB-1" / "runs"', joined)
        self.assertIn("benchmark_run_manifest.json", joined)
        self.assertTrue(all(not cell.get("outputs") and cell.get("execution_count") is None
                            for cell in notebook["cells"] if cell.get("cell_type") == "code"))
        self.assertNotIn("embedding/embedding/ground_truth_queries_v2.jsonl", joined)
        self.assertIn("p95_ms", sources[29])
        self.assertIn("multiagent_latency_percentiles.csv", sources[31])
        self.assertIn('select_dtypes(include="number")', sources[29])
        self.assertNotIn('describe(include="all")', sources[29])
        self.assertIn("if RUN_AGENT_BENCHMARK or RUN_LIVE_DEMO:", sources[23])
        self.assertIn('assistant.evidence.backend_name != "qdrant_cloudflare_hybrid"', sources[23])
        self.assertIn("fallback is intentionally disabled", sources[23])
        self.assertIn('assistant.evidence.backend_name != "qdrant_cloudflare_hybrid"', sources[31])
        self.assertNotIn("???", markdown)
        self.assertNotIn("\ufffd", markdown)
        self.assertIn("API key rotation, concurrency and rate limits", markdown)
        self.assertIn("Deterministic Quant snapshot", markdown)
        for cell_index in (3, 23, 27, 29, 31):
            compile(sources[cell_index], f"gaib_notebook_cell_{cell_index}", "exec")

    def test_notebook_loader_selects_only_development_ready_records(self):
        notebook = json.loads(
            (GAIB_DIR / "Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb").read_text(
                encoding="utf-8"
            )
        )
        source = "".join(notebook["cells"][27]["source"])
        namespace = {
            "GAIB_GT_ALL_PATH": ROOT / "multi_agent" / "gt" / "ground_truth_fed_v1.jsonl",
            "GAIB_GT_READY_PATH": ROOT / "multi_agent" / "gt" / "ground_truth_fed_ready_v1.jsonl",
            "GAIB_GT_GAPS_PATH": ROOT / "multi_agent" / "gt" / "ground_truth_fed_source_gaps_v1.jsonl",
            "GAIB_BENCHMARK_SPLIT": "development",
            "read_jsonl": builder.read_jsonl,
            "pd": pd,
            "display": lambda _: None,
        }
        exec(compile(source, "gaib_ground_truth_loader", "exec"), namespace)
        self.assertEqual(len(namespace["GROUND_TRUTH"]), 6)
        self.assertTrue(all(row["split"] == "development" for row in namespace["GROUND_TRUTH"]))
        self.assertEqual(len(namespace["GROUND_TRUTH_SOURCE_GAPS"]), 6)

    def test_enabling_agent_benchmark_initializes_remote_backend_without_second_opt_in(self):
        notebook = json.loads(
            (GAIB_DIR / "Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb").read_text(
                encoding="utf-8"
            )
        )
        source = "".join(notebook["cells"][23]["source"])

        class FakeAssistant:
            def __init__(self):
                self.evidence = type(
                    "Evidence",
                    (),
                    {
                        "ready": True,
                        "backend_name": "qdrant_cloudflare_hybrid",
                        "backend": type("Backend", (), {"chunks": [1, 2, 3]})(),
                    },
                )()

        namespace = {
            "RUN_AGENT_BENCHMARK": True,
            "RUN_LIVE_DEMO": False,
            "CF_ACCOUNT_ID": "configured",
            "CF_API_TOKEN": "configured",
            "QDRANT_URL": "configured",
            "QDRANT_API_KEY": "configured",
            "JINA_API_KEYS": ["configured"],
            "LOCAL_NEWS_DIR": None,
            "THAILLM_API_KEYS": ["configured"],
            "GoldAssistantMultiAgent": FakeAssistant,
            "print": lambda *args, **kwargs: None,
        }
        exec(compile(source, "gaib_remote_setup", "exec"), namespace)
        self.assertIsInstance(namespace["assistant"], FakeAssistant)

    def test_asset_inventory_explains_non_tabular_row_counts(self):
        notebook = json.loads(
            (GAIB_DIR / "Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb").read_text(
                encoding="utf-8"
            )
        )
        source = "".join(notebook["cells"][5]["source"])
        self.assertNotIn('"rows":None', source)
        self.assertIn('"rows":"N/A (model bundle; not a row-based table)"', source)
        self.assertIn('"rows":"See simulator table counts below"', source)
        self.assertIn('"rows":"N/A (chunk corpus; not a single table)"', source)
        self.assertIn('"rows":"N/A (directory; not a table)"', source)
        self.assertIn('file_inventory["rows"] = file_inventory["rows"].fillna("N/A (not applicable)")', source)
        compile(source, "gaib_asset_inventory", "exec")

    def test_retrieval_metrics_match_original_id_and_source_url_aliases(self):
        notebook = json.loads(
            (GAIB_DIR / "Gold_Assistant_5_Agent_Collaborative_Pipeline_GAIB1.ipynb").read_text(
                encoding="utf-8"
            )
        )
        source = "".join(notebook["cells"][29]["source"])
        start = source.index("def normalized_document_alias")
        end = source.index("def write_latency_percentiles", start)
        namespace = {"math": math, "np": np}
        exec(compile(source[start:end], "gaib_retrieval_metrics", "exec"), namespace)
        ground_truth = {
            "relevance_judgments": [{"document_id": "expected-document", "relevance_grade": 3}],
            "evidence": [
                {
                    "document_id": "expected-document",
                    "source_url": "https://example.test/source",
                }
            ],
        }
        unrelated = {"document_id": "unrelated", "original_id": "other-document"}
        original_id_match = {
            "document_id": "hashed-qdrant-document",
            "original_id": "expected-document",
        }
        url_match = {
            "document_id": "different-hash",
            "url": "https://example.test/source/",
        }
        rank_by_original_id = namespace["rank_metrics"](
            ground_truth, [unrelated, original_id_match], k=10
        )
        self.assertEqual(rank_by_original_id["known_relevant_recall@10"], 1.0)
        self.assertEqual(rank_by_original_id["mrr@10"], 0.5)
        rank_by_url = namespace["rank_metrics"](ground_truth, [url_match], k=10)
        self.assertEqual(rank_by_url["known_relevant_recall@10"], 1.0)
        self.assertEqual(rank_by_url["mrr@10"], 1.0)


if __name__ == "__main__":
    unittest.main()
