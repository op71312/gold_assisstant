# Prompt สำหรับ AI Coding Agent: สร้าง Gold Assistant Integrated Benchmark (GAIB-1)

คุณคือ Senior AI Evaluation Engineer, Quant Research Engineer และ Data Quality Auditor งานของคุณคือสร้าง benchmark ที่ทำซ้ำได้สำหรับระบบ **Gold Assistant** ซึ่งใช้ ThaiLLM, A2 RAG, Function Calling, Quant tools, GaussianHMM และ synthetic portfolio simulator

เป้าหมายไม่ใช่สร้างคำถามจำนวนมากให้ดูเหมือนครบ แต่สร้าง **ground truth ที่มีที่มาชัดเจน ตรวจซ้ำได้ และไม่ใช้ LLM เป็นผู้ตัดสินคำตอบอ้างอิงของตัวเอง** ต้องรักษา dataset provenance, no-look-ahead, citation integrity และความแตกต่างระหว่างข้อมูลตลาดจริงกับพอร์ตจำลองอย่างเคร่งครัด

## A. Project paths และไฟล์อ้างอิง

Project root:
`D:\Project_Github\gold assisstant\`

ไฟล์/โฟลเดอร์สำคัญที่คาดว่าจะมี (ให้ค้นหาไฟล์จริงก่อน ห้ามสมมติว่า path นี้มีอยู่):

- `rag\Gold_Assistant_Full_RAG_End_to_End.ipynb`
- `rag\2.Gold_Assistant_RAG_Latency_Experiments.ipynb`
- `dataset\news\fed\` และข่าว/เอกสาร macro อื่น ๆ
- `dataset\datset a gold price\data\processed\thai_gold_features_v1.parquet`
- `model\gold_hmm_v1\model.joblib`
- `dataset\thai-gold-portfolio-simulator\`
- `pack.rar` หากยังไม่ extract ให้ตรวจว่ามี 7-Zip/unrar รองรับหรือไม่ และรายงานข้อจำกัดแทนการเดาเนื้อหา
- `fed_press_releases_classified.jsonl` (เป็น source classification โดย ThaiLLM ไม่ใช่ human gold label)
- `ground_truth_fed_v1.jsonl`, `ground_truth_fed_ready_v1.jsonl`, `ground_truth_fed_source_gaps_v1.jsonl`, `fed_missing_source_manifest.jsonl`, `fed_groundtruth_audit_report.json` ที่ส่งมาพร้อมงานนี้ ถ้าไฟล์เหล่านี้ยังไม่ได้อยู่ใน Project root ให้ใช้ไฟล์ที่ผู้ใช้วางไว้ในโฟลเดอร์ input ของ benchmark หรือรายงานให้ชัดเจน

ก่อนสร้างอะไร ให้ inspect Notebook, README, source code และ schema ที่ระบบใช้อยู่จริง โดยเฉพาะ RAG loader, chunk metadata, exact tool names/signatures, feature preprocessing ของ HMM และ simulator accounting code

## B. ขอบเขตและข้อห้าม

1. **ห้ามแก้ไข production pipeline, model weights, RAG index หรือ source dataset ต้นฉบับ** ในงาน benchmark นี้ ให้สร้างไฟล์ใหม่ภายใต้ `benchmark\GAIB-1\` เท่านั้น
2. ห้ามแต่ง document ID, URL, quote, chunk ID, observation, numeric result, portfolio ID หรือ model output
3. ห้ามใช้ LLM สร้าง expected numeric answers, expected HMM state outputs หรือ expected accounting outputs เป็นแหล่ง truth เพียงแหล่งเดียว ให้คำนวณจาก Python และ source records จริง
4. LLM อาจช่วยร่าง wording ของคำถามได้ แต่คำถามและ expected facts ต้อง trace กลับไปยัง source/calculation record ได้ และต้องผ่าน validation
5. ห้ามถือว่า citation ID ถูกต้องเพียงเพราะ ID มีอยู่; claim-level support ต้องตรวจว่า source span สนับสนุน claim จริง
6. ห้ามอ้างว่า Fed policy announcement ทำให้ราคาทองขึ้น/ลงโดยตรงจากแถลงการณ์เพียงฉบับเดียว การวัด causal effect ต้องเป็นงานวิจัยแยก มี market data aligned ตามเวลาประกาศและ methodology ที่ระบุชัด
7. ห้ามปฏิบัติต่อ simulator transactions หรือ synthetic portfolios ว่าเป็นข้อมูลลูกค้าจริง ต้องติดป้าย `synthetic=true` หรือเทียบเท่าทุกครั้ง
8. ห้ามเปลี่ยน A2 RAG config เงียบ ๆ เพื่อให้ benchmark ผ่าน
9. ห้าม mark `PASS` หากมี validation error, unresolved source gaps, broken evidence links หรือ test ที่ไม่ได้รันจริง
10. หากไฟล์หรือ capability ขาด ให้หยุดในส่วนที่เกี่ยวข้อง สร้าง issue/blocked manifest และอธิบายสิ่งที่ขาด ห้ามสร้าง proxy แทน input จริงโดยไม่แจ้ง

## C. Source of Truth และ A2 control

ใช้ A2 ใน `2.Gold_Assistant_RAG_Latency_Experiments.ipynb` เป็น RAG control configuration ที่ frozen ไว้ ค่าที่ต้องตรวจจาก source code จริงก่อนรันรวมถึง:

- Cloudflare embedding model / configuration ที่ตั้งไว้
- Qdrant Dense retrieval
- BM25 retrieval
- Reciprocal Rank Fusion และ RRF constant
- Jina reranker รุ่นที่ตั้งค่าไว้และ fallback status
- `FINAL_K`, context budget, per-chunk budget
- ThaiLLM model, temperature, max tokens, timeout, retries
- API concurrency/rate-limit gates และ checkpoint configuration

อย่ากำหนดค่า A2 จากข้อความใน Markdown อย่างเดียว หาก code cell ขัดกับ Markdown ให้รายงาน discrepancy และอย่าแก้ให้เองแบบเงียบ ๆ ค่า benchmark ทุกครั้งต้องเก็บ effective config จาก runtime ลง manifest

Fed dataset ที่ส่งมามี 4,553 records ระหว่าง 2006-01-03 ถึง 2026-10-16 และ classification ถูกสร้างโดย ThaiLLM ดังนั้น label `relevant/uncertain/not_relevant` เป็น **silver label** ที่ช่วยคัดกรอง ไม่ใช่คำตอบ benchmark ที่ผ่าน human validation แล้ว

Fed source gaps ที่ทราบ:
- `https://www.federalreserve.gov/newsevents/pressreleases/monetary20240501a.htm`
- `https://www.federalreserve.gov/newsevents/pressreleases/monetary20250129a.htm`

URL ทั้งสองนี้ไม่พบในไฟล์ `fed_press_releases_classified.jsonl` ที่แนบมาล่าสุด แต่ official pages ยังเข้าถึงได้ หากจะใช้คำถามที่อ้างสอง URL นี้ใน retrieval benchmark ต้องดึงหน้า official แบบเต็ม เก็บ metadata/เนื้อหาและ ingest ผ่าน production parsing/chunking/indexing pipeline แล้วจึง rerun source mapping/evidence recall ตรวจ ID/URL consistency ด้วย อย่าแก้ Ground Truth ให้ดูเหมือน source อยู่ใน index แล้ว หากยังไม่ ingest

## D. Deliverables

สร้างโฟลเดอร์ใหม่:
`benchmark\GAIB-1\`

ต้องมีอย่างน้อย:

1. `ground_truth_fed_v1.jsonl` — ชุด Fed ทั้งหมด พร้อม field บอกสถานะ source availability
2. `ground_truth_fed_ready_v1.jsonl` — เฉพาะคำถามที่ source record/quote อยู่ใน corpus ที่ benchmark ใช้งานจริงแล้ว
3. `ground_truth_fed_source_gaps_v1.jsonl` — คำถามที่ blocked เพราะ source ยังไม่อยู่ใน local/indexed corpus
4. `ground_truth_quant_v1.jsonl` — deterministic Quant Function Calling cases
5. `ground_truth_hmm_v1.jsonl` — HMM inference contract / deterministic reference tests
6. `ground_truth_portfolio_v1.jsonl` — accounting / P&L attribution cases
7. `ground_truth_multi_agent_v1.jsonl` — End-to-End 5-Agent cases
8. `ground_truth_all_v1.jsonl` — รวมเฉพาะ schema-compatible, non-duplicate records พร้อม `track` field ชัดเจน
9. `source_inventory.json` — inventory, file hashes, dimensions/date ranges/schema/record counts
10. `build_report.md` — methodology, coverage, limitations, unresolved issues, commands to reproduce
11. `validation_report.json` — machine-readable pass/fail results
12. `human_review_queue.csv` — queries/claims ที่ยังต้องมนุษย์ตรวจ
13. `build_gaib_benchmark.py` — script สร้าง/อัปเดตชุด benchmark แบบ reproducible
14. `tests/test_ground_truth_integrity.py` — unit tests ตรวจ data integrity
15. `benchmark_manifest.json` — versions, config, SHA-256, query counts, seed, source mapping และ date/time of build

ถ้าสร้าง deliverable บางไฟล์ไม่ได้ ให้ใส่ `BLOCKED` ใน validation report พร้อมเหตุผลและ input ที่ขาด อย่าตั้งชื่อไฟล์เป็น ready ถ้าไม่ผ่าน

## E. Track B — Quant Function Calling (เป้าหมายเริ่มต้น 30 cases)

ใช้ feature dataset จริงและตรวจ schema ก่อนออกแบบคำถาม อย่าสันนิษฐานว่ามี DXY, Treasury yields หรือ feature columns ที่ไม่ได้อยู่ในไฟล์จริง

ต้องตรวจอย่างน้อย:
- Date/time columns, timezone/ordering, duplicate timestamps, missingness
- Column names, types, units, price convention, frequency/irregular intervals
- Date coverage และ observation counts
- มี feature ที่คำนวณล่วงหน้าแล้วหรือไม่ และสูตร/แหล่งที่มาระบุไว้หรือไม่

สร้าง cases ให้ครอบคลุมอย่างสมดุล:
- latest observed value ณ as-of date ที่มีอยู่จริง
- return calculation ตาม definition ที่บันทึกไว้
- rolling volatility ที่ระบุ window และ `ddof`
- correlation ระหว่าง series ที่มีอยู่จริง โดยระบุ alignment/dropna policy
- missing date / invalid date / insufficient observations
- query ที่ขอ feature ซึ่งไม่มีใน dataset (ระบบต้องคืน `not_available` ไม่ใช่สร้างค่า)
- as-of time ที่ป้องกัน look-ahead
- unit/percentage-point/percentage confusion

ทุก case ต้องมี `expected_tool_calls`, exact arguments, expected output fields, units, tolerance และ independent calculation reference/formula. อย่าสร้าง expected result โดยเรียก handler เดียวกันที่กำลังถูกทดสอบเพียงอย่างเดียว; ใช้ independent test implementation หรือ freeze expected outputs พร้อม input fingerprint เพื่อหลีกเลี่ยง circular evaluation

## F. Track C — HMM Contract & Inference (เป้าหมายเริ่มต้น 20 cases)

โหลด `model.joblib` จริงและ inspect keys, model type, `scaler`, `feature_cols`, number of states, training metadata และ preprocessing code ที่สร้าง input features

มีข้อมูลเดิมที่ต้องระวัง: model contract ที่รายงานก่อนหน้าระบุ `bar_buy_log_return` และ `intraday_range_pct`, ขณะที่ `thai_gold_features_v1.csv` ที่ตรวจในอีกชุดมี 6,261 rows/31 columns แต่ขาดอย่างน้อยหนึ่ง feature ตามชื่อนี้ ห้ามสร้าง proxy ด้วย high-low range แทน feature ที่หาย เว้นแต่ preprocessing/training code จะยืนยันสูตรนั้น

สร้าง cases สำหรับ:
- valid input rows และ feature order
- exact expected `predict`/`predict_proba` outputs โดยอิง model hash + scaler + feature vector ที่ตรึงไว้
- probability rows รวมได้ประมาณ 1 ภายใน tolerance
- missing feature / wrong feature order / nonnumeric value / NaN / insufficient window ต้อง fail closed หรือใช้ documented preprocessing เท่านั้น
- as-of cutoff และ no-look-ahead
- deterministic repeatability ด้วย input เดิม
- input date missing/duplicate/out-of-order ที่ต้องเตือนหรือ normalize ตาม contract
- model bundle absent/unsupported หรือ metadata mismatch

สำคัญ: **ไม่มี external regime labels ก็ห้ามรายงาน HMM accuracy หรืออ้างว่า state 0 = bullish, state 1 = crisis** ชุดนี้ให้เรียกว่า implementation/contract regression benchmark ไม่ใช่ economic-regime accuracy benchmark

## G. Track D — Portfolio Accounting (เป้าหมายเริ่มต้น 30 cases)

Inspect simulator code และ source tables ก่อน โดยเฉพาะ transaction ledger, monthly valuations, realized/unrealized P&L, weighted average cost, cash, remaining gold, fees/spreads และ P&L attribution components

สร้าง cases แบบมี ground truth ที่คำนวณซ้ำได้ เช่น:
- buy-only / sell-only / partial sell / remaining inventory
- realized vs unrealized P&L แยกกัน
- transaction cost / product cost / price effect / timing effect ตามนิยามใน source code จริง
- date-range P&L attribution
- zero activity / no-price / invalid transaction / insufficient cash
- duplicate identifiers หรือ accounting flags ที่พบจริงใน dataset
- reconciliation pass/fail cases โดยมี tolerance ที่ประกาศไว้ชัดเจน

แต่ละ case ต้องระบุ `portfolio_id`, time window, source row IDs หรือ transaction IDs ที่จำเป็น, expected amounts, units, formula, numerical tolerance และ `synthetic=true`. อย่าคิดสูตรขึ้นใหม่หาก codebase มีสูตร production อยู่แล้ว; สกัด definition จาก code และเทียบด้วย independent checker

อย่าสุ่ม split แถวจาก portfolio เดียวกันลง train/dev/test จนเกิด leakage หากมี portfolio ID, archetype/cohort หรือ simulation seed ให้ group split ตาม entity/seed ตามความเหมาะสมและบันทึกวิธีแบ่ง

## H. Track E — End-to-End 5-Agent (เป้าหมายเริ่มต้น 30 cases)

ออกแบบ cases ที่ทดสอบ workflow จริง ไม่ใช่เพียงคำถามปลายเปิด:
- News retrieval + market facts
- Macro explanation ที่ต้องแยก observation ออกจาก interpretation
- Quant tool + HMM state inference
- Portfolio accounting + attribution explanation (พร้อม synthetic-data warning)
- conflicting evidence ระหว่าง agents หรือ dataset versions
- missing evidence / out-of-range as-of date / missing feature
- question ที่ขอ DXY/yields ทั้งที่ dataset ไม่ได้มี series ดังกล่าว
- source/citation mismatch
- system ควร abstain เพราะไม่มีข้อมูล
- Agent มีโอกาสเรียก unauthorized tool หรือใช้ incorrect arguments

ทุก case ควรระบุ:
- required agents และ optional agents
- expected tools และ arguments (หรือ allowed alternatives ถ้าหลายเส้นทางถูกต้อง)
- minimum acceptable evidence IDs/documents
- expected factual claims และ forbidden unsupported claims
- expected abstention/failure behavior
- validators ที่ต้องผ่าน
- human-review status

หากกำหนด ground truth ของ semantic claim ไม่ได้จาก source ให้ติดป้าย `needs_human_review`; ห้ามใช้คำตอบ LLM ที่ไม่ผ่าน review เป็น definitive gold answer

## I. Schema และ IDs

ให้ใช้ JSONL UTF-8 หนึ่ง JSON object ต่อบรรทัด ห้ามมี trailing commas หรือ Markdown fence ในไฟล์ข้อมูล

สำหรับ RAG-style records ให้สอดคล้องกับ Ground Truth schema v2 ที่มีอยู่ โดยอย่างน้อยมี:
- `schema_version`, `query_id`, `query`, `query_language`, `query_type`, `difficulty`, `question_pattern_id`
- `source_filter`, `source_scope`
- `evidence[]` ที่มี `evidence_id`, `document_id`, `source`, `source_file`, `source_url`, `title`, `publication_date`, `exact_quote`, `start_offset`, `end_offset`, `offset_basis`
- `expected_answer.text` และ `expected_answer.facts[]`
- `relevance_judgments[]`, `review_status`, `review_notes`, `created_by`, `split`, `split_group_ids`

สำหรับ non-RAG tracks ให้เพิ่ม fields ที่เหมาะสม เช่น `track`, `expected_tool_calls`, `expected_arguments`, `expected_outputs`, `formula`, `numeric_tolerance`, `assertions`, `provenance`, `synthetic` โดยไม่ปลอมให้ทุกคำถามเป็น RAG query

IDs ต้อง unique ตลอด `ground_truth_all_v1.jsonl`. ห้ามทับ `gtv2_*` records เดิม. ใช้ prefix แยก track เช่น `gaib_quant_`, `gaib_hmm_`, `gaib_portfolio_`, `gaib_e2e_`.

Evidence offsets ต้องนับ character offsets ตาม `offset_basis` อย่างถูกต้องและตรวจด้วย `content[start_offset:end_offset] == exact_quote`. หาก quote ไม่อยู่ใน local source ให้ mark blocked และอย่ากำหนด offsets ขึ้นเอง

## J. Benchmark metrics ที่ต้องรองรับ

RAG:
- Evidence Recall@k, MRR@k และ source document mapping
- Context Precision/Recall หาก Ground Truth มี relevance judgments ที่เหมาะสม
- Expected-fact coverage, claim-level citation support, unsupported claims และ invalid citation IDs

Function calling:
- Tool-call precision/recall/F1
- Exact tool-name correctness, argument correctness, required-parameter coverage
- Unauthorized tool-call rate, retry/error rate และ redundant call count

Quant/HMM/Portfolio:
- Absolute/relative numeric error, unit/date correctness, missing-data behavior
- HMM feature-contract pass rate, probability normalization, repeatability และ as-of violations
- Accounting reconciliation residual, component error และ transaction traceability

End-to-End / inference:
- Task success, factual correctness, evidence support, completeness และ correct abstention
- End-to-end P50/P90/P95/P99 latency
- Component latency แยก retrieval, embedding, reranking, ThaiLLM, tool execution, orchestration และ validation
- input/output/total tokens, tool calls per query, retries/429, error rate และ cost/request ถ้ามีราคาที่เชื่อถือได้

ห้ามตีความ average latency อย่างเดียวว่าเป็นผลดีขึ้น ให้เทียบ configuration เดียวกันและรายงาน percentiles พร้อม query-type breakdown

## K. Source splits และ leakage prevention

- Preserve original `split`/`query_id` ของ Fed Ground Truth ที่ได้รับมา
- ห้ามใช้ cases จาก test split เพื่อเขียน/ปรับ prompt แล้วรายงานคะแนนเดิมเป็น unbiased test performance
- For newly created cases, split โดย `document_id`, document family, date cluster, portfolio ID หรือ simulation seed ตาม track เพื่อหลีกเลี่ยง near-duplicate leakage
- Cross-period tasks ต้อง group ทั้ง source documents ใน case เดียวกัน ไม่แยก source A ไป dev และ source B ไป test ถ้าจะทำให้เกิด leakage
- บันทึกทุก split rule และ stable seed

## L. Required Validation Checklist — ต้องรันจริงและติ๊กผล

### Input/data integrity
- [ ] ตรวจพบและบันทึก hash (SHA-256) ของทุก input file
- [ ] บันทึก row counts, schema, data types, units (ถ้าทราบ), min/max dates, nulls, duplicates
- [ ] ระบุ source files ที่ missing, unreadable, ambiguous หรือ older version
- [ ] ตรวจ that Fed ThaiLLM labels are silver labels only, not ground truth
- [ ] ระบุ historical market data vs synthetic simulator data แยกจากกัน
- [ ] ตรวจ HMM bundle feature contract เทียบ training preprocessing และ actual inference inputs

### Ground Truth validity
- [ ] ทุก query มี unique `query_id`
- [ ] ทุก `evidence_id` unique ภายใน query และ maps to an actual source
- [ ] ทุก exact quote อยู่ใน source ที่ระบุ และ offsets match exact text
- [ ] ทุก expected numeric answer เกิดจาก deterministic Python reference calculation
- [ ] ทุก value มี unit/period/as-of/comparison basis ตามที่จำเป็น
- [ ] ทุก expected tool call มี tool ที่ลงทะเบียนจริงและ valid schema
- [ ] ไม่มี unsupported columns/features ถูกสมมติขึ้น
- [ ] แหล่งที่หายถูก mark `BLOCKED`, ไม่ถูกแทนด้วย fabricated evidence
- [ ] คำถามที่มี semantic uncertainty ถูกส่งเข้า human review queue
- [ ] ไม่มีคำกล่าวอ้างเชิงสาเหตุเรื่องทองคำที่ไม่มี methodology แยกรองรับ
- [ ] synthetic portfolios/transactions ถูกติดป้ายชัดเจนทุกกรณี

### Schema/tests
- [ ] JSONL ทุกไฟล์ parse ได้ทีละบรรทัด
- [ ] Schema validation ผ่านสำหรับทุก record
- [ ] Query IDs ไม่ซ้ำระหว่างทุก track
- [ ] Citation references และ file/source links ตรวจย้อนกลับได้
- [ ] Numerical fields เป็น numeric types จริง ไม่ใช่ string เมื่อควรเป็น numeric
- [ ] Unit/tolerance validation ผ่าน
- [ ] Test split ไม่รั่วจาก document/portfolio IDs ที่ซ้ำกัน
- [ ] Regression tests ตรวจ fail-closed behavior เมื่อ input/feature/source หาย
- [ ] `pytest` ผ่านทุก test ที่ประกาศไว้
- [ ] Build script รันซ้ำแล้วได้ output ที่ reproducible ตาม input hashes/seed
- [ ] Validation report แสดง pass/fail/blocked ต่อ checklist item โดยไม่ซ่อน failure

### Benchmark execution and reporting
- [ ] Smoke test ขนาดเล็กผ่านก่อน
- [ ] A2 baseline config ถูกบันทึกจาก runtime และไม่เปลี่ยนโดยไม่ตั้งใจ
- [ ] Jina reranker status / fallback status ถูกบันทึกต่อ request
- [ ] Tool calls จริงและ tool results ถูกบันทึกแยกจาก text ที่ LLM อ้างว่าเรียก
- [ ] Retry/429/timeouts/errors ถูกนับครบ
- [ ] Latency วัดแบบ end-to-end และ component-level
- [ ] รายงาน P50/P90/P95/P99 แทนค่าเฉลี่ยอย่างเดียว
- [ ] คุณภาพคำตอบ/citations วัดควบคู่กับ latency/token/cost
- [ ] Human review queue ถูกสร้างสำหรับทุก claim/case ที่ยังไม่มี semantic sign-off
- [ ] ไม่มี benchmark score ใดถูก mark `PASS` หากมี source gaps หรือ validation failures ที่กระทบ test นั้น

## M. Acceptance gates

ส่งงานเมื่อสร้าง artifacts และ validation report ครบ หากบาง track blocked ให้ส่งส่วนที่ validated แล้วและทำรายการ blocked ชัดเจน

**PASS**: schema/tests pass, all evaluated cases traceable, source hashes recorded, no fabricated evidence, no numeric ground truth generated only by LLM, no unreported source gaps.

**CONDITIONAL**: artifact works but human semantic review / source ingestion remains; must not claim final answer accuracy or regime accuracy.

**FAIL**: hallucinated sources/values, broken offsets, source mismatch, synthetic data presented as empirical, silent A2 config drift, or missing required checklist/report.

สุดท้ายให้สรุปเป็นภาษาไทยว่า (1) สร้างไฟล์อะไรสำเร็จ (2) จำนวน cases ต่อ track (3) อะไร ready/blocked/requires human review (4) test commands และผลจริง (5) limitations (6) ขั้นตอนรัน benchmark โดยยังไม่เรียก API จำนวนมากเองจนกว่าผู้ใช้ opt-in
