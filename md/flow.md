# datset
## dataset a
-คัดลอกโค้ดตารางจาก https://gtadmin.goldtraders.or.th/updatepricelist/ ได้ D:\Project_Github\gold assisstant\dataset\datset a gold price\gold price.html
-ให้ antigravity แปลงเป็น csv
-D:\Project_Github\gold assisstant\dataset\datset a gold price\Dataset A_gold price.ipynb -> D:\Project_Github\gold assisstant\dataset\datset a gold price\Dataset A_gold price cleaned.ipynb -> D:\Project_Github\gold assisstant\dataset\datset a gold price\data\processed\thai_gold_features_v1.csv

## dataset b
-D:\Project_Github\gold assisstant\dataset\news\Dataset B_Event_thaipbs.ipynb->D:\Project_Github\gold assisstant\dataset\news\pbs\gold_relevance_audit_v2.jsonl
-D:\Project_Github\gold assisstant\dataset\news\Dataset B_Event_fed.ipynb -> D:\Project_Github\gold assisstant\dataset\news\Dataset B_Event_fed_cleaned.ipynb ->D:\Project_Github\gold assisstant\dataset\news\Dataset B_Event_fed_classified.ipynb->D:\Project_Github\gold assisstant\dataset\news\fed\fed_press_releases_cleaned_audit\fed_press_releases_classified.jsonl
-D:\Project_Github\gold assisstant\dataset\news\Dataset B_Event_bls_cpi.ipynb->D:\Project_Github\gold assisstant\dataset\news\bls\cpi\clean
-D:\Project_Github\gold assisstant\dataset\news\Dataset B_Event_bls_NFP.ipynb->D:\Project_Github\gold assisstant\dataset\news\bls\nfp\clean

## สร้างโมเดล
-D:\Project_Github\gold assisstant\dataset\datset a gold price\Dataset A_gold price cleaned.ipynb -> D:\Project_Github\gold assisstant\model\gold_hmm_v1\model.joblib ซึ่งต้องใส่ bar_buy_log_return และ intraday_range_pct

## chunk
-วัดผลเลือกอัลกอ D:\Project_Github\gold assisstant\dataset\ground_truth_source_data_4_datasets.jsonl -> D:\Project_Github\gold assisstant\embedding\gold_assistant_retrieval_evaluation_cloudflare.ipynb -> D:\Project_Github\gold assisstant\embedding\embedding\retrieval_eval_v2\retrieval_metrics_summary.csv
-สร้าง chunk D:\Project_Github\gold assisstant\embedding\create_chunk.ipynb -> D:\Project_Github\gold assisstant\embedding\artifacts\chunking_real\structure_aware

## emdedding
-D:\Project_Github\gold assisstant\embedding\gold_assistant_retrieval_evaluation_cloudflare.ipynb เปรียบเทียบคัดอัลกอริธึมที่ดีที่สุด โดยใช้ ground truth จาก D:\Project_Github\gold assisstant\embedding\embedding\ground_truth_queries_v2.jsonl
-สร้าง embedding D:\Project_Github\gold assisstant\embedding\create_embedding.ipynb -> D:\Project_Github\gold assisstant\embedding\artifacts\chunking_real\structure_aware\chunks_structure_aware_real.jsonl

## สร้าง vector store
-D:\Project_Github\gold assisstant\vector_database\qdrant.ipynb

## RAG
-หาอัลกอริธึมที่ดีที่สุด D:\Project_Github\gold assisstant\rag\rag_eval.ipynb -> D:\Project_Github\gold assisstant\rag\rag_comparison
-full pipeline D:\Project_Github\gold assisstant\rag\Gold_Assistant_Full_RAG_End_to_End.ipynb -> D:\Project_Github\gold assisstant\rag\gold_assistant_outputs

## multi agent
-D:\Project_Github\gold assisstant\function\langgraph.ipynb