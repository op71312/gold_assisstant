'use client';

import { useState } from 'react';
import {
  ArrowDownRight,
  ArrowRight,
  BookOpenText,
  CheckCircle2,
  CircleHelp,
  Database,
  FileSearch,
  FlaskConical,
  Layers3,
  Network,
  Search,
  Sparkles,
  Waypoints,
} from 'lucide-react';
import { ViewHeader } from './shared';
import type { MarketPayload } from '@/lib/gold/payload';

type StageId = 'dataset' | 'eda' | 'features' | 'hmm' | 'corpus' | 'chunking' | 'embedding' | 'vector-db' | 'rag';
type NodeKind = 'source' | 'process' | 'result' | 'focal';

interface FlowNode {
  id: StageId;
  title: string;
  detail: string;
  kind: NodeKind;
}

interface JourneyStage {
  id: StageId;
  number: string;
  group: string;
  title: string;
  subtitle: string;
  icon: typeof Database;
  input: string;
  process: string;
  result: string;
  decision: string;
  evidence: string;
  status: 'measured' | 'caveat';
}

const STAGES: JourneyStage[] = [
  {
    id: 'dataset',
    number: '01',
    group: 'ข้อมูลต้นทาง',
    title: 'Dataset',
    subtitle: 'ข้อมูลตลาดและเอกสารหลักฐาน',
    icon: Database,
    input: 'ราคาประกาศย้อนหลังจากสมาคมค้าทองคำ (GTA) 24,519 รายการ ช่วง พ.ค. 2006–ต.ค. 2026; เอกสารข่าว/เศรษฐกิจจาก Thai PBS API, Federal Reserve และ BLS',
    process: 'เก็บสำเนา HTML ราคาทองและแปลงเป็นตาราง; ดึงข่าว/รายงานตาม archive แล้วเก็บ publication date, source และ metadata สำหรับตรวจย้อนกลับ',
    result: 'ได้ข้อมูลราคาตามประกาศจริง และเอกสาร 5,058 ฉบับสำหรับสาย retrieval: Thai PBS 9, Fed 4,553, CPI 248, NFP 248',
    decision: 'แยกข้อมูลราคาที่สังเกตได้ออกจากเอกสารและข้อมูลจำลอง; ใช้ source ที่มีร่องรอยตรวจสอบได้ ไม่เรียกข้อมูล snapshot ว่าเป็น live feed',
    evidence: 'md/flow.md · md/notebooks.md · README: ชุดข้อมูลและที่มา',
    status: 'measured',
  },
  {
    id: 'eda',
    number: '02',
    group: 'ข้อมูลตลาด',
    title: 'EDA & Quality',
    subtitle: 'ตรวจ timestamp, missing และแถวซ้ำ',
    icon: Search,
    input: 'ประกาศราคา 24,519 แถว มีวัน เวลา session ราคา bar/ornament, Spot และ USD/THB; ช่วงข้อมูล 2006-05-01 ถึง 2026-10-13',
    process: 'แปลงวันเวลาและเรียงตาม timestamp/session; พบ timestamp ซ้ำ 8 กลุ่ม (16 แถว) ที่บางกลุ่มมีราคาต่างกัน จึงไม่ลบซ้ำแบบทิ้งข้อมูล แต่รวมเป็นรายวันด้วย first/last/high/low',
    result: 'วันและเวลา parse ไม่ผ่าน 0 แถว; ได้ 6,261 วันรายวัน; Spot ขาด 540 วัน และ FX ขาด 691 วันใน feature snapshot ปัจจุบัน',
    decision: 'เก็บ missing เป็น null ไม่เติมค่า และเก็บการเคลื่อนไหวระหว่างวันด้วย high/low แทนการเลือกแถวซ้ำตามอำเภอใจ',
    evidence: 'dataset/datset a gold price/Dataset A_gold price cleaned.ipynb · web/data/manifest.json',
    status: 'measured',
  },
  {
    id: 'features',
    number: '03',
    group: 'ข้อมูลตลาด',
    title: 'Feature Engineering',
    subtitle: 'สร้างสัญญาณระดับวัน',
    icon: Layers3,
    input: 'ราคา GTA รายวัน, ราคา Gold Spot, USD/THB และราคาทองซื้อเข้า/ขายออกที่สังเกตได้',
    process: 'คำนวณผลตอบแทนไทย/ทองโลก/FX, global-plus-FX return และ residual; สร้าง rolling volatility 20/60 วัน, rolling correlations 60 วัน และ robust residual z-score',
    result: 'thai_gold_features_v1 มี 6,261 แถวรายวันและ market-quality flags; ไม่มีการ impute ค่า Spot/FX',
    decision: 'เก็บทั้งผลตอบแทนของทองบาทและองค์ประกอบ Spot/FX เพื่อแยกการเคลื่อนไหวที่สอดคล้องกับทองโลกออกจากส่วนต่าง ไม่ตีความ correlation เป็นเหตุและผล',
    evidence: 'dataset/datset a gold price/data/processed/thai_gold_features_v1.csv · web/data/manifest.json',
    status: 'measured',
  },
  {
    id: 'hmm',
    number: '04',
    group: 'ข้อมูลตลาด',
    title: 'HMM Regimes',
    subtitle: 'Gaussian HMM · 3 latent states',
    icon: Waypoints,
    input: '6,260 model observations จาก bar_buy_log_return และ intraday_range_pct; วันแรกไม่มี return จึงไม่เข้า model',
    process: 'StandardScaler fit เฉพาะ train; split ตามเวลา 70/15/15 (4,382/939/939); ทดลอง K=2,3,4 และ seeds 11,21,42 ด้วย GaussianHMM (diag, up to 200 iterations); ใช้ filtered probabilities ตามลำดับเวลา',
    result: 'เลือก K=3 จาก validation predictive log-likelihood ต่อแถว -0.8837; test predictive log-likelihood -1.8923 บน 939 วัน. State เรียงตามช่วง intraday range ไม่ใช่ label วิกฤต',
    decision: 'ใช้ 3 states เพราะ validation score ดีกว่า K=2 และ K=4 ภายใน baseline 2-feature; ไม่เรียกผลนี้ว่า accuracy หรือสัญญาณซื้อขาย. EGARCH+HMM มี 3 features จึงเทียบ raw log-likelihood ข้ามกันตรง ๆ ไม่ได้',
    evidence: 'model/gold_hmm_v1/metadata.json · dataset/datset a gold price/Dataset A_gold price cleaned.ipynb',
    status: 'measured',
  },
  {
    id: 'corpus',
    number: '05',
    group: 'สายเอกสาร → RAG',
    title: 'Evidence Corpus',
    subtitle: 'ข่าวและรายงานที่อ้างกลับต้นทางได้',
    icon: FileSearch,
    input: 'Thai PBS, Fed press releases, BLS CPI และ Employment Situation; มี source evidence 264 records และ Ground Truth 114 queries',
    process: 'ทำความสะอาด/ตัดซ้ำ, แยกเอกสารและตารางตามโครงสร้าง; สร้างคำถามทดสอบพร้อม evidence IDs และ source spans',
    result: 'Corpus 5,058 documents / 19,784 structure-aware chunks; query split 21 development, 25 validation, 68 test',
    decision: 'เก็บโครงสร้าง section/table และ provenance; Ground Truth ผ่าน source-span check แล้ว แต่ยังรอ human semantic review จึงถือคะแนนเป็น provisional',
    evidence: 'embedding/artifacts/chunking_real/structure_aware/chunking_manifest.json · embedding/embedding/ground_truth_queries_v2.jsonl',
    status: 'caveat',
  },
  {
    id: 'chunking',
    number: '06',
    group: 'สายเอกสาร → RAG',
    title: 'Chunking Evaluation',
    subtitle: 'เปรียบเทียบ 5 วิธีบน query set เดียวกัน',
    icon: FlaskConical,
    input: '5,058 เอกสาร และ 114 queries ที่มี source document/evidence อ้างอิง',
    process: 'เทียบ existing baseline, recursive fixed, structure-aware, semantic และ adaptive; ใช้ BGE-M3 รุ่นเดียวกันและ exact cosine ใน NumPy เพื่อตัดผล ANN ออก',
    result: 'Top-10: adaptive evidence recall 83.3%; structure-aware document hit 92.1% (เสมอ adaptive) และ evidence MRR 0.640 สูงสุด',
    decision: 'เลือก structure-aware เป็น corpus สำหรับ vector store เพราะรักษา section/table, ได้ MRR สูงสุดและ document hit เสมออันดับหนึ่ง; ยอมรับว่า adaptive ยังนำด้าน evidence recall 1.7 จุด',
    evidence: 'embedding/embedding/retrieval_eval_v2/retrieval_metrics_summary.csv · embedding/README.md',
    status: 'caveat',
  },
  {
    id: 'embedding',
    number: '07',
    group: 'สายเอกสาร → RAG',
    title: 'Embedding',
    subtitle: 'BGE-M3 · 1,024 dimensions',
    icon: Sparkles,
    input: 'ข้อความจาก 19,784 chunks แบบ structure-aware พร้อม chunk ID และ metadata',
    process: 'ส่งข้อความเข้า @cf/baai/bge-m3; เก็บเวกเตอร์พร้อม text hash และ chunk ID เพื่อ reuse และ resume งานที่ทำไปแล้ว',
    result: 'สร้าง embedding checkpoint ครบ 19,784 vectors มิติ 1,024 สำหรับ retrieval/index',
    decision: 'คงโมเดลเดียวกันตลอดการเทียบ chunking เพื่อไม่ให้ความต่างของ model ปะปนกับความต่างของ chunker',
    evidence: 'vector_database/embeddings_checkpoint.jsonl · embedding/create_embedding.ipynb',
    status: 'measured',
  },
  {
    id: 'vector-db',
    number: '08',
    group: 'สายเอกสาร → RAG',
    title: 'Vector DB · Qdrant',
    subtitle: 'Cosine search · resumable upsert',
    icon: Database,
    input: 'Structure-aware chunks และ embeddings 1,024 มิติ',
    process: 'ตรวจ SHA-256, ใช้ cache/checkpoint, batch upsert แบบรอผล และเก็บ payload metadata ลง collection gold_news_structure_aware',
    result: 'Notebook บันทึก 19,784 points; workspace checkpoint ปัจจุบันมี 6,080 IDs และ journal 13,640 IDs ซึ่งไม่ตรงกับ snapshot',
    decision: 'เลือก Qdrant สำหรับ vector retrieval ใน runtime; ยังไม่อ้างว่า live collection sync ครบจนกว่าจะตรวจ ID set/count กับ Cloud',
    evidence: 'vector_database/qdrant.ipynb · vector_database/upsert_checkpoint.json · vector_database/upsert_checkpoint.jsonl',
    status: 'caveat',
  },
  {
    id: 'rag',
    number: '09',
    group: 'สายเอกสาร → RAG',
    title: 'RAG & Prompt Selection',
    subtitle: 'Hybrid retrieval → rerank → grounded answer',
    icon: Network,
    input: '114 evidence-grounded questions, corpus/chunks และ index; ประเมิน retrieval กับ prompt แยกชุดทดลอง',
    process: 'เทียบ BM25, dense, hybrid Reciprocal Rank Fusion (k=60), และ hybrid + Jina reranker; ทดสอบ citation prompt A2/A3 แยกบน 114 × 3 รอบ',
    result: 'Hybrid + Jina: evidence recall@10 52.6% เทียบ hybrid RRF 35.5% (+17.1 จุด), document hit 73.7%, retrieval+rerank mean 6.40 s. ใน prompt run เดียวกัน A2 citation 95.9%, structured output 98.2%, mean 14.58 s / P95 32.30 s',
    decision: 'ใช้ hybrid + Jina เมื่อเน้น evidence coverage โดยยอมรับ latency เพิ่ม; เลือก A2 เป็นจุดสมดุลของ citation/latency (A3 structured validity สูงกว่า 99.1% แต่ mean 16.78 s / P95 69.78 s). ผลยัง provisional',
    evidence: 'rag/rag_comparison/rag_comparison_summary.csv · rag/rag_latency_experiments/20261028T070459Z/experiment_summary.csv',
    status: 'caveat',
  },
];

const MARKET_FLOW: FlowNode[] = [
  { id: 'dataset', title: 'GTA · ราคาประกาศ', detail: '24,519 แถว · 2006–2026', kind: 'source' },
  { id: 'eda', title: 'EDA · ตรวจคุณภาพ', detail: 'timestamp ซ้ำ 8 กลุ่ม', kind: 'process' },
  { id: 'features', title: 'Daily Features', detail: '6,261 วัน · null preserved', kind: 'result' },
  { id: 'hmm', title: 'Gaussian HMM', detail: '3 states · test LL -1.8923', kind: 'focal' },
];

const RAG_FLOW: FlowNode[] = [
  { id: 'corpus', title: 'Fed · BLS · PBS', detail: '5,058 เอกสาร · 114 queries', kind: 'source' },
  { id: 'chunking', title: 'Structure-aware', detail: '19,784 chunks · MRR .640', kind: 'focal' },
  { id: 'embedding', title: 'BGE-M3', detail: '1,024D · exact-cosine eval', kind: 'process' },
  { id: 'vector-db', title: 'Qdrant', detail: '19,784 points in notebook', kind: 'result' },
  { id: 'rag', title: 'Hybrid + Jina', detail: 'evidence recall@10 52.6%', kind: 'focal' },
];

function FlowDiagram({
  id,
  title,
  description,
  nodes,
  selected,
  onSelect,
}: {
  id: string;
  title: string;
  description: string;
  nodes: FlowNode[];
  selected: StageId;
  onSelect: (id: StageId) => void;
}) {
  const viewWidth = nodes.length === 4 ? 1180 : 1280;
  const boxWidth = nodes.length === 4 ? 224 : nodes.length === 5 ? 220 : 180;
  const gap = nodes.length === 4 ? 64 : nodes.length === 5 ? 24 : 32;
  const left = nodes.length === 4 ? 46 : 20;
  const boxY = 72;
  const boxHeight = 120;
  const centerY = boxY + boxHeight / 2;
  const viewHeight = 268;
  const marker = `${id}-arrow`;

  return (
    <section className="card-warm overflow-hidden rounded-2xl">
      <div className="border-b border-border px-4 py-3 md:px-5">
        <p className="label-caps">{title}</p>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </div>
      <div className="nice-scroll overflow-x-auto">
        <svg
          className="block h-auto min-w-[1180px] bg-cream"
          style={{ minWidth: `${viewWidth}px` }}
          viewBox={`0 0 ${viewWidth} ${viewHeight}`}
          role="img"
          aria-labelledby={`${id}-title ${id}-desc`}
        >
          <title id={`${id}-title`}>{title}</title>
          <desc id={`${id}-desc`}>{description}</desc>
          <defs>
            <marker id={marker} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0,8 3,0 6" fill="#6e6552" />
            </marker>
            <marker id={`${id}-arrow-accent`} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0,8 3,0 6" fill="#96690c" />
            </marker>
            <marker id={`${id}-arrow-link`} markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
              <polygon points="0 0,8 3,0 6" fill="#1c2942" />
            </marker>
          </defs>
          <rect width={viewWidth} height={viewHeight} fill="#fbf8f1" />
          <text x="32" y="34" fill="#6e6552" fontSize="10" fontFamily="Geist Mono, monospace" letterSpacing="1.2">
            INPUT → PROCESS → MEASURED OUTPUT
          </text>

          {nodes.slice(0, -1).map((node, index) => {
            const x1 = left + index * (boxWidth + gap) + boxWidth;
            const x2 = left + (index + 1) * (boxWidth + gap);
            return (
              <path
                key={`${node.id}-to-${nodes[index + 1].id}`}
                d={`M ${x1} ${centerY} H ${x2}`}
                fill="none"
                stroke="#6e6552"
                strokeWidth="1.5"
                markerEnd={`url(#${marker})`}
              />
            );
          })}

          {nodes.map((node, index) => {
            const x = left + index * (boxWidth + gap);
            const isSelected = selected === node.id;
            const fill =
              node.kind === 'source' ? '#f3ebd7' : node.kind === 'result' ? '#f1f0eb' : node.kind === 'focal' ? '#f7e3b0' : '#ffffff';
            const stroke = isSelected || node.kind === 'focal' ? '#96690c' : node.kind === 'source' ? '#847a65' : '#6e6552';
            return (
              <g
                key={node.id}
                className="journey-flow-node"
                role="button"
                tabIndex={0}
                aria-label={`${node.title}: ${node.detail}`}
                aria-pressed={isSelected}
                onClick={() => onSelect(node.id)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    onSelect(node.id);
                  }
                }}
              >
                <rect
                  x={x}
                  y={boxY}
                  width={boxWidth}
                  height={boxHeight}
                  rx="6"
                  fill={isSelected ? '#fff7df' : fill}
                  stroke={stroke}
                  strokeWidth={isSelected ? '2' : '1'}
                />
                <text x={x + 14} y={boxY + 27} fill="#6e6552" fontSize="9" fontFamily="Geist Mono, monospace" letterSpacing=".4">
                  {String(index + 1).padStart(2, '0')} · {node.kind.toUpperCase()}
                </text>
                <text x={x + 14} y={boxY + 57} fill="#2a251b" fontSize="14" fontWeight="600" fontFamily="Noto Sans Thai, sans-serif">
                  {node.title}
                </text>
                <text x={x + 14} y={boxY + 84} fill="#6e6552" fontSize="10.5" fontFamily="Noto Sans Thai, sans-serif">
                  {node.detail}
                </text>
                <text x={x + 14} y={boxY + 105} fill="#96690c" fontSize="9.5" fontWeight="600" fontFamily="Noto Sans Thai, sans-serif">
                  เลือกเพื่อดูรายละเอียด
                </text>
              </g>
            );
          })}

          <line x1="32" y1="218" x2={viewWidth - 32} y2="218" stroke="#e8e0cc" />
          <circle cx="44" cy="242" r="5" fill="#f3ebd7" stroke="#847a65" />
          <text x="56" y="246" fill="#6e6552" fontSize="10" fontFamily="Noto Sans Thai, sans-serif">แหล่งข้อมูล</text>
          <circle cx="158" cy="242" r="5" fill="#ffffff" stroke="#6e6552" />
          <text x="170" y="246" fill="#6e6552" fontSize="10" fontFamily="Noto Sans Thai, sans-serif">ขั้นประมวลผล</text>
          <circle cx="292" cy="242" r="5" fill="#f1f0eb" stroke="#6e6552" />
          <text x="304" y="246" fill="#6e6552" fontSize="10" fontFamily="Noto Sans Thai, sans-serif">ผลที่วัดได้</text>
          <circle cx="410" cy="242" r="5" fill="#f7e3b0" stroke="#96690c" />
          <text x="422" y="246" fill="#6e6552" fontSize="10" fontFamily="Noto Sans Thai, sans-serif">จุดที่เลือกใช้</text>
        </svg>
      </div>
    </section>
  );
}

function DetailPanel({ stage }: { stage: JourneyStage }) {
  const Icon = stage.icon;
  const sections = [
    { title: 'Input', body: stage.input, icon: ArrowDownRight },
    { title: 'Process', body: stage.process, icon: Waypoints },
    { title: 'Result', body: stage.result, icon: CheckCircle2 },
    { title: 'เลือกวิธีนี้เพราะ', body: stage.decision, icon: ArrowRight },
  ];

  return (
    <section className="card-warm rounded-2xl">
      <div className="flex flex-wrap items-start gap-3 border-b border-border px-4 py-4 md:px-5">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent text-accent-foreground">
          <Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="label-caps">{stage.group} · ขั้นที่ {stage.number}</p>
          <h3 className="mt-1 font-display text-lg font-bold">{stage.title}</h3>
          <p className="text-xs text-muted-foreground">{stage.subtitle}</p>
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ${
            stage.status === 'measured' ? 'bg-gain/10 text-gain' : 'bg-amber-50 text-amber-900'
          }`}
        >
          {stage.status === 'measured' ? <CheckCircle2 className="h-3 w-3" /> : <CircleHelp className="h-3 w-3" />}
          {stage.status === 'measured' ? 'มีผลวัดจาก artifact' : 'มีข้อจำกัด / ยัง provisional'}
        </span>
      </div>

      <div className="grid gap-px bg-border sm:grid-cols-2 xl:grid-cols-4">
        {sections.map(({ title, body, icon: SectionIcon }) => (
          <div key={title} className="bg-white p-4 md:p-4.5">
            <div className="mb-2 flex items-center gap-2 text-xs font-bold text-foreground">
              <SectionIcon className="h-3.5 w-3.5 text-gold-deep" />
              {title}
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">{body}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-start gap-x-2 gap-y-1 px-4 py-3 text-[11px] text-muted-foreground md:px-5">
        <BookOpenText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gold-deep" />
        <span className="font-semibold text-foreground/75">แหล่งตรวจสอบ:</span>
        <code className="min-w-0 break-all font-mono">{stage.evidence}</code>
      </div>
    </section>
  );
}

export function ResearchJourneyView({
  data,
  onOpenAssistant,
  panelId = 'journey-panel',
  labelledBy = 'journey-tab',
  showHeader = true,
}: {
  data: MarketPayload;
  onOpenAssistant: () => void;
  panelId?: string;
  labelledBy?: string;
  showHeader?: boolean;
}) {
  const [selectedId, setSelectedId] = useState<StageId>('eda');
  const selectedStage = STAGES.find((stage) => stage.id === selectedId) ?? STAGES[0];

  return (
    <div id={panelId} className="space-y-5" role="tabpanel" aria-labelledby={labelledBy} tabIndex={0}>
      {showHeader && (
        <ViewHeader
          title="เส้นทางพัฒนา Gold Assistant"
          subtitle="จากข้อมูลต้นทาง → ตรวจคุณภาพ → สร้าง features / HMM → เลือก chunking, vector search และ RAG ด้วยผลทดลองที่วัดได้"
          data={data}
          right={
            <button
              type="button"
              onClick={onOpenAssistant}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-gold/50 bg-white px-3 text-xs font-semibold text-accent-foreground transition-colors hover:bg-accent/50"
            >
              <Sparkles className="h-4 w-4" />
              ถาม Gold Assistant
            </button>
          }
        />
      )}

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <MetricTile label="Raw GTA quotes" value="24,519" note="ราคาแบบประกาศ" />
        <MetricTile label="Daily features" value="6,261" note="ไม่เติมค่า null" />
        <MetricTile label="HMM validation LL" value="-0.8837" note="3 states · 939 วัน" />
        <MetricTile label="Retrieval evidence recall" value="52.6%" note="Hybrid + Jina · Top 10" />
      </div>

      <FlowDiagram
        id="market-flow"
        title="สายวิเคราะห์ข้อมูลตลาด"
        description="ราคาทอง GTA ผ่าน EDA และ feature engineering ก่อนสร้าง regime ด้วย HMM; เลือกโหนดเพื่อดู Input, Process, Result และเหตุผล"
        nodes={MARKET_FLOW}
        selected={selectedId}
        onSelect={setSelectedId}
      />

      <FlowDiagram
        id="rag-flow"
        title="สายเอกสารหลักฐานและ RAG"
        description="ข่าวและรายงานเศรษฐกิจถูกทำเป็น corpus, ประเมิน chunking และ embedding, เก็บใน Qdrant และทดลอง hybrid retrieval กับ prompt"
        nodes={RAG_FLOW}
        selected={selectedId}
        onSelect={setSelectedId}
      />

      <DetailPanel stage={selectedStage} />

      <aside className="flex items-start gap-2.5 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-xs leading-relaxed text-amber-950">
        <CircleHelp className="mt-0.5 h-4 w-4 shrink-0" />
        <p>
          <b>ขอบเขตของแผนภาพ:</b> แสดง Dataset/EDA/Feature Engineering/HMM และ Embedding/Vector DB/RAG เท่านั้น
          ไม่รวม Multi-agent; HMM เป็น latent statistical regime ไม่ใช่คำทำนายวิกฤต และคะแนน Retrieval/RAG ยัง provisional
          เพราะ Ground Truth 114 ข้อยังรอ human semantic review. Qdrant checkpoint ยังต้องตรวจให้ตรงกับ Cloud.
        </p>
      </aside>
    </div>
  );
}

function MetricTile({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="card-warm min-w-0 rounded-xl px-3 py-3 md:px-4">
      <p className="truncate text-[10px] font-semibold text-muted-foreground md:text-[11px]">{label}</p>
      <p className="mt-1 font-display text-xl font-bold tracking-tight text-foreground md:text-2xl">{value}</p>
      <p className="mt-0.5 truncate text-[10px] text-muted-foreground">{note}</p>
    </div>
  );
}
