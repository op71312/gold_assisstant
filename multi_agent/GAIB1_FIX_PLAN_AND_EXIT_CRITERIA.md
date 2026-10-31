# GAIB-1 — แผนแก้ไขและเกณฑ์ผ่านแบบบังคับ (Fix Plan & Exit Criteria)

**เวอร์ชัน:** 1.0  
**อิงจาก:** Run `20261029T045405Z-ec23a8f0`, token/root-cause experiments ใน bundle เดียวกัน, historical baseline `20261028T150635Z-99522ade` และ live acceptance 6 queries  
**สถานะเริ่มต้น:** `NO-GO` สำหรับ unattended/external use; ใช้ได้เฉพาะ controlled development และ supervised testing  

> ตัวเลขด้านล่างเป็น engineering acceptance policy ที่เสนอสำหรับ Gold Assistant ไม่ใช่ threshold สากลจากงานวิจัย ห้ามเปลี่ยนสถานะ `NOT_EVALUATED` ให้เป็น `PASS` โดยไม่มีหลักฐาน

---

## 1. คำตัดสินปัจจุบัน

หลักฐานปัจจุบันแสดงความก้าวหน้าด้าน JSON/schema: compact prompt ผ่าน 8/9 targeted failure-enriched `(query, agent)` pairs เทียบกับ baseline 2/9 แต่ชุดนี้มีเพียง 9 pairs ที่เลือกจาก failure เดิม จึงใช้เป็นหลักฐานว่าแนวทางแก้มีศักยภาพ ไม่ใช่หลักฐานว่า production reliability ผ่านแล้ว

Live acceptance 6 queries:

- Query completion: 6/6
- Reported JSON/schema validity: 100%
- Reports with citations: 4/6
- Numeric-fact questions answered with cited findings: 1/3
- Mean wall time: 20.60 seconds/query; max 27.12 seconds
- Task correctness: `NOT_EVALUATED_WITHOUT_DOMAIN_ORACLE`
- Semantic citation support: `NOT_HUMAN_REVIEWED`

**เหตุผล NO-GO:** `gtv2_000070` และ `gtv2_000078` ให้ `NO_CLAIMS` ทั้งที่ target document ปรากฏใน reranked/evidence-context results; current retrieval metrics are mainly document/URL-level, not verified answer-bearing-span recall. Citation semantics ยังไม่ผ่าน human review.

---

## 2. Release levels และความหมายของคำว่า “ผ่าน”

### Level 0 — Development only (อนุญาตได้ตอนนี้)
ใช้ผลลัพธ์เพื่อ debug เท่านั้น ห้ามอ้างว่า verified research answer.

### Level 1 — Supervised internal pilot
ผ่าน mandatory gates A–F ด้านล่าง มีมนุษย์ตรวจรายงานก่อนนำไปตัดสินใจ ไม่มี automatic trade/order execution.

### Level 2 — Limited team release
ผ่าน Level 1 และประเมินบน frozen held-out set ที่ใหญ่กว่า มี monitoring, rollback, incident runbook และผล paired comparison กับ simpler baseline.

### Level 3 — Broader/production use
ผ่าน Level 2, ได้ทดสอบ repeatability/load ที่สอดคล้องกับ use case, domain/tool contracts ทั้งหมดผ่าน, มีการจัดการ incidents และเปิดเผยข้อจำกัดของระบบอย่างชัดเจน ห้ามใช้ LLM report เป็นคำสั่งซื้อขายโดยลำพัง.

**Rule:** ทุก mandatory gate ต้องเป็น `PASS`; ค่า `NOT_EVALUATED`, `INSUFFICIENT_SAMPLE`, `UNVERIFIED` หรือ `FAIL` ห้ามนับเป็นผ่าน.

---

## 3. Workstream P0 — ความถูกต้องของ measurement และ run integrity

### ต้องแก้
1. แยก logical query result, agent result และ HTTP attempt ออกจากกัน ห้ามใช้ตารางเดียวปน aggregation levels.
2. ทุก record มี `run_id`, `variant`, model ID, `source_hash`, prompt/schema version, config snapshot, query ID, agent, attempt number, timestamp.
3. บันทึกทุก attempt รวมถึง API exception, retry, `finish_reason`, requested max tokens, prompt/completion tokens, latency, error class.
4. แยก `initial_json_parse`, `final_json_parse`, `schema_valid`, `task_success`, `any_attempt_truncated` และ `final_attempt_truncated`.
5. ห้ามให้ `status=success` อยู่ร่วมกับ `json_parse=false` หรือ `schema_valid=false`.
6. ไฟล์ CSV ที่ไม่มี records ต้องยังมี headers ครบและอ่านได้.
7. แยก historical provenance ที่ไม่ครบจาก fresh run; ห้ามนำ historical และ fresh rows มารวมเป็น estimate โดยไม่กรอง `run_id`/`variant`.
8. แก้ `citation_paragraph_coverage` ไม่ให้นับ Markdown heading เป็น paragraph; ห้ามคำนวณ semantic support จากการตรวจ citation IDs อย่างเดียว.

### เกณฑ์ผ่าน P0
- 100% ของ expected records ถูก accounted for; missing/failures แสดงชัดเจน.
- 0 duplicate keys ใน `(run_id, query_id, agent, attempt)`.
- 0 contradictory status/validity flags.
- 100% ของ runs มี config, model, code/source hash, prompt/schema version และ index/corpus version.
- ทุก retry/API error มี attempt row; token counts ไม่ปะปนระหว่าง initial, repair และ cumulative.
- Offline unit tests ผ่านทั้งหมดก่อนยิง remote calls.

หากไม่ผ่าน P0 ให้ run เป็น `INVALID_FOR_COMPARISON` และห้ามสรุปว่า variant ใดดีขึ้น.

---

## 4. Workstream P0 — แก้ answer completeness ของ numeric facts

### ปัญหาที่พิสูจน์ได้จาก live run
- `gtv2_000070`: ไม่มี findings/citations (`NO_CLAIMS`).
- `gtv2_000078`: ไม่มี findings/citations (`NO_CLAIMS`).
- ทั้งสองเป็น numeric-fact questions และ expected target documents ปรากฏใน reranked/evidence-context candidate report.
- `gtv2_000055`: คำตอบมีเนื้อหาเกี่ยวกับ inflation แต่ต่างจาก expected statement; ต้อง human review ว่าเป็น answer mismatch หรือ acceptable paraphrase/incomplete answer.

### ต้องเพิ่ม diagnostic trace ต่อ query
สำหรับ `gtv2_000070` และ `gtv2_000078` ให้เก็บและตรวจเนื้อหาจริง ไม่ใช่แค่ IDs:
1. Ground Truth: expected document ID, URL, exact quote, offsets, expected numeric fact.
2. Retrieval: Dense top-k, BM25 top-k, RRF top-k, Jina results พร้อม `chunk_id`, full text/excerpt, dates, score และ match flags.
3. Final context: exact text ที่ส่งให้ specialist โดยระบุว่ามี target-range sentence จริงหรือไม่.
4. AI1 raw response, parsed data, schema errors และ `evidence_ids`.
5. AI5 input payload ที่ผ่าน schema validation.
6. AI5 findings ก่อน render, rendered findings หลัง validation และเหตุผลที่ claim ถูก drop.

จำแนก root cause เป็น `SOURCE_NOT_INDEXED`, `PASSAGE_NOT_RETRIEVED`, `PASSAGE_NOT_IN_CONTEXT`, `SPECIALIST_EXTRACTION_FAILURE`, `AI5_SYNTHESIS_DROPPED_FINDING`, `CITATION_VALIDATION_DROPPED_FINDING`, `GROUND_TRUTH_ISSUE` หรือ `UNRESOLVED`.

### เกณฑ์ผ่าน P0 Answer Completeness
- ใน regression set ของ 6 live queries: numeric factual answer coverage ต้อง 3/3 เมื่อ evidence มีจริง; หากหลักฐานไม่พอ ต้อง abstain พร้อมเหตุผลที่ถูกต้อง ไม่ใช่ `NO_CLAIMS` แบบไม่มีคำอธิบาย.
- เพิ่ม `expected_fact_coverage`, `answer_attempted`, `abstention_reason`, `abstention_correctness`.
- 100% ของ critical numeric/date/policy facts ใน deterministic oracle regression set ต้องตอบตรงค่า/หน่วย/วันที่/action หรือ abstain อย่างถูกต้องเมื่อ evidence ขาด.
- ห้ามให้ schema-valid report ที่มี `NO_CLAIMS` ถูกนับเป็น task success หาก query ขอ fact ที่มี expected answer.

---

## 5. Workstream P0 — Retrieval ต้องวัดระดับ passage ที่ตอบคำถามได้

### ต้องแก้
1. คง document/URL recall เป็น diagnostic metric แต่เพิ่ม `answer_bearing_span_recall@k` และ `evidence_span_in_final_context`.
2. ตรวจ exact quote/offset ของ Ground Truth เทียบกับ chunk content จริง.
3. แยก `index_coverage_verified`, `retrieved_in_candidate_pool`, `retrieved_in_final_top_k`, `present_in_final_context` และ `used_by_final_claim`.
4. Runtime index coverage `COVERED` ต้องไม่ถูกตีความเป็น retrieval success.
5. เมื่อ relevance judgments ไม่ exhaustive ให้เรียก `known_relevant_recall@k` และแสดงข้อจำกัด.
6. วัด Dense-only, BM25-only, Hybrid/RRF และ Jina แยกกัน; ห้ามเลือก method จากผล 6 queries อย่างเดียว.

### เกณฑ์ผ่าน Retrieval
**Level 1 pilot (บน held-out benchmark ที่ตรวจ labels แล้ว):**
- 100% ของ cases ที่นำไปคิดคะแนนมี expected source/evidence span อยู่ใน index หรือถูกจัด exclusion พร้อมเหตุผล.
- Document-level known-relevant Recall@10 ≥ 0.85.
- MRR@10 ≥ 0.60; nDCG@10 ≥ 0.70.
- Answer-bearing-span Recall@10 ≥ 0.90.
- Worst major query category Recall@10 ≥ 0.75.
- 100% ของ critical numeric/policy cases ใน reviewed regression set ต้องส่ง answer-bearing evidence ถึง final context หรือ abstain อย่างถูกต้อง.
- ทุก miss มี stage-by-stage diagnostics.

**Level 2:** Recall@10 ≥ 0.90, MRR@10 ≥ 0.70, nDCG@10 ≥ 0.80, span recall@10 ≥ 0.95 และ worst major category Recall@10 ≥ 0.85.

**Sample size:** อย่างน้อย 100 held-out queries สำหรับ Level 1 และให้มีอย่างน้อย 20 cases ต่อ major category เท่าที่ชุดข้อมูลรองรับ; หากมีน้อยกว่านี้ให้ระบุ `PRELIMINARY` ไม่ใช่ `PASS`. ห้ามปรับ prompt/parameters จาก frozen test set.

---

## 6. Workstream P0 — compact output contracts และ recovery

### หลักฐานปัจจุบัน
บน 9 failure-enriched query-agent pairs:
- Baseline 900 tokens: schema-valid 2/9; truncation observed 6/9.
- 1,200 tokens: schema-valid 4/9; truncation 4/9.
- AI3 ที่ 1,500 tokens: ยัง truncation 4/4.
- Compact 900 tokens: schema-valid 8/9; truncation 1/9.
- AI2 บน `gtv2_000071` ยัง truncation ภายใต้ compact 900.

### ต้องทำ
1. ใช้ compact contract เป็น leading candidate ไม่ใช่ global production default.
2. แก้ AI1 nested field typing, AI4 enum `go_no_go`, AI5 list fields และ field-specific schema failures.
3. สำหรับ confirmed truncation ให้ retry แบบ bounded ด้วย compact prompt และ 1,200-token budget; เพิ่มเป็น 1,500 เฉพาะเมื่อมี finish reason ยืนยันว่า 1,200 ยังถูกตัด.
4. ไม่ retry เพิ่ม budget เพียงเพราะ schema violation ที่ไม่เกี่ยวกับ truncation; ใช้ targeted schema repair.
5. AI5 รับเฉพาะ schema-valid specialist data; failed specialist ต้องเป็น explicit `unavailable/partial` และห้ามส่ง raw invalid JSON เป็น trusted findings.
6. ทุก recovery ต้องเก็บ initial/final result, attempts, token overhead และ recovered flag.

### เกณฑ์ผ่าน Reliability
- JSON parse rate หลัง bounded recovery ≥ 99% (Level 1), ≥ 99.5% (Level 2).
- Schema-valid rate หลัง bounded recovery ≥ 98% (Level 1), ≥ 99.5% (Level 2).
- Downstream payloads ที่ใช้เป็น trusted data ต้องผ่าน schema 100%.
- Final report renderer/schema validity 100%.
- 0 unlogged retries; 0 silent conversion of invalid output to success.
- Conditional fallback ทำงานครบทุก fault-injection test.
- ต้องประเมินบนตัวอย่าง representative ไม่ใช่เพียง 9 failure-enriched pairs.

---

## 7. Workstream P0 — citations และ semantic support

### ต้องแก้
1. เก็บ `raw_proposed_citation_ids` ก่อน deterministic renderer กรอง IDs.
2. คำนวณ `report_has_citations_rate`, raw citation validity, rendered citation validity, claim citation coverage และ semantic citation support แยกกัน.
3. แก้ paragraph parser ให้ไม่นับ headings และประเมิน structured claim blocks เป็นหลัก.
4. `NO_CLAIMS` ต้องมีสถานะแยกจาก claims ที่ไม่มี citations.
5. Claim ที่ไม่มีหลักฐานต้องถูก mark unsupported/abstain; ห้ามเติม citation เพื่อให้ metric ผ่าน.
6. ตรวจทุก citation ว่าสนับสนุน claim ที่แนบจริง โดย human review หรือ evaluator ที่เทียบกับ human labels แล้ว.

### เกณฑ์ผ่าน
- Citation IDs ใน final report: 100% valid.
- ทุก external-source factual report มี citations หรือแสดง explicit abstention/no-source state.
- Material factual claim coverage: ≥ 95% Level 1, ≥ 98% Level 2.
- Human-reviewed citation support rate: ≥ 95% Level 1, ≥ 98% Level 2.
- High-impact numeric/date/policy/P&L claims ที่อยู่ใน reviewed sample: support 100%; unsupported critical claims = 0.
- ตรวจ human อย่างน้อย 100 claims แบบ stratified; double-review ≥20% และ adjudicate disagreements. ถ้ายังมีน้อยกว่านี้ให้รายงาน `PRELIMINARY`.

---

## 8. Workstream P1 — correctness, language และ tool contracts

### เกณฑ์ผ่าน
- Numeric facts: 100% ของ critical oracle cases ตรง expected value, unit, period/date และ action.
- Ordinary human-reviewed factual claims: ≥95% correctness.
- Insufficient-evidence cases: correct abstention/explicit caveat 100% ใน curated regression subset.
- Output language: ตรงกับ query language 100% ใน language-adherence tests เว้นแต่ผู้ใช้ขอภาษาอื่น.
- Quant/statistical deterministic unit tests: 100% pass.
- HMM contract: 100% pass สำหรับ feature order, preprocessing/scaler version, as-of timestamp, missingness handling และ output schema; contract pass ไม่เท่ากับ predictive validity.
- Portfolio/P&L ledger invariants: 100% reconcile; ไม่มี duplicate transaction identity หรือ silent mismatch ที่ยังไม่อธิบาย.
- หาก feature dataset มี missingness ต้องรายงานเป็นราย feature และพิสูจน์ว่าการเติม/คัดทิ้งไม่ทำให้ feature contract เปลี่ยนจาก training.
- ทุก critical factual/numerical failure ต้อง root-cause, fix และ regression test ก่อนปล่อย.

หมายเหตุ: live FOMC benchmark นี้ยังไม่ validate HMM predictive accuracy หรือ portfolio-risk outputs. `hmm_status=available` ไม่ใช่หลักฐานว่า HMM ให้คำตอบถูก และ `risk_snapshot_ms=0` หมายถึง run นี้ไม่ได้ทดสอบ risk snapshot จริง.

---

## 9. Workstream P1 — Latency, cost และ Multi-Agent value

### Operational gates สำหรับ Level 1
- Completion rate หลัง bounded retry/explicit fallback ≥99%.
- Simple lookup P95 ≤15 seconds.
- Full research mode P95 ≤60 seconds.
- Mean total tokens/full research query ≤30,000 เป็น soft budget; hard per-query cost/token cap ต้องตั้งและ enforce.
- วัด end-to-end ≥100 full runs ก่อนอ้าง P95 เป็น operational estimate; รายงาน `n`, median, P95 และ max.
- แยก retrieval, reranker, each agent, repair และ final synthesis timings.

### ต้องพิสูจน์ว่า 5 Agents คุ้มค่า
เปรียบเทียบ 5-agent architecture กับ single-agent+RAG และ routed-agent variant บน queries, evidence และ evaluation rubric เดียวกัน.

คง 5-agent default เฉพาะเมื่อมีอย่างน้อยหนึ่งข้อ:
- verified quality/citation support ดีขึ้น ≥5 percentage points โดยไม่มี critical correctness regression; หรือ
- คุณภาพเท่าเดิมแต่ mean latency หรือต้นทุนลด ≥20% ด้วย router; หรือ
- มี capability เพิ่มที่วัดได้และผู้ใช้ต้องการจริง.

ใช้ paired comparisons พร้อม confidence intervals; อย่าตัดสินจาก 6 queries.

---

## 10. แผนทำงานและ exit criteria ทีละ phase

### Phase 1 — Instrumentation freeze
**ทำ:** แก้ telemetry, status semantics, attempt accounting, headers ของ empty CSV, aggregation levels, citation parser, run manifest.

**Exit:** Unit tests ผ่าน 100%; 0 duplicate/missing/contradictory records; ทุก retry มี telemetry; reproducible offline run.

### Phase 2 — แก้ answer failures บน 6-query regression
**ทำ:** Trace `gtv2_000070` และ `gtv2_000078` จาก expected quote ถึง final report; trace `gtv2_000055` กับ human review; เพิ่ม expected-fact checks และ language check.

**Exit:** 6/6 query outputs มีสถานะถูกต้อง; numeric 3/3 answered correctly with valid support หรือ abstain correctly; no unexplained `NO_CLAIMS`; all factual claims have verified evidence IDs.

### Phase 3 — เลือก compact/recovery variant
**ทำ:** Compact 900 เป็น candidate; targeted conditional 1,200 retry สำหรับ failure class ของ AI2; schema-specific repair ของ AI1/AI4/AI5; ทำ regression tests.

**Exit:** ผ่าน JSON/schema thresholds และ downstream gate 100%; ไม่มีกลุ่ม failure ที่ถูกซ่อนด้วย average; token/latency overhead อยู่ใน budget.

### Phase 4 — Retrieval qualification
**ทำ:** เพิ่ม answer-bearing-span recall, ตรวจ index coverage และ judgments, แยก Dense/BM25/RRF/Jina results; แก้ missed spans.

**Exit:** ผ่าน retrieval thresholds จาก held-out benchmark; critical numeric regression 100%.

### Phase 5 — Citation/human-review qualification
**ทำ:** ตรวจอย่างน้อย 100 claims แบบ stratified, double-review ≥20%, แก้ unsupported claims และ audit metrics.

**Exit:** ผ่าน citation thresholds; 0 unsupported high-impact claims; ไม่มี metric ที่ยัง `NOT_HUMAN_REVIEWED` ใน release decision.

### Phase 6 — Pilot benchmark and decision
**ทำ:** ≥100 held-out queries, task types/languages/difficulty/abstention cases ที่เป็นตัวแทน; ≥100 end-to-end runs สำหรับ latency; run single-agent baseline.

**Exit:** All mandatory Level 1 gates `PASS`; ถ้าข้อใดยัง `NOT_EVALUATED` ให้คง `NO-GO` สำหรับ unattended release.

### Phase 7 — Limited release
**ทำ:** ≥200–300 held-out queries; ≥200 operational runs ภายใต้ load representative; monitoring, alerts, rollback, incident runbook.

**Exit:** All Level 2 targets pass on frozen test; ไม่มี critical failure; มีหลักฐาน value เทียบ simpler baseline.

---

## 11. Definition of Done ของแต่ละ bug

ห้ามปิด bug ด้วยข้อความว่า “รันผ่านแล้ว” อย่างเดียว ต้องมีครบ:
1. Reproducible failing test ก่อนแก้.
2. Root-cause classification พร้อม evidence.
3. Fix ที่แคบที่สุดและอธิบายได้.
4. Regression test ที่ fail ก่อน/ผ่านหลัง.
5. Paired before/after metrics บน query IDs/config ที่เทียบกันได้.
6. Negative results และ regressions ถูกบันทึก.
7. Code/config/prompt/schema versions ถูกเก็บใน manifest.
8. ไม่มีการใช้ held-out/test set เพื่อจูน variant.

---

## 12. Overall Go/No-Go

### NO-GO หากมีข้อใดข้อหนึ่ง
- Telemetry invalid หรือผลทดลองทำซ้ำไม่ได้.
- Numeric critical case ตอบผิด/ไม่ตอบทั้งที่ evidence อยู่จริง โดยไม่ abstain อย่างชัดเจน.
- Raw invalid specialist output เข้า AI5 ในฐานะ trusted data.
- Citation ไม่มี ID ที่ valid หรือมี unsupported critical claim.
- Retrieval score มาจาก document/URL match อย่างเดียว แต่ถูกอ้างว่า evidence-span recall ผ่าน.
- Deterministic tool/ledger/HMM contract tests ไม่ผ่าน.
- Task correctness หรือ human citation support ยัง `NOT_EVALUATED` แต่รายงานถูกนำเสนอว่า verified.

### GO — Supervised Internal Pilot
ทุก Level 1 gates ผ่าน; human review ก่อนใช้งาน; explicit partial/abstention; no automated trading.

### GO — Limited Release
ทุก Level 2 gates ผ่านบน frozen holdout; มี monitoring/rollback/runbook; multi-agent value ได้รับการพิสูจน์.

---

## 13. ลำดับความสำคัญแบบสั้น

1. **P0:** Trace `gtv2_000070` และ `gtv2_000078` จาก exact evidence span ถึง final report; ห้ามให้ `NO_CLAIMS` นับเป็น success.
2. **P0:** แก้ evaluation measurement: span-level retrieval, citation parser, `NO_CLAIMS`, raw vs rendered IDs, aggregation levels.
3. **P0:** ใช้ compact contract เป็น candidate แล้วแก้ AI2 residual truncation และ schema contracts; bounded recovery.
4. **P0:** ทำ deterministic oracle สำหรับ numeric facts และ human-review citation support.
5. **P1:** ขยาย held-out dataset และวัด latency/cost ด้วยจำนวนตัวอย่างเพียงพอ.
6. **P1:** พิสูจน์ multi-agent value เทียบ simpler baseline ก่อนรักษา 5-agent default.

**หยุดเมื่อ:** ทุก mandatory release gate ของระดับเป้าหมายเป็น `PASS`, ไม่มี `NOT_EVALUATED` ที่เกี่ยวกับความถูกต้อง/หลักฐาน, และทุก failure ที่พบมี regression test ป้องกันไม่ให้กลับมาอีก.
