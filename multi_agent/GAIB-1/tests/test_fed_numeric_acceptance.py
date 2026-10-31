import unittest

from build_fed_numeric_acceptance_v2 import _resolve_source_path, build_records


def source(document_id, publication_date, content, title="FOMC statement"):
    compact_date = publication_date.replace("-", "")
    return {
        "document_id": document_id,
        "title": title,
        "publication_date": publication_date,
        "url": (
            "https://www.federalreserve.gov/newsevents/pressreleases/"
            f"monetary{compact_date}a.htm"
        ),
        "content": content,
    }


class FedNumericAcceptanceTests(unittest.TestCase):
    def test_builds_exact_grounded_rows_with_disjoint_source_groups(self):
        rows = [
            source(
                f"doc-{index}",
                f"200{index}-01-31",
                "The Committee decided to maintain the target range for the federal funds rate at 0 to 1/4 percent.",
            )
            for index in range(1, 4)
        ]
        existing = [{
            "query_id": "old",
            "evidence": [{"document_id": "already-used"}],
        }]
        records, summary = build_records(rows, existing, target_count=3)
        self.assertEqual(len(records), 3)
        self.assertEqual(summary["unique_source_document_count"], 3)
        self.assertEqual(summary["existing_ground_truth_source_overlap_count"], 0)
        self.assertTrue(all(row["split"] == "held_out" for row in records))
        for row in records:
            evidence = row["evidence"][0]
            self.assertEqual(
                rows[int(row["query_id"][-4:]) - 1]["content"][
                    evidence["start_offset"] : evidence["end_offset"]
                ],
                evidence["exact_quote"],
            )
            self.assertEqual(
                row["expected_answer"]["facts"][0]["value_text"],
                "0 to 1/4 percent",
            )

    def test_excludes_existing_groups_and_non_statement_or_invalid_sources(self):
        rows = [
            source(
                "used",
                "2001-01-31",
                "The target for the federal funds rate at 5 percent.",
            ),
            source(
                "not-statement",
                "2002-01-31",
                "The target for the federal funds rate at 5 percent.",
                title="FOMC meeting schedule",
            ),
            source(
                "insecure",
                "2003-01-31",
                "The target for the federal funds rate at 5 percent.",
            ) | {"url": "http://www.federalreserve.gov/example"},
            source(
                "usable",
                "2004-01-31",
                "The Committee decided to maintain the target for the federal funds rate at 5 percent.",
            ),
        ]
        existing = [{"evidence": [{"document_id": "used"}]}]
        records, summary = build_records(rows, existing, target_count=1)
        self.assertEqual(records[0]["evidence"][0]["document_id"], "usable")
        self.assertEqual(summary["rejected_source_rows"]["overlapping_existing_source"], 1)

    def test_excludes_existing_urls_even_when_document_ids_change(self):
        url = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20040415a.htm"
        rows = [
            {
                "document_id": "live-doc-1",
                "title": "FOMC statement",
                "publication_date": "2004-04-15",
                "url": url,
                "content": "The Committee decided to maintain the target range for the federal funds rate at 1 to 1 1/4 percent.",
            }
        ]
        existing = [{
            "split": "development",
            "evidence": [{"document_id": "different-doc-id", "source_url": url}],
        }]
        with self.assertRaisesRegex(ValueError, "Only 0 unique"):
            build_records(rows, existing, target_count=1)

    def test_refuses_to_pad_insufficient_source_grounded_cases(self):
        rows = [source("one", "2001-01-31", "No target is stated.")]
        with self.assertRaisesRegex(ValueError, "Only 0 unique"):
            build_records(rows, [], target_count=1)

    def test_reports_zero_source_group_overlap_against_every_prior_split(self):
        rows = [source(
            "new-source",
            "2004-01-31",
            "The Committee decided to maintain the target for the federal funds rate at 5 percent.",
        )]
        prior = [
            {"split": "development", "evidence": [{"document_id": "dev-source"}]},
            {"split": "test", "evidence": [{"document_id": "test-source"}]},
        ]
        _, summary = build_records(rows, prior, target_count=1)
        self.assertEqual(
            summary["source_group_overlap_by_existing_split"],
            {"development": 0, "test": 0},
        )

    def test_prefers_fed_source_paths_over_general_chunking_real_corpus(self):
        resolved = str(_resolve_source_path())
        self.assertIn("fed", resolved.lower())
        self.assertNotIn("chunks_structure_aware_real", resolved)
        self.assertTrue("fed_press_releases" in resolved or "fed_press_releases_cleaned" in resolved)


if __name__ == "__main__":
    unittest.main()
