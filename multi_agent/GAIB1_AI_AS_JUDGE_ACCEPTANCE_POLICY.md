# GAIB-1 — เกณฑ์การประเมินผลด้วย AI-as-a-Judge สำหรับ Gold Assistant

**สถานะ:** เกณฑ์ Release Gates ฉบับปรับปรุงสำหรับ Gold Assistant (GAIB-1)  
**อ้างอิงสถาปัตยกรรม 5 Agents:** [`md/agent.md`](../md/agent.md)  
**เป้าหมาย:** ประเมินคุณภาพการวิเคราะห์ตลาดทองคำไทยได้อย่างมีประสิทธิภาพ ปฏิบัติได้จริง ไม่ซับซ้อนเกินขนาดของโปรเจกต์ (Pragmatic & Domain-Aligned)

---

## 1. บริบทและบทบาทของ 5 Agents ใน Gold Assistant

ระบบ Gold Assistant แบ่งการทำงานออกเป็น 4 ผู้เชี่ยวชาญเฉพาะทาง (AI 1–4) และ 1 ผู้ตรวจสอบ/สังเคราะห์ผล (AI 5) โดยยึดหลักการสำคัญ:
> **"Python และเครื่องมือเชิงคำนวณเป็นผู้คำนวณตัวเลขทางสถิติและแบบจำลอง (Deterministic) ส่วน LLM มีหน้าที่ช่วยตีความผล ไม่ให้ LLM เดาหรือคำนวณตัวเลขเอง"**

- **AI 1 — News Analyst:** วิเคราะห์ข่าวเศรษฐกิจ ข่าวทองคำ และเหตุการณ์สำคัญที่กระทบต่อราคาทอง
- **AI 2 — Macro Analyst:** วิเคราะห์ Bond Yield, Dollar Index (DXY) และอัตราแลกเปลี่ยน USD/THB
- **AI 3 — Quant Analyst:** คำนวณ Returns, Correlation และเรียกใช้ **GaussianHMM** เพื่อวิเคราะห์ Market Regime (รันด้วย Python / scikit-learn / joblib)
- **AI 4 — Risk Analyst:** ตรวจสอบ Data Quality, ข้อจำกัดของข้อมูล, Anomalies และเตือนเมื่อข้อมูลไม่พอสรุปผล
- **AI 5 — Lead Researcher:** ตรวจสอบตัวเลขและหลักฐานจาก AI 1–4, ตรวจจับข้อขัดแย้ง และสังเคราะห์เป็นรายงานสุดท้าย พร้อม Citation IDs:
  - `[S#]` สำหรับหลักฐานจากเอกสารข่าว/บทวิเคราะห์
  - `[Q#]` สำหรับตัวเลขเชิงปริมาณและสถิติจาก Python
  - `[H#]` สำหรับผล Market Regime จากแบบจำลอง GaussianHMM

---

## 2. โมเดลภาษาที่รองรับ (ThaiLLM Supported Models)

โมเดลทั้งหมดทำงานผ่าน ThaiLLM API (`https://thaillm.or.th/api/v1`) โดยมีรายชื่อโมเดลมาตรฐานของระบบดังนี้:

| Model ID | บทบาทที่แนะนำ | จุดเด่น |
| :--- | :--- | :--- |
| `openthaigpt-thaillm-8b-instruct-v7.2` | **Generator หลัก** (AI 1–5) | เสถียร เข้าใจภาษาไทยและบริบทคำสั่งได้ดี |
| `pathumma-thaillm-qwen3-8b-think-3.0.0` | **Primary AI Judge** | มีความสามารถด้านการคิดวิเคราะห์ (Reasoning/Thinking) เหมาะสำหรับตรวจจับความสอดคล้อง |
| `typhoon-s-thaillm-8b-instruct` | **Alternative Judge / Generator** | โมเดลภาษาไทยประสิทธิภาพสูง ใช้เป็นตัวเลือกสลับได้ |
| `thalle-0.2-thaillm-8b-fa` | **Specialized Alternative** | โมเดลทางเลือกสำหรับงานเฉพาะทาง |

*หมายเหตุ: ไม่มีการใช้งานหรือบังคับโมเดลภายนอกที่ไม่มีในระบบ (เช่น `qwen3.6-35b-a3b` หรือตระกูลโมเดล 35B+ อื่นๆ) เพื่อป้องกันความผิดพลาดด้าน API และปัญหา Latency*

---

## 3. สถาปัตยกรรมการประเมิน (Evaluation Architecture)

ระบบใช้สถาปัตยกรรมแบบ 2 ชั้นที่กระชับและเชื่อถือได้จริง:

```
[Agent Output / Final Report]
           │
           ▼
┌────────────────────────────────────────┐
│ Layer A: Deterministic Checks (Python) │
│ - JSON Parsing & Schema Validation     │
│ - Math & Quant Consistency (AI 3/4)    │
│ - Citation Existence [S#], [Q#], [H#]  │
└──────────────────┬─────────────────────┘
                   │ (ผ่าน Layer A)
                   ▼
┌────────────────────────────────────────┐
│ Layer B: Primary AI-as-a-Judge         │
│ - ใช้โมเดลแยกจาก Generator            │
│   (เช่น Pathumma-Think หรือ Typhoon)   │
│ - ตรวจ Factual Entailment กับ Evidence │
│ - ตรวจ Completeness & Abstention       │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ Human Spot-Check Audit (Optional/Gate) │
│ - สุ่มตรวจ 10–20 claims สำคัญ          │
│   โดยผู้พัฒนา/ผู้เชี่ยวชาญคนเดียว     │
└────────────────────────────────────────┘
```

### Layer A — Deterministic Checks (ต้องผ่าน 100%)
- **JSON Format & Schema:** ผลลัพธ์ของ Agent ทุกตัวต้องเป็น JSON ที่ parse ได้ตรงตาม schema
- **Citation ID Validation:** Citation Token ทุกตัว (`[S#]`, `[Q#]`, `[H#]`) ต้องมีอยู่ใน Context ที่ค้นพบจริง ห้ามสร้าง Citation หลอก
- **Deterministic Math & Quant:** ค่าตัวเลขของ AI 3 (เช่น Regime State, Volatility, Returns) และ AI 4 ต้องตรงกับผลลัพธ์ของโค้ด Python
- **ห้าม AI Judge ขัดแย้งกับ Deterministic Oracle:** หากโค้ดตรวจพบว่าตัวเลขหรือ Citation ไม่ตรง AI Judge ไม่มีสิทธิ์ตัดสินให้ผ่าน

### Layer B — Primary AI Judge
- **แยก Model จาก Generator:** หาก Generator ใช้ `openthaigpt-thaillm-8b-instruct-v7.2` ให้ตั้ง Judge เป็น `pathumma-thaillm-qwen3-8b-think-3.0.0` หรือ `typhoon-s-thaillm-8b-instruct`
- **ประเมินแบบ Blind Evidence:** ป้อนเฉพาะ Query, ข้อความอ้างอิง (Claim) และหลักฐานจริงที่ดึงมา (Retrieved Evidence) โดยซ่อนชื่อ Generator
- **ตัด Layer C (Second Judge Escalation) ออก:** เพื่อไม่ให้เกิด Token Overload, ปัญหา Timeout และความล่าช้าที่ไม่จำเป็นสำหรับโปรเจกต์ขนาดนี้

---

## 4. Claim-Level Rubric สำหรับ AI Judge

ทุก Claim ที่ AI Judge ตรวจสอบจะคืนโครงสร้าง JSON ดังนี้:
- `claim_id`: รหัสอ้างอิงของข้อความ
- `claim_text`: ข้อความที่ประเมิน
- `claim_type`: `numeric | policy | attributed | explanation | abstention`
- `correctness`:
  - `supported` — มีหลักฐานใน Evidence สนับสนุนชัดเจน
  - `contradicted` — ขัดแย้งกับหลักฐานที่มี
  - `insufficient_evidence` — หลักฐานไม่พอที่จะยืนยัน
- `citation_entailment`: `entailed | partial | not_entailed`
- `completeness`: `complete | partially_complete | incomplete`
- `confidence`: ตัวเลข 0–100
- `rationale`: เหตุผลสั้นๆ พร้อมระบุ Citation ID ที่เกี่ยวข้อง

---

## 5. การสุ่มตรวจโดยมนุษย์ (Human Spot-Check Audit)

ปรับจากเกณฑ์วิชาการเดิมที่บังคับตรวจ 50 claims พร้อมผู้ตรวจอิสระ 2 คน (Double Review) เป็นเกณฑ์ที่ทำได้จริง:
- **จำนวน:** สุ่มตรวจ **10–20 claims** ต่อรอบการประเมิน Release
- **ผู้ตรวจ:** ผู้พัฒนาหรือนักวิเคราะห์ตลาดทองคำ **1 คน**
- **สัดส่วนที่เน้นตรวจ:**
  - ตัวเลขเชิงปริมาณหรือสถิติราคา (Numeric facts) 5 claims
  - ข่าวและปัจจัยมหภาคที่ส่งผลต่อทอง (Attributed/Macro) 5 claims
  - กรณีที่ AI Judge ให้คะแนนก้ำกึ่ง (Borderline / Low confidence) 5 claims
  - กรณีสุ่มทั่วไปเพื่อยืนยันผล 5 claims

---

## 6. Release Gates ที่ปรับปรุงให้เหมาะสม (Practical Release Gates)

### Gate A — Pipeline Integrity & Schema
- 100% ของคำถามที่รัน ต้องได้ผลลัพธ์หรือบันทึก Error ชัดเจน
- อัตราการ Parse JSON สำเร็จของ 5 Agents $\ge 95\%$
- ผ่าน Regression Tests ของระบบ

### Gate B — Retrieval Quality (Gold Context)
- Qdrant + Jina Reranker สามารถค้นคืนเนื้อหาที่เกี่ยวข้องกับคำถาม:
  - Document Recall@10 $\ge 0.85$
  - MRR@10 $\ge 0.60$

### Gate C — Citation & Factual Grounding
- Citation ID Validity $= 100\%$ (Citation ทุกตัวต้องมีอยู่จริงในเอกสารที่ค้นมา)
- AI-Judge Correctness (ความถูกต้องตามหลักฐาน) $\ge 85\%$
- อัตราความสอดคล้องของการอ้างอิง (Citation Entailment) $\ge 85\%$
- Unsupported Critical Numeric Claims $= 0$ (ไม่มีการกุตัวเลขราคาหรือสถิติขึ้นมาเองโดยไม่มีหลักฐาน)

### Gate D — Performance & Latency
- รันการวิเคราะห์ผ่าน 5 Agents ได้อย่างต่อเนื่องโดยไม่เกิด Token Truncation วิกฤต
- เวลาประเมินของ AI Judge ต่อ 1 คำถาม ไม่ทำให้ระบบค้างหรือเกินขีดจำกัดของ ThaiLLM API

---

## 7. กฎเหล็กที่คงไว้ (Core Safeguards)
1. ห้ามใช้โมเดล Generator เดียวกันมาตัดสินคำตอบตัวเองเพียงตัวเดียว
2. ห้ามตัดทอนผลลัพธ์ที่ผิดพลาดออกเพื่อทำให้คะแนนดูผ่าน
3. ห้ามให้ LLM ทำหน้าที่คำนวณสถิติเชิงปริมาณหรือ GaussianHMM แทนโค้ด Python
4. ผลลัพธ์เชิงตัวเลขและข้อความอ้างอิง ต้องตรวจสอบย้อนกลับไปยัง Citation ID ได้เสมอ
