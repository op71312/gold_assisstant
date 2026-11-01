'use client';

import { useState, type KeyboardEvent, type ReactNode } from 'react';
import {
  ArrowDownRight,
  ArrowRight,
  Bot,
  CheckCircle2,
  CircleHelp,
  FileCheck2,
  FileSearch,
  Gauge,
  GitBranch,
  Layers3,
  Network,
  Search,
  ShieldCheck,
  Sparkles,
  Waypoints,
  type LucideIcon,
} from 'lucide-react';
import evaluation from '../../../../data/gaib1-evaluation.json';
import { ViewHeader } from './shared';
import type { MarketPayload } from '@/lib/gold/payload';

type PanelId = 'agents' | 'retrieval' | 'evaluation' | 'render';
type AgentId = 'news' | 'macro' | 'quant' | 'risk' | 'lead';
type RetrievalId = 'question' | 'dense' | 'bm25' | 'rrf' | 'rerank' | 'context';

interface AgentStage {
  id: AgentId;
  number: string;
  name: string;
  role: string;
  icon: LucideIcon;
  input: string;
  process: string;
  result: string;
  decision: string;
  evidence: string;
}

interface RetrievalStage {
  id: RetrievalId;
  number: string;
  name: string;
  detail: string;
  input: string;
  process: string;
  result: string;
  decision: string;
}

const AGENTS: AgentStage[] = [
  {
    id: 'news',
    number: 'AI 1',
    name: 'News Analyst',
    role: 'ค้นข่าวและสรุปหลักฐาน',
    icon: FileSearch,
    input: 'คำถาม, ชุดข่าวและเอกสารที่ค้นคืน พร้อม source IDs/วันที่',
    process: 'ค้นหลักฐานด้วย hybrid retrieval แล้วสรุปข่าวพร้อมเชื่อมโยงช่วงข้อมูลตลาดตามวัน โดยคงรหัสอ้างอิงต้นทาง',
    result: 'ข้อค้นพบข่าวพร้อม citation IDs เช่น [S#] และข้อจำกัดของการจับคู่ข่าวกับราคา',
    decision: 'แยกการพบข่าวร่วมเวลาออกจากข้ออ้างเชิงเหตุและผล; ข่าวที่สัมพันธ์กันไม่ได้พิสูจน์ว่าเป็นสาเหตุ',
    evidence: 'GAIB-1 pipeline notebook · section 9',
  },
  {
    id: 'macro',
    number: 'AI 2',
    name: 'Macro Analyst',
    role: 'ตีความทองโลก, FX และตัวแปรมหภาค',
    icon: GitBranch,
    input: 'หลักฐานที่ค้นคืนและ daily gold-feature dataset ตาม as-of date',
    process: 'อ่านผลตอบแทนทอง/เงินบาท, volatility และ rolling correlation จากค่าที่คำนวณด้วย Python; ไม่ให้ LLM คำนวณตัวเลข',
    result: 'ข้อค้นพบ macro พร้อม feature evidence IDs เช่น [Q#]',
    decision: 'ใช้ deterministic feature snapshot เพื่อให้ตัวเลขตรวจซ้ำได้ และไม่อ้าง correlation เป็นเหตุเป็นผล',
    evidence: 'GAIB-1 pipeline notebook · sections 5, 9',
  },
  {
    id: 'quant',
    number: 'AI 3',
    name: 'Quant / Regime Analyst',
    role: 'สถิติและ latent market regimes',
    icon: Gauge,
    input: 'Feature dataset, model bundle, scaler และ feature schema',
    process: 'คำนวณสถิติตามวัน as-of และอ่าน GaussianHMM ตาม feature schema; ข้อมูล High–Low ของวันเต็มใช้ได้เฉพาะ retrospective end-of-day',
    result: 'สถิติและ HMM state/posterior พร้อม evidence IDs เช่น [H#]',
    decision: 'อ่าน feature columns จาก model bundle; state เป็น latent regime ไม่ใช่สัญญาณ bullish/bearish หรือค่าที่ปราศจาก look-ahead',
    evidence: 'GAIB-1 pipeline notebook · sections 5, 6, 9',
  },
  {
    id: 'risk',
    number: 'AI 4',
    name: 'Risk & Data Auditor',
    role: 'ตรวจคุณภาพข้อมูลและกระทบยอดพอร์ต',
    icon: ShieldCheck,
    input: 'Features และ simulator ledgers, valuations, attribution กับ market-price tables',
    process: 'ตรวจ data-quality flags, synthetic-data status, duplicate transaction IDs และสมการ P&L attribution',
    result: 'ข้อค้นพบด้านความเสี่ยง/ข้อจำกัด พร้อม audit evidence IDs เช่น [R#]',
    decision: 'รายงาน residual สำหรับกระทบยอดด้วย tolerance 0.01 THB; ข้อมูลพอร์ตทั้งหมดเป็น synthetic ไม่ใช่บัญชีลูกค้า',
    evidence: 'GAIB-1 pipeline notebook · sections 7, 9',
  },
  {
    id: 'lead',
    number: 'AI 5',
    name: 'Lead Researcher',
    role: 'ตรวจทานและสังเคราะห์รายงาน',
    icon: Sparkles,
    input: 'Structured findings จาก AI 1–4 และ evidence manifest',
    process: 'แก้ความขัดแย้ง ตรวจ schema และ citation IDs กับ manifest; กู้ตัวเลขได้เมื่อมี source record รองรับเท่านั้น',
    result: 'รายงานคำตอบที่รวมข้อค้นพบและ citations; evaluation ใช้ blind judge แยกจาก generator',
    decision: 'Lead ไม่ใช่เพียงการนำข้อความมาต่อกัน; citation ID ที่มีอยู่จริงยังต้องผ่าน human review ด้านความหมาย',
    evidence: 'GAIB-1 pipeline notebook · sections 10–12',
  },
];

const RETRIEVAL_STAGES: RetrievalStage[] = [
  {
    id: 'question',
    number: '01 · INPUT',
    name: 'คำถาม + วันอ้างอิง',
    detail: 'Thai gold development query',
    input: 'หนึ่ง query จากชุด development พร้อมวัน as-of/ข้อเท็จจริงที่ต้องค้น',
    process: 'ส่ง query เดียวกันไปยังเส้น dense และ lexical เพื่อรวบรวม candidates จาก corpus ที่กำหนด',
    result: 'query ที่ถูกใช้ร่วมกันในการวัด retrieval; ผลเป็น known-relevant ไม่ใช่ exhaustive corpus relevance',
    decision: 'คงชุดคำถามเดิมระหว่าง retrieval และ agent evaluation เพื่อให้ตรวจเทียบผลซ้ำได้',
  },
  {
    id: 'dense',
    number: '02A · DENSE',
    name: 'Cloudflare + Qdrant',
    detail: 'BGE-M3 · top 40',
    input: 'query text และ structure-aware chunk corpus 19,784 chunks',
    process: 'สร้าง query embedding ด้วย Cloudflare BGE-M3 แล้วค้น dense candidates 40 รายการใน Qdrant collection gold_news_structure_aware',
    result: 'อันดับ dense candidates พร้อม document/chunk provenance',
    decision: 'ใช้ vector search หาเนื้อหาที่ใกล้เชิงความหมาย; Python GAIB-1 runtime บน Render เรียก Qdrant สำหรับขั้นตอนนี้',
  },
  {
    id: 'bm25',
    number: '02B · LEXICAL',
    name: 'Local BM25',
    detail: 'local corpus · top 40',
    input: 'query text และ local JSONL corpus ชุดเดียวกัน',
    process: 'คำนวณ lexical ranking บนเครื่องจาก corpus 19,784 chunks เพื่อหา exact terms และชื่อเฉพาะ',
    result: 'อันดับ lexical candidates 40 รายการ',
    decision: 'เสริม dense retrieval ด้วยคำตรง/เลขเฉพาะ และตรวจให้ corpus identity สอดคล้องกับชุด query',
  },
  {
    id: 'rrf',
    number: '03 · FUSION',
    name: 'RRF · k = 60',
    detail: 'ผสาน dense + BM25',
    input: 'รายการ dense 40 candidates และ BM25 40 candidates',
    process: 'รวม rank lists ด้วย Reciprocal Rank Fusion โดยใช้ k=60',
    result: 'hybrid candidate ranking ก่อน rerank',
    decision: 'ผสานการค้นแบบ semantic และ lexical โดยไม่ต้องเทียบค่าคะแนนดิบจากคนละระบบ',
  },
  {
    id: 'rerank',
    number: '04 · RERANK',
    name: 'Jina reranker',
    detail: 'jina-reranker-v3.5 · top 10',
    input: 'hybrid candidate list และ query เดิม',
    process: 'จัดอันดับ candidate ใหม่ด้วย Jina jina-reranker-v3.5 และตัดเหลือ 10 รายการ',
    result: 'หลักฐานลำดับสุดท้ายสำหรับ context',
    decision: 'A2 strict mode ต้องได้ผลจาก Jina จริง; หากบริการหรือ credentials ใช้ไม่ได้ ให้หยุด ไม่ใช้ rank-order fallback แล้วอ้างว่าเป็น A2',
  },
  {
    id: 'context',
    number: '05 · OUTPUT',
    name: 'Evidence context',
    detail: '[S#] · ≤16k chars',
    input: 'top-10 reranked sources พร้อม document/original/chunk IDs',
    process: 'กรองตามวัน/phase และเตรียม cited context ไม่เกิน 16,000 ตัวอักษรรวม และ 2,500 ตัวอักษรต่อ chunk',
    result: 'evidence manifest พร้อม [S#] สำหรับ specialist agents และ Lead Researcher',
    decision: 'คง provenance และจำกัด context เพื่อให้ทุก claim ย้อนกลับไปตรวจ source ได้; citation presence ไม่เท่ากับ semantic support',
  },
];

const PANELS: { id: PanelId; title: string; icon: LucideIcon }[] = [
  { id: 'agents', title: '5-Agent workflow', icon: Network },
  { id: 'retrieval', title: 'Hybrid RAG', icon: Search },
  { id: 'evaluation', title: 'ผลประเมิน', icon: CheckCircle2 },
  { id: 'render', title: 'Vercel + Render', icon: Layers3 },
];

const percent = (value: number) => `${(value * 100).toFixed(2)}%`;

export function MultiAgentPipelineView({
  data,
  onOpenAssistant,
  panelId = 'pipeline-panel',
  labelledBy = 'pipeline-tab',
  showHeader = true,
}: {
  data: MarketPayload;
  onOpenAssistant: () => void;
  panelId?: string;
  labelledBy?: string;
  showHeader?: boolean;
}) {
  const [panel, setPanel] = useState<PanelId>('agents');
  const [agentId, setAgentId] = useState<AgentId>('news');
  const [retrievalId, setRetrievalId] = useState<RetrievalId>('rrf');

  const selectedAgent = AGENTS.find((agent) => agent.id === agentId) ?? AGENTS[0];
  const selectedRetrieval = RETRIEVAL_STAGES.find((stage) => stage.id === retrievalId) ?? RETRIEVAL_STAGES[3];

  return (
    <div id={panelId} className="space-y-5" role="tabpanel" aria-labelledby={labelledBy} tabIndex={0}>
      {showHeader && (
        <ViewHeader
          title="GAIB-1 · Five-agent pipeline"
          subtitle="อ่าน architecture จาก notebook, เลือก node เพื่อดู Input → Process → Result → เหตุผล และเทียบกับ runtime ที่เว็บใช้จริง"
          data={data}
          right={
            <button
              type="button"
              onClick={onOpenAssistant}
              className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-gold/50 bg-white px-3 text-xs font-semibold text-accent-foreground transition-colors hover:bg-accent/50"
            >
              <Bot className="h-4 w-4" />
              ถาม Gold Assistant
            </button>
          }
        />
      )}

      <section className="rounded-2xl border border-gold/50 bg-white px-4 py-3.5" role="note">
        <p className="text-sm font-bold text-foreground">ขอบเขตที่ต้องแยกให้ชัด</p>
        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
          Gold Assistant บน Vercel ส่งคำถามผ่าน streaming proxy ไปยัง Render Python service ที่รัน pipeline จาก notebook จริง รวม hybrid RAG, HMM/risk evidence และ agent 1–5. Qdrant เป็น vector store ภายนอก; คำถามสดใช้ artifacts ย้อนหลังและไม่ได้วิเคราะห์ portfolio ที่เลือกในหน้าตารางหรือข้อมูลตลาดสด
        </p>
      </section>

      <div className="flex flex-wrap gap-1 border-b border-border" role="tablist" aria-label="แผนภาพ GAIB-1">
        {PANELS.map(({ id, title, icon: Icon }) => (
          <button
            key={id}
            id={`gaib-${id}-tab`}
            type="button"
            role="tab"
            aria-selected={panel === id}
            aria-controls={`gaib-${id}-panel`}
            onClick={() => setPanel(id)}
            className={`inline-flex min-h-10 items-center gap-1.5 border-b-2 px-3 text-xs font-semibold transition-colors ${
              panel === id ? 'border-gold-deep text-accent-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {title}
          </button>
        ))}
      </div>

      {panel === 'agents' && (
        <section id="gaib-agents-panel" role="tabpanel" aria-labelledby="gaib-agents-tab" tabIndex={0} className="space-y-4">
          <SectionHeading
            eyebrow="COLLABORATIVE PIPELINE"
            title="สี่ specialist สร้างหลักฐาน → Lead ตรวจทานก่อนตอบ"
            description="ใน GAIB-1 AI 1–4 วิเคราะห์แยกตามบทบาทและรับ evidence/calculated snapshots; AI 5 รับ findings ทั้งหมดเพื่อสังเคราะห์และตรวจ citation"
          />
          <AgentArchitectureDiagram selected={agentId} onSelect={setAgentId} />
          <StageDetail stage={selectedAgent} group="GAIB-1 · Agent" />
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            เว็บเรียก `GoldAssistantMultiAgent.run()` จาก notebook โดยตรง: AI 1–4 ทำงานขนานกันตามค่ากำหนด แล้วส่งผลให้ AI 5; SSE ใช้รายงานสถานะระหว่างที่ pipeline เดิมทำงาน
          </p>
        </section>
      )}

      {panel === 'retrieval' && (
        <section id="gaib-retrieval-panel" role="tabpanel" aria-labelledby="gaib-retrieval-tab" tabIndex={0} className="space-y-4">
          <SectionHeading
            eyebrow="A2 STRICT HYBRID RETRIEVAL"
            title="Dense + lexical candidates → RRF → Jina top-10"
            description="โหนด Cloudflare/Qdrant และ local BM25 ค้นพร้อมกันก่อนรวมอันดับ; เลือกแต่ละขั้นเพื่อดูข้อมูลเข้าและผลที่ส่งต่อ"
          />
          <RetrievalDiagram selected={retrievalId} onSelect={setRetrievalId} />
          <StageDetail stage={selectedRetrieval} group="GAIB-1 · Evidence retrieval" />
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            ผล Recall เป็น known-relevant recall จาก judgments ที่ไม่ exhaustive; การประเมิน notebook ปิด local-only และ rank-order fallback เพื่อให้ run นี้เป็น A2 จริง
          </p>
        </section>
      )}

      {panel === 'evaluation' && (
        <section id="gaib-evaluation-panel" role="tabpanel" aria-labelledby="gaib-evaluation-tab" tabIndex={0} className="space-y-4">
          <EvaluationSummary />
        </section>
      )}

      {panel === 'render' && (
        <section id="gaib-render-panel" role="tabpanel" aria-labelledby="gaib-render-tab" tabIndex={0} className="space-y-4">
          <SectionHeading
            eyebrow="DEPLOYMENT BOUNDARY"
            title="สิ่งที่ถูก deploy กับสิ่งที่ยังเป็น research"
            description="Vercel ให้บริการ Next.js UI/proxy และ Render รัน Python service จาก GAIB-1 notebook; RAG เชื่อม Qdrant, Cloudflare embeddings และ Jina reranking"
          />
          <RenderArchitectureDiagram />
          <div className="grid gap-3 md:grid-cols-2">
            <RuntimeCard
              title="ขอบเขตบริการ Vercel + Render"
              icon={CheckCircle2}
              items={[
                'Vercel ให้บริการ Next.js UI และ API routes',
                'GET /api/data อ่าน versioned gzip JSON snapshots',
                'POST /api/agents proxy SSE ไปยัง Render Python runtime',
                'Notebook agents 1–5 รัน structured ThaiLLM outputs และ citation audit',
                'RAG ใช้ Cloudflare embeddings + Qdrant hybrid search + Jina reranking',
              ]}
              tone="ready"
            />
            <RuntimeCard
              title="ข้อจำกัดที่ยังคงอยู่"
              icon={CircleHelp}
              items={[
                'ส่ง portfolio ID ที่เลือกในหน้าเว็บเข้า notebook (risk audit ยังเป็นระดับโครงการ)',
                'ราคาตลาดและข่าวสด',
                'release approval หลัง human review',
                'ฐานข้อมูลแอป / Supabase / persistent disk; Qdrant เป็นบริการ vector ภายนอกที่ pipeline ต้องใช้',
              ]}
              tone="pending"
            />
          </div>
          <p className="rounded-xl border border-gold/40 bg-accent/30 px-3.5 py-3 text-xs leading-relaxed text-accent-foreground">
            ThaiLLM, Cloudflare, Qdrant และ Jina secrets อยู่ใน Render; shared service token ตั้งค่าเหมือนกันบน Render และ Vercel. หาก runtime หรือ provider ไม่พร้อม เว็บจะแสดง error และไม่สลับไปใช้คำตอบ fallback
          </p>
        </section>
      )}
    </div>
  );
}

function AgentArchitectureDiagram({
  selected,
  onSelect,
}: {
  selected: AgentId;
  onSelect: (id: AgentId) => void;
}) {
  return (
    <DiagramFrame>
      <svg
        className="block h-auto min-w-[1120px] bg-cream"
        style={{ minWidth: '1520px' }}
        viewBox="0 0 1520 324"
        role="img"
        aria-labelledby="gaib-agent-flow-title gaib-agent-flow-desc"
      >
        <title id="gaib-agent-flow-title">GAIB-1 five-agent research architecture</title>
        <desc id="gaib-agent-flow-desc">Query and datasets feed shared evidence and deterministic calculations, four specialist agents send findings to the Lead Researcher, who produces a checked report.</desc>
        <defs>
          <marker id="gaib-agent-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0,8 3,0 6" fill="#6e6552" />
          </marker>
          <marker id="gaib-agent-arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0,8 3,0 6" fill="#96690c" />
          </marker>
        </defs>
        <rect width="1520" height="324" fill="#fbf8f1" />
        <path d="M 204 158 H 248 M 484 158 H 534 M 954 158 H 1000 M 1180 158 H 1224" fill="none" stroke="#6e6552" strokeWidth="1.6" markerEnd="url(#gaib-agent-arrow)" />
        <DiagramNode x={32} y={116} width={172} height={84} eyebrow="INTAKE" title={['Query +', 'as-of date']} detail={['Thai gold query']} />
        <DiagramNode x={248} y={116} width={236} height={84} eyebrow="SHARED CONTEXT" title={['Evidence +', 'calculated data']} detail={['Corpus · features · HMM · ledger']} />
        <rect x="534" y="40" width="420" height="236" rx="8" fill="#f3ebd7" stroke="#847a65" />
        <text x="556" y="68" fill="#6e6552" fontSize="10" fontFamily="Geist Mono, monospace" letterSpacing="1">SPECIALISTS · AI 1–4</text>
        {AGENTS.slice(0, 4).map((agent, index) => {
          const x = index % 2 === 0 ? 556 : 752;
          const y = index < 2 ? 88 : 176;
          const isSelected = selected === agent.id;
          return (
            <g
              key={agent.id}
              role="button"
              tabIndex={0}
              aria-label={`${agent.number}: ${agent.name}, ${agent.role}`}
              aria-pressed={isSelected}
              className="journey-flow-node"
              onClick={() => onSelect(agent.id)}
              onKeyDown={(event: KeyboardEvent<SVGGElement>) => activateOnKeyboard(event, () => onSelect(agent.id))}
            >
              <rect x={x} y={y} width="178" height="68" rx="6" fill={isSelected ? '#fff7df' : '#ffffff'} stroke={isSelected ? '#96690c' : '#6e6552'} strokeWidth={isSelected ? 2 : 1} />
              <text x={x + 12} y={y + 22} fill="#96690c" fontSize="9" fontFamily="Geist Mono, monospace">{agent.number.toUpperCase()}</text>
              <text x={x + 12} y={y + 43} fill="#2a251b" fontSize="12" fontWeight="600" fontFamily="Noto Sans Thai, sans-serif">{agent.name}</text>
              <text x={x + 12} y={y + 58} fill="#6e6552" fontSize="9" fontFamily="Noto Sans Thai, sans-serif">{agent.role}</text>
            </g>
          );
        })}
        <DiagramNode x={1000} y={116} width={180} height={84} eyebrow="REVIEW" title={['AI 5 · Lead', 'Researcher']} detail={['Findings + evidence']} focal />
        <DiagramNode x={1224} y={116} width={244} height={84} eyebrow="OUTPUT" title={['Cited research', 'report']} detail={['schema + citation audit']} />
        <line x1="32" y1="298" x2="1468" y2="298" stroke="#e8e0cc" />
        <text x="32" y="316" fill="#6e6552" fontSize="10" fontFamily="Noto Sans Thai, sans-serif">AI 1–4 ส่ง structured findings และ evidence ให้ AI 5 ตรวจทานก่อนสังเคราะห์รายงาน</text>
      </svg>
    </DiagramFrame>
  );
}

function RetrievalDiagram({
  selected,
  onSelect,
}: {
  selected: RetrievalId;
  onSelect: (id: RetrievalId) => void;
}) {
  const nodes: { stage: RetrievalStage; x: number; y: number; width: number; height: number }[] = [
    { stage: RETRIEVAL_STAGES[0], x: 32, y: 112, width: 184, height: 80 },
    { stage: RETRIEVAL_STAGES[1], x: 310, y: 54, width: 220, height: 76 },
    { stage: RETRIEVAL_STAGES[2], x: 310, y: 174, width: 220, height: 76 },
    { stage: RETRIEVAL_STAGES[3], x: 650, y: 112, width: 180, height: 80 },
    { stage: RETRIEVAL_STAGES[4], x: 930, y: 112, width: 180, height: 80 },
    { stage: RETRIEVAL_STAGES[5], x: 1190, y: 112, width: 180, height: 80 },
  ];

  return (
    <DiagramFrame>
      <svg
        className="block h-auto min-w-[1120px] bg-cream"
        style={{ minWidth: '1400px' }}
        viewBox="0 0 1400 300"
        role="img"
        aria-labelledby="gaib-retrieval-title gaib-retrieval-desc"
      >
        <title id="gaib-retrieval-title">GAIB-1 A2 hybrid retrieval</title>
        <desc id="gaib-retrieval-desc">The query fans out to Cloudflare and Qdrant dense search plus local BM25, merges rankings with RRF, reranks with Jina and produces a cited evidence context.</desc>
        <defs>
          <marker id="gaib-retrieval-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0,8 3,0 6" fill="#6e6552" />
          </marker>
          <marker id="gaib-retrieval-arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0,8 3,0 6" fill="#96690c" />
          </marker>
        </defs>
        <rect width="1400" height="300" fill="#fbf8f1" />
        <path
          d="M 216 152 H 260 V 92 H 310 M 216 152 H 276 V 212 H 310 M 530 92 H 584 V 138 H 650 M 530 212 H 602 V 166 H 650 M 830 152 H 930 M 1110 152 H 1190"
          fill="none"
          stroke="#6e6552"
          strokeWidth="1.5"
          markerEnd="url(#gaib-retrieval-arrow)"
        />
        {nodes.map(({ stage, x, y, width, height }) => (
          <DiagramNode
            key={stage.id}
            x={x}
            y={y}
            width={width}
            height={height}
            eyebrow={stage.number}
            title={[stage.name]}
            detail={[stage.detail]}
            focal={stage.id === 'context'}
            selected={selected === stage.id}
            role="button"
            ariaLabel={`${stage.number}: ${stage.name}, ${stage.detail}`}
            onClick={() => onSelect(stage.id)}
          />
        ))}
        <line x1="32" y1="276" x2="1368" y2="276" stroke="#e8e0cc" />
        <text x="32" y="292" fill="#6e6552" fontSize="10" fontFamily="Noto Sans Thai, sans-serif">Dense และ lexical ทำงานขนาน; A2 strict mode ต้องใช้ remote retrieval และ Jina สำเร็จ</text>
      </svg>
    </DiagramFrame>
  );
}

function DiagramNode({
  x,
  y,
  width,
  height,
  eyebrow,
  title,
  detail,
  focal = false,
  selected = false,
  role,
  ariaLabel,
  onClick,
}: {
  x: number;
  y: number;
  width: number;
  height: number;
  eyebrow: string;
  title: string[];
  detail: string[];
  focal?: boolean;
  selected?: boolean;
  role?: 'button';
  ariaLabel?: string;
  onClick?: () => void;
}) {
  const titleY = y + (title.length > 1 ? 46 : 48);
  return (
    <g
      role={role}
      tabIndex={role ? 0 : undefined}
      aria-label={ariaLabel}
      aria-pressed={role ? selected : undefined}
      className={role ? 'journey-flow-node' : undefined}
      onClick={onClick}
      onKeyDown={role ? (event: KeyboardEvent<SVGGElement>) => activateOnKeyboard(event, onClick) : undefined}
    >
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        rx="6"
        fill={selected ? '#fff7df' : focal ? '#f7e3b0' : '#ffffff'}
        stroke={selected || focal ? '#96690c' : '#6e6552'}
        strokeWidth={selected ? 2 : 1}
      />
      <text x={x + 12} y={y + 20} fill="#6e6552" fontSize="8.5" fontFamily="Geist Mono, monospace" letterSpacing=".35">{eyebrow}</text>
      <text x={x + 12} y={titleY} fill="#2a251b" fontSize="12" fontWeight="600" fontFamily="Noto Sans Thai, sans-serif">
        {title.map((line, index) => <tspan key={`${line}-${index}`} x={x + 12} dy={index === 0 ? 0 : 16}>{line}</tspan>)}
      </text>
      <text x={x + 12} y={y + height - 12} fill="#6e6552" fontSize="9" fontFamily="Noto Sans Thai, sans-serif">
        {detail.map((line, index) => <tspan key={`${line}-${index}`} x={x + 12} dy={index === 0 ? 0 : 12}>{line}</tspan>)}
      </text>
    </g>
  );
}

function StageDetail({
  stage,
  group,
}: {
  stage: AgentStage | RetrievalStage;
  group: string;
}) {
  const isAgent = 'number' in stage && 'role' in stage;
  const Icon = isAgent ? stage.icon : Network;
  const number = stage.number;
  const title = stage.name;
  const subtitle = isAgent ? stage.role : stage.detail;
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
          <p className="label-caps">{group} · {number}</p>
          <h3 className="mt-1 font-display text-lg font-bold">{title}</h3>
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-gain/10 px-2.5 py-1 text-[11px] font-semibold text-gain">
          <CheckCircle2 className="h-3 w-3" /> มีหลักฐานใน notebook
        </span>
      </div>
      <div className="grid gap-3 p-4 md:grid-cols-2 md:p-5">
        {sections.map(({ title: sectionTitle, body, icon: SectionIcon }) => (
          <div key={sectionTitle} className="rounded-xl border border-border/70 bg-white/80 p-3.5">
            <div className="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-foreground/80">
              <SectionIcon className="h-3.5 w-3.5 text-gold-deep" />
              {sectionTitle}
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">{body}</p>
          </div>
        ))}
      </div>
      {isAgent && (
        <p className="border-t border-border px-4 py-3 text-[11px] text-muted-foreground md:px-5">
          แหล่งอ้างอิง: <code className="break-all font-mono">{stage.evidence}</code>
        </p>
      )}
    </section>
  );
}

function EvaluationSummary() {
  const metrics = [
    {
      label: 'Known-relevant Recall@10',
      value: percent(evaluation.metrics.rerankedKnownRelevantRecallAt10),
      target: `เป้าหมาย ≥ ${percent(evaluation.thresholds.rerankedKnownRelevantRecallAt10)}`,
      detail: 'Qdrant + Jina reranked',
    },
    {
      label: 'MRR@10',
      value: evaluation.metrics.rerankedMrrAt10.toFixed(3),
      target: `เป้าหมาย ≥ ${evaluation.thresholds.rerankedMrrAt10.toFixed(2)}`,
      detail: 'ตำแหน่งหลักฐานที่เกี่ยวข้อง',
    },
    {
      label: 'Agent JSON parse',
      value: percent(evaluation.metrics.agentJsonParseRate),
      target: `เป้าหมาย ≥ ${percent(evaluation.thresholds.agentJsonParseRate)}`,
      detail: '105 agent records',
    },
    {
      label: 'Blind AI-judge correctness',
      value: percent(evaluation.metrics.aiJudgeCorrectnessRate),
      target: `เป้าหมาย ≥ ${percent(evaluation.thresholds.aiJudgeCorrectnessRate)}`,
      detail: 'judge model แยกจาก generator',
    },
    {
      label: 'Citation entailment',
      value: percent(evaluation.metrics.citationEntailmentRate),
      target: `เป้าหมาย ≥ ${percent(evaluation.thresholds.citationEntailmentRate)}`,
      detail: 'AI judge ตรวจ claim กับ evidence',
    },
    {
      label: 'Unsupported critical numeric claims',
      value: String(evaluation.metrics.unsupportedCriticalNumericClaims),
      target: 'เป้าหมาย = 0',
      detail: 'ตัวเลขวิกฤตที่ไม่มีหลักฐานรองรับ',
    },
  ];

  return (
    <div className="space-y-4">
      <SectionHeading
        eyebrow="RECORDED DEVELOPMENT RUN"
        title="ผล 21 development queries · 31 ต.ค. 2026"
        description={`Run ${evaluation.runId} · ${evaluation.retrievalResults}/${evaluation.expectedQueries} retrieval · ${evaluation.agentResults}/${evaluation.expectedQueries} agent runs · ${evaluation.perAgentRecords} agent records · ${evaluation.retrievalErrors + evaluation.agentErrors} errors`}
      />
      <section className="rounded-2xl border-2 border-gain/35 bg-white p-4 md:p-5">
        <div className="flex flex-wrap items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-gain" />
          <h3 className="text-sm font-bold">Notebook decision: {evaluation.decision}</h3>
          <span className="ml-auto rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-bold text-amber-900">Development only · not release approval</span>
        </div>
        <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
          สรุปผลมี failed gates 0 รายการ แต่ยกเว้น human spot check 10–20 claims และ human review ของ Ground Truth ไว้; จึงยังห้ามตีความว่าเป็นการอนุมัติ release หรือเป็นคะแนนของคำตอบจากเว็บ
        </p>
      </section>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {metrics.map((metric, index) => (
          <MetricCard key={metric.label} {...metric} focal={index === 0} />
        ))}
      </div>
      <section className="card-warm rounded-2xl p-4 md:p-5">
        <div className="flex items-center gap-2">
          <FileCheck2 className="h-4 w-4 text-gold-deep" />
          <h3 className="text-sm font-bold">ตัวแปร run ที่สำคัญ</h3>
        </div>
        <dl className="mt-3 grid gap-x-6 gap-y-2 text-xs sm:grid-cols-2">
          <Definition label="Retrieval backend" value="Qdrant + Cloudflare hybrid; local BM25 corpus" />
          <Definition label="Generator" value={evaluation.generatorModel} />
          <Definition label="Blind judge" value={evaluation.judgeModel} />
          <Definition label="Elapsed / throughput" value={`${(evaluation.wallSeconds / 60).toFixed(1)} นาที · ${evaluation.queriesPerSecond} query/s`} />
          <Definition label="Split / readiness" value={`${evaluation.split} · ${evaluation.datasetReadiness}`} />
          <Definition label="Raw citation-ID rate" value="Not included in summary JSON; policy threshold is 100%" />
        </dl>
      </section>
      <p className="rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-3 text-xs leading-relaxed text-amber-950">
        Known-relevant judgments ไม่ exhaustive; source-span check ไม่แทน semantic review. Run นี้เป็นผล batch notebook ไม่ใช่ latency, correctness หรือ uptime ของบริการ Render.
      </p>
      <p className="text-[11px] text-muted-foreground">
        แหล่งข้อมูล: <code className="break-all font-mono">{evaluation.source}</code>
      </p>
    </div>
  );
}

function RenderArchitectureDiagram() {
  return (
    <DiagramFrame>
      <svg
        className="block h-auto min-w-[1120px] bg-cream"
        style={{ minWidth: '1240px' }}
        viewBox="0 0 1240 332"
        role="img"
        aria-labelledby="gaib-render-title gaib-render-desc"
      >
        <title id="gaib-render-title">Gold Assistant Vercel and Render production boundary</title>
        <desc id="gaib-render-desc">The browser streams questions to a Next.js proxy on Vercel, which forwards them to a Python service on Render running the GAIB-1 notebook. The Python service reads repository artifacts and calls Qdrant, Cloudflare embeddings, Jina, and ThaiLLM.</desc>
        <defs>
          <marker id="gaib-render-arrow" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0,8 3,0 6" fill="#6e6552" />
          </marker>
          <marker id="gaib-render-arrow-accent" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
            <polygon points="0 0,8 3,0 6" fill="#96690c" />
          </marker>
        </defs>
        <rect width="1240" height="332" fill="#fbf8f1" />
        <path d="M 210 166 H 285 M 525 154 H 600 M 600 184 H 525 M 870 144 H 905 V 84 H 940 M 870 190 H 905 V 250 H 940 M 525 210 V 250 H 940" fill="none" stroke="#6e6552" strokeWidth="1.5" markerEnd="url(#gaib-render-arrow)" />
        <DiagramNode x={30} y={124} width={180} height={84} eyebrow="PUBLIC UI" title={['Browser']} detail={['HTTPS · streamed SSE']} />
        <DiagramNode x={285} y={112} width={240} height={108} eyebrow="VERCEL · NEXT.JS" title={['Frontend + API proxy']} detail={['/api/agents · /api/data']} focal />
        <DiagramNode x={600} y={112} width={270} height={108} eyebrow="RENDER · PYTHON" title={['GAIB-1 notebook']} detail={['RAG → HMM → agents 1–5 → audit']} />
        <DiagramNode x={940} y={38} width={280} height={92} eyebrow="REPOSITORY ARTIFACTS" title={['Features · HMM · corpus']} detail={['Versioned JSON · simulator tables']} />
        <DiagramNode x={940} y={204} width={280} height={92} eyebrow="REMOTE SERVICES" title={['Qdrant · Cloudflare · Jina']} detail={['ThaiLLM · secrets server-side']} />
        <line x1="30" y1="314" x2="1220" y2="314" stroke="#e8e0cc" />
        <text x="30" y="329" fill="#6e6552" fontSize="10" fontFamily="Noto Sans Thai, sans-serif">ไม่มีฐานข้อมูลแอป / Supabase / persistent disk; Qdrant เป็น vector database ภายนอกที่ GAIB-1 ต้องใช้</text>
      </svg>
    </DiagramFrame>
  );
}

function RuntimeCard({
  title,
  icon: Icon,
  items,
  tone,
}: {
  title: string;
  icon: LucideIcon;
  items: string[];
  tone: 'ready' | 'pending';
}) {
  return (
    <section className={`rounded-2xl border bg-white p-4 ${tone === 'ready' ? 'border-gain/25' : 'border-amber-300'}`}>
      <h3 className="flex items-center gap-2 text-sm font-bold">
        <Icon className={`h-4 w-4 ${tone === 'ready' ? 'text-gain' : 'text-amber-800'}`} />
        {title}
      </h3>
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-xs leading-relaxed text-muted-foreground">
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${tone === 'ready' ? 'bg-gain' : 'bg-amber-700'}`} />
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <header>
      <p className="label-caps">{eyebrow}</p>
      <h2 className="mt-1 font-display text-lg font-bold">{title}</h2>
      <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{description}</p>
    </header>
  );
}

function MetricCard({
  label,
  value,
  target,
  detail,
  focal,
}: {
  label: string;
  value: string;
  target: string;
  detail: string;
  focal?: boolean;
}) {
  return (
    <article className={`min-w-0 rounded-xl border bg-white p-3 ${focal ? 'border-gold-deep/50' : 'border-border'}`}>
      <p className="text-[11px] font-semibold leading-snug text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-bold tabular-nums text-foreground">{value}</p>
      <p className="mt-1 text-[10px] font-semibold text-gain">{target}</p>
      <p className="mt-1 text-[10px] leading-snug text-muted-foreground">{detail}</p>
    </article>
  );
}

function Definition({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="font-semibold text-foreground/75">{label}</dt>
      <dd className="break-words text-muted-foreground">{value}</dd>
    </div>
  );
}

function DiagramFrame({ children }: { children: ReactNode }) {
  return <div className="card-warm overflow-hidden rounded-2xl"><div className="nice-scroll overflow-x-auto">{children}</div></div>;
}

function activateOnKeyboard(event: KeyboardEvent<SVGGElement>, action?: () => void) {
  if ((event.key === 'Enter' || event.key === ' ') && action) {
    event.preventDefault();
    action();
  }
}
