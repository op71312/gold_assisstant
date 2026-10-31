#!/usr/bin/env python
"""Build a small, source-verified Thai gold-market development set."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


GAIB_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = GAIB_DIR.parents[1]
SOURCE_PATH = PROJECT_ROOT / "dataset" / "news" / "pbs" / "gold_audit_direct.jsonl"
CHUNKS_PATH = (
    PROJECT_ROOT
    / "embedding"
    / "artifacts"
    / "chunking_real"
    / "structure_aware"
    / "chunks_structure_aware_real.jsonl"
)
FEATURES_PATH = (
    PROJECT_ROOT
    / "dataset"
    / "datset a gold price"
    / "data"
    / "processed"
    / "thai_gold_features_v1.csv"
)
MODEL_PATH = PROJECT_ROOT / "model" / "gold_hmm_v1" / "model.joblib"
OUTPUT_PATH = GAIB_DIR / "ground_truth_gold_market_v1.jsonl"
MANIFEST_PATH = GAIB_DIR / "ground_truth_gold_market_v1_manifest.json"

NEWS_QUERIES = [
    ("thgold_001", "thaipbs:news:571381", "ราคาทองคำแท่งและทองรูปพรรณปิดตลาดวันที่ 20 ต.ค. 2569 เท่าไร และราคาปรับขึ้นหรือลงกี่บาท?", "numeric_fact", "AI1_News_Analyst", "ทองคำแท่งขายออก 65,600 บาทต่อบาททองคำ ทองรูปพรรณขายออก 66,400 บาท ลดลง 650 บาท และผันผวน 21 ครั้ง"),
    ("thgold_002", "thaipbs:news:571550", "วันที่ 23 ต.ค. 2569 ทองคำแท่งและทองรูปพรรณขายออกเท่าไร ราคาทองเปลี่ยนแปลงกี่บาทและกี่ครั้ง?", "numeric_fact", "AI1_News_Analyst", "ทองคำแท่งขายออก 64,350 บาท ทองรูปพรรณขายออก 65,150 บาท ลดลง 1,000 บาท และผันผวน 24 ครั้ง"),
    ("thgold_003", "thaipbs:news:571437", "ข่าวปิดตลาดวันที่ 21 ต.ค. 2569 รายงานราคาทองคำแท่งและทองรูปพรรณอย่างไร?", "numeric_fact", "AI1_News_Analyst", "ราคาทองไม่เปลี่ยนแปลง ผันผวน 20 ครั้ง ทองคำแท่งขายออก 65,600 บาท และทองรูปพรรณขายออก 66,400 บาท"),
    ("thgold_004", "thaipbs:news:571164", "วันที่ 16 ต.ค. 2569 ราคาทองปิดตลาดเปลี่ยนแปลงเท่าไร และทองคำแท่งขายออกเท่าไร?", "numeric_fact", "AI1_News_Analyst", "ราคาทองบวก 150 บาท ผันผวน 23 ครั้ง และทองคำแท่งขายออก 66,100 บาท"),
    ("thgold_005", "thaipbs:news:571076", "ข่าวปิดตลาดวันที่ 15 ต.ค. 2569 ระบุการเปลี่ยนแปลงและราคาขายออกของทองคำแท่งเท่าไร?", "numeric_fact", "AI2_Macro_Analyst", "ราคาทองไม่เปลี่ยนแปลง ผันผวน 18 ครั้ง และทองคำแท่งขายออก 65,950 บาท"),
    ("thgold_006", "thaipbs:news:571033", "เช้าวันที่ 15 ต.ค. 2569 ราคาทองเปิดตลาดเปลี่ยนแปลงเท่าไร และทองคำแท่งขายออกเท่าไร?", "numeric_fact", "AI2_Macro_Analyst", "เปิดตลาดลดลง 100 บาท (ครั้งที่ 2 เพิ่มขึ้น 100 บาท) และทองคำแท่งขายออก 65,850 บาท"),
    ("thgold_007", "thaipbs:news:570971", "เช้าวันที่ 14 ต.ค. 2569 ทองรูปพรรณขายออกเท่าไร และข่าวระบุการเปลี่ยนแปลงราคาเท่าไร?", "numeric_fact", "AI2_Macro_Analyst", "ทองรูปพรรณขายออก 67,000 บาท และราคาเปิดตลาดลดลง 300 บาท"),
    ("thgold_008", "thaipbs:news:571503", "วันที่ 22 ต.ค. 2569 ราคาทองปิดตลาดเปลี่ยนแปลงเท่าไร และทองคำแท่งขายออกเท่าไร?", "numeric_fact", "AI2_Macro_Analyst", "ราคาทองลดลง 250 บาท ผันผวน 25 ครั้ง และทองคำแท่งขายออก 65,350 บาท"),
    ("thgold_009", "thaipbs:news:571012", "วันที่ 14 ต.ค. 2569 ราคาทองปิดตลาดเปลี่ยนแปลงเท่าไร และทองคำแท่งขายออกเท่าไร?", "numeric_fact", "AI3_Quant_Regime_Analyst", "ราคาทองลดลง 550 บาท ผันผวน 19 ครั้ง และทองคำแท่งขายออก 65,950 บาท"),
    ("thgold_010", "thaipbs:news:571381", "ข่าววันที่ 20 ต.ค. 2569 กล่าวถึงปัจจัยตลาดใดบ้างพร้อมกับราคาทองที่ลดลง? แยกสิ่งที่รายงานจากข้อสรุปเชิงเหตุและผล", "economic_explanation", "AI1_News_Analyst", "ข่าวรายงานว่าน้ำมันดิบปรับขึ้น มีความเสี่ยงจากสหรัฐฯ–อิสราเอลที่กำลังพิจารณาโจมตีอิหร่าน และดอลลาร์อ่อนค่า โดยไม่ได้พิสูจน์ว่าปัจจัยใดเป็นสาเหตุโดยตรง"),
    ("thgold_011", "thaipbs:news:571550", "ข่าววันที่ 23 ต.ค. 2569 ระบุว่าราคาทองคำโลกปรับลงกี่ดอลลาร์?", "numeric_fact", "AI1_News_Analyst", "ราคาทองคำโลกปรับลง 116.7 ดอลลาร์"),
    ("thgold_012", "thaipbs:news:571437", "ข่าววันที่ 21 ต.ค. 2569 กล่าวถึงดอลลาร์ ยีลด์พันธบัตร 2 ปี และการเจรจาสหรัฐฯ–อิหร่านอย่างไร?", "economic_explanation", "AI2_Macro_Analyst", "ข่าวระบุว่าดอลลาร์ทรงตัว ยีลด์ 2 ปีมีความเสี่ยงปรับสูงขึ้น และการเจรจาสหรัฐฯ–อิหร่านตึงเครียด; เป็นปัจจัยที่รายงานกล่าวถึง ไม่ใช่หลักฐานยืนยันเหตุและผล"),
    ("thgold_013", "thaipbs:news:571164", "ข่าววันที่ 16 ต.ค. 2569 กล่าวถึงการลงทุนของ World Bank ในแร่สำคัญและเหตุการณ์ภูมิรัฐศาสตร์ใด?", "economic_explanation", "AI1_News_Analyst", "ข่าวกล่าวถึง World Bank ใช้งบ 1.9 หมื่นล้านดอลลาร์สนับสนุนแร่สำคัญ และติดตามวิกฤตยูเครน"),
    ("thgold_014", "thaipbs:news:571076", "ข่าววันที่ 15 ต.ค. 2569 รายงานความเสี่ยงด้านภูมิรัฐศาสตร์และพลังงานใดที่เกี่ยวข้องกับมุมมองต่อทอง?", "economic_explanation", "AI2_Macro_Analyst", "ข่าวกล่าวถึงแผนโจมตีอิหร่านของสหรัฐฯ ซึ่งเสี่ยงซ้ำเติมวิกฤตพลังงานและกดดันราคาทอง โดยไม่ยืนยันความเป็นเหตุโดยตรง"),
    ("thgold_015", "thaipbs:news:571033", "ข่าวเช้าวันที่ 15 ต.ค. 2569 ระบุข้อมูลเงินเฟ้อสหรัฐฯ และความกังวลเรื่องดอกเบี้ยอย่างไร?", "economic_explanation", "AI2_Macro_Analyst", "ข่าวระบุว่าเงินเฟ้อสหรัฐฯ สูงกว่าคาด และตลาดกังวลว่า Fed อาจขึ้นดอกเบี้ยเพิ่มเติม"),
    ("thgold_016", "thaipbs:news:570971", "ข่าวเช้าวันที่ 14 ต.ค. 2569 ระบุระดับราคาทองโลกและปัจจัยเสี่ยงใดบ้าง?", "economic_explanation", "AI3_Quant_Regime_Analyst", "ข่าวระบุว่าทองเผชิญแรงขายหลังยืนเหนือ 4,200 ดอลลาร์ไม่ได้ พร้อมกล่าวถึงความไม่แน่นอนของสงครามในตะวันออกกลางและราคาน้ำมันที่สูงขึ้น"),
    ("thgold_017", "thaipbs:news:571503", "ข่าววันที่ 22 ต.ค. 2569 อธิบายบริบทที่เกิดพร้อมกับราคาทองที่ลดลงอย่างไร?", "economic_explanation", "AI1_News_Analyst", "ข่าวกล่าวถึงราคาน้ำมันดิบที่พุ่งสูง และสหรัฐฯ–อิสราเอลเตรียมโจมตีอิหร่านหลังการเลือกตั้ง; ไม่สรุปว่าเป็นเหตุโดยตรง"),
    ("thgold_018", "thaipbs:news:571012", "ข่าวปิดตลาดวันที่ 14 ต.ค. 2569 ระบุความเสี่ยงมหภาคใดที่ตลาดกำลังติดตาม?", "economic_explanation", "AI2_Macro_Analyst", "ข่าวระบุความเสี่ยงด้านพลังงานและเงินเฟ้อ ท่ามกลางความไม่แน่นอนรัสเซีย–ยูเครน"),
]

EXPECTED_NUMERIC_FACTS = {
    "thgold_001": [
        {"value_text": "65,600", "direction": "neutral"},
        {"value_text": "66,400", "direction": "neutral"},
        {"value_text": "650", "direction": "down"},
        {"value_text": "21", "direction": "neutral"},
    ],
    "thgold_002": [
        {"value_text": "64,350", "direction": "neutral"},
        {"value_text": "65,150", "direction": "neutral"},
        {"value_text": "1,000", "direction": "down"},
        {"value_text": "24", "direction": "neutral"},
    ],
    "thgold_003": [
        {"value_text": "20", "direction": "neutral"},
        {"value_text": "65,600", "direction": "neutral"},
        {"value_text": "66,400", "direction": "neutral"},
    ],
    "thgold_004": [
        {"value_text": "150", "direction": "up"},
        {"value_text": "23", "direction": "neutral"},
        {"value_text": "66,100", "direction": "neutral"},
    ],
    "thgold_005": [
        {"value_text": "18", "direction": "neutral"},
        {"value_text": "65,950", "direction": "neutral"},
    ],
    "thgold_006": [
        {"value_text": "100", "direction": "down"},
        {"value_text": "2", "direction": "neutral"},
        {"value_text": "100", "direction": "up"},
        {"value_text": "65,850", "direction": "neutral"},
    ],
    "thgold_007": [
        {"value_text": "67,000", "direction": "neutral"},
        {"value_text": "300", "direction": "down"},
    ],
    "thgold_008": [
        {"value_text": "250", "direction": "down"},
        {"value_text": "25", "direction": "neutral"},
        {"value_text": "65,350", "direction": "neutral"},
    ],
    "thgold_009": [
        {"value_text": "550", "direction": "down"},
        {"value_text": "19", "direction": "neutral"},
        {"value_text": "65,950", "direction": "neutral"},
    ],
    "thgold_011": [{"value_text": "116.7", "direction": "down"}],
    "thgold_013": [{"value_text": "1.9", "direction": "neutral"}],
    "thgold_016": [{"value_text": "4,200", "direction": "neutral"}],
    "thgold_019": [
        {"value_text": "65,950", "direction": "neutral"},
        {"value_text": "64,350", "direction": "neutral"},
        {"value_text": "1,600", "direction": "neutral"},
    ],
    "thgold_020": [
        {"value_text": "65,950", "direction": "neutral"},
        {"value_text": "0", "direction": "neutral"},
    ],
    "thgold_021": [{"value_text": "10", "direction": "neutral"}],
}

SOURCE_QUOTE_SPECS = {
    "thaipbs:news:570971": (
        "ราคาทองคำวันนี้ ลบ 300 บาท",
        "ราคาทองรูปพรรณขายออกบาทละ 67,000 บาท",
    ),
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_indexed_chunks(article_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    matches: dict[str, list[dict[str, Any]]] = {}
    with CHUNKS_PATH.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not any(article_id in line for article_id in article_ids):
                continue
            chunk = json.loads(line)
            article_id = str(chunk.get("original_id") or "")
            if article_id in article_ids:
                matches.setdefault(article_id, []).append(chunk)
    return matches


def make_evidence(
    article: dict[str, Any],
    chunks: list[dict[str, Any]],
    query_id: str,
) -> dict[str, Any]:
    source = article.get("source") or {}
    abstract = str(article.get("abstract") or "").strip()
    title = str(article.get("title") or "").strip()
    quote = ""
    chunk = None
    quote_spec = SOURCE_QUOTE_SPECS.get(str(article.get("article_id") or ""))
    if quote_spec:
        content = str(article.get("content") or "")
        start = content.find(quote_spec[0])
        end = content.find(quote_spec[1], start) if start >= 0 else -1
        if start < 0 or end < 0:
            raise ValueError(f"{query_id}: source quote markers not found in {article['article_id']}")
        quote = content[start:end + len(quote_spec[1])]
        chunk = next(
            (candidate for candidate in chunks if quote in str(candidate.get("content") or "")),
            None,
        )
    else:
        chunk = next(
            (candidate for candidate in chunks if abstract and abstract in str(candidate.get("content") or "")),
            None,
        )
        quote = abstract
        if chunk is None and title:
            chunk = next(
                (candidate for candidate in chunks if title in str(candidate.get("content") or "")),
                None,
            )
            quote = title
    if chunk is None:
        raise ValueError(f"{query_id}: no exact source span found in indexed chunks for {article['article_id']}")
    return {
        "evidence_id": f"{query_id}_e{len(chunks)}",
        "document_id": chunk["document_id"],
        "chunk_id": chunk["chunk_id"],
        "source": "thai_pbs_gold",
        "source_file": "gold_audit_direct.jsonl",
        "source_url": source.get("url"),
        "title": title,
        "publication_date": str(chunk.get("publication_date") or "")[:10],
        "exact_quote": quote,
        "source_span_validated_against_uploaded_corpus": True,
    }


def make_row(
    query_id: str,
    query: str,
    query_type: str,
    focus_agent: str,
    expected_answer: Any,
    article_ids: list[str],
    articles_by_id: dict[str, dict[str, Any]],
    chunks_by_id: dict[str, list[dict[str, Any]]],
    extra_evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    evidence = [
        make_evidence(articles_by_id[article_id], chunks_by_id.get(article_id, []), query_id)
        for article_id in article_ids
    ]
    evidence.extend(extra_evidence or [])
    relevance = []
    seen_document_ids = set()
    for item in evidence:
        if item.get("source") != "thai_pbs_gold":
            continue
        document_id = str(item["document_id"])
        if document_id in seen_document_ids:
            continue
        seen_document_ids.add(document_id)
        relevance.append({
            "document_id": document_id,
            "relevance_grade": 3,
            "judgment_basis": "The indexed Thai PBS gold-market source directly supports the requested fact.",
        })
    return {
        "schema_version": "1.0",
        "query_id": query_id,
        "query": query,
        "query_language": "th",
        "query_type": query_type,
        "difficulty": "medium",
        "focus_agent": focus_agent,
        "evidence": evidence,
        "expected_answer": expected_answer,
        "expected_numeric_facts": [
            dict(fact) for fact in EXPECTED_NUMERIC_FACTS.get(query_id, [])
        ],
        "relevance_judgments": relevance,
        "judgment_set_exhaustive": False,
        "review_status": "source_verified_not_human_reviewed",
        "review_notes": "Development set. Source spans and local numeric facts are verified; semantic answer quality still requires human spot-check.",
        "created_by": "build_gold_market_ground_truth.py",
        "split": "development",
        "benchmark_readiness": "development_only",
        "qdrant_index_coverage_verified": False,
        "track": "thai_gold_market",
    }


def main() -> None:
    for path in (SOURCE_PATH, CHUNKS_PATH, FEATURES_PATH, MODEL_PATH):
        if not path.is_file():
            raise FileNotFoundError(f"Required Ground Truth source is missing: {path}")

    articles = read_jsonl(SOURCE_PATH)
    articles_by_id = {str(row.get("article_id")): row for row in articles}
    article_ids = {row[1] for row in NEWS_QUERIES}
    article_ids.update({"thaipbs:news:571012", "thaipbs:news:571550"})
    missing_articles = article_ids - set(articles_by_id)
    if missing_articles:
        raise ValueError(f"Gold source records are missing: {sorted(missing_articles)}")

    chunks_by_id = load_indexed_chunks(article_ids)
    missing_chunks = article_ids - set(chunks_by_id)
    if missing_chunks:
        raise ValueError(f"Gold source records are not in the local RAG corpus: {sorted(missing_chunks)}")

    rows = []
    for query_id, article_id, query, query_type, focus_agent, expected_answer in NEWS_QUERIES:
        rows.append(make_row(
            query_id, query, query_type, focus_agent, expected_answer,
            [article_id], articles_by_id, chunks_by_id,
        ))

    rows.append(make_row(
        "thgold_019",
        "เปรียบเทียบราคาขายออกทองคำแท่งปิดตลาดวันที่ 14 ต.ค. กับ 23 ต.ค. 2569: วันที่ 14 ต.ค. สูงกว่ากี่บาท?",
        "multi_evidence",
        "AI3_Quant_Regime_Analyst",
        "วันที่ 14 ต.ค. ขายออก 65,950 บาท และวันที่ 23 ต.ค. ขายออก 64,350 บาท ดังนั้นวันที่ 14 ต.ค. สูงกว่า 1,600 บาท",
        ["thaipbs:news:571012", "thaipbs:news:571550"],
        articles_by_id,
        chunks_by_id,
    ))

    latest_feature = {
        "evidence_id": "thgold_020_local_features",
        "document_id": "thai_gold_features_v1:2026-10-13",
        "source": "local_feature_data",
        "source_file": FEATURES_PATH.name,
        "source_path": str(FEATURES_PATH.relative_to(PROJECT_ROOT)),
        "source_record_key": "2026-10-13 12:09:00",
        "exact_quote": "timestamp=2026-10-13 12:09:00; bar_buy=66500; bar_sell=66700; gold_spot_clean=4197; thb_usd_clean=33.58",
        "source_validation_status": "verified_local_feature_record",
    }
    latest_hmm = {
        "evidence_id": "thgold_020_hmm",
        "document_id": "gold_hmm_v1:latest_state",
        "source": "gaussian_hmm",
        "source_file": MODEL_PATH.name,
        "source_path": str(MODEL_PATH.relative_to(PROJECT_ROOT)),
        "source_record_key": "feature_data_as_of=2026-10-13 12:09:00",
        "exact_quote": "model=GaussianHMM; latest_state=0; as_of=2026-10-13 12:09:00; max_state_posterior=0.9998015738; state IDs are latent statistical regimes",
        "source_validation_status": "verified_runtime_model_output",
    }
    rows.append(make_row(
        "thgold_020",
        "ข่าวปิดตลาดวันที่ 14 ต.ค. 2569 รายงานราคาขายออกทองคำแท่งเท่าไร และข้อมูล feature ล่าสุดของระบบให้ GaussianHMM latent state หมายเลขใด? แยกวันที่ของสองแหล่งและอย่าตีความ state เป็นขาขึ้นหรือขาลง",
        "numeric_fact",
        "AI3_Quant_Regime_Analyst",
        "ข่าววันที่ 14 ต.ค. รายงานทองคำแท่งขายออก 65,950 บาท; ข้อมูล feature ล่าสุดถึง 13 ต.ค. 2569 เวลา 12:09 และ GaussianHMM ให้ latent state 0 ซึ่งไม่มีป้ายความหมายขาขึ้นหรือขาลง",
        ["thaipbs:news:571012"],
        articles_by_id,
        chunks_by_id,
        [latest_feature, latest_hmm],
    ))

    freshness_feature = dict(latest_feature, evidence_id="thgold_021_local_features")
    freshness_hmm = dict(latest_hmm, evidence_id="thgold_021_hmm")
    rows.append(make_row(
        "thgold_021",
        "เมื่อมีข่าวทองคำถึงวันที่ 23 ต.ค. 2569 แต่ feature ล่าสุดของระบบคือวันที่ 13 ต.ค. 2569 เวลา 12:09 แล้ว ควรอ้าง HMM state ว่าเป็นภาวะตลาดวันที่ 23 ต.ค. หรือไม่ และข้อมูลล่าช้ากี่วัน?",
        "data_quality",
        "AI4_Risk_Data_Auditor",
        "ไม่ควรอ้าง HMM state เป็นภาวะตลาดวันที่ 23 ต.ค.; feature ล่าสุดคือ 13 ต.ค. 2569 เวลา 12:09 จึงล่าช้า 10 วัน",
        ["thaipbs:news:571550"],
        articles_by_id,
        chunks_by_id,
        [freshness_feature, freshness_hmm],
    ))

    query_ids = [str(row["query_id"]) for row in rows]
    if len(rows) != 21 or len(set(query_ids)) != len(rows):
        raise ValueError(f"Expected 21 unique Thai gold queries; got {len(rows)}.")
    if any(not row["relevance_judgments"] for row in rows):
        raise ValueError("Every query must have at least one source-backed retrieval judgment.")
    for row in rows:
        for evidence in row["evidence"]:
            if not evidence.get("source_file") or not evidence.get("exact_quote"):
                raise ValueError(f"{row['query_id']}: evidence source metadata is incomplete.")

    OUTPUT_PATH.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    manifest = {
        "dataset_version": "thai_gold_market_v1",
        "query_count": len(rows),
        "unique_news_document_count": len(article_ids),
        "query_type_counts": {
            query_type: sum(row["query_type"] == query_type for row in rows)
            for query_type in sorted({row["query_type"] for row in rows})
        },
        "split": "development",
        "human_semantic_review_complete": False,
        "qdrant_index_coverage_verified": False,
        "source_files": {
            str(path.relative_to(PROJECT_ROOT)): sha256(path)
            for path in (SOURCE_PATH, CHUNKS_PATH, FEATURES_PATH, MODEL_PATH)
        },
        "output_path": str(OUTPUT_PATH.relative_to(PROJECT_ROOT)),
        "output_sha256": sha256(OUTPUT_PATH),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
