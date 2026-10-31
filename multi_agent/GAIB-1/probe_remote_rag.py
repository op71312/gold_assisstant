#!/usr/bin/env python
"""Read-only smoke test for the configured Cloudflare embedding + Qdrant path."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GT_PATH = ROOT / "multi_agent" / "gt" / "ground_truth_fed_ready_v1.jsonl"
REPORT_PATH = OUT / "remote_rag_smoke_test.json"


def load_report() -> dict[str, Any]:
    load_dotenv(ROOT / ".env", override=False)
    required = ["CLOUDFLARE_ACCOUNT_ID", "QDRANT_URL", "QDRANT_API_KEY"]
    missing = [name for name in required if not os.getenv(name, "").strip()]
    token = (os.getenv("CLOUDFLARE_API_TOKEN") or os.getenv("CLOUDFLARE_AUTH_TOKEN", "")).strip()
    if not token:
        missing.append("CLOUDFLARE_API_TOKEN or CLOUDFLARE_AUTH_TOKEN")
    if missing:
        raise RuntimeError("Missing required remote RAG settings: " + ", ".join(missing))

    gt = [
        json.loads(line)
        for line in GT_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    samples = [row for row in gt if row.get("split") == "development" and row.get("evidence")]
    if not samples:
        raise RuntimeError("No development Fed Ground Truth query with evidence is available.")
    sample = samples[0]
    query = str(sample.get("query") or "").strip()
    expected_ids = {
        str(evidence.get("document_id"))
        for evidence in sample["evidence"]
        if evidence.get("document_id")
    }
    if not query or not expected_ids:
        raise RuntimeError("Selected development Ground Truth record has no query or evidence document ID.")

    model = os.getenv("EMBEDDING_MODEL", "@cf/baai/bge-m3").strip()
    account_id = os.environ["CLOUDFLARE_ACCOUNT_ID"].strip()
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    embedding_response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"text": [query]},
        timeout=30,
    )
    embedding_response.raise_for_status()
    body = embedding_response.json()
    if body.get("success") is False:
        raise RuntimeError("Cloudflare rejected the embedding request.")
    result = body.get("result") or {}
    vectors = result.get("data") or result.get("embeddings")
    if not vectors:
        raise RuntimeError("Cloudflare returned no embedding vector.")
    vector = vectors[0]
    if isinstance(vector, dict):
        vector = vector.get("embedding", vector.get("vector"))
    if not isinstance(vector, list) or not vector:
        raise RuntimeError("Cloudflare returned an invalid embedding vector.")

    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "gold_news_structure_aware").strip()
    client = QdrantClient(
        url=os.environ["QDRANT_URL"].strip(),
        api_key=os.environ["QDRANT_API_KEY"].strip(),
        timeout=20,
    )
    collection = client.get_collection(collection_name)
    query_result = client.query_points(
        collection_name=collection_name,
        query=vector,
        limit=10,
        with_payload=True,
        with_vectors=False,
    )
    points = query_result.points
    expected_original_ids = set()
    for row in gt:
        if row.get("query_id") == sample.get("query_id"):
            expected_original_ids = {
                str(evidence.get("source_document_id_in_uploaded_corpus") or evidence.get("document_id"))
                for evidence in row.get("evidence", [])
                if evidence.get("source_document_id_in_uploaded_corpus") or evidence.get("document_id")
            }
    matching_ranks = []
    for rank, point in enumerate(points, start=1):
        payload = point.payload or {}
        found_ids = {
            str(payload.get(key))
            for key in ("document_id", "original_id", "source_document_id")
            if payload.get(key) is not None
        }
        if found_ids & expected_original_ids:
            matching_ranks.append(rank)

    return {
        "status": "PASS" if points and matching_ranks else "PARTIAL",
        "tested_at_utc": datetime.now(timezone.utc).isoformat(),
        "cloudflare": {
            "status": "PASS",
            "http_status": embedding_response.status_code,
            "model": model,
            "embedding_dimensions": len(vector),
        },
        "qdrant": {
            "status": "PASS" if points else "PARTIAL",
            "collection": collection_name,
            "collection_status": str(collection.status),
            "points_count": collection.points_count,
            "returned_top_k": len(points),
            "top_k": 10,
            "expected_source_document_found": bool(matching_ranks),
            "expected_source_document_ranks": matching_ranks,
        },
        "sample": {
            "query_id": sample.get("query_id"),
            "split": sample.get("split"),
            "qdrant_index_coverage": "SMOKE_TESTED_FOR_THIS_QUERY_ONLY",
        },
        "note": "This proves one Cloudflare embedding and Qdrant search succeeded; it is not full-corpus index verification or a benchmark run.",
    }


def main() -> int:
    try:
        report = load_report()
    except Exception as exc:
        report = {
            "status": "FAIL",
            "tested_at_utc": datetime.now(timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
            "note": "No credentials or response body details are written to this report.",
        }
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Remote RAG smoke test failed: {type(exc).__name__}")
        return 1
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
