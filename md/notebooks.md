# Notebooks ที่ใช้จริงของโปรเจกต์ Gold Assistant

เอกสารสำหรับสังเขป Jupyter notebook แต่ละไฟล์ที่**ถูกใช้จริง**ใน pipeline
การเก็บและเตรียมข้อมูล เพื่อให้ผู้อ่านคนใหม่เข้าใจภาพรวมได้เร็ว
โครงเรื่องวางตาม [flow.md](flow.md) — แยก Dataset A (ราคาทอง) กับ Dataset B (ข่าว/เหตุการณ์)

- แผนภาพ pipeline: [notebooks_diagram.html](notebooks_diagram.html) (เปิดดับเบิลคลิกใน browser ได้เลย)
- รายละเอียด output ที่ได้และ schema: [dataset_vector_db.md](datset_vector_db.md)

---

## Dataset A — ราคาทองคำ (สมาคมค้าทองคำ / Thai Gold Traders)

### 1. `dataset/datset a gold price/Dataset A_gold price.ipynb`

| | |
|---|---|
| **หน้าที่** | อ่านตาราง `informationTable` จากไฟล์ `gold price.html` (คัดลอกตารางจาก https://gtadmin.goldtraders.or.th/updatepricelist/) แล้วแปลงเป็น DataFrame |
| **ขนาด** | 61 code cells |
| **library หลัก** | `pandas`, `matplotlib`, `numpy` |
| **อ่าน** | คอลัมน์ วันที่ / เวลา / ครั้งที่ / ทองรูปพรรณ / ทองแท่ง / Gold Spot / THB / การปรับเปลี่ยน |
| **ผลลัพธ์** | CSV ดิบที่ยังมีค่า (NaN, null) ตามต้นฉบับ ส่งต่อไปขั้นที่ 2 |

### 2. `dataset/datset a gold price/Dataset A_gold price cleaned.ipynb`

| | |
|---|---|
| **หน้าที่** | ทำความสะอาด + วิเคราะห์สำรวจ (EDA) ต่อขั้นจาก notebook แรก ให้ข้อมูลพร้อมใช้ |
| **ขนาด** | 134 code cells — ใหญ่ที่สุดในโปรเจกต์ |
| **library หลัก** | `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy` (pearsonr, spearman) |
| **ขั้นหลัก** | แปลงวันที่, จัดการ null/NaN, ตรวจสอบคุณภาพให้เงียบและมีข้อมูลในแต่ละวัน, วาดภาพโค้งราคา 20 ปี |
| **ผลลัพธ์** | [`gold_data_cleaned.csv`](../dataset/datset%20a%20gold%20price/gold_data_cleaned.csv) — 24,519 แถว (2006-05 → 2026-10) |

---

## Dataset B — ข่าว / เหตุการณ์ (Event data)

### 3. `dataset/news/Dataset B_Event_thaipbs.ipynb` — ข่าวทองภาษาไทย

| | |
|---|---|
| **หน้าที่** | ดึงข่าวจาก Thai PBS API (`https://api.thaipbs.net`), บันทึกเป็น JSONL, แล้วให้ LLM ภาษาไทย (ThaiLLM `openthaigpt-thaillm-8b-instruct-v7.2` ผ่าน endpoint แบบ OpenAI-compatible) จำแนกความเกี่ยวข้องกับราคาทอง: `direct` / `indirect` / `uncertain` พร้อมเหตุผลและหลักฐาน |
| **การจัดคีย์** | ใช้ `dotenv` อ่าน API key จาก `.env` (แยก client key ออกจากโค้ดไว้เรียบร้อย) |
| **ผลลัพธ์** | `dataset/news/pbs/gold_relevance_audit_v2.jsonl` → แยกเป็น `gold_audit_direct.jsonl` / `gold_audit_indirect.jsonl` / `gold_audit_uncertain.jsonl` |

### 4. สาย Federal Reserve — 4 ไฟล์, จำนวน 4 ขั้น (ทำต่อกันเป็น pipeline)

| # | Notebook | หน้าที่ | Input → Output |
|---|---|---|---|
| 4.1 | `Dataset B_Event_fed.ipynb` | scrape แถลงการณ์ press releases ของ Federal Reserve Board ทุกปีตั้งแต่ 2006 แล้วเก็บเป็น JSONL | เว็บ federalreserve.gov → `fed_press_releases.jsonl` |
| 4.2 | `Dataset B_Event_fed_cleaned.ipynb` | ทำความสะอาด — แก้ encoding เสีย (ระบุจำนวนซ่อม), ลบข้อมูลสื่อท้ายเอกสาร, บันทึก `cleaning_flags`, คำนวณ `document_id` (SHA1) กันซ้ำ, ดึง `publication_date` | `fed_press_releases.jsonl` → ไฟล์ cleaned |
| 4.3 | `Dataset B_Event_fed_classified.ipynb` | จำแนกด้วย LLM: label `relevant` / `uncertain` / `not_relevant` พร้อมเหตุผล-หลักฐาน (แบบ parallel threads, มีจัดการ rate-limit ด้วย, บันทึก progress/errors แยกไฟล์) | cleaned → `fed_press_releases_classified.jsonl` |
| 4.4 | `Dataset B_Event_fed_audit_v2.ipynb` | audit รอบสอง — ตรวจความเกี่ยวข้องบทความที่จำแนกไปแล้ว เพื่อบอกว่าก่อนไป vector DB ผลที่สุดของ label นั่นแน่นอน | classified → `fed/.../fed_press_releases_cleaned_audit/` |

ไฟล์อื่นที่เหลืออยู่ในโฟลเดอร์ (`Dataset B_Event_fed_audit.ipynb`, `Dataset B_Event_fed_audit_backup.ipynb`, `Dataset B_Event_fed_classified.ipynb.bak`) เป็น draft/backup เก่า — อย่าใช้ ใช้ 4.4 (`_v2`) ขั้นสุดท้ายแทน

### 5. `dataset/news/Dataset B_Event_bls_NFP.ipynb` — Employment Situation (การจ้างงาน / NFP)

| | |
|---|---|
| **หน้าที่** | ดึงรายงานประจำเดือน "The Employment Situation" จากหลังหน้า archive ของ BLS ปี 2008–2026 แล้วทำความสะอาด + แยก chunks ตามหัวข้อ |
| **รายละเอียด** | ทำงานแบบ async (`aiohttp` + `playwright` สำหรับหน้าที่ต้องการ JS) ตัด header/footer ตาม "Last modified", แยก parse ตารางสรุป A, ตารางอื่นเก็บเป็น "raw blocks" คงรูปแบบเดิม |
| **ผลลัพธ์** | [`dataset/news/bls/nfp/clean/`](dataset/news/bls/nfp/clean/) — 248 ไฟล์ `empsit_<MMDDYYYY>_clean.json` รวม 3,535 chunks (2006-01-06 → 2026-10-02) |

### 6. `dataset/news/Dataset B_Event_bls_cpi.ipynb` — Consumer Price Index (เงินเฟ้อ / CPI)

| | |
|---|---|
| **หน้าที่** | เหมือนตอนข้อ 5 — ดึงรายงาน CPI-U ประจำเดือนของ BLS แบบ 2008–2026 แล้ว clean และแยก chunks ตามหัวข้อเหมือนกัน |
| **รายละเอียด** | ตารางรูปแบบ "dot leader" (จุดแบน) ของรายงาน CPI ถูกแยก parse อัตโนมัติเช่นกัน |
| **ผลลัพธ์** | [`dataset/news/bls/cpi/clean/`](dataset/news/bls/cpi/clean/) — 248 ไฟล์ `cpi_<MMDDYYYY>_clean.json` รวม 3,054 chunks (2006-01-18 → 2026-10-14) |

---

## แผนภาพ

```
Dataset A : gold price.html ──▶ 1. Dataset A_gold price.ipynb ──▶ 2. ... cleaned.ipynb ──▶ gold_data_cleaned.csv

Dataset B
 ├── 3. Thai PBS     : Dataset B_Event_thaipbs.ipynb ────────────────────────────────────▶ pbs/gold_relevance_audit_v2.jsonl
 ├── 4. Federal Res. : 4.1 fed ─▶ 4.2 fed_cleaned ─▶ 4.3 fed_classified ─▶ 4.4 fed_audit_v2 ─▶ fed/.../classified.jsonl
 ├── 5. BLS NFP      : Dataset B_Event_bls_NFP.ipynb ────────────────────────────────────▶ bls/nfp/clean (248 ไฟล์)
 └── 6. BLS CPI      : Dataset B_Event_bls_cpi.ipynb ────────────────────────────────────▶ bls/cpi/clean (248 ไฟล์)
```
