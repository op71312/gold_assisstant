import json
import unittest
from unittest.mock import patch

from web.python import gaib_pipeline


class CitationRecoveryTests(unittest.TestCase):
    def test_normalizes_bracketed_and_comma_separated_citation_ids(self):
        normalized = gaib_pipeline.normalize_citation_fields({
            "evidence_ids": "[S1], [Q2]",
            "nested": [{"tool_result_ids": ["H3", "[R4]", "not a citation"]}],
        })

        self.assertEqual(normalized["evidence_ids"], ["S1", "Q2"])
        self.assertEqual(normalized["nested"][0]["tool_result_ids"], ["H3", "R4", "not a citation"])

    def test_agent_json_validation_accepts_bracketed_citations_but_rejects_unknown_ids(self):
        class FakeLLM:
            def __init__(self, evidence_id):
                self.evidence_id = evidence_id

            def generate(self, *_args, **_kwargs):
                return {
                    "text": json.dumps({
                        "status": "available",
                        "reported_fact": "Source-backed finding.",
                        "event_date": None,
                        "possible_market_channel": "",
                        "evidence_ids": [f"[{self.evidence_id}]"],
                        "relevant_events": [],
                        "concise_summary": "",
                        "price_bias": "unknown",
                        "evidence_strength": "medium",
                        "missing_evidence": [],
                        "cautions": [],
                    }),
                    "finish_reason": "stop",
                }

        valid = gaib_pipeline.call_agent_json(
            FakeLLM("S1"), "AI1_News_Analyst", "news analyst", "Evidence [S1]",
            allowed_ids={"S1"},
        )
        self.assertTrue(valid["schema_valid"])
        self.assertEqual(valid["data"]["evidence_ids"], ["S1"])

        invalid = gaib_pipeline.call_agent_json(
            FakeLLM("S99"), "AI1_News_Analyst", "news analyst", "Evidence [S1]",
            allowed_ids={"S1"},
        )
        self.assertFalse(invalid["schema_valid"])
        self.assertIn("unknown_evidence_ids:S99", invalid["schema_errors"])

    def test_citation_audit_ignores_headings_and_requires_every_claim_cited(self):
        report = "## Evidence-based findings\n- Supported project fact [R1]"
        audit = gaib_pipeline.citation_audit(report, {"R1"})
        audit.update(gaib_pipeline.claim_evidence_audit(
            [{"claim": "Supported project fact", "evidence_ids": ["R1"]}],
            {"R1"},
        ))

        self.assertEqual(audit["citation_paragraph_coverage"], 1.0)
        self.assertTrue(gaib_pipeline.citation_audit_passes(audit))

        missing_claim_citation = gaib_pipeline.claim_evidence_audit(
            [{"claim": "Unsupported claim", "evidence_ids": []}],
            {"R1"},
        )
        self.assertFalse(gaib_pipeline.citation_audit_passes({
            **audit,
            **missing_claim_citation,
        }))

    def test_risk_fallback_uses_only_registered_project_audit_values(self):
        manifest = {
            "rag_sources": [],
            "market_records": [],
            "hmm_records": [],
            "risk_records": [
                {"name": "synthetic_portfolio_rate", "value": 1.0, "status": "WARN", "evidence_id": "R8"},
                {"name": "duplicate_transaction_id_rate", "value": 0.531, "status": "WARN", "evidence_id": "R18"},
                {"name": "unregistered_metric", "value": 99, "evidence_id": "R99"},
            ],
        }

        findings, strategy = gaib_pipeline.deterministic_citation_fallback_findings(
            "สรุปความเสี่ยงจากพอร์ต simulator",
            manifest,
        )

        self.assertEqual(strategy, "project_risk_metrics")
        self.assertEqual([item["evidence_ids"] for item in findings], [["R8"], ["R18"]])
        self.assertTrue(all(item["claim_type"] == "fact" for item in findings))

    def test_failed_lead_researcher_recovers_with_cited_project_facts(self):
        manifest = {
            "rag_sources": [],
            "market_records": [],
            "hmm_records": [],
            "risk_records": [
                {"name": "synthetic_portfolio_rate", "value": 1.0, "status": "WARN", "evidence_id": "R8"},
            ],
        }
        failed_result = {
            "status": "api_error",
            "schema_valid": False,
            "data": {},
            "metrics": {"api_success": False, "error_type": "api_error"},
        }

        with patch.object(gaib_pipeline, "call_agent_json", return_value=failed_result):
            result = gaib_pipeline.LeadResearcherAgent().run(
                None,
                "สรุปความเสี่ยงจากพอร์ต simulator",
                {},
                manifest,
                {},
                {},
                {},
                {},
            )

        self.assertEqual(result["status"], "recovered")
        self.assertTrue(result["schema_valid"])
        self.assertEqual(result["metrics"]["citation_recovery_strategy"], "project_risk_metrics")
        report, claims = gaib_pipeline.render_evidence_report(result["data"], {"R8"})
        citations = gaib_pipeline.citation_audit(report, {"R8"})
        citations.update(claims)
        self.assertTrue(gaib_pipeline.citation_audit_passes(citations))

    def test_lead_researcher_without_cited_claims_uses_verified_fallback(self):
        manifest = {
            "rag_sources": [],
            "market_records": [],
            "hmm_records": [],
            "risk_records": [
                {"name": "synthetic_portfolio_rate", "value": 1.0, "status": "WARN", "evidence_id": "R8"},
            ],
        }
        successful_but_empty = {
            "status": "success",
            "schema_valid": True,
            "data": {"evidence_based_findings": []},
            "metrics": {"api_success": True},
        }

        with patch.object(gaib_pipeline, "call_agent_json", return_value=successful_but_empty):
            result = gaib_pipeline.LeadResearcherAgent().run(
                None,
                "สรุปความเสี่ยงจากพอร์ต simulator",
                {},
                manifest,
                {},
                {},
                {},
                {},
            )

        self.assertEqual(result["status"], "recovered")
        self.assertEqual(result["metrics"]["citation_recovery_reason"], "success")
        self.assertEqual(result["metrics"]["citation_recovery_strategy"], "project_risk_metrics")

    def test_missing_evidence_does_not_create_fabricated_fallback(self):
        findings, strategy = gaib_pipeline.deterministic_citation_fallback_findings(
            "ตอบคำถามที่ไม่มีข้อมูล",
            {"rag_sources": [], "market_records": [], "hmm_records": [], "risk_records": []},
        )

        self.assertEqual(findings, [])
        self.assertEqual(strategy, "none")

    def test_hmm_fallback_cites_state_and_observation_date(self):
        manifest = {
            "rag_sources": [],
            "market_records": [],
            "hmm_records": [
                {"name": "hmm_latest_state", "value": 2, "evidence_id": "H2"},
                {"name": "hmm_latest_observation", "value": "2026-10-13", "evidence_id": "H3"},
            ],
            "risk_records": [],
        }

        findings, strategy = gaib_pipeline.deterministic_citation_fallback_findings(
            "HMM ระบุสถานะอะไร",
            manifest,
        )

        self.assertEqual(strategy, "hmm_snapshot")
        self.assertEqual(findings[0]["evidence_ids"], ["H2", "H3"])
        self.assertIn("ไม่ใช่ทิศทางราคาทอง", findings[0]["claim"])

    def test_generic_fallback_quotes_retrieved_excerpt_verbatim_with_its_source_id(self):
        excerpt = "ธนาคารกลางรายงานว่าคงอัตราดอกเบี้ยในการประชุมครั้งนี้"
        manifest = {
            "rag_sources": [
                {
                    "citation_id": "S1",
                    "title": "รายงานนโยบาย",
                    "publication_date": "2026-10-10",
                    "text_excerpt": excerpt,
                }
            ],
            "market_records": [],
            "hmm_records": [],
            "risk_records": [],
        }

        findings, strategy = gaib_pipeline.deterministic_citation_fallback_findings(
            "สรุปข่าวที่พบ",
            manifest,
        )

        self.assertEqual(strategy, "quoted_source_excerpt")
        self.assertIn(excerpt, findings[0]["claim"])
        self.assertEqual(findings[0]["evidence_ids"], ["S1"])


if __name__ == "__main__":
    unittest.main()
