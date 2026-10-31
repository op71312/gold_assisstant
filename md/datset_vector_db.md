# Dataset สำหรับ Vector DB — Gold Assistant

เอกสารนี้สรุปชุดข้อมูลข่าว/รายงาน 4 ชุดที่ใช้เป็น Knowledge Base สำหรับการทำ RAG / Vector DB
เพื่อวิเคราะห์ปัจจัยที่มีผลต่อราคาทองคำ ครอบคลุมข่าวตลาดทองไทย (Thai PBS),
แถลงการณ์ธนาคารกลางสหรัฐฯ (Federal Reserve), และรายงานเศรษฐกิจจาก BLS (NFP และ CPI)

| # | Dataset | แหล่งที่มา | รูปแบบ | จำนวน | ช่วงเวลา |
|---|---------|-----------|--------|-------|----------|
| 1 | gold_audit_direct.jsonl | Thai PBS | JSONL | 9 records | ต.ค. 2026 (บทความย้อนหลังเก่ากว่า) |
| 2 | fed_press_releases_classified.jsonl | Federal Reserve | JSONL | 4,553 records | 2006-01-03 → 2026-10-16 |
| 3 | bls/nfp/clean | BLS — Employment Situation | JSON (1 ไฟล์/1 รายงาน) | 248 ไฟล์ / 3,535 chunks | 2006-01-06 → 2026-10-02 |
| 4 | bls/cpi (clean) | BLS — Consumer Price Index | JSON (1 ไฟล์/1 รายงาน) | 248 ไฟล์ / 3,054 chunks | 2006-01-18 → 2026-10-14 |

---

## 1. Thai PBS — `dataset/news/pbs/gold_audit_direct.jsonl`

### คำอธิบาย
ข่าวราคาทองคำจากเว็บไซต์ Thai PBS (`thaipbs.or.th`) ที่ผ่านการตรวจสอบ (audit) ด้วย LLM
แล้วว่ามี**ความเกี่ยวข้องโดยตรง (direct relevance)** กับราคาทองคำ — เช่น ข่าวสรุปราคา
ทองคำแท่ง/ทองรูปพรรณ "ฮั่วเซ่งเฮง" ประจำวัน เป็น subset จากไฟล์ `gold_relevance_audit.jsonl`
(ไฟล์แม่ที่ให้ผลการ audit ครบทุกอัน) โดยมีไฟล์พี่น้องคือ `gold_audit_indirect.jsonl`
(เกี่ยวข้องโดยอ้อม) และ `gold_audit_uncertain.jsonl` (ไม่แน่ใจ)

### โครงสร้าง (หนึ่ง JSON ต่อหนึ่งบทความ, JSONL)
```jsonc
{
  "article_id": "thaipbs:news:571381",          // ID ไม่ซ้ำ รูปแบบ thaipbs:news:<id>
  "source": {
    "name": "Thai PBS",
    "site": "news",
    "url": "https://www.thaipbs.or.th/news/..."
  },
  "title": "สรุปราคาทองคำ 20 ต.ค.2569 ...",        // พาดหัวข่าว (ภาษาไทย)
  "abstract": "ราคาทองคำ ลบ 650 บาท ...",          // ย่อหน้านำ
  "content": "วันนี้ (20 ต.ค.2569) \"ฮั่วเซ่งเฮง\" ...",  // เนื้อข่าวเต็ม ← ใช้ chunk ตอน embed
  "published_at": "...",                          // วันที่ข่าวตีพิมพ์ (ISO 8601)
  "retrieved_at": "...",                          // วันที่ดาวน์โหลด
  "tags": [...], "categories": [...],
  "content_status": "...",                        // สถานะการดึงเนื้อหา
  "content_hash": "...",                          // ลายเซ็นตรวจซ้ำ
  "classification": {                              // ผลจำแนกครั้งแรก
    "relevance": "direct",
    "confidence": 95,
    "reason": "...",                               // เหตุผลภาษาไทย
    "evidence": ["..."]                            // ข้อความหลักฐานในบทความ
  },
  "classification_metadata": { "provider": "ThaiLLM", "model": "openthaigpt-thaillm-8b-instruct-v7.2", ... },
  "audit": { ... },                                // ผล audit รอบสอง (ตรวจซ้ำ)
  "audit_metadata": {
    "provider": "ThaiLLM", "model": "openthaigpt-thaillm-8b-instruct-v7.2",
    "framework": "LangChain", "prompt_version": "gold-relevance-audit-v1",
    "audited_at": "2026-10-26T03:45:51+00:00", ...
  }
}
```

### สถิติ
- **9 records** (ไฟล์ละเอียดเพราะเป็น subset ที่ผ่าน audit เป็น `direct` เท่านั้น)
- ข่าวที่ audit ผ่านระยะ 2026-10-14 → 2026-10-23 แต่ content อาจเป็นข่าวย้อนหลัง (เช่น พาดหัวปี 2569/2570)
- **ภาษา:** ภาษาไทยทั้งหมด → ควรใช้ embedding model ที่รองรับภาษาไทย

### ตัวอย่าง record
```json
{
  "article_id": "thaipbs:news:571381",
  "source": { "name": "Thai PBS", "site": "news",
              "url": "https://www.thaipbs.or.th/news/content/571381" },
  "title": "สรุปราคาทองคำ 20 ต.ค.2569 ปิดตลาด ผันผวน 21 ครั้ง ลบ 650 บาท",
  "abstract": "ราคาทองคำ ลบ 650 บาท ผันผวน 21 ครั้ง ... \"รูปพรรณ\" ขายออก 66,400 บาท ทองคำ \"ทองคำแท่ง\" ขายออก 65,600 บาท",
  "content": "วันนี้ (20 ต.ค.2569) \"ฮั่วเซ่งเฮง\" เปิดเผยภาพรวมราคาทองโลก ...",
  "classification": { "relevance": "direct", "confidence": 95, ... },
  "audit_metadata": { "provider": "ThaiLLM", "model": "openthaigpt-thaillm-8b-instruct-v7.2",
                      "prompt_version": "gold-relevance-audit-v1", ... }
}
```

---

## 2. Federal Reserve — `dataset/news/fed/fed_press_releases_cleaned_audit/fed_press_releases_classified.jsonl`

### คำอธิบาย
แถลงการณ์สำนักข่าว (press releases) ของ Federal Reserve Board ฉบับเต็มตั้งแต่ปี 2006
ถึง 2026 ที่ถูก "cleaned" (แก้ encoding, ลบชื่อผู้ประสานงานสื่อท้ายเอกสาร เป็นต้น)
แล้วจำแนกด้วย LLM ว่าแต่ละฉบับ**เกี่ยวข้องกับราคาทองคำมากน้อยเพียงใด**
(ใช้จัดกลุ่มก่อนทำ embedding แทนการ dump ทั้งหมดลง vector DB)

### โครงสร้าง (JSONL)
```jsonc
{
  "document_id": "f55b7cb4d4d597c9a9e341df2b5805bf8cab633a",  // ลายเซ็น SHA1
  "source": "Federal Reserve Board",
  "title": "Frederic S. Mishkin sworn in as member of the Board of Governors",
  "publication_date": "2006-09-05",
  "publication_date_source": "content",       // ดึงวันที่จากเนื้อหา / จาก URL
  "release_time_text": "For immediate release",
  "document_type": "general",                 // ประเภทเอกสาร (general, monetary ... ฯลฯ)
  "source_archive_year": 2006,
  "url": "https://www.federalreserve.gov/newsevents/pressreleases/other20060905a.htm",
  "content": "Frederic S. Mishkin on Tuesday took the oath ...",   // เนื้อหาเต็ม (ภาษาอังกฤษ)
  "collected_at": "2026-10-26T06:12:35.886862+00:00",
  "encoding_repairs": 1,                       // จำนวนครั้งที่แก้ encoding
  "cleaning_flags": ["terminal_media_contact_removed"],   // สิ่งที่ถูกทำความสะอาดออก
  "classification": {
    "label": "not_relevant",                   // not_relevant | relevant | uncertain
    "confidence": 95,
    "reason": "บทความนี้รายงาน ...",              // เหตุผลภาษาไทย
    "evidence": [],                            // หลักฐาน (ถ้ามี)
    "topics": []                               // หัวข้อที่ลิงก์กับทองคำ (ถ้ามี)
  },
  "classification_metadata": {
    "provider": "ThaiLLM", "model": "openthaigpt-thaillm-8b-instruct-v7.2",
    "framework": "OpenAI Python SDK", "prompt_version": "fed-gold-relevance-v1.0",
    "classified_at": "2026-10-27T02:48:29.630753+00:00"
  }
}
```

### สถิติการจำแนก
| label | จำนวน | หมายเหตุ |
|---|---|---|
| `relevant` | 536 | แถลงการณ์ที่มีผลต่อราคาทองคำ (เช่น FOMC statement, policy) |
| `uncertain` | 717 | จำแนกไม่ชัดเทียงเกิดยก (เสนอทบทวนด้วยมือ / ตั้ง threshold) |
| `not_relevant` | 3,300 | แถลงการณ์ทั่วไปที่ไม่มีผลต่อตลาดทอง (เช่น แต่งตั้งผู้บริหาร) |
| *รวม* | **4,553** | ช่วง 2006-01-03 → 2026-10-16 |

### ไฟล์อื่นในโฟลเดอร์เดียวกัน
- `fed_press_releases_classification_errors.jsonl` — ฉบับที่จำแนกขัดข้อง (พบ 9 errors เช่น rate-limit)
- `fed_press_releases_classification_progress.json` — แฟ้มติดตามความคืบหน้าของการจำแนก
- ไฟล์แม่ (ดิบ, ไม่ได้ classified): `dataset/news/fed/fed_press_releases.jsonl`

### ตัวอย่าง record (สรุป)
```json
{
  "document_id": "f55b7cb4d4d597c9a9e341df2b5805bf8cab633a",
  "title": "Frederic S. Mishkin sworn in as member of the Board of Governors",
  "publication_date": "2006-09-05",
  "document_type": "general",
  "content": "Frederic S. Mishkin on Tuesday took the oath of office as a member ...",
  "classification": {
    "label": "not_relevant", "confidence": 95,
    "reason": "บทความนี้รายงานการสาบานตนเข้ารับตำแหน่ง ... ไม่มีผลต่อราคาทองคำ",
    "evidence": [], "topics": []
  },
  "classification_metadata": { "model": "openthaigpt-thaillm-8b-instruct-v7.2",
                               "prompt_version": "fed-gold-relevance-v1.0", ... }
}
```

---

## 3. BLS — NFP (Employment Situation) — `dataset/news/bls/nfp/clean/`

### คำอธิบาย
รายงานประจำเดือน **"The Employment Situation"** (รายงานการจ้างงาน/Non-Farm Payroll)
จากสำนักสถิติแรงงานสหรัฐฯ (Bureau of Labor Statistics) ตั้งแต่ปี 2006 ถึง 2026
ที่ถูกทำความสะอาด (ลบ header/footer, คงโครงสร้างตารางแบบ raw text block)
แล้วแยกพาดหน้าเป็น **chunks พร้อมหัวข้อ** เพื่อใช้ chunk-based embedding ได้ทันที

### โครงสร้าง (1 ไฟล์ JSON ต่อ 1 รายงานประจำเดือน, ตั้งชื่อ `empsit_<MMDDYYYY>_clean.json`)
```jsonc
{
  "doc_id": "bls_nfp_2012_12",                 // เดือนรายงาน (Jan 2012 data → ไฟล์ 01042013 = ประกาศ 4 ก.พ. 2013)
  "source": "U.S. Bureau of Labor Statistics",
  "source_file": "empsit_01042013.txt",        // ไฟล์ raw ต้นทาง
  "source_url": "https://www.bls.gov/news.release/archives/empsit_01042013.htm",
  "publication_date": "2013-01-04",            // วันที่ประกาศ
  "report_period": "December 2012",            // เดือนข้อมูลที่รายงาน
  "title": "THE EMPLOYMENT SITUATION -- DECEMBER 2012",
  "content_type": "Employment Situation news release",
  "cleaning": {
    "header_removed": true,
    "footer_removed_from_last_modified_date": true,
    "table_a_parsed": true,                     // ตาราง A (สรุป) ถูกแยกออกอัตโนมัติ
    "table_a_format": "nfp_summary_table_tab",
    "tables_preserved_as_raw_blocks": [         // ตารางที่เก็บเป็น raw block (เก็บรูปแบบเดิม)
      "A_rev", "B_rev", "B", "A-1","A-2","A-3", ... "B-9"
    ]
  },
  "chunks": [
    {
      "chunk_id": "bls_nfp_2012_12_001",         // doc_id + running number (001, 002, ...)
      "heading": "Overview",                     // หัวข้อ (Overview, Household Survey Data, ...)
      "content": "Nonfarm payroll employment rose by 155,000 ...",  // เนื้อหา section ตามตัวหนังสือ
      "source_file": "empsit_01042013.txt",
      "source_url": "https://www.bls.gov/news.release/archives/empsit_01042013.htm",
      "publication_date": "2013-01-04",         // ← ทำซ้ำในทุก chunk เพื่อ filter/ติด metadata ง่าย
      "report_period": "December 2012"
    },
    { "chunk_id": "bls_nfp_2012_12_002", "heading": "Household Survey Data", ... }
  ]
}
```

### สถิติ
- ไฟล์รายงาน **248 ไฟล์**, รวมทั้งหมด **3,535 chunks**
- วันที่ประกาศตั้งแต่ **2006-01-06** ถึง **2026-10-02** (รายเดือน ประมาณเดือนละ 1 รายงาน)
- **ภาษาอังกฤษทั้งหมด** → ใช้ embedding model อังกฤษมาตรฐานได้

### ตัวอย่างพาดหน้าโครงสร้าง
```
doc_id:    bls_nfp_2012_12         (ประกาศ 4 ม.ค. 2013, ข้อมูลเดือน ธ.ค. 2012)
chunks[0]: { chunk_id: "..._001", heading: "Overview",
             content: "Nonfarm payroll employment rose by 155,000 in December, and the
                       unemployment rate was unchanged at 7.8 percent, the U.S. Bureau
                       of Labor Statistics reported today. ..." }
chunks[1]: { chunk_id: "..._002", heading: "Household Survey Data", ... }
```

---

## 4. BLS — CPI — `dataset/news/bls/cpi/` (โฟลเดอร์ `clean/`)

### คำอธิบาย
รายงานดัชนีราคาผู้บริโภค (Consumer Price Index) ประจำเดือนของ BLS (CPI-U)
ตั้งแต่ปี 2006 ถึง 2026 ใช้สโนร์ม schema เดียวกับ NFP — รายงาน 1 เดือน = 1 ไฟล์ JSON
ที่แยกเนื้อหาเป็น chunks พร้อมหัวข้อแล้ว ใช้เป็นข่าว/ข้อมูลเงินเฟ้อที่เกี่ยวพันมาก
ที่สุดกับราคาทองคำ (ทองมักใช้ hedge inflation)

### โครงสร้าง (1 ไฟล์ JSON ต่อ 1 รายงานประจำเดือน, ตั้งชื่อ `cpi_<MMDDYYYY>_clean.json`)
```jsonc
{
  "doc_id": "bls_cpi_2018_12",                 // ข้อมูลเดือน ธ.ค. 2018 → ประกาศ 11 ม.ค. 2019
  "source": "U.S. Bureau of Labor Statistics",
  "source_file": "cpi_01112019.txt",
  "source_url": "https://www.bls.gov/news.release/archives/cpi_01112019.htm",
  "publication_date": "2019-01-11",
  "report_period": "December 2018",
  "title": "CONSUMER PRICE INDEX – DECEMBER 2018",
  "content_type": "CPI news release",
  "cleaning": {
    "header_removed": true,
    "footer_removed_from_last_modified_date": true,
    "table_a_parsed": true,
    "table_a_format": "cpi_fixed_dot_leader",
    "tables_preserved_as_raw_blocks": ["1","2","3","4","5","6","7"]
  },
  "chunks": [
    {
      "chunk_id": "bls_cpi_2018_12_001",
      "heading": "Overview",
      "content": "The Consumer Price Index for All Urban Consumers (CPI-U) declined 0.1 percent
                  in December on a seasonally adjusted basis ...",
      "source_file": "...", "source_url": "...",
      "publication_date": "2019-01-11", "report_period": "December 2018"
    }
  ]
}
```

### สถิติ
- ไฟล์รายงาน **248 ไฟล์**, รวม **3,054 chunks**
- วันที่ประกาศตั้งแต่ **2006-01-18** ถึง **2026-10-14**
- **ภาษาอังกฤษทั้งหมด**

### ไฟล์อื่นในโฟลเดอร์ cpi/ (นอก clean/)
- `cpi_manifest.csv` — สารบัญรายการไฟล์รายงาน CPI (ลำดับ, วันที่, URL ต้นทาง) ไว้ดู metadata โดยไม่ต้องเปิดไฟล์เนื้อหา
- `text/` — เนื้อหา raw ที่ยังไม่ได้ทำ chunk

---

## การใช้งานกับ Vector DB (แนะเสนอ)

### Schema metadata ทุก record ควรติดตอยู่
| field | PBS | Fed | NFP | CPI |
|---|---|---|---|---|
| id | `article_id` | `document_id` | `chunk_id` | `chunk_id` |
| แหล่งที่มา | `Thai PBS` | `Federal Reserve` | `BLS-NFP` | `BLS-CPI` |
| วันที่ | `published_at` | `publication_date` | `publication_date` | `publication_date` |
| เดือนข้อมูล | — | — | `report_period` | `report_period` |
| ภาษา | ไทย | อังกฤษ | อังกฤษ | อังกฤษ |
| การจำแนก (filter ก่อน embed) | `classification.relevance = "direct"` | `classification.label = "relevant"` | — | — |
| URL | `source.url` | `url` | `source_url` | `source_url` |

### ข้อแนะนำในการ pipeline
1. **กรองก่อน embed** — PBS: เฉพาะ `relevance = direct` | Fed: เฉพาะ `label = relevant`
   (จะได้แค่ 536 ฉบับจาก 4,553 ตัดขนาด DB และ noise ได้มหาศาล), BLS: embed ทุก chunk
   เพราะเป็นข้อมูลหลักเชิงเศรษฐกิจที่โดยตรง payload เตลิดชิ้น
2. **Chunking** — NFP/CPI ทำ chunk ไว้แล้ว (ใช้ `chunks[]` ขวัย้างตรง);
   PBS/Fed ยังเป็นข้อความเต็ม ยังต้องสร้าง chunk ก่อน
3. **Embedding model** — ต้องเลือกแบบรองรับ 2 ภาษา (ไทย-อังกฤษ), หรือแยก
   collection ไทย/อังกฤษ แล้ว cross-retrieve เพื่อไม่ให้ภาษากลายเป็นข้อจำกัด
4. **Time-aware retrieval** — ทุก record มี `publication_date`/`report_period` ให้
   filter ช่วงเวลาได้ จำใช้ตอนระวังการอำลาโลกเก่าและไม่ให้ข่าวย้อนหลังรั่วเข้ามา
5. **สอดคล้องกับราคาทอง** — Dataset นี้คู่กับ CSV ราคาทองรายวัน
   (`gold_price_2006_2026.csv`) เพื่อ join "ข่าว/ข้อมูลประกาศ ↔ ราคาทองวันนั้น"
   ทั้งจาก vector retrieval และ event study
