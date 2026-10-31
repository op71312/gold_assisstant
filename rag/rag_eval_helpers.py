"""Ground-truth-aware document mapping and retrieval metrics."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any


def normalize_text(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def _identifiers(record: dict[str, Any]) -> set[str]:
    return {
        str(record[key]).strip()
        for key in ("document_id", "original_id", "source_document_id", "doc_id")
        if record.get(key) not in (None, "")
    }


def build_document_mapping(
    chunks: list[dict[str, Any]],
    queries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    """Map Ground Truth document IDs to local chunk document IDs using explicit IDs/URLs."""
    alias_to_chunk_docs: dict[str, set[str]] = defaultdict(set)
    for chunk in chunks:
        physical_id = str(chunk.get("document_id") or "").strip()
        if not physical_id:
            continue
        for alias in _identifiers(chunk):
            alias_to_chunk_docs[alias].add(physical_id)
        for key in ("url", "source_url"):
            value = chunk.get(key)
            if value:
                alias_to_chunk_docs[str(value).strip()].add(physical_id)

    evidence_by_document: dict[str, dict[str, Any]] = {}
    for query in queries:
        for evidence in query.get("evidence") or []:
            document_id = str(evidence.get("document_id") or "").strip()
            if document_id and document_id not in evidence_by_document:
                evidence_by_document[document_id] = evidence

    mapping: dict[str, set[str]] = {}
    report: list[dict[str, Any]] = []
    for document_id, evidence in sorted(evidence_by_document.items()):
        candidates = set(alias_to_chunk_docs.get(document_id, set()))
        source_url = str(evidence.get("source_url") or "").strip()
        if source_url:
            candidates.update(alias_to_chunk_docs.get(source_url, set()))
        mapping[document_id] = candidates

        if len(candidates) == 1:
            status = "mapped"
        elif not candidates:
            status = "missing_from_chunk_corpus"
        else:
            status = "ambiguous_mapping"

        report.append(
            {
                "ground_truth_document_id": document_id,
                "source": evidence.get("source"),
                "source_file": evidence.get("source_file"),
                "source_url": source_url,
                "title": evidence.get("title"),
                "publication_date": evidence.get("publication_date"),
                "mapping_status": status,
                "chunk_document_ids": ";".join(sorted(candidates)),
                "chunk_count": sum(
                    1 for chunk in chunks
                    if str(chunk.get("document_id") or "").strip() in candidates
                ),
            }
        )

    return report, mapping


def query_document_coverage(
    query: dict[str, Any],
    document_mapping: dict[str, set[str]],
) -> dict[str, Any]:
    gold_ids = {
        str(evidence.get("document_id") or "").strip()
        for evidence in query.get("evidence") or []
        if evidence.get("document_id")
    }
    mapped_ids = {
        document_id
        for document_id in gold_ids
        if len(document_mapping.get(document_id, set())) == 1
    }
    missing_ids = sorted(gold_ids - mapped_ids)
    return {
        "evidence_document_count": len(gold_ids),
        "evidence_documents_mapped": len(mapped_ids),
        "evidence_document_coverage": (
            len(mapped_ids) / len(gold_ids) if gold_ids else 0.0
        ),
        "missing_evidence_document_ids": ";".join(missing_ids),
    }


def _retrieved_gold_document_ids(
    retrieved: list[dict[str, Any]],
    document_mapping: dict[str, set[str]],
) -> set[str]:
    retrieved_ids = {
        identifier
        for item in retrieved
        for identifier in _identifiers(item)
    }
    return {
        document_id
        for document_id, physical_ids in document_mapping.items()
        if document_id in retrieved_ids or physical_ids.intersection(retrieved_ids)
    }


def evaluate_one_query(
    query_record: dict[str, Any],
    retrieved: list[dict[str, Any]],
    document_mapping: dict[str, set[str]],
    k: int = 10,
) -> dict[str, Any]:
    evidence = query_record.get("evidence") or []
    gold_doc_ids = {
        str(item.get("document_id") or "").strip()
        for item in evidence
        if item.get("document_id")
    }

    retrieved_items = retrieved[:k]
    normalized_texts = []
    for item in retrieved_items:
        normalized_texts.append(normalize_text(item.get("text", "")))

    retrieved_gold_doc_ids = _retrieved_gold_document_ids(
        retrieved_items, document_mapping
    )
    document_hit = bool(gold_doc_ids & retrieved_gold_doc_ids)
    quote_text_hits = set()
    grounded_evidence_hits = set()
    for evidence_index, item in enumerate(evidence):
        quote = normalize_text(item.get("exact_quote"))
        document_id = str(item.get("document_id") or "").strip()
        if not quote:
            continue
        if any(quote in text for text in normalized_texts):
            quote_text_hits.add(evidence_index)
        physical_ids = document_mapping.get(document_id, set())
        aliases = physical_ids | {document_id}
        if any(
            quote in text and aliases.intersection(_identifiers(retrieved_item))
            for text, retrieved_item in zip(normalized_texts, retrieved_items)
        ):
            grounded_evidence_hits.add(evidence_index)

    denominator = len(evidence)
    evidence_recall = (
        len(grounded_evidence_hits) / denominator if denominator else float("nan")
    )
    quote_text_recall = (
        len(quote_text_hits) / denominator if denominator else float("nan")
    )

    first_relevant_rank = next(
        (
            rank
            for rank, item in enumerate(retrieved_items, start=1)
            if gold_doc_ids
            & _retrieved_gold_document_ids([item], document_mapping)
        ),
        None,
    )
    mrr = 1.0 / first_relevant_rank if first_relevant_rank else 0.0
    coverage = query_document_coverage(query_record, document_mapping)

    return {
        f"document_hit_at_{k}": int(document_hit),
        f"evidence_recall_at_{k}": evidence_recall,
        f"quote_text_recall_at_{k}": quote_text_recall,
        f"mrr_at_{k}": mrr,
        **coverage,
    }
