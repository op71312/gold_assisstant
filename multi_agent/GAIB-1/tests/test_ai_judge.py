import json
import unittest

from gaib1_ai_judge import (
    SYSTEM_PROMPT,
    _blind_payload,
    _json_object,
    build_human_review_template,
    build_policy_gates,
    compute_calibration_metrics,
    compute_judge_quality_metrics,
    evaluate_claims,
    extract_claims,
    select_calibration_claims,
    validate_claim_judgment,
)


def valid_judgment(claim_id, claim_text, claim_type="numeric", correctness="supported"):
    return {
        "claim_id": claim_id,
        "claim_text": claim_text,
        "claim_type": claim_type,
        "supporting_citation_ids": ["S1"],
        "evidence_span_ids": ["S1:span-1"],
        "correctness": correctness,
        "citation_entailment": "entailed",
        "completeness": "complete",
        "severity": "critical" if claim_type == "numeric" else "minor",
        "confidence": 95,
        "rationale": "S1 directly states the claim.",
        "abstention_quality": "not_applicable",
    }


class AiJudgeTests(unittest.TestCase):
    def test_blind_judge_requires_abstention_quality_for_every_claim(self):
        payload = _blind_payload(
            "What was the price?",
            {
                "claim_id": "q1:claim-1",
                "claim_text": "The price was 100 baht.",
                "claim_type": "numeric",
                "is_abstention": False,
            },
            [],
        )
        self.assertIn("Always include abstention_quality", SYSTEM_PROMPT)
        self.assertTrue(any(
            "use not_applicable for a non-abstention claim" in rule
            for rule in payload["rules"]
        ))

    def test_json_object_parser_extracts_structured_response_from_prose(self):
        raw = '''
The user wants me to act as a blinded evaluator.
JSON Construction:
* claim_id: "q1:claim-1"
* claim_text: "The target range is 1 to 2 percent."
* claim_type: "numeric"
* supporting_citation_ids: ["S1"]
* evidence_span_ids: ["S1:span-1"]
* correctness: "supported"
* citation_entailment: "entailed"
* completeness: "complete"
* severity: "major"
* confidence: 92
* rationale: "Direct evidence in S1." 
* abstention_quality: "not_applicable"
No more commentary.
'''
        parsed = _json_object(raw)
        self.assertEqual(parsed["claim_id"], "q1:claim-1")
        self.assertEqual(parsed["correctness"], "supported")
        self.assertEqual(parsed["supporting_citation_ids"], ["S1"])

    def test_extracts_every_bullet_and_does_not_count_no_claims_as_success(self):
        claims = extract_claims(
            "run1",
            "q1",
            "## Findings\n- Fact one with enough descriptive text. [S1]\n* Fact two with enough descriptive text. [S2]",
            "ANSWERED",
        )
        self.assertEqual(len(claims), 2)
        self.assertEqual(claims[0]["claim_type"], "attributed" if "stated" in claims[0]["claim_text"] else "explanation")
        abstention = extract_claims("run1", "q2", "## Findings\nNo claims.", "NO_CLAIMS")
        self.assertEqual(len(abstention), 1)
        self.assertTrue(abstention[0]["is_abstention"])
        self.assertEqual(abstention[0]["claim_type"], "abstention")
        paragraph = extract_claims(
            "run1",
            "q3",
            "## Summary\nThe retrieved report states that inflation remained elevated during this period.",
            "ANSWERED",
        )
        self.assertEqual(len(paragraph), 1)
        self.assertFalse(paragraph[0]["is_abstention"])

    def test_rubric_rejects_unknown_evidence_references(self):
        judgment = valid_judgment("q1:claim", "The target range is 1 to 2 percent.")
        errors = validate_claim_judgment(
            judgment,
            "q1:claim",
            {"S1"},
            {"S1:span-1"},
        )
        self.assertEqual(errors, [])
        judgment["evidence_span_ids"] = ["S9:span-1"]
        self.assertIn(
            "unknown_evidence_span_reference",
            validate_claim_judgment(judgment, "q1:claim", {"S1"}, {"S1:span-1"}),
        )

    def test_evidence_judging_does_not_conflate_the_query_oracle_with_claim_support(self):
        seen = []

        def invoke(model, phase, payload):
            seen.append((model, phase, payload))
            claim = payload["claim"]
            claim_id = claim["claim_id"]
            claim_text = claim["claim_text"]
            return json.dumps(valid_judgment(claim_id, claim_text))

        judgments, calls = evaluate_claims(
            run_id="run1",
            run_rows=[{
                "query_id": "q1",
                "query": "What target range?",
                "query_type": "numeric_fact",
                "final_report": "- The target range is 1 to 2 percent. [S1]",
                "answer_status": "ANSWERED",
                "expected_fact_coverage": 1.0,
                "all_citation_ids_valid": True,
                "evidence_span_in_final_context": True,
            }],
            ground_truth_by_id={
                "q1": {
                    "query_id": "q1",
                    "query": "What target range?",
                    "query_type": "numeric_fact",
                    "expected_answer": {"facts": [{"value_text": "1 to 2 percent"}]},
                }
            },
            run_details_by_id={
                "q1": {
                    "evidence_sources": [{
                        "citation_id": "S1",
                        "text_excerpt": "The target range is 1 to 2 percent.",
                    }]
                }
            },
            primary_model="judge-a",
            generator_model="generator",
            invoke=invoke,
        )
        self.assertEqual([call[1] for call in seen], ["blind_evidence"])
        self.assertNotIn("expected_answer", seen[0][2])
        self.assertTrue(any("exact ID verbatim in rationale" in rule for rule in seen[0][2]["rules"]))
        self.assertTrue(any("do not paraphrase" in rule for rule in seen[0][2]["rules"]))
        self.assertEqual(judgments[0]["judge_status"], "PASS")
        self.assertFalse(judgments[0]["expected_fact_required"])
        self.assertEqual(judgments[0]["final_judgment_status"], "PASS")
        self.assertFalse(judgments[0]["second_judge_required"])
        self.assertTrue(all(call["schema_valid"] for call in calls))

    def test_blind_judge_repairs_mechanical_schema_errors_once(self):
        phases = []
        claim_text = "The target range is 1 to 2 percent. [S1]"

        def invoke(model, phase, payload):
            phases.append(phase)
            if phase == "blind_evidence":
                judgment = valid_judgment("q1:claim-1", "Paraphrased claim.")
                judgment["rationale"] = "The source supports this."
                return json.dumps(judgment)
            claim = payload["original_evaluation"]["claim"]
            return json.dumps(valid_judgment(claim["claim_id"], claim["claim_text"]))

        judgments, calls = evaluate_claims(
            run_id="run1",
            run_rows=[{
                "query_id": "q1",
                "query": "What target range?",
                "final_report": f"- {claim_text}",
                "answer_status": "ANSWERED",
            }],
            ground_truth_by_id={"q1": {"query": "What target range?"}},
            run_details_by_id={
                "q1": {
                    "evidence_sources": [{
                        "citation_id": "S1",
                        "text_excerpt": "The target range is 1 to 2 percent.",
                    }]
                }
            },
            primary_model="judge-a",
            invoke=invoke,
        )
        self.assertEqual(phases, ["blind_evidence", "blind_evidence_schema_repair"])
        self.assertEqual([call["schema_valid"] for call in calls], [False, True])
        self.assertEqual(judgments[0]["judge_status"], "PASS")
        self.assertEqual(judgments[0]["blind_judgment"]["claim_text"], claim_text)

    def test_correctness_metric_uses_evidence_judgment_not_query_fact_coverage(self):
        metrics = compute_judge_quality_metrics(
            [{
                "is_abstention": False,
                "query_type": "numeric_fact",
                "judge_status": "PASS",
                "correctness": "supported",
                "citation_entailment": "entailed",
                "completeness": "incomplete",
                "expected_fact_required": False,
                "deterministic_numeric_status": "FAIL",
            }],
            [{"schema_valid": True}],
        )
        self.assertEqual(metrics["ai_judge_correctness_rate"], 1.0)
        self.assertEqual(metrics["answer_completeness_rate"], 0.0)

    def test_second_judge_escalation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Second-judge escalation"):
            evaluate_claims(
                run_id="run1",
                run_rows=[],
                ground_truth_by_id={},
                run_details_by_id={},
                primary_model="judge-a",
                second_model="judge-b",
                generator_model="generator",
                invoke=lambda *_args: None,
            )

    def test_stratified_calibration_template_never_invents_claims(self):
        rows = []
        for claim_type in ("numeric", "attributed", "explanation"):
            for index in range(10):
                rows.append({
                    "claim_id": f"{claim_type}-{index}",
                    "claim_type": claim_type,
                    "judge_status": "PASS",
                    "judge_confidence": 95,
                    "correctness": "supported",
                    "citation_entailment": "entailed",
                })
        rows.extend({
            "claim_id": f"uncertain-{index}",
            "claim_type": "other",
            "judge_status": "FAIL",
            "judge_confidence": 50,
            "correctness": "insufficient_evidence",
            "citation_entailment": "partial",
        } for index in range(10))
        rows.extend({
            "claim_id": f"pass-{index}",
            "claim_type": "other",
            "judge_status": "PASS",
            "judge_confidence": 95,
            "correctness": "supported",
            "citation_entailment": "entailed",
        } for index in range(10))
        selected = select_calibration_claims(rows, "fixed-seed")
        self.assertEqual(len(selected), 50)
        template = build_human_review_template(selected, "run1")
        double_review_ids = {
            row["claim_id"] for row in template if row["reviewer_slot"] == "B"
        }
        self.assertEqual(len(double_review_ids), 10)
        self.assertEqual(len({row["claim_id"] for row in selected}), 50)
        self.assertEqual(
            len(select_calibration_claims(rows[:7], "fixed-seed")),
            7,
        )

    def test_human_calibration_requires_explicit_independent_labels(self):
        judgments = [{
            "claim_id": f"c{i}",
            "correctness": "supported",
            "citation_entailment": "entailed",
            "completeness": "complete",
            "severity": "critical" if i < 10 else "minor",
            "judge_status": "PASS",
            "final_judgment_status": "PASS",
        } for i in range(50)]
        human_rows = []
        for i in range(50):
            reviewers = ("A", "B") if i < 10 else ("A",)
            for slot in reviewers:
                human_rows.append({
                    "claim_id": f"c{i}",
                    "reviewer_id": f"reviewer-{slot}",
                    "human_correctness": "supported",
                    "citation_supported": "yes",
                    "completeness": "complete",
                    "unsupported_critical_claim": "no",
                    "used_for_judge_prompt_development": "no",
                })
        metrics = compute_calibration_metrics(judgments, human_rows)
        self.assertEqual(metrics["reviewed_claim_count"], 50)
        self.assertEqual(metrics["double_reviewed_claim_count"], 10)
        self.assertEqual(metrics["supported_unsupported_agreement"], 1.0)
        self.assertEqual(metrics["supported_unsupported_kappa"], 1.0)
        self.assertEqual(metrics["prompt_development_overlap_count"], 0)
        human_rows[0]["used_for_judge_prompt_development"] = "yes"
        self.assertGreater(
            compute_calibration_metrics(judgments, human_rows)["prompt_development_overlap_count"],
            0,
        )

    def test_quality_correctness_is_evidence_focused_and_grouped_by_query_type(self):
        judgments = [
            {
                "claim_id": "numeric-matched",
                "query_type": "numeric_fact",
                "correctness": "supported",
                "judge_status": "PASS",
                "deterministic_numeric_status": "PASS",
                "expected_fact_required": True,
                "expected_fact_judgment": {"expected_fact_status": "matched"},
            },
            {
                "claim_id": "numeric-mismatch",
                "query_type": "numeric_fact",
                "correctness": "supported",
                "judge_status": "PASS",
                "deterministic_numeric_status": "PASS",
                "expected_fact_required": True,
                "expected_fact_judgment": {"expected_fact_status": "mismatch"},
            },
            {
                "claim_id": "explanation",
                "query_type": "explanation",
                "correctness": "supported",
                "judge_status": "PASS",
                "deterministic_numeric_status": "NOT_APPLICABLE",
                "expected_fact_required": False,
                "completeness": "incomplete",
                "citation_entailment": "not_entailed",
            },
        ]
        metrics = compute_judge_quality_metrics(judgments, [])
        self.assertEqual(metrics["ai_judge_correctness_rate"], 1.0)
        self.assertEqual(
            metrics["correctness_by_query_type"],
            {"explanation": 1.0, "numeric_fact": 1.0},
        )

    def test_missing_expected_fact_judgment_fails_closed_without_crashing(self):
        metrics = compute_judge_quality_metrics(
            [
                {
                    "claim_id": "numeric-unjudged",
                    "query_type": "numeric_fact",
                    "correctness": "supported",
                    "judge_status": "PASS",
                    "expected_fact_required": True,
                    "expected_fact_judgment": None,
                }
            ],
            [],
        )

        self.assertEqual(metrics["expected_fact_comparison_count"], 0)
        self.assertEqual(metrics["expected_fact_comparison_required_count"], 1)
        self.assertEqual(metrics["expected_fact_match_rate"], 0.0)
        self.assertEqual(metrics["fully_judged_claim_count"], 0)

    def test_practical_policy_gates_distinguish_development_from_release(self):
        common = {
            "query_count": 21,
            "eligible_query_count": 21,
            "retrieval_metrics": {
                "reranked_known_relevant_recall@10": 0.9,
                "reranked_mrr@10": 0.7,
            },
            "quality_metrics": {
                "agent_json_parse_rate": 0.98,
                "ai_judge_correctness_rate": 0.90,
                "ai_judge_citation_entailment_rate": 0.90,
                "citation_id_validity_rate": 1.0,
                "unsupported_critical_numeric_claim_count": 0,
                "critical_truncation_count": 0,
                "judge_timeout_count": 0,
            },
            "calibration_metrics": {"reviewed_claim_count": 0},
            "latency_metrics": {"judge_p95_ms": 1000, "judge_timeout_ms": 30000},
            "baseline_comparison_complete": False,
            "primary_model": "judge-a",
            "second_model": "",
            "generator_model": "generator",
            "index_version": "idx-1",
            "deterministic_numeric_failures": 0,
            "source_coverage_complete": True,
            "run_integrity_pass": True,
        }
        development = build_policy_gates(
            split="development",
            dataset_readiness="development_only",
            human_review_complete=False,
            **common,
        )
        self.assertEqual(development["decision"], "DEVELOPMENT_PASS")
        self.assertEqual(development["release_tier"], "development_benchmark_only")
        self.assertEqual(
            development["gates"]["human_spot_check_10_to_20_claims"],
            "NOT_REQUIRED_FOR_DEVELOPMENT",
        )

        failing = dict(common)
        failing["retrieval_metrics"] = {
            "reranked_known_relevant_recall@10": 0.80,
            "reranked_mrr@10": 0.70,
        }
        no_go = build_policy_gates(split="development", **failing)
        self.assertEqual(no_go["decision"], "NO-GO")
        self.assertEqual(no_go["gates"]["document_recall_at_10_min_085"], "FAIL")

        release_common = dict(common)
        release_common["calibration_metrics"] = {"reviewed_claim_count": 15}
        approved = build_policy_gates(
            split="validation",
            dataset_readiness="human_reviewed",
            human_review_complete=True,
            **release_common,
        )
        self.assertEqual(approved["decision"], "GO")

        unreviewed = build_policy_gates(
            split="validation",
            dataset_readiness="development_only",
            human_review_complete=False,
            **common,
        )
        self.assertEqual(unreviewed["decision"], "NO-GO")
        self.assertEqual(unreviewed["gates"]["ground_truth_human_review_complete"], "FAIL")


if __name__ == "__main__":
    unittest.main()
