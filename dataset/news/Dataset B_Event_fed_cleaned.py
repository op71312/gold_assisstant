"""Clean Federal Reserve press-release JSONL and create RAG-ready chunks.

Edit INPUT_PATH below to point to your fed_press_releases.jsonl file.
The raw input is never modified.
"""
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from collections import Counter

# ----------------------------- CONFIG -----------------------------
INPUT_PATH = Path("fed_press_releases.jsonl")  # Edit this if needed
OUTPUT_DIR = INPUT_PATH.parent / "fed_press_releases_cleaned"
CHUNK_SIZE = 1400
CHUNK_OVERLAP = 180
# ------------------------------------------------------------------

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Cannot find {INPUT_PATH.resolve()}. Edit INPUT_PATH at the top of this script."
    )
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with INPUT_PATH.open("r", encoding="utf-8-sig") as f:
    raw_records = [json.loads(line) for line in f if line.strip()]

# Archive/listing pages do not have archive_type; individual releases do.
article_records = [r for r in raw_records if r.get("archive_type")]
archive_records = [r for r in raw_records if not r.get("archive_type")]

seen_urls = set()
articles_unique = []
duplicates_removed = 0
for record in article_records:
    url = (record.get("url") or "").strip()
    if url and url in seen_urls:
        duplicates_removed += 1
        continue
    if url:
        seen_urls.add(url)
    articles_unique.append(record)

MOJIBAKE_SEQUENCE_RE = re.compile(r"[\u00C2-\u00F4][\u0080-\u00BF]{1,3}")
RELEASE_RE = re.compile(r"^\s*For\s+(?:immediate\s+release|release\s+at\b.*)$", re.I)
DATE_FORMATS = ("%B %d, %Y", "%b %d, %Y")


def repair_text(text):
    """Repair UTF-8 bytes that were incorrectly decoded as Latin-1, conservatively."""
    if not isinstance(text, str):
        text = str(text or "")
    replacements = 0

    def replace_match(match):
        nonlocal replacements
        try:
            fixed = match.group(0).encode("latin-1").decode("utf-8")
            replacements += 1
            return fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            return match.group(0)

    text = MOJIBAKE_SEQUENCE_RE.sub(replace_match, text)
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return text, replacements


def parse_date_line(value):
    value = (value or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def extract_publication_date(raw_content, url):
    lines = (raw_content or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for line in lines[:12]:
        date_value = parse_date_line(line)
        if date_value:
            return date_value.isoformat(), "content"

    # Fallback for Federal Reserve URL slugs containing YYYYMMDD, e.g. monetary20090504a.htm.
    match = re.search(r"((?:19|20)\d{2})(\d{2})(\d{2})[a-z]?\.htm$", url or "", re.I)
    if match:
        try:
            date_value = datetime.strptime("".join(match.groups()), "%Y%m%d").date()
            return date_value.isoformat(), "url_fallback"
        except ValueError:
            pass
    return None, "not_found"


def normalize_key(value):
    return re.sub(r"\s+", " ", (value or "")).strip().casefold()


def clean_body(raw_content, title):
    text, encoding_repairs = repair_text(raw_content)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [line.rstrip() for line in lines]

    release_time_text = None
    for line in lines[:15]:
        if RELEASE_RE.match(line):
            release_time_text = line.strip()
            break

    cleaning_flags = []

    # Some older releases include a contact block immediately after Share.
    share_idx = next(
        (i for i, line in enumerate(lines[:15]) if line.strip().casefold() == "share"),
        None,
    )
    if share_idx is not None:
        contact_window = lines[share_idx + 1:share_idx + 9]
        has_contact_block = any(
            "spokesman" in line.casefold()
            or re.search(r"\(?\d{3}\)?[ .-]*\d{3}[.-]\d{4}", line)
            or ("email" in line.casefold() and ("protected" in line.casefold() or "@" in line))
            for line in contact_window
        )
        if has_contact_block:
            body_start = None
            for j in range(share_idx + 1, min(len(lines), share_idx + 18)):
                candidate = lines[j].strip()
                if len(candidate) >= 80 or ("--" in candidate and len(candidate) >= 40):
                    body_start = j
                    break
            if body_start is not None:
                lines = lines[:share_idx] + lines[body_start:]
                cleaning_flags.append("leading_contact_block_removed")

    fixed_title, _ = repair_text(title)
    title_key = normalize_key(fixed_title)
    result = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.casefold() in {"share", "print"}:
            continue
        if i < 12 and parse_date_line(stripped):
            continue
        if i < 12 and title_key and normalize_key(stripped) == title_key:
            continue
        if i < 15 and RELEASE_RE.match(stripped):
            continue
        if i < 5 and normalize_key(stripped) == "financial services policy committee":
            continue
        result.append(stripped)

    # Remove a likely terminal media-contact footer, not an in-body mention.
    contact_idx = next(
        (
            i for i, line in enumerate(result)
            if i >= max(0, len(result) - 12)
            and re.match(r"^for media inquiries\b", line.strip(), re.I)
        ),
        None,
    )
    if contact_idx is not None:
        result = result[:contact_idx]
        cleaning_flags.append("terminal_media_contact_removed")

    normalized = []
    previous_blank = False
    for line in result:
        stripped = line.strip()
        if not stripped:
            if normalized and not previous_blank:
                normalized.append("")
            previous_blank = True
        else:
            normalized.append(re.sub(r"[ \t]+", " ", stripped))
            previous_blank = False

    cleaned = "\n".join(normalized).strip()
    if not cleaned:
        cleaned = text.strip()
        cleaning_flags.append("body_cleanup_fallback")

    return cleaned, encoding_repairs, release_time_text, cleaning_flags


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


cleaned_records = []
for record in articles_unique:
    url = record.get("url") or ""
    publication_date, date_source = extract_publication_date(record.get("content", ""), url)
    title, _ = repair_text(record.get("title", ""))
    content, encoding_repairs, release_time_text, flags = clean_body(
        record.get("content", ""), title
    )
    if date_source == "url_fallback":
        flags.append("publication_date_from_url")
    elif date_source == "not_found":
        flags.append("publication_date_not_found")

    cleaned_records.append({
        "document_id": hashlib.sha1((url or title).encode("utf-8")).hexdigest(),
        "source": record.get("source") or "Federal Reserve Board",
        "title": title.strip(),
        "publication_date": publication_date,
        "publication_date_source": date_source,
        "release_time_text": release_time_text,
        "document_type": record.get("archive_type") or "unknown",
        "source_archive_year": record.get("archive_year"),
        "url": url,
        "content": content,
        "collected_at": record.get("collected_at"),
        "encoding_repairs": encoding_repairs,
        "cleaning_flags": flags,
    })

clean_path = OUTPUT_DIR / "fed_press_releases_clean.jsonl"
archive_path = OUTPUT_DIR / "fed_press_release_archive_pages_raw.jsonl"
review_path = OUTPUT_DIR / "fed_press_releases_needs_review.jsonl"
write_jsonl(clean_path, cleaned_records)
write_jsonl(archive_path, archive_records)  # Kept separately; not sent to the vector DB.
needs_review = [
    r for r in cleaned_records
    if not r["publication_date"] or len(r["content"].strip()) < 40
]
write_jsonl(review_path, needs_review)


def chunk_text(text, max_chars=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = min(start + max_chars, text_length)
        if end < text_length:
            lower_bound = start + int(max_chars * 0.65)
            candidates = [
                text.rfind("\n", lower_bound, end),
                text.rfind(". ", lower_bound, end),
                text.rfind(" ", lower_bound, end),
            ]
            split_at = max(candidates)
            if split_at > start:
                end = split_at + 1 if text[split_at:split_at + 2] == ". " else split_at
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = max(end - overlap, start + 1)
    return chunks


rag_chunks = []
for doc in cleaned_records:
    parts = chunk_text(doc["content"])
    for index, part in enumerate(parts):
        rag_chunks.append({
            "chunk_id": hashlib.sha1(f"{doc['document_id']}:{index}".encode("utf-8")).hexdigest(),
            "document_id": doc["document_id"],
            "chunk_index": index,
            "chunk_count": len(parts),
            "source": doc["source"],
            "title": doc["title"],
            "publication_date": doc["publication_date"],
            "release_time_text": doc["release_time_text"],
            "document_type": doc["document_type"],
            "url": doc["url"],
            "content": part,
            "text_for_embedding": (
                f"Title: {doc['title']}\n"
                f"Publication date: {doc['publication_date'] or 'unknown'}\n\n"
                f"{part}"
            ),
        })

chunks_path = OUTPUT_DIR / "fed_press_releases_rag_chunks.jsonl"
write_jsonl(chunks_path, rag_chunks)

report = {
    "input_file": str(INPUT_PATH.resolve()),
    "input_records": len(raw_records),
    "archive_index_records_separated": len(archive_records),
    "article_records_raw": len(article_records),
    "duplicate_article_urls_removed": duplicates_removed,
    "clean_article_records": len(cleaned_records),
    "rag_chunks": len(rag_chunks),
    "missing_publication_date": sum(not r["publication_date"] for r in cleaned_records),
    "publication_date_source_counts": dict(Counter(r["publication_date_source"] for r in cleaned_records)),
    "empty_or_short_clean_content": sum(len(r["content"].strip()) < 40 for r in cleaned_records),
    "records_with_encoding_repairs": sum(r["encoding_repairs"] > 0 for r in cleaned_records),
    "encoding_sequences_repaired": sum(r["encoding_repairs"] for r in cleaned_records),
    "records_with_cleaning_flags": sum(bool(r["cleaning_flags"]) for r in cleaned_records),
    "needs_review_records": len(needs_review),
    "outputs": {
        "clean_dataset": str(clean_path.resolve()),
        "archive_pages": str(archive_path.resolve()),
        "rag_chunks": str(chunks_path.resolve()),
        "needs_review": str(review_path.resolve()),
    },
}
report_path = OUTPUT_DIR / "cleaning_report.json"
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
print(f"\nFinished. Output directory: {OUTPUT_DIR.resolve()}")
