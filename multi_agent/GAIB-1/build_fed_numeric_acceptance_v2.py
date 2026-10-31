"""Build a traceable, machine-constructed FOMC numeric benchmark candidate."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


GAIB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = GAIB_DIR.parents[1]
LEGACY_SOURCE_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "news"
    / "fed"
    / "fed_press_releases_cleaned"
    / "fed_press_releases_clean.jsonl"
)
ACTIVE_SOURCE_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "news"
    / "fed"
    / "fed_press_releases_cleaned_audit"
    / "fed_press_releases_classified.jsonl"
)
REAL_CORPUS_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "news"
    / "fed"
    / "fed_press_releases_cleaned"
    / "fed_press_releases_rag_chunks.jsonl"
)


def _resolve_source_path() -> Path:
    override = os.getenv("GAIB_FED_SOURCE_PATH")
    if override:
        return Path(override)
    if ACTIVE_SOURCE_PATH.exists():
        return ACTIVE_SOURCE_PATH
    if LEGACY_SOURCE_PATH.exists():
        return LEGACY_SOURCE_PATH
    return REAL_CORPUS_PATH


SOURCE_PATH = _resolve_source_path()
EXISTING_GROUND_TRUTH_PATH = GAIB_DIR / "ground_truth_fed_v1.jsonl"
OUTPUT_PATH = GAIB_DIR / "ground_truth_fed_numeric_acceptance_v2.jsonl"
MANIFEST_PATH = GAIB_DIR / "ground_truth_fed_numeric_acceptance_v2_manifest.json"
TARGET_PATTERN = re.compile(
    r"(?P<target>(?:target range for|target for) the federal funds rate)"
    r"\s+(?:at|of|to)\s+"
    r"(?P<value>[^.;\r\n]{1,80}?(?:percent|basis points?))",
    flags=re.IGNORECASE,
)
FED_URL_PREFIX = "https://www.federalreserve.gov/"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _known_source_document_ids(rows: Iterable[dict[str, Any]]) -> set[str]:
    result = set()
    for row in rows:
        for evidence in row.get("evidence") or []:
            identifier = evidence.get("document_id")
            if identifier:
                result.add(str(identifier))
    return result


def _known_source_urls(rows: Iterable[dict[str, Any]]) -> set[str]:
    result = set()
    for row in rows:
        for evidence in row.get("evidence") or []:
            for key in ("source_url", "url"):
                value = evidence.get(key)
                if value:
                    result.add(str(value).rstrip("/"))
    return result


def _record_aliases(record: dict[str, Any]) -> set[str]:
    aliases = set()
    for key in ("document_id", "source_document_id_in_uploaded_corpus", "source_document_id", "original_id"):
        value = record.get(key)
        if value:
            aliases.add(str(value))
    for key in ("source_url", "url"):
        value = record.get(key)
        if value:
            aliases.add(str(value).rstrip("/"))
    return aliases


def _valid_date(value: Any) -> str | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def build_records(
    source_rows: Iterable[dict[str, Any]],
    prior_ground_truth: Iterable[dict[str, Any]],
    target_count: int = 100,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if target_count < 1:
        raise ValueError("target_count must be positive.")
    prior_rows = list(prior_ground_truth)
    existing_ids = _known_source_document_ids(prior_rows)
    existing_urls = _known_source_urls(prior_rows)
    candidates = []
    rejected = {
        "overlapping_existing_source": 0,
        "not_fomc_statement": 0,
        "invalid_source_metadata": 0,
        "no_explicit_target_fact": 0,
    }

    for source in source_rows:
        document_id = str(source.get("document_id") or source.get("source_document_id_in_uploaded_corpus") or "")
        publication_date = _valid_date(source.get("publication_date"))
        url = str(source.get("url") or source.get("source_url") or "")
        if document_id and document_id in existing_ids:
            rejected["overlapping_existing_source"] += 1
            continue
        if url and url.rstrip("/") in existing_urls:
            rejected["overlapping_existing_source"] += 1
            continue
        title = str(source.get("title") or "")
        if not re.search(r"\bFOMC statement\b", title, flags=re.IGNORECASE):
            rejected["not_fomc_statement"] += 1
            continue
        content = str(source.get("content") or "")
        url_date_match = re.search(r"(?:monetary|fomc)(20\d{6})", url, flags=re.IGNORECASE)
        url_date = None
        if url_date_match:
            try:
                url_date = datetime.strptime(url_date_match.group(1), "%Y%m%d").date().isoformat()
            except ValueError:
                url_date = None
        if (
            not document_id
            or not publication_date
            or not url.startswith(FED_URL_PREFIX)
            or url_date != publication_date
            or not content
        ):
            rejected["invalid_source_metadata"] += 1
            continue
        match = TARGET_PATTERN.search(content)
        if not match:
            rejected["no_explicit_target_fact"] += 1
            continue
        quote = match.group(0).strip()
        start = content.find(quote)
        if start < 0 or content[start : start + len(quote)] != quote:
            rejected["invalid_source_metadata"] += 1
            continue
        candidates.append({
            "source": source,
            "publication_date": publication_date,
            "document_id": document_id,
            "quote": quote,
            "value": match.group("value").strip(),
            "target_kind": (
                "range"
                if match.group("target").casefold().startswith("target range")
                else "rate"
            ),
            "start": start,
            "end": start + len(quote),
        })

    candidates.sort(key=lambda item: (item["publication_date"], item["document_id"]))
    unique_by_group = {}
    for candidate in candidates:
        unique_by_group.setdefault(candidate["document_id"], candidate)
    candidates = list(unique_by_group.values())
    if len(candidates) < target_count:
        raise ValueError(
            f"Only {len(candidates)} unique, source-grounded cases are available; "
            f"{target_count} were requested."
        )

    # Evenly sample the chronologically ordered source groups without random labels.
    selected_indices = [
        min(len(candidates) - 1, int((index + 0.5) * len(candidates) / target_count))
        for index in range(target_count)
    ]
    selected = [candidates[index] for index in selected_indices]
    if len({item["document_id"] for item in selected}) != target_count:
        raise ValueError("Deterministic source-group sampling produced duplicate documents.")

    records = []
    for index, item in enumerate(selected, start=1):
        source = item["source"]
        document_id = item["document_id"]
        publication_date = item["publication_date"]
        quote = item["quote"]
        value = item["value"]
        group_id = f"fed:{document_id}"
        evidence_id = f"fedaccv2_{index:04d}_e1"
        unit = "basis_points" if re.search(r"basis points?", value, re.I) else "percent"
        target_label = "target range" if item["target_kind"] == "range" else "target"
        query = (
            f"What federal funds rate {target_label} did the FOMC state "
            f"on {publication_date}?"
        )
        evidence = {
            "evidence_id": evidence_id,
            "document_id": document_id,
            "source": "fed",
            "source_file": source.get("source_file") or SOURCE_PATH.name,
            "source_url": source.get("url") or source.get("source_url") or "",
            "title": source.get("title") or "",
            "publication_date": publication_date,
            "report_period": None,
            "heading": None,
            "chunk_id": None,
            "exact_quote": quote,
            "start_offset": item["start"],
            "end_offset": item["end"],
            "offset_basis": "clean_source_content",
            "source_classification": "relevant",
            "local_source_status": "present_in_uploaded_fed_corpus",
            "source_document_id_in_uploaded_corpus": document_id,
            "source_span_validated_against_uploaded_corpus": (
                source.get("content", "")[item["start"] : item["end"]] == quote
            ),
        }
        records.append({
            "schema_version": "2.0",
            "created_by": "build_fed_numeric_acceptance_v2.py",
            "query_id": f"fedaccv2_{index:04d}",
            "query": query,
            "query_language": "en",
            "query_type": "numeric_fact",
            "track": "fed",
            "split": "held_out",
            "split_group_ids": [group_id],
            "question_pattern_id": "fomc_fed_funds_target_v2_auto",
            "difficulty": "medium",
            "source_scope": ["fed"],
            "source_filter": "fed",
            "evidence": [evidence],
            "expected_answer": {
                "text": f"The stated federal funds rate {target_label} was {value}.",
                "facts": [{
                    "name": (
                        "federal_funds_target_range"
                        if item["target_kind"] == "range"
                        else "federal_funds_target_rate"
                    ),
                    "raw_value": value,
                    "value_text": value,
                    "unit": unit,
                    "period": publication_date,
                    "publication_date": publication_date,
                    "evidence_document_id": document_id,
                    "decision_action": None,
                }],
            },
            "relevance_judgments": [{
                "document_id": document_id,
                "relevance_grade": 3,
                "judgment_basis": (
                    "Machine-constructed exact source span contains the requested "
                    "date-specific target; human semantic review is still required."
                ),
            }],
            "judgment_set_exhaustive": False,
            "review_status": "source_span_validated_needs_human_semantic_review",
            "benchmark_readiness": (
                "machine_constructed_exact_span_unreviewed_index_coverage_unverified"
            ),
            "review_notes": [
                "Generated from an official Federal Reserve press-release record in the local corpus.",
                "The target phrase and character offsets were extracted and checked deterministically.",
                "This record has not received human semantic review; query clarity and answer completeness remain unverified.",
                "Qdrant index coverage is unverified until the live retrieval audit.",
                "Source document groups are disjoint from all existing GAIB-1 Ground Truth evidence.",
            ],
            "source_gap_documents": [],
            "qdrant_index_coverage_verified": False,
        })

    record_aliases = set()
    for row in records:
        for evidence in row.get("evidence") or []:
            record_aliases |= _record_aliases(evidence)
    split_overlap = {}
    for split in sorted({str(row.get("split") or "") for row in prior_rows}):
        prior_aliases = set()
        for row in prior_rows:
            if str(row.get("split") or "") != split:
                continue
            for evidence in row.get("evidence") or []:
                prior_aliases |= _record_aliases(evidence)
        split_overlap[split] = len(record_aliases & prior_aliases)
    summary = {
        "target_count": target_count,
        "candidate_count_after_source_validation": len(candidates),
        "selected_query_count": len(records),
        "unique_source_document_count": len({r["evidence"][0]["document_id"] for r in records}),
        "unique_publication_date_count": len({r["evidence"][0]["publication_date"] for r in records}),
        "existing_ground_truth_source_overlap_count": len(
            record_aliases & (existing_ids | existing_urls)
        ),
        "source_group_overlap_by_existing_split": split_overlap,
        "query_type_counts": {
            query_type: sum(row.get("query_type") == query_type for row in records)
            for query_type in sorted({row.get("query_type") for row in records})
        },
        "human_semantic_review_complete": False,
        "qdrant_index_coverage_verified": False,
        "split": "held_out",
        "rejected_source_rows": rejected,
        "date_min": records[0]["evidence"][0]["publication_date"],
        "date_max": records[-1]["evidence"][0]["publication_date"],
    }
    return records, summary


def main() -> None:
    source_rows = _read_jsonl(SOURCE_PATH)
    prior_ground_truth = _read_jsonl(EXISTING_GROUND_TRUTH_PATH)
    records, summary = build_records(source_rows, prior_ground_truth)
    OUTPUT_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
        encoding="utf-8",
    )
    manifest = {
        **summary,
        "source_path": str(SOURCE_PATH),
        "source_sha256": hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        "existing_ground_truth_sha256": hashlib.sha256(
            EXISTING_GROUND_TRUTH_PATH.read_bytes()
        ).hexdigest(),
        "output_path": str(OUTPUT_PATH),
        "output_sha256": hashlib.sha256(OUTPUT_PATH.read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
