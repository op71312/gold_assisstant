# Task Brief for AI Coding Agent — Autonomous Root-Cause Analysis and Multi-Variant Experiments for Gold Assistant GAIB-1

## เป้าหมายหลัก

คุณเป็น Senior Research/ML Systems Engineer ที่รับผิดชอบตรวจและปรับปรุง notebook `Gold_Assistant_GAIB1_Reliability_Experiment_Phase1_2(1).ipynb` (ถ้าไม่มีให้หาไฟล์ชื่อใกล้เคียงที่สุดใน workspace) เพื่อทำให้ระบบ Gold Assistant วัดผลได้อย่างถูกต้อง, ค้น evidence ได้ตรงขึ้น, ส่งข้อมูลระหว่าง Agent อย่างมี schema, สร้าง citations ที่ตรวจสอบย้อนกลับได้ และมี benchmark ที่บอกได้ว่าการเปลี่ยนแปลงใดช่วยจริง

**คุณต้องสืบหาสาเหตุเอง ทดลองแนวทางมากกว่าหนึ่งแบบ วัดผล เปรียบเทียบ และเลือกจากหลักฐาน ห้ามหยุดที่การเสนอคำแนะนำ ห้ามแก้ทุกอย่างพร้อมกัน และห้ามประกาศว่าผ่านเพียงเพราะ notebook รันจบ**

ใช้ ThaiLLM ต่อไปตาม configuration ปัจจุบัน ห้ามย้ายไป Gemini หรือเปลี่ยน provider/model โดยไม่จำเป็นและไม่มีผลทดลองรองรับ รักษาสถาปัตยกรรม Qdrant + Cloudflare embeddings + local BM25 + RRF + Jina reranker และ AI1–AI5 เป็น baseline จนกว่าจะมีหลักฐานว่าองค์ประกอบใดเป็นต้นเหตุหรือไม่มีประโยชน์

---

## 0. กฎความปลอดภัยและการทำงาน

1. **ห้ามเขียนทับ notebook ต้นฉบับ** ให้สร้างสำเนาใหม่ชื่อ `Gold_Assistant_GAIB1_Reliability_Experiment_Phase3.ipynb` และเก็บไฟล์ source เดิมพร้อม checksum ไว้
2. ก่อนแก้ ให้สำรวจ workspace, notebook, source data, current benchmark outputs และ environment variable names เท่าที่จำเป็น ห้าม print ค่า API keys/tokens, connection strings หรือ secrets ลง output/log
3. ทำ audit แบบ offline ก่อน ทุก function สำคัญต้องมี unit tests ที่ไม่เรียก API จริง ใช้ mocks/fixtures สำหรับ Qdrant, Cloudflare, Jina และ ThaiLLM
4. ห้ามยิง test split เพื่อปรับ prompt, token budget, BM25 tokenizer, RRF K หรือ candidate count ใช้ `development` สำหรับ diagnosis/tuning; validation ใช้เลือก candidate configuration; test/holdout ใช้ครั้งสุดท้ายเมื่อ configuration ถูกล็อกแล้วเท่านั้น
5. ห้ามสร้าง ground-truth labels, relevance judgments, evidence IDs หรือคำตอบที่อ้างว่าเป็นผลจริงขึ้นมาเอง ถ้า label ไม่พอ ให้บันทึก `UNJUDGED`/`NOT_EVALUATED` และระบุข้อมูลที่ต้องเติม
6. ห้ามเปลี่ยน semantics ของ metric เพื่อให้คะแนนสูงขึ้น ห้ามนับ `NO_CITATIONS`, `NO_CLAIMS`, `NOT_EVALUATED`, failed queries หรือ coverage-ineligible queries เป็น 0/1 โดยไม่ระบุ denominator และ policy อย่างชัดเจน
7. ทุกการทดลองต้องระบุ hypothesis, change, control, fixed variables, dataset/split, query IDs, metric, result, resource usage, interpretation, limitations และ decision
8. ทำ one-factor-at-a-time ในขั้น diagnosis ก่อน แล้วจึงทำ small factorial/interaction tests เฉพาะปัจจัยที่มีหลักฐานเกี่ยวข้อง ห้ามสุ่มเปลี่ยนหลาย config พร้อมกันจนหาสาเหตุไม่ได้
9. ใส่ budget guard สำหรับ external calls เช่น `MAX_REMOTE_COMPLETION_REQUESTS`, `MAX_EMBEDDING_REQUESTS`, `MAX_RERANK_REQUESTS`, `MAX_EXPERIMENT_VARIANTS` ให้ตรวจงบก่อน call ทุกครั้ง หากงบหมดต้องหยุดอย่างสะอาดและเขียนผลที่ทำเสร็จแล้ว
10. ห้ามเอา model-generated judge มาเรียกว่า ground truth; ถ้าใช้ LLM-as-judge ต้องแยก metric, calibrate กับ human-reviewed subset, เก็บ prompt/version และติดป้าย `AUTOMATED_JUDGE_NOT_HUMAN_GOLD`
11. ให้ notebook รันจากบนลงล่างได้ใน fresh kernel โดยไม่พึ่งตัวแปรจากการรันเก่าหรือ output cell ที่ cache ไว้
12. หลังทุก phase ให้บันทึก checkpoint/CSV/JSON และพิมพ์ผลสรุป รวม traceback ฉบับเต็มเมื่อเกิด exception

---

## 1. Baseline ที่ต้องบันทึกก่อนแก้

ผล benchmark ล่าสุดที่ผู้ใช้ให้มา:

- Retrieval: 5 queries; coverage-eligible = 5
- Hybrid known-relevant Recall@10 = 0.40; median = 0.0
- Hybrid MRR@10 = 0.065; nDCG@10 = 0.14046
- Reranked Recall@10 = 0.40; MRR@10 = 0.22222; nDCG@10 = 0.26021
- Multi-agent: attempted/completed = 5/5; completion rate = 1.0
- API success rate = 1.0; JSON parse rate = 0.68; schema-valid rate = 0.48
- Task success = `NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE`
- Latency P50 = 23,128.66 ms; P95 = 73,818.57 ms
- Mean tokens = 29,862.2 per query
- Report citation presence = 0.20
- Citation ID validity when present = 1.0
- Mean claim citation coverage = 0.25
- Mean citation paragraph coverage = 0.13333
- Semantic citation support = `NOT_HUMAN_REVIEWED`

ผลเหล่านี้เป็น **baseline เฉพาะชุด 5 queries** ไม่ใช่ข้อสรุปทั่วไปของระบบ และไม่ใช่เกณฑ์ที่ยอมรับความถูกต้องของคำตอบได้แล้ว

### สร้าง baseline immutable

สร้าง `experiment_outputs/<run_id>/baseline_manifest.json` ซึ่งบันทึก:
- notebook source checksum + source filename
- Python/package versions, OS, timestamp, timezone
- model/provider identifiers (ห้าม secrets), prompt/schema version
- dataset paths, source count, corpus count, Qdrant collection/vector name, embedding model
- `DENSE_CANDIDATES`, `BM25_CANDIDATES`, `HYBRID_CANDIDATES`, `FINAL_K`, `RRF_K`
- BM25 tokenizer implementation, chunk chars/overlap, `CONTEXT_MAX_CHARS`, per-chunk limit
- reranker model, ThaiLLM token limits, timeout, retry/repair settings, concurrency setting
- split, query IDs, coverage status, benchmark config hash

หาก baseline ที่ให้มาจาก CSV ไม่ครบ ให้รันเฉพาะ smoke baseline ที่กำหนดงบไว้ และระบุความแตกต่าง ห้ามสร้าง baseline ตัวเลขขึ้นมาแทน

---

## 2. สร้าง Autonomous Diagnosis Harness ก่อนแก้ระบบ

ให้ทำ diagnostic runner ที่สามารถอ่าน notebook/functions และข้อมูล benchmark ปัจจุบัน สร้าง root-cause candidates ตามหลักฐาน ทดสอบทีละสมมติฐาน และเขียนรายงานโดยไม่ต้องให้ผู้ใช้ชี้จุดเอง

### 2.1 สร้าง artifact อย่างน้อย

ภายใต้ `experiment_outputs/<run_id>/` ให้สร้าง:

1. `root_cause_register.csv` — suspected cause, supporting evidence, counter-evidence, confidence, test, result, verdict (`CONFIRMED`/`LIKELY`/`REJECTED`/`UNRESOLVED`)
2. `experiment_plan.csv` — variant matrix, hypothesis, independent variable, control, fixed variables, query IDs, API estimate, run status
3. `experiment_results.csv` — หนึ่งแถวต่อ variant/config/query พร้อม metrics และ usage
4. `retrieval_case_diagnostics.csv` — query, expected document group, source file, corpus match, Qdrant match, content match, dense rank, BM25 rank, RRF rank, Jina rank, exclusion reason
5. `retrieval_stage_candidates.jsonl` — candidates + IDs + rank + raw scores + normalized aliases ต่อ stage
6. `schema_error_breakdown.csv` — agent, field/path, failure class, first attempt, repair result, finish reason, tokens, latency
7. `agent_attempt_telemetry.jsonl` — ทุก model attempt รวม failed API attempts, response status, finish reason, parse/schema status, tokens, latency; redact secrets
8. `citation_audit_detailed.csv` — raw proposed IDs vs allowed/accepted IDs, report presence, claim counts, valid-ID counts, support status, exclusion reason
9. `latency_token_breakdown.csv` — per-query/per-agent/per-attempt and retrieval-stage timing/tokens
10. `experiment_decision_report.md` — root causes, evidence, tested variants, comparisons, chosen config, remaining uncertainty, next actions
11. `reliability_regression_tests.json` หรือ `.csv` — test name, expected, actual, pass/fail, artifact pointer
12. `patch_summary.md` — exact functions/cells changed, reason, risk, how to roll back

ต้องมี `run_id` และ config hash ในทุก row ที่ใช้เปรียบเทียบ

### 2.2 Process ที่ต้องทำซ้ำได้

สำหรับแต่ละ suspected cause:

1. ระบุ failure ที่เห็นจริงจาก log (ไม่ใช่คาดเดา)
2. สร้าง minimal reproducer/unit test
3. เสนอสมมติฐานอย่างน้อย 2 แบบที่อธิบายข้อมูลเดียวกันได้
4. ออกแบบการทดสอบเพื่อแยกสมมติฐาน (discriminating test)
5. ทดลอง baseline แล้วทดลอง variant แบบเปลี่ยนทีละปัจจัย
6. บันทึกผลและข้อผิดพลาดทั้งหมด
7. ยอมรับสมมติฐานก็ต่อเมื่อ test สนับสนุน; ถ้าผลไม่ชี้ขาดให้บอก `UNRESOLVED`
8. ทำ regression test กันไม่ให้ปัญหาเดิมกลับมา

ห้ามใช้ “ดูเหมือน”, “น่าจะ” เป็นคำสรุปสุดท้ายโดยไม่มีผลทดสอบรองรับ

---

## 3. Workstream A — Retrieval: แก้สาม query ที่พลาด และทดสอบหลายวิธี

### ปัญหาที่เห็น

Baseline Recall@10 = 0.40; Jina เพิ่ม MRR/nDCG แต่ไม่เพิ่ม Recall โดยรวม มี query ที่ Dense, BM25 และ Hybrid ไม่พบ expected doc ใน ranking ตาม report ล่าสุด ทั้งนี้ coverage audit ที่ผ่านไม่ได้รับประกันว่า text ที่ใช้ค้นหาเหมือน source span หรือ identifier mapping ถูกต้องทุกจุด

### 3.1 ตรวจ ID/corpus/index ก่อนปรับ ranking

ใน `normalize_chunk()` ปัจจุบัน `chunk_id` มี fallback ไปยัง `document_id` และ `document_id` มี fallback กลับไปยัง `chunk_id`; ใน `dense_search()` local lookup ใช้ payload `chunk_id`; ใน `chunk_identity()` ใช้ `chunk_id` ก่อน `document_id`. **นี่คือสมมติฐานที่ต้องทดสอบ ไม่ใช่สรุปว่าเป็น root cause แล้ว**

ทำ audit อย่างน้อย:

- นับ blank/missing `chunk_id`, `document_id`, `url`, text และ source date
- นับ duplicate IDs และ collision ระหว่าง chunk/document IDs
- เปรียบเทียบ local BM25 corpus กับ Qdrant payload: count, stable IDs, document ID aliases, chunk ID aliases, URL aliases, text hashes
- ตรวจว่า local corpus file จริงเป็น version เดียวกับ Qdrant collection หรือไม่
- สำหรับทุก expected evidence group ตรวจว่า source file มีอยู่, exact quote อยู่ใน source, quote อยู่ใน raw document, text อยู่ใน chunk, chunk อยู่ใน local BM25 corpus และ point อยู่ใน Qdrant
- แยก `source_exists`, `source_text_match`, `chunk_text_match`, `bm25_corpus_match`, `qdrant_payload_match`, `query_retrieval_match` เป็นคนละ field
- ห้ามให้ `COVERED` อาศัยการ match alias อย่างเดียว ถ้าไม่ได้ยืนยัน identity/contents; ออกแบบ status แยก `SOURCE_VERIFIED`, `CORPUS_VERIFIED`, `INDEX_VERIFIED`, `RETRIEVAL_MATCHED`
- ตรวจ candidate mapping ว่า Qdrant point ที่ได้ map เป็น local chunk ที่ถูกต้องหรือ fallback ไป normalize payload จน `chunk_id`/`document_id` เปลี่ยนความหมาย
- ตรวจ raw scores, query vector dimension, Qdrant collection vector dimensions/name/distance metric, embedding model consistency กับการ build index โดยไม่เปลี่ยน production collection
- อย่า scroll/log vectors หรือ API secrets; metadata และ text excerpt สั้น ๆ พอสำหรับการวินิจฉัย

### 3.2 ทำ controlled retrieval experiment matrix

สร้าง retrieval experiment runner ที่คำนวณ dense/BM25 outputs เพียงครั้งเดียวเมื่อทำได้ แล้ว reuse outputs สำหรับ fusion variants เพื่อลด remote callsและควบคุมความแปรปรวน

| Variant | สิ่งที่เปลี่ยน | จุดประสงค์ |
|---|---|---|
| R0 | Baseline: Dense 40 + BM25 40 + RRF K=60 + Jina Top 10 | Control |
| R1 | Dense-only | แยกคุณค่าของ dense retrieval |
| R2 | BM25-only | แยกคุณค่าของ lexical retrieval |
| R3 | Hybrid RRF K=20 | ทดสอบ rank-fusion parameter |
| R4 | Hybrid RRF K=60 | Control สำหรับ K |
| R5 | Hybrid RRF K=100 | ทดสอบ rank-fusion parameter |
| R6 | Candidate pool 20/20 | ดูต้นทุนและ recall ที่ candidate depth ต่ำ |
| R7 | Candidate pool 60/60 (ถ้า budget/latency อนุญาต) | ตรวจว่าขาด candidate depth หรือไม่ |
| R8 | Jina off: RRF Top 10 | วัด incremental value ของ reranker |
| R9 | Jina rerank 20/40 candidates แล้วเอา Top 10 | ตรวจ candidate pool/latency trade-off |
| R10 | Current Thai `newmm` tokenizer | Control lexical preprocessing |
| R11 | Fallback regex tokenizer | เทียบการตัดคำที่มีอยู่ใน code |
| R12 | Thai character/bigram or word+bigram variant | ทดลองเฉพาะเมื่อวิเคราะห์ failure ชี้ว่า tokenization คือสาเหตุ |
| R13 | query normalization แบบไม่เปลี่ยนความหมาย (วันที่, punctuation, FOMC aliases) | ตรวจ exact terminology/date mismatch |
| R14 | metadata-aware BM25 ที่ใส่ title/date/period ซ้ำอย่างมีน้ำหนัก | ทดลองเฉพาะเมื่อ corpus audit พบ field สำคัญไม่อยู่ใน indexed text |

ห้ามต้องทดลองทุก variant หาก early diagnosis หักล้างสมมติฐานได้ ให้บันทึกเหตุผลที่ยุติ variant นั้น

### 3.3 Metrics และการตัดสิน

เก็บ Dense/BM25/RRF/Jina Recall@5/@10/@20/@40 (ตาม candidate size), MRR@10, nDCG@10, first-relevant rank, expected-document coverage, rank of expected doc, unique document count, duplicate chunk rate, retrieval latency, embedding/rerank calls

- Candidate recall เป็นข้อจำกัดบนสุด: reranker ไม่สามารถนำเอกสารที่ไม่อยู่ใน input มาจัดอันดับได้
- ถ้า source/index ไม่ถูกต้อง ห้ามใช้ query นั้นวัด ranking algorithm
- ถ้าเอกสารมีใน index และอยู่ใน text แต่ทั้ง Dense/BM25 หาไม่พบ ให้ทดลอง ranking/tokenization/query normalization อย่างมีหลักฐาน
- ถ้าระบบค้นเจอแต่ rank ต่ำ ให้พิจารณา fusion/reranking และเปรียบเทียบกับ no-rerank
- ใช้ per-query rows ควบคู่กับ aggregate; 5 queries เป็น sample เล็ก ห้ามอ้างนัยสำคัญทางสถิติจากค่าเฉลี่ยเพียงอย่างเดียว
- เก็บ relevance judgments เดิม; ห้ามแก้ judgment เพื่อให้ variant ใหม่ได้คะแนนสูงขึ้น
- หาก judgments ไม่ exhaustive ให้เรียกค่า metric `known_relevant_*` และอธิบายว่าค่านี้วัด judged docs ที่ทราบเท่านั้น

### 3.4 Selection policy

เลือก candidate config จาก development results โดยเรียงลำดับ:
1. Source/index integrity ผ่าน
2. Candidate Recall ไม่แย่ลงอย่างชัดเจน
3. nDCG/MRR ดีขึ้นใน queries ที่ candidate มี expected docs
4. ไม่มี regression รุนแรงใน query ใด query หนึ่ง
5. latency/API calls อยู่ใน budget
6. ทดสอบ finalist บน validation set แล้วล็อก config ก่อน test/holdout

อย่าเลือก config จากคะแนนเฉลี่ยอย่างเดียวหากทำให้ query ที่เคยผ่านล้มเหลว หรืออาศัยจูนกับ 5 queries เดิมอย่างเดียว

---

## 4. Workstream B — Agent JSON/schema reliability

### ปัญหาที่เห็น

JSON parse rate 0.68; schema-valid rate 0.48. ปัจจุบัน `call_agent_json()` ทำได้สูงสุดสอง generation-level attempts (initial + 1 repair) และ `ThaiLLMClient.generate()` มี retry ภายในสำหรับ API transport; เป็นคนละ retry layer ต้องนับแยกกัน

จุดใน implementation ที่ต้องตรวจ:

- `validate_agent_schema()` ตรวจ required types/บาง nested keys แต่ไม่ได้ตรวจชนิดข้อมูล/enum/empty constraints ทุก nested fields เท่ากันทุก Agent
- ถ้า `finish_reason` บ่งชี้ `length` function หยุดทันทีและไม่ทำ structured repair
- `api_success` ตั้ง True เมื่อมี response สักครั้ง ไม่ได้แยก initial/final attempt outcome อย่างสมบูรณ์
- `parse_success` อาจคงค่าจาก attempt ก่อน หาก attempt ถัดไปเกิด exception ก่อน parse; จึงต้องมี per-attempt states แทนการอาศัย boolean สุดท้ายค่าเดียว
- `attempt_count=len(responses)` ไม่นับ transport/API attempts ที่เกิด exception เพราะ responses เก็บเฉพาะ successful response payloads
- summary มี `json_valid_rate` อ่านจาก `agent_json_valid_rate`, แต่ benchmark result อาจไม่มี column นี้ จึงเกิดค่าว่าง; ให้ตรวจ schema ของ dataframe จริงและแก้ source-of-truth แทนการเติม 0

### 4.1 ทำ per-attempt state machine

เก็บ record ต่อ generation attempt:
- query_id, agent, attempt_index, stage (`initial`/`repair`/`retry`), provider/model
- API request attempted, API response received, transport/API error class
- finish_reason, latency, prompt/completion/total tokens
- raw-output checksum, raw output (แยกไฟล์และจำกัดสิทธิ์; redact sensitive strings)
- JSON parse result, schema result, schema error list, invalid evidence IDs
- repair strategy/prompt version, final promoted/not promoted

สร้าง aggregates ที่มี semantics ไม่ซ้อนกัน:
- `api_attempt_success_rate` = successful HTTP/API responses / actual API requests
- `agent_any_response_rate` = agent calls ที่ได้รับ response อย่างน้อยหนึ่งครั้ง / agent calls
- `first_attempt_json_parse_rate`
- `final_attempt_json_parse_rate` = output จาก attempt สุดท้ายที่ได้รับจริง parse ได้หรือไม่; if no final response -> `NOT_AVAILABLE` ไม่ใช่ True
- `first_attempt_schema_valid_rate`
- `post_repair_schema_valid_rate`
- `full_schema_pass_query_rate` = queries ที่ Agent ทุกตัวที่ task plan ต้องใช้ผ่าน schema / completed queries
- `promoted_output_schema_valid_rate` ต้อง 100% โดย design; invalid output ห้ามส่ง downstream เป็น structured result
- `repair_recovery_rate` = invalid initial outputs ที่ repair แล้วผ่าน / invalid initial outputs ที่มี repair
- `truncation_rate`, error-class rate, `api_call_attempts_per_agent_call`

อย่าใช้ `api_success_rate` เป็น synonym ของ task success หรือ answer correctness

### 4.2 ทดลองอย่างน้อย 5 schema variants (ทำ pilot ก่อน)

| Variant | วิธี |
|---|---|
| S0 | Current prompt + current manual validator; immutable baseline |
| S1 | Role prompt แบบสั้นลง + exact JSON skeleton ตัวอย่างที่ตรงกับ Agent schema; ไม่เพิ่ม factual content |
| S2 | Field-by-field instructions: อธิบาย nullable, allowed enums, empty arrays, evidence_ids และความหมายของ `status`; ห้าม Markdown fences |
| S3 | Repair prompt แบบ concise: ส่งเฉพาะ validation errors + schema contract + invalid output; ลดการส่ง original task ซ้ำทั้งก้อน แต่คงคำสั่งห้ามแต่ง evidence |
| S4 | Repair prompt ปัจจุบันเป็น control; เปรียบเทียบกับ S3 |
| S5 | Token budget 900/1200/1600 สำหรับ specialist และ 1600/2200 (หรือ budget ที่ผู้ใช้กำหนดได้) สำหรับ AI5 เฉพาะเมื่อ `finish_reason=length` หรือ length failures มีหลักฐาน; วัด quality/cost ไม่ใช่เพิ่มโดยอัตโนมัติ |
| S6 | Schema validation ด้วย `jsonschema` หรือ Pydantic ที่ครบ nested types/enums; สร้าง fixtures ก่อนเปลี่ยน production behavior |
| S7 | ลอง provider-native `response_format`/constrained JSON output เฉพาะหลัง capability probe ยืนยันว่า ThaiLLM endpoint รองรับ; ถ้าไม่รองรับให้ fallback และบันทึกผล ห้ามสมมติ OpenAI-compatible เท่ากับรองรับทุก feature |
| S8 | Sequential vs concurrent Agent calls ภายใต้ query IDs/model/prompt เดียวกัน; ดู rate limiting, latency tail และ variance ก่อนเลือก |

ไม่จำเป็นต้องวิ่งทุก variant กับทั้ง 5 queries ตั้งแต่แรก: ทำ offline fixtures ก่อน จากนั้น live pilot 2–3 queries เฉพาะ finalist แล้วเทียบครบ 5 queries ใน development set โดยจำกัด remote call budget

### 4.3 Schema contract requirements

- Required fields และ types ต้องมี specification เดียวกันระหว่าง prompt, validator, repair prompt และ downstream consumers
- Nested lists ต้องตรวจ field-by-field; `evidence_ids` ต้องเป็น list of strings และทุก ID ต้องอยู่ใน allowed manifest
- enum validation ต้อง case/whitespace-normalize ได้เฉพาะเมื่อ normalization มีเหตุผล และบันทึกค่าก่อน normalize
- `None`, empty list และ empty string ต้องมี semantics ชัดเจน; ห้าม autofill ข้อเท็จจริงที่ model ไม่ได้ให้
- เพิ่ม max lengths/limits เฉพาะที่จำเป็นเพื่อกัน output runaway; ถ้าตัดข้อมูลให้บันทึกว่า truncation/compaction เกิดขึ้น
- แยก `schema invalid` จาก `API error` และ `truncated_output`
- ต้องไม่ส่ง partial/invalid `data` ไปยัง AI5; ส่ง error status + structured diagnostics เท่านั้น
- AI5 ต้องสรุปได้จาก specialist ที่ผ่าน schema เท่านั้น; เมื่อมี specialist ล้มเหลวต้องระบุ limitation และ abstain จากข้อสรุปที่ต้องพึ่งข้อมูลนั้น

### 4.4 Regression fixtures

สำหรับแต่ละ Agent สร้าง fixture อย่างน้อย 8 แบบ:
1. JSON valid ครบ fields
2. Markdown fenced JSON
3. JSON syntax error
4. missing required field
5. wrong field type
6. malformed nested list item
7. invalid enum
8. unknown evidence ID
9. `finish_reason=length`/truncated output
10. response empty/API exception

ทดสอบ expected status, metrics, repair policy, and whether output is allowed downstream. Fixtures เหล่านี้ต้องผ่านโดยไม่ใช้ live ThaiLLM.

---

## 5. Workstream C — Citation/evidence correctness

### ปัญหาที่เห็น

มี citation ในรายงาน 20%; claim coverage 25%; paragraph coverage 13.3%; `citation_support_rate=NOT_HUMAN_REVIEWED`. `citation_id_valid_rate_when_present=100%` ไม่ได้พิสูจน์ว่า citations สนับสนุน claim และ metric นี้ถูกคำนวณเฉพาะรายงานที่มี citation

ใน implementation `citation_audit()` ตรวจรูปแบบ `[S1]`, `[Q1]`, `[H1]`, `[R1]` เทียบ `allowed_ids`; `claim_evidence_audit()` นับว่ามี valid ID แต่ไม่ได้ตรวจ semantic support; `render_evidence_report()` สร้าง Markdown จาก structured `evidence_based_findings` — ควรรักษา design ที่ renderer deterministic และไม่ให้ LLM สร้าง Markdown เอง

### 5.1 แยก citation stages

เก็บ metrics:
- `raw_claim_count`, `final_claim_count`, `no_claims_status`
- `raw_proposed_citation_ids`, `valid_proposed_ids`, `invalid_proposed_ids`
- `raw_proposed_citation_id_valid_rate` ก่อน renderer กรอง
- `report_has_citations_rate`
- `claim_citation_coverage`
- `citation_id_validity_after_render`
- `citation_paragraph_coverage` หรือ rename เป็น `citation_line_coverage` ถ้าตรวจทีละบรรทัด
- `citation_semantic_support` ต้อง `NOT_HUMAN_REVIEWED` จนมี human review จริง
- `unsupported_claim_rate`, `claim_type`, `reviewer_label`, `reviewer_notes`

ทุก metric ต้องมี explicit denominator และ count fields; แยก `NO_CLAIMS`, `NO_CITATIONS`, `NOT_REVIEWED` ออกจากเลข 0

### 5.2 Root-cause classification สำหรับ report ที่ไม่มี citations

สำหรับทุก query ที่ไม่มี citations ให้ classify ว่าเกิดจากสาเหตุใด:
- AI5 API failure
- AI5 JSON parse failure
- AI5 schema failure
- AI5 schema-valid แต่ `evidence_based_findings=[]`
- findings มีอยู่แต่ `evidence_ids=[]`
- proposed IDs ไม่อยู่ใน manifest
- allowed evidence manifest ว่างหรือสร้างไม่ครบ
- renderer/regex/summary bug
- report ถูกแทนที่ด้วย fallback

บันทึก expected vs actual IDs และ evidence manifest counts ก่อนสรุปว่า prompt เป็นปัญหา

### 5.3 Evidence validator

ทำ deterministic checks สำหรับ:
- ทุก factual claim ที่จะ render ต้องมี evidence ID ที่ valid อย่างน้อยหนึ่งรายการ หรือถูก render เป็น `Needs evidence review`/abstention
- IDs ต้องมาจาก manifest ปัจจุบันของ query เท่านั้น ไม่ใช่ IDs ที่จำได้จาก run อื่น
- Q/H/R records ต้องมี `as_of`, units, source/lineage และ result ID ตามชนิดข้อมูลที่มี
- ตัวเลขและวันที่ใน claims ที่อ้าง deterministic Quant/HMM/Risk tools ต้องเทียบกับ tool records ก่อนส่งออก
- อย่าพยายาม “พิสูจน์” semantic citation support ด้วย regex อย่างเดียว; ให้ human review subset และใช้ LLM evaluator เป็น triage เท่านั้น

### 5.4 Citation experiments

- C0: current deterministic renderer (baseline)
- C1: improve prompt with one compact example of a claim and its IDs
- C2: evidence-first generation: first select evidence IDs per claim, then draft claims, validate, then render
- C3: deterministic claim-to-source mapping for numeric/date/period facts from tools
- C4: no-evidence/insufficient-evidence abstention path
- C5: vary manifest ordering and context position with fixed evidence to diagnose order/context sensitivity; do not add more context by default

Compare `report_has_citations_rate`, claim coverage, invalid ID rate, unsupported claims on human-reviewed subset, token usage, schema validity. Citation rate alone is not an optimization objective: do not encourage spurious citations to increase coverage.

---

## 6. Workstream D — Benchmark integrity and summary metrics

### Bugs/risks to examine

- Summary currently looks up `multiagent_benchmark_df.get("agent_json_valid_rate")`, but verify whether that column is actually created. If it is not, the `json_valid_rate` summary becomes NaN; either remove duplicate metric or implement its true definition.
- `NO_CITATIONS` and `NO_CLAIMS` are strings converted to NaN by `pd.to_numeric(..., errors="coerce")`; means may hide failure modes. Show valid denominator and categorical counts explicitly.
- `latency_p95_ms` with five queries is not reliable enough for production SLA. Report sample size, max latency and per-query distribution. Do not compare P95 with another run if query IDs or completion coverage differ.
- failed queries/errors must not disappear from summary denominator; completion rate must include attempts, including errors and blocked items.
- aggregate API success must distinguish actual API requests from “at least one response received during agent call.”
- if task success has no deterministic domain oracle, retain `NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE`; do not substitute schema validity.
- bootstrap confidence intervals require enough independent queries; with n=5, mark as exploratory and do not overstate inferential certainty.

### Add summary columns

`attempted_queries`, `completed_queries`, `failed_queries`, `blocked_queries`, `completion_rate`, `coverage_eligible_queries`, `coverage_ineligible_queries`, `api_request_attempts`, `api_attempt_success_rate`, `first_attempt_json_parse_rate`, `final_attempt_json_parse_rate`, `first_attempt_schema_valid_rate`, `post_repair_schema_valid_rate`, `full_schema_pass_query_rate`, `promoted_output_schema_valid_rate`, `repair_recovery_rate`, `truncation_rate`, `report_has_citations_rate`, `mean_claim_citation_coverage`, `citation_id_valid_rate_when_present`, `citation_support_rate`, `mean_tokens`, `p50`, `p90`, `p95`, `max_latency_ms`, `n_latency_samples`.

When `NO_CLAIMS`/`NO_CITATIONS` appear, report both value-status counts and numeric averages over a clearly named eligible subset. Keep a machine-readable schema/version for each CSV.

---

## 7. Workstream E — Latency and token cost experiments

### Diagnosis first

Trace per stage: embedding, Qdrant query, BM25, RRF, Jina, deterministic Quant snapshot, HMM inference, Risk snapshot, AI1–AI4 individually, AI5, repair, citation validation and total wall time.

At least record per agent and per attempt:
- `wall_latency_ms`, `api_latency_ms` if available, prompt/completion/total tokens
- initial vs repair attempt
- finish reason
- queue/semaphore wait if concurrent
- retry and rate-limit details without secrets

### Experiment variants

- L0: Current settings (control)
- L1: Sequential specialist calls
- L2: Concurrent specialist calls (current env flag) with bounded workers and rate limit telemetry
- L3: reduce duplicate evidence/context to AI5 while keeping same evidence IDs and specialist findings
- L4: reduce context length only after evidence relevance is verified
- L5: targeted token budget increase only for length-truncated outputs
- L6: targeted retry policy for transient transport failures vs schema/parse repair, counted separately
- L7: task routing only after establishing an A/B oracle for when an Agent is unnecessary; do not change architecture in same run as prompt/schema

Use identical query IDs/config where possible. Never choose a faster option if it reduces schema validity, evidence support, retrieval quality or task correctness beyond a predeclared tolerance. Since current task correctness is not evaluated, first add at least some deterministic or human-reviewed correctness labels before claiming an optimization is safe.

---

## 8. Domain-oracle strategy: do not fake `task_success_rate`

Build separate tests for deterministic functions already present in the notebook:

- Quant snapshot: recompute selected statistics with independent simple pandas/NumPy assertions on fixed fixture data
- HMM: contract tests for feature order, required columns, scaler/model metadata, timestamp/as-of consistency, output state values and missing-feature failure
- Risk/portfolio: accounting identities, P&L reconciliation, fees/cost sign checks, duplicate event invariants, synthetic-vs-real provenance
- RAG factual answers: use expected answer/facts/evidence spans; exact/numeric/date checks where deterministic; human-review remaining semantic cases
- abstention: queries with absent evidence should not be marked wrong solely for refusing to infer a fact; assert that no unsupported external claim is promoted

For each oracle mark source of expected result, test version and whether human gold is reviewed. `task_success_rate` should be populated only for tasks with an oracle and be broken down by task type; otherwise preserve `NOT_EVALUATED`.

---

## 9. Experiment sequencing — run in this exact order

### Phase 0: Read and snapshot

- Load the newest reliability notebook and compare to previous Phase 1–2 copy if present.
- Identify actual paths/config, baseline outputs and installed dependencies.
- Produce baseline manifest and source diff; do not make behavior-changing edits yet.

### Phase 1: Offline diagnostics + regression tests

- Implement unit tests for ID normalization/aliasing, schema, repair decision logic, citation renderer/audit, metric aggregation and failures.
- Reproduce `json_valid_rate` missing-field issue if present.
- Test `NO_CITATIONS`, `NO_CLAIMS`, API exception after a prior parse, truncation and one invalid evidence ID.
- Do not make external calls.

### Phase 2: Retrieval root-cause audit

- Evaluate 5 current query IDs from `development` with no ranking changes.
- Save exact source/chunk/Qdrant audit and candidate-stage diagnostics.
- For all misses, identify the earliest stage where expected content becomes unavailable.
- Only if root cause is known, run the relevant retrieval variants in Section 3.2.

### Phase 3: Schema root-cause audit

- Parse schema errors from existing `agent_quality_and_latency.csv` first.
- Run local fixtures across all 5 agent schemas.
- Pilot schema variants S1–S7 on 2–3 development queries with strict request budget; run finalists on the same 5 queries.
- Do not change retrieval and schema prompts in the same experimental comparison.

### Phase 4: Citation audit/experiments

- Classify missing citation causes on each query.
- Run C0–C5 as needed based on cause; preserve raw proposed IDs before filtering.
- Create a small human review template with claim, cited excerpts, source URL, supported/partially supported/unsupported/unverifiable labels.

### Phase 5: Latency and cost

- Use instrumented timings from the same five query IDs.
- Try L1/L2 and context/token variants one at a time; maintain a budget guard.
- Report `max_latency_ms` alongside quantiles and disclose tiny n.

### Phase 6: Candidate integration + regression

- Integrate only variants supported by evidence.
- Rerun all offline tests, the same five development queries, and then the complete development set that passes data/coverage audit.
- Compare per query against the immutable baseline; list regressions even if the aggregate mean improves.
- Lock chosen config, write validation plan, do not tune on test split.

---

## 10. Acceptance criteria

### Mandatory software integrity

- [ ] Original notebook remains unchanged; Phase 3 copy exists.
- [ ] Fresh-kernel top-to-bottom run with configured credentials is possible; no stale notebook variables required.
- [ ] Offline unit/contract tests pass.
- [ ] Every attempted query has a record: completed, failed, or blocked, with reason.
- [ ] Exceptions preserve full traceback and do not silently vanish from denominators.
- [ ] No secret values appear in notebook outputs, CSVs, logs or reports.

### Retrieval

- [ ] Ground Truth source text and identity mapping are audited, not just alias presence.
- [ ] Every retrieval miss has a stage-level diagnosis or is explicitly unresolved.
- [ ] Dense-only, BM25-only and Hybrid/RRF are compared on identical query IDs.
- [ ] Reranker is evaluated by incremental change to ranking and by candidate-recall ceiling.
- [ ] Config choice records quality, latency, calls and per-query regressions.

### Agent schemas

- [ ] Every output promoted to downstream is schema-valid; invalid output only travels as a structured error state.
- [ ] API attempt success, parse validity, schema validity and task success have separate definitions.
- [ ] First-attempt vs post-repair metrics are available.
- [ ] Schema fixtures cover all five agents and relevant error cases.

### Citations

- [ ] Raw proposed IDs are logged before filtering.
- [ ] Citation presence and validity denominators are explicit.
- [ ] Claim coverage is separate from semantic support.
- [ ] No semantic support metric is labeled human-reviewed unless an actual reviewer label is present.
- [ ] Any factual claim with no evidence is marked for review or omitted; no synthetic citations are fabricated.

### Reliable conclusions

- [ ] No claim of `task_success_rate` without a domain oracle.
- [ ] Tiny-sample latency percentiles are labeled exploratory.
- [ ] No test/holdout data used for tuning.
- [ ] Report includes limitations and unresolved causes.
- [ ] A chosen change is supported by a repeatable comparison, not merely one successful example.

---

## 11. Research-informed design guardrails

Use papers as design guidance, not as a reason to assume a method will improve this specific corpus:

- BEIR, *A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models*, NeurIPS 2021: retain lexical retrieval baselines and test retrieval methods across tasks rather than assume one retriever is universally best. https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/65b9eea6e1cc6bb9f0cd2a47751a186f-Abstract-round2.html
- Cormack, Clarke & Büttcher, *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods*, SIGIR 2009: keep RRF as a baseline, but validate parameters/config on our data. https://doi.org/10.1145/1571941.1572114
- Ru et al., *RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation*, NeurIPS 2024: measure retrieval and generation failure separately. https://arxiv.org/abs/2408.08067
- Gao et al., *Enabling Large Language Models to Generate Text with Citations* (ALCE), EMNLP 2023: distinguish answer correctness from citation quality. https://aclanthology.org/2023.emnlp-main.398/
- Saad-Falcon et al., *ARES: An Automated Evaluation Framework for RAG Systems*, NAACL 2024: automated judges can help, but use human annotations/calibration to control evaluator errors. https://aclanthology.org/2024.naacl-long.20/
- Geng et al., *Generating Structured Outputs from Language Models: Benchmark and Studies* (JSONSchemaBench), 2025: measure schema conformance, constraint coverage and output quality separately; do not assume a compatible endpoint supports every constrained decoding feature. https://arxiv.org/abs/2501.10868
- Liu et al., *Lost in the Middle*, TACL 2024: larger context is not automatically better; experiment with evidence ordering/position under fixed evidence. https://aclanthology.org/2024.tacl-1.9/
- Liu et al., *AgentBench: Evaluating LLMs as Agents*, ICLR 2024: evaluate task-level behavior and failure types, not only whether tool/API calls returned. https://proceedings.iclr.cc/paper_files/paper/2024/hash/e9df36b21ff4ee211a8b71ee8b7e9f57-Abstract-Conference.html

Do not copy benchmark thresholds from these papers as if they are mandatory acceptance thresholds for Gold Assistant. The thresholds in Section 10 are engineering safeguards for this project, and any product-level quality target must be stated separately.

---

## 12. Final report format — required

At completion, print a concise executive summary and save the full report with these headings:

1. **What was run** — source notebook, run ID, query IDs, environment/config fingerprint (no secrets)
2. **Baseline reproduced** — actual observed values; explain any differences from supplied table
3. **Root-cause findings** — confirmed/likely/rejected/unresolved with supporting artifact paths
4. **Variants tested** — all tested and stopped variants, including negative results
5. **Before/after table** — same query IDs, same denominator; show per-query regressions
6. **Chosen changes** — exact cells/functions changed and why
7. **Tests** — offline unit tests, contract tests, live test status, failures and traceback references
8. **Cost/performance** — API requests, retries, tokens, latency distribution, max latency and budget usage
9. **Citation audit** — raw ID validity, report presence, claim coverage and human support status
10. **Remaining uncertainty** — particularly query-set size, relevance-judgment exhaustiveness and unreviewed semantic claims
11. **How to rerun** — cells/commands/environment variable names; no secret values
12. **Rollback** — exact original file and steps to restore

The final response to the user must clearly state what actually ran, what was modified, what improved, what regressed, what remains unresolved, and where the evidence artifacts were saved. Never claim an experiment passed unless its test result exists in the saved artifacts.
