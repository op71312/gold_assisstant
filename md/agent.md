5 Agent ที่เราวางแผนไว้สำหรับโปรเจกต์ Gold Assistant คือระบบ Multi-Agent ที่แบ่งหน้าที่วิเคราะห์ตลาดทองคำออกเป็น 4 Agent เฉพาะทาง แล้วให้ Agent ที่ 5 ตรวจสอบและสังเคราะห์ผลลัพธ์เป็นรายงานสุดท้าย

## สรุป 5 Agents

## AI 1

News Analyst — นักวิเคราะห์ข่าว

- ค้นหาและวิเคราะห์ข่าวเศรษฐกิจ ข่าวทองคำ และเหตุการณ์สำคัญ
- ใช้ข่าวเพื่ออธิบายว่ามีปัจจัยอะไรที่อาจเกี่ยวข้องกับการเคลื่อนไหวของราคาทอง
- เชื่อมโยงข่าวกับข้อมูลตลาดและตัวเลขที่ตรวจสอบได้

## AI 2

Macro Analyst — นักวิเคราะห์เศรษฐกิจมหภาค

- วิเคราะห์ Yield หรืออัตราผลตอบแทนพันธบัตร
- วิเคราะห์ DXY หรือดัชนีค่าเงินดอลลาร์
- วิเคราะห์ FX โดยเฉพาะอัตราแลกเปลี่ยน USD/THB
- เปรียบเทียบการเปลี่ยนแปลงของปัจจัยเหล่านี้กับราคาทองคำ

## AI 3

Quant Analyst — นักวิเคราะห์เชิงปริมาณ

- คำนวณ Returns, Correlation และสถิติตลาด
- วิเคราะห์ความสัมพันธ์ระหว่างตัวแปรด้วยวิธีเชิงปริมาณ
- เรียกใช้ GaussianHMM เพื่อวิเคราะห์ Market Regime หรือภาวะตลาด
- ส่งผลการคำนวณที่ทำซ้ำและตรวจสอบได้ให้ Agent อื่นนำไปใช้

## AI 4

Risk Analyst — นักวิเคราะห์ความเสี่ยงและคุณภาพข้อมูล

- ตรวจสอบ Data Quality, Missing Values และ Anomalies
- ตรวจสอบความน่าเชื่อถือของหลักฐานที่ Agent อื่นใช้
- ระบุข้อจำกัดของข้อมูลและความเสี่ยงในการตีความ
- เตือนเมื่อข้อมูลไม่เพียงพอที่จะสรุปความสัมพันธ์หรือสาเหตุ

## AI 5

Lead Researcher — หัวหน้าทีมวิจัย

- รับผลวิเคราะห์จาก AI 1–4
- เรียกใช้เครื่องมือตรวจสอบตัวเลขและแหล่งข้อมูลอีกครั้ง
- ตรวจสอบว่าข้อสรุปของแต่ละ Agent สอดคล้องกันหรือขัดแย้งกัน
- สังเคราะห์เป็นรายงานสุดท้าย พร้อมหลักฐาน ข้อจำกัด และข้อมูลที่ยังต้องหาเพิ่ม

## Workflow ที่เราวางไว้

Market Data + News + Macro Data

ข้อมูลราคาและข้อมูลประกอบการวิเคราะห์

AI 1

ข่าวและเหตุการณ์

AI 2

Macro และ FX

AI 3

Quant และ HMM

AI 4

Risk และ Data Quality

## AI 5 — Lead Researcher

Verify → Cross-check → Synthesize → Report

Final Gold Market Research Report

ข้อค้นพบ · หลักฐาน · ความสัมพันธ์ · ข้อจำกัด · ข้อมูลที่ต้องตรวจสอบเพิ่ม

หลักการสำคัญ: AI 1–4 ทำงานเฉพาะทางโดยใช้เครื่องมือและข้อมูลที่เหมาะกับหน้าที่ ส่วน AI 5 ไม่ควรเชื่อคำตอบของ Agent อื่นโดยอัตโนมัติ แต่ต้องตรวจสอบตัวเลขและหลักฐานก่อนสรุป

อีกประเด็นที่เราวางไว้คือ อย่าให้ LLM เป็นผู้คำนวณตัวเลขทางสถิติโดยตรง ให้ Python หรือเครื่องมือเชิงคำนวณทำงาน แล้วให้ Agent ช่วยตีความผล วิธีนี้ทำให้ระบบตรวจสอบย้อนกลับได้และลดความเสี่ยงจากการสร้างตัวเลขขึ้นเอง&#x20;

---
อ้างอิงการทำงานของ AI
AI1 : D:\Project_Github\gold assisstant\rag\Gold_Assistant_Full_RAG_End_to_End.ipynb
AI2 : D:\Project_Github\gold assisstant\rag\Gold_Assistant_Full_RAG_End_to_End.ipynb,D:\Project_Github\gold assisstant\dataset\datset a gold price\data\processed\thai_gold_features_v1.parquet
AI3 : D:\Project_Github\gold assisstant\dataset\datset a gold price\data\processed\thai_gold_features_v1.parquet,D:\Project_Github\gold assisstant\model\gold_hmm_v1\model.joblib
AI4 : D:\Project_Github\gold assisstant\dataset\thai-gold-portfolio-simulator,D:\Project_Github\gold assisstant\dataset\datset a gold price\data\processed\thai_gold_features_v1.parquet
AI5 : ใช้ได้หมด ที่ AI1,2,3,4 ใช้ได้แ
