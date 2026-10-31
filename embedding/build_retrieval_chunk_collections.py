"""Build deterministic chunk collections for the retrieval evaluation notebook."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


METHODS = (
    "existing_baseline",
    "recursive_fixed",
    "structure_aware",
    "semantic",
    "adaptive",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(row)
    return rows


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def split_fixed(text: str, size: int = 1200, overlap: int = 180) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = max(
                text.rfind("\n", start + size // 2, end),
                text.rfind(" ", start + size // 2, end),
            )
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def split_paragraphs(text: str, size: int) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        parts = [paragraph] if len(paragraph) <= size else split_fixed(paragraph, size, 0)
        for part in parts:
            candidate = f"{current}\n\n{part}" if current else part
            if current and len(candidate) > size:
                chunks.append(current)
                current = part
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks


def split_sentences(text: str, size: int = 1000, hard_limit: int = 1500) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        sentences = re.split(r"(?<=[.!?。！？])\s+|(?<=ฯ)\s+", paragraph)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) > hard_limit:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.extend(split_fixed(sentence, size, 0))
                continue
            candidate = f"{current} {sentence}" if current else sentence
            if current and len(candidate) > size:
                chunks.append(current)
                current = sentence
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks


def source_text(raw: dict[str, Any], dataset: str) -> str:
    if dataset in {"bls_cpi", "bls_nfp"}:
        sections = raw.get("chunks") or []
        return "\n\n".join(
            str(section.get("content") or "").strip()
            for section in sections
            if str(section.get("content") or "").strip()
        )
    return str(raw.get("content") or "").strip()


def make_chunks(
    method: str,
    document: dict[str, Any],
) -> list[dict[str, Any]]:
    raw = document["raw_data"]
    dataset = document["dataset"]
    document_id = str(raw.get("document_id") or raw.get("doc_id") or raw.get("article_id") or document["record_id"])
    title = str(raw.get("title") or "").strip()
    source = dataset
    text = source_text(raw, dataset)

    if method == "existing_baseline" and dataset in {"bls_cpi", "bls_nfp"}:
        original_chunks = raw.get("chunks") or []
        pieces = [
            (
                str(part.get("heading") or "").strip(),
                str(part.get("content") or "").strip(),
                str(part.get("chunk_id") or "").strip(),
            )
            for part in original_chunks
            if str(part.get("content") or "").strip()
        ]
    elif method == "recursive_fixed":
        pieces = [("", part, "") for part in split_fixed(text)]
    elif method == "structure_aware":
        if dataset in {"bls_cpi", "bls_nfp"}:
            pieces = [
                (
                    str(part.get("heading") or "").strip(),
                    str(part.get("content") or "").strip(),
                    "",
                )
                for part in raw.get("chunks") or []
                if str(part.get("content") or "").strip()
            ]
        else:
            pieces = [("", part, "") for part in split_paragraphs(text, 1800)]
    elif method == "semantic":
        pieces = [("", part, "") for part in split_sentences(text)]
    elif method == "adaptive":
        size = 1600 if len(text) <= 3000 else 1200 if len(text) <= 10000 else 900
        pieces = [("", part, "") for part in split_paragraphs(text, size)]
    elif method == "existing_baseline":
        pieces = [("", part, "") for part in split_fixed(text, size=1200, overlap=0)]
    else:
        raise ValueError(f"Unknown chunking method: {method}")

    chunks = []
    for index, (heading, content, original_id) in enumerate(pieces, start=1):
        content = content.strip()
        if not content:
            continue
        chunk_id = original_id or f"{document_id}_{method}_{index:04d}"
        chunks.append(
            {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source": source,
                "source_file": raw.get("source_file") or document.get("source_file"),
                "source_url": raw.get("source_url") or raw.get("url"),
                "title": title,
                "heading": heading,
                "publication_date": raw.get("publication_date") or raw.get("published_at"),
                "report_period": raw.get("report_period"),
                "content": content,
                "embedding_text": "\n".join(value for value in (title, heading, content) if value),
                "chunk_method": method,
                "chunk_index": index,
            }
        )
    return chunks


def build_collections(project_root: Path) -> dict[str, int]:
    source_path = project_root / "dataset" / "ground_truth_source_data_4_datasets.jsonl"
    ground_truth_path = project_root / "embedding" / "embedding" / "ground_truth_queries_v2.jsonl"
    output_dir = project_root / "artifacts" / "chunking_benchmark"
    if not source_path.is_file():
        raise FileNotFoundError(f"Raw source sample not found: {source_path}")
    if not ground_truth_path.is_file():
        raise FileNotFoundError(f"Ground Truth file not found: {ground_truth_path}")

    documents = read_jsonl(source_path)
    document_map: dict[str, dict[str, Any]] = {}
    for document in documents:
        raw = document.get("raw_data") or {}
        document_id = str(
            raw.get("document_id") or raw.get("doc_id") or raw.get("article_id") or document.get("record_id") or ""
        ).strip()
        if not document_id:
            raise ValueError(f"Source record has no document ID: {document.get('record_id')}")
        if document_id in document_map:
            raise ValueError(f"Duplicate source document ID: {document_id}")
        document["document_id"] = document_id
        document_map[document_id] = document

    ground_truth = read_jsonl(ground_truth_path)
    evidence_by_document: dict[str, list[str]] = {}
    for query in ground_truth:
        for evidence in query.get("evidence") or []:
            document_id = str(evidence.get("document_id") or "").strip()
            if document_id:
                evidence_by_document.setdefault(document_id, []).append(
                    str(evidence.get("exact_quote") or "")
                )
    missing_documents = sorted(set(evidence_by_document) - set(document_map))
    if missing_documents:
        raise ValueError(
            "The raw sample does not contain all Ground Truth evidence documents: "
            + ", ".join(missing_documents)
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    method_chunks: dict[str, list[dict[str, Any]]] = {}
    for method in METHODS:
        chunks = [
            chunk
            for document in documents
            for chunk in make_chunks(method, document)
        ]
        if not chunks:
            raise ValueError(f"No chunks generated for method {method}")
        by_document: dict[str, list[str]] = {}
        for chunk in chunks:
            by_document.setdefault(chunk["document_id"], []).append(chunk["content"])
        for document_id, quotes in evidence_by_document.items():
            corpus_text = " ".join(by_document.get(document_id, []))
            normalized_corpus = normalize_text(corpus_text)
            missing_quotes = [
                quote
                for quote in quotes
                if quote and normalize_text(quote) not in normalized_corpus
            ]
            if missing_quotes:
                raise ValueError(
                    f"{method} failed to preserve {len(missing_quotes)} evidence quotes "
                    f"from {document_id}"
                )
        method_chunks[method] = chunks
        counts[method] = len(chunks)

    for method, chunks in method_chunks.items():
        target = output_dir / f"chunks_{method}.jsonl"
        temporary = target.with_suffix(target.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as file:
            for chunk in chunks:
                file.write(json.dumps(chunk, ensure_ascii=False, separators=(",", ":")) + "\n")
        temporary.replace(target)

    manifest = {
        "generator": "embedding/build_retrieval_chunk_collections.py",
        "source_file": str(source_path.relative_to(project_root)),
        "ground_truth_file": str(ground_truth_path.relative_to(project_root)),
        "document_count": len(documents),
        "ground_truth_evidence_document_count": len(evidence_by_document),
        "methods": {
            "existing_baseline": "Preserve provided BLS source chunks; split Fed and Thai PBS text into contiguous 1200-character chunks without overlap.",
            "recursive_fixed": "Deterministic 1200-character splitting with 180-character overlap and whitespace boundaries.",
            "structure_aware": "Preserve BLS heading sections; paragraph-group Fed and Thai PBS text to 1800 characters.",
            "semantic": "Deterministic sentence/paragraph grouping; this is a text-boundary heuristic, not model-based semantic chunking.",
            "adaptive": "Paragraph-aware grouping with a per-document target of 1600, 1200, or 900 characters.",
        },
        "chunk_counts": counts,
        "evidence_quotes_preserved": True,
    }
    manifest_path = output_dir / "generated_chunk_collections_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return counts


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = build_collections(root)
    print(f"Chunk collections written to: {root / 'artifacts' / 'chunking_benchmark'}")
    print(f"Source documents: {len(read_jsonl(root / 'dataset' / 'ground_truth_source_data_4_datasets.jsonl'))}")
    for method, count in result.items():
        print(f"{method}: {count:,} chunks")
