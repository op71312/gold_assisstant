'use client';

import { useState } from 'react';
import {
  ArrowRight,
  BookOpenText,
  ChartNoAxesCombined,
  Database,
  FlaskConical,
  Layers3,
  Search,
  ShieldAlert,
  type LucideIcon,
} from 'lucide-react';
import { ProjectDataView } from './ProjectDataView';
import { MultiAgentPipelineView } from './MultiAgentPipelineView';
import { ResearchJourneyView } from './ResearchJourneyView';
import { ViewHeader } from './shared';
import { formatThaiDate } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

type ProjectSection = 'overview' | 'eda' | 'retrieval' | 'tables' | 'journey' | 'agents';

const SECTIONS: { id: ProjectSection; label: string; icon: LucideIcon }[] = [
  { id: 'overview', label: 'ภาพรวมและชุดข้อมูล', icon: Database },
  { id: 'eda', label: 'ผลทดลอง · EDA / HMM', icon: ChartNoAxesCombined },
  { id: 'retrieval', label: 'ผลทดลอง · Embedding / RAG', icon: Search },
  { id: 'tables', label: 'ตารางข้อมูล', icon: BookOpenText },
  { id: 'journey', label: 'Pipeline ทั้งโครงการ', icon: Layers3 },
  { id: 'agents', label: 'GAIB-1 · 5 AI agents', icon: FlaskConical },
];

const DATASETS = [
  {
    name: 'ราคาทองคำไทย · GTA',
    acquisition: 'บันทึก historical HTML จากสมาคมค้าทองคำ แล้ว parse, clean และสร้าง daily features',
    size: '24,519 ประกาศ → 6,261 วัน · 2006-05-01–2026-10-13',
    use: 'ราคาสังเกตจริงสำหรับ EDA, HMM และ simulator; ไม่ใช่ธุรกรรมผู้ลงทุน',
  },
  {
    name: 'Thai PBS',
    acquisition: 'ดึงรายการข่าวผ่าน Thai PBS API และจัดประเภท/ตรวจ audit ความเกี่ยวข้อง',
    size: '7,874 records · audit v2 จำนวน 885 · direct 9 เรื่อง',
    use: 'ข่าวภาษาไทยใน evidence corpus; ความเกี่ยวข้องไม่ได้พิสูจน์เหตุและผล',
  },
  {
    name: 'Federal Reserve',
    acquisition: 'เก็บ press releases จาก archive แล้วแก้ encoding, clean, deduplicate และจัดประเภท',
    size: '4,553 เอกสาร · 2006-01-03–2026-10-16',
    use: 'นโยบายและหลักฐานเศรษฐกิจมหภาค พร้อม source provenance',
  },
  {
    name: 'BLS · CPI และ Employment Situation',
    acquisition: 'เก็บรายงาน CPI/NFP จาก archive; ตัด header/footer และแยกตามหัวข้อ/ตาราง',
    size: 'CPI 248 รายงาน · NFP 248 รายงาน',
    use: 'หลักฐานเงินเฟ้อและแรงงาน; เก็บตารางสำคัญให้ตรวจตัวเลขย้อนกลับได้',
  },
  {
    name: 'พอร์ตและธุรกรรม simulator',
    acquisition: 'Seeded event-driven replay/Monte Carlo บนราคาตลาด GTA ตามพฤติกรรมที่กำหนดเป็นสมมติฐาน',
    size: 'R_FEATURE_V1 · 1,050 พอร์ต · 40,466 transaction events',
    use: 'ข้อมูลจำลองทั้งหมด ไม่ใช่บัญชีลูกค้าและไม่ใช่พฤติกรรมจริงของนักลงทุน',
  },
  {
    name: 'Retrieval corpus และ Ground Truth',
    acquisition: 'คัดเอกสาร B1–B4, structure-aware chunking และเชื่อม evidence IDs/source spans กับคำถาม',
    size: '5,058 documents · 19,784 chunks · 264 evidence records · 114 queries',
    use: 'ชุดประเมิน retrieval/RAG; semantic quality ยังต้อง human review',
  },
];

const RETURNS = [
  { label: 'ทองคำไทย · thai_gold_return', n: '6,260', mean: '0.000281', sd: '0.008270', min: '-0.119844', max: '0.074901' },
  { label: 'Gold Spot · global_gold_return', n: '5,189', mean: '0.000216', sd: '0.011028', min: '-0.115849', max: '0.105241' },
  { label: 'USD/THB · usd_thb_return', n: '4,936', mean: '-0.000005', sd: '0.003820', min: '-0.029687', max: '0.030629' },
];

const CORRELATIONS = [
  { pair: 'ทองไทย – Gold Spot', n: '5,189', pearson: '0.9249', spearman: '0.8948' },
  { pair: 'ทองไทย – USD/THB', n: '4,936', pearson: '-0.1582', spearman: '-0.1791' },
  { pair: 'Gold Spot – USD/THB', n: '4,935', pearson: '-0.4519', spearman: '-0.5121' },
];

const HMM_STATES = [
  { name: 'low-range', logReturn: '0.000464', range: '0.000%', mass: '41.1%' },
  { name: 'mid-range', logReturn: '0.000372', range: '0.330%', mass: '45.6%' },
  { name: 'high-range', logReturn: '-0.001180', range: '0.883%', mass: '13.3%' },
];

const CHUNKING_RESULTS = [
  { method: 'Existing baseline', count: '750', hit: '88.6%', recall: '80.7%', mrr: '0.627' },
  { method: 'Recursive fixed', count: '1,205', hit: '90.4%', recall: '80.3%', mrr: '0.580' },
  { method: 'Structure-aware', count: '671', hit: '92.1%', recall: '81.6%', mrr: '0.640' },
  { method: 'Semantic', count: '1,332', hit: '87.7%', recall: '76.8%', mrr: '0.568' },
  { method: 'Adaptive', count: '1,481', hit: '92.1%', recall: '83.3%', mrr: '0.554' },
];

const RETRIEVAL_RESULTS = [
  { method: 'BM25', hit: '43.0%', recall: '27.6%', quote: '28.5%', mrr: '0.131', latency: '0.27 s' },
  { method: 'Dense', hit: '48.2%', recall: '34.2%', quote: '36.0%', mrr: '0.276', latency: '1.63 s' },
  { method: 'Hybrid RRF', hit: '58.8%', recall: '35.5%', quote: '37.3%', mrr: '0.280', latency: '1.90 s' },
  { method: 'Hybrid RRF + Jina', hit: '73.7%', recall: '52.6%', quote: '55.3%', mrr: '0.469', latency: '6.40 s' },
];

export function ProjectDetailsView({
  data,
  onOpenAssistant,
}: {
  data: MarketPayload;
  onOpenAssistant: () => void;
}) {
  const [section, setSection] = useState<ProjectSection>('overview');
  const facts = data.facts;

  return (
    <div className="space-y-5">
      <ViewHeader
        title="รายละเอียดโปรเจกต์"
        subtitle="ที่มาของข้อมูล ผล EDA/Feature Engineering/HMM และสถาปัตยกรรม pipeline อ้างอิง README และเอกสารวิจัย"
        data={data}
        right={
          <button
            type="button"
            onClick={onOpenAssistant}
            className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-gold/50 bg-white px-3 text-xs font-semibold text-accent-foreground transition-colors hover:bg-accent/50"
          >
            ถาม Gold Assistant <ArrowRight className="h-4 w-4" />
          </button>
        }
      />

      <div className="nice-scroll flex gap-1 overflow-x-auto border-b border-border" role="tablist" aria-label="ข้อมูลโครงการ Gold Assistant">
        {SECTIONS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            id={`project-${id}-tab`}
            type="button"
            role="tab"
            aria-selected={section === id}
            aria-controls={`project-${id}-panel`}
            onClick={() => setSection(id)}
            className={`inline-flex min-h-11 items-center gap-2 border-b-2 px-3 text-[13px] font-semibold transition-colors ${
              section === id ? 'border-gold-deep text-accent-foreground' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </button>
        ))}
      </div>

      {section === 'overview' && (
        <section id="project-overview-panel" role="tabpanel" aria-labelledby="project-overview-tab" tabIndex={0} className="space-y-5">
          <section className="card-warm rounded-2xl p-4 md:p-5">
            <div className="mb-2 flex items-center gap-2">
              <BookOpenText className="h-4 w-4 text-gold-deep" />
              <h2 className="font-display text-sm font-bold">Gold Assistant คืออะไร</h2>
            </div>
            <p className="text-[13px] leading-relaxed text-foreground/90">
              โปรเจกต์ทดลองวิเคราะห์ราคาทองคำไทยจากข้อมูลตลาดที่สังเกตได้ ข่าว/เอกสารเศรษฐกิจ การค้นคืนหลักฐาน และการจำลองพอร์ต โดยแยกผลจริงออกจากผลจำลองและแสดงข้อจำกัด ไม่ใช่ฟีดราคาสดหรือระบบบัญชีลูกค้า
            </p>
            <dl className="mt-4 grid gap-2 sm:grid-cols-3">
              <Fact label="Market snapshot ถึง" value={formatThaiDate(facts.lastDate)} />
              <Fact label="จำนวน daily rows" value={data.coverage.dailyObservations.toLocaleString('th-TH')} />
              <Fact label="หน่วยราคาทองไทย" value="ทองคำแท่ง 96.5% · 15.244 กรัม" />
            </dl>
          </section>

          <section className="space-y-3">
            <div>
              <p className="label-caps">DATASETS · SOURCE → PROCESS → USE</p>
              <h2 className="mt-1 font-display text-base font-bold">ข้อมูลทั้งหมดและวิธีได้มา</h2>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {DATASETS.map((dataset) => (
                <article key={dataset.name} className="card-warm min-w-0 rounded-2xl p-4">
                  <h3 className="text-sm font-bold">{dataset.name}</h3>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground"><b className="text-foreground/80">ที่มา/วิธีเก็บ:</b> {dataset.acquisition}</p>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground"><b className="text-foreground/80">ปริมาณ:</b> {dataset.size}</p>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground"><b className="text-foreground/80">การใช้งาน:</b> {dataset.use}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="card-warm rounded-2xl p-4 md:p-5">
            <h2 className="font-display text-sm font-bold">จากต้นทางสู่เว็บ Render</h2>
            <ol className="mt-3 grid gap-3 md:grid-cols-5">
              {[
                ['เก็บต้นทาง', 'GTA HTML · Thai PBS API · Fed/BLS archives'],
                ['เตรียมข้อมูล', 'clean · audit · features · preserve provenance'],
                ['ทดลองโมเดล/RAG', 'HMM · chunking · embeddings · Qdrant'],
                ['export เว็บ', 'versioned gzip JSON + manifest/checksum'],
                ['ใช้งานเว็บ', 'Next.js snapshot API + Python GAIB-1 runtime · Qdrant ภายนอก'],
              ].map(([title, detail], index) => (
                <li key={title} className="rounded-xl border border-border/70 bg-white/80 p-3">
                  <span className="text-[10px] font-bold text-gold-deep">0{index + 1}</span>
                  <h3 className="mt-1 text-xs font-bold">{title}</h3>
                  <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{detail}</p>
                </li>
              ))}
            </ol>
          </section>

          <p className="rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-3 text-xs leading-relaxed text-amber-950">
            ตารางตลาดและ GAIB-1 ใช้ feature snapshot เดียวกัน 6,261 แถว ถึง 2026-10-13; runtime ยังใช้ historical RAG corpus และบริการ Qdrant/Cloudflare/Jina ภายนอก. พอร์ต/ธุรกรรมเป็น synthetic; ไม่มีราคาหรือข่าวสด, application database, Supabase หรือ persistent disk
          </p>
        </section>
      )}

      {section === 'eda' && (
        <section id="project-eda-panel" role="tabpanel" aria-labelledby="project-eda-tab" tabIndex={0} className="space-y-5">
          <SectionHeading
            eyebrow="EDA · FEATURE ENGINEERING · HMM"
            title="จากประกาศราคา 24,519 รายการ สู่ daily model 6,260 observations"
            description={`ช่วงข้อมูล ${formatThaiDate(data.coverage.startDate)}–${formatThaiDate(facts.lastDate)} · สรุปจาก md/eda.md และ notebook snapshot ไม่ใช่การคำนวณสด`}
          />

          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Metric label="ประกาศ GTA ดิบ" value="24,519" note="timestamp ซ้ำ 8 กลุ่ม" />
            <Metric label="วันใน feature set" value="6,261" note="31 columns · วันไม่มี quote ไม่เติมแถว" />
            <Metric label="Spot / FX missing" value="540 / 691" note="เก็บ null ไม่ forward-fill" />
            <Metric label="HMM observations" value="6,260" note="วันแรกไม่มี log return" />
          </div>

          <section className="card-warm overflow-hidden rounded-2xl">
            <SectionTitle title="ผลตอบแทนรายวัน · log return" note="ค่าด้านล่างเป็นสัดส่วน ไม่ใช่เปอร์เซ็นต์ (0.01 ≈ 1%)" />
            <div className="nice-scroll overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground"><tr>{['Series', 'ใช้ได้', 'ค่าเฉลี่ย', 'ส่วนเบี่ยงเบนฯ', 'ต่ำสุด', 'สูงสุด'].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr></thead>
                <tbody className="divide-y divide-border/60">{RETURNS.map((row) => <tr key={row.label}><th className="px-3 py-2 font-semibold">{row.label}</th><td className="px-3 py-2 tabular-nums">{row.n}</td><td className="px-3 py-2 tabular-nums">{row.mean}</td><td className="px-3 py-2 tabular-nums">{row.sd}</td><td className="px-3 py-2 tabular-nums">{row.min}</td><td className="px-3 py-2 tabular-nums">{row.max}</td></tr>)}</tbody>
              </table>
            </div>
          </section>

          <section className="card-warm overflow-hidden rounded-2xl">
            <SectionTitle title="ความสัมพันธ์ระหว่างผลตอบแทน" note="Pairwise observations; descriptive correlation ไม่ใช่หลักฐานเหตุและผล" />
            <CorrelationPlot />
            <div className="nice-scroll overflow-x-auto">
              <table className="w-full min-w-[540px] text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground"><tr>{['คู่ตัวแปร', 'จำนวนคู่', 'Pearson r', 'Spearman ρ'].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr></thead>
                <tbody className="divide-y divide-border/60">{CORRELATIONS.map((row) => <tr key={row.pair}><th className="px-3 py-2 font-semibold">{row.pair}</th><td className="px-3 py-2 tabular-nums">{row.n}</td><td className="px-3 py-2 tabular-nums">{row.pearson}</td><td className="px-3 py-2 tabular-nums">{row.spearman}</td></tr>)}</tbody>
              </table>
            </div>
            <p className="border-t border-border/60 px-3 py-3 text-xs text-muted-foreground">
              Rolling median Pearson (60 observations; อย่างน้อย 30 คู่): ไทย–Spot 0.9388 · ไทย–FX -0.1707 · Spot–FX -0.5163
            </p>
          </section>

          <div className="grid gap-3 lg:grid-cols-2">
            <section className="card-warm rounded-2xl p-4">
              <SectionTitle title="ปัญหาที่พบและการจัดการ" />
              <ul className="mt-3 space-y-2 text-xs leading-relaxed text-muted-foreground">
                <li><b className="text-foreground/80">timestamp ซ้ำ:</b> พบ 8 กลุ่มในประกาศดิบ; เรียงตาม timestamp/session แล้วรวม daily ด้วย first/last/high/low ไม่ทิ้งราคาในวันนั้น</li>
                <li><b className="text-foreground/80">ไม่มีประกาศบางวัน:</b> 6,261 วันมี quote จากปฏิทิน 7,471 วัน; ไม่เติมวันหยุดเป็นราคาสังเคราะห์</li>
                <li><b className="text-foreground/80">Spot/FX missing:</b> เก็บ null; residual หาย 1,326 จุด และ rolling volatility 60 วันของ FX/residual หาย 3,974 จุดจาก source gaps และหน้าต่างที่ต้องครบ</li>
                <li><b className="text-foreground/80">ราคาเป็น level:</b> ราคาทองแท่งรับซื้อใน snapshot อยู่ 10,050–81,400 บาท จึงสร้าง log return เพื่อเทียบการเปลี่ยนแปลงระหว่างช่วงราคาได้เหมาะกว่า</li>
              </ul>
            </section>
            <section className="card-warm rounded-2xl p-4">
              <SectionTitle title="Feature engineering" note="แถวเรียงตามวัน; ไม่มีการ impute" />
              <ul className="mt-3 space-y-2 text-xs leading-relaxed text-muted-foreground">
                <li><b className="text-foreground/80">Returns:</b> log return ของ bar buy, Gold Spot และ USD/THB; แยก global + FX, Thai − global และ FX-adjusted residual</li>
                <li><b className="text-foreground/80">Volatility:</b> sample standard deviation (`ddof=1`) ของไทย/Spot/FX/residual ด้วยหน้าต่าง 20 และ 60 observations; ต้องมีข้อมูลครบหน้าต่าง</li>
                <li><b className="text-foreground/80">Correlation:</b> rolling Pearson 60 observations, ขั้นต่ำ 30 คู่; รวม robust residual z-score ด้วย rolling median/MAD</li>
                <li><b className="text-foreground/80">ข้อจำกัด:</b> decomposition ยังไม่ calibrate premium, spread, ภาษีหรือหน่วยสัญญา; residual ไม่ใช่ mispricing หรือกำไรที่ทำได้จริง</li>
              </ul>
            </section>
          </div>

          <section className="card-warm overflow-hidden rounded-2xl">
            <SectionTitle title="Gaussian HMM · เลือก 3 latent states" note="validation predictive log-likelihood ต่อแถว; ไม่ใช่ accuracy" />
            <div className="nice-scroll overflow-x-auto">
              <table className="w-full min-w-[620px] text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground"><tr>{['K', 'seed ที่เลือก', 'validation LL/row', 'ผล'].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr></thead>
                <tbody className="divide-y divide-border/60">
                  <tr><td className="px-3 py-2">2</td><td className="px-3 py-2">11</td><td className="px-3 py-2 tabular-nums">-1.710718</td><td className="px-3 py-2">ไม่เลือก</td></tr>
                  <tr className="bg-accent/25"><td className="px-3 py-2 font-bold">3</td><td className="px-3 py-2">42</td><td className="px-3 py-2 font-bold tabular-nums">-0.883659</td><td className="px-3 py-2 font-bold text-gain">เลือก</td></tr>
                  <tr><td className="px-3 py-2">4</td><td className="px-3 py-2">21</td><td className="px-3 py-2 tabular-nums">-1.643224</td><td className="px-3 py-2">ไม่เลือก</td></tr>
                </tbody>
              </table>
            </div>
            <div className="grid gap-3 p-4 md:grid-cols-2">
              <Fact label="Features" value="bar_buy_log_return · intraday_range_pct" />
              <Fact label="Chronological split" value="4,382 / 939 / 939 · train/validation/test" />
              <Fact label="Preprocessing/model" value="StandardScaler บน train · GaussianHMM diag · seeds 11/21/42" />
              <Fact label="Selected test score" value="-1.892303 LL/row · 939 observations" />
            </div>
            <div className="nice-scroll overflow-x-auto border-t border-border/60">
              <table className="w-full min-w-[580px] text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground"><tr>{['คำอธิบาย state', 'Weighted mean log return', 'Mean intraday range', 'Train posterior mass'].map((h) => <th key={h} className="px-3 py-2 font-semibold">{h}</th>)}</tr></thead>
                <tbody className="divide-y divide-border/60">{HMM_STATES.map((state) => <tr key={state.name}><th className="px-3 py-2 font-semibold">{state.name}</th><td className="px-3 py-2 tabular-nums">{state.logReturn}</td><td className="px-3 py-2 tabular-nums">{state.range}</td><td className="px-3 py-2 tabular-nums">{state.mass}</td></tr>)}</tbody>
              </table>
            </div>
          </section>

          <p className="rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-3 text-xs leading-relaxed text-amber-950">
            HMM state เป็น latent statistical regime ไม่ใช่ป้ายวิกฤต สัญญาณซื้อขาย หรือคะแนนทายถูก; `intraday_range_pct` ใช้ข้อมูลทั้งวันจึงเป็น retrospective end-of-day feature. EGARCH+HMM มี 3 features จึงห้ามเทียบ raw likelihood กับ baseline 2 features โดยตรง
          </p>
          <p className="text-[11px] text-muted-foreground">แหล่งอ้างอิง: md/eda.md · model/gold_hmm_v1/metadata.json · Dataset A_gold price cleaned.ipynb</p>
        </section>
      )}

      {section === 'retrieval' && (
        <section id="project-retrieval-panel" role="tabpanel" aria-labelledby="project-retrieval-tab" tabIndex={0} className="space-y-5">
          <SectionHeading
            eyebrow="CHUNKING · EMBEDDING · VECTOR SEARCH · RAG"
            title="ค้นหลักฐานให้เจอ แล้วตรวจว่าคำตอบอ้างอิงได้จริง"
            description="แยกการทดลอง local chunking, Qdrant retrieval, RAG prompt และ GAIB-1 development benchmark ออกจากกัน เพราะใช้คนละชุดคำถามและวัดคนละสิ่ง"
          />

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="เอกสาร / evidence records" value="264 / 264" note="เอกสารชุด chunking และ retrieval" />
            <Metric label="Chunking queries" value="114" note="source-document coverage ครบทุกวิธี" />
            <Metric label="Embedding" value="1,024D" note="@cf/baai/bge-m3 · ไม่ได้ fine-tune" />
            <Metric label="RAG corpus" value="5,058 / 19,784" note="documents / chunks ตาม manifest" />
          </div>

          <section className="card-warm rounded-2xl p-4 md:p-5">
            <SectionTitle title="โจทย์ทดลองและลำดับการเลือก" note="input → process → result → decision" />
            <ol className="mt-3 grid gap-3 md:grid-cols-4">
              {[
                ['1 · Input', 'เอกสาร 264 ชุดและคำถามที่มี source/evidence mapping จำนวน 114 ข้อ'],
                ['2 · Process', 'เปรียบเทียบ chunking 5 วิธีด้วยโมเดลและ query set เดียวกัน จากนั้นวัด Top-10'],
                ['3 · Result', 'Adaptive ได้ recall สูงสุด 83.3%; structure-aware ได้ MRR สูงสุด 0.640'],
                ['4 · Decision', 'ไม่มีวิธีชนะทุก metric: เลือก structure-aware เมื่อต้องการหลักฐานต้นอันดับ; เลือก adaptive เมื่อเน้น recall'],
              ].map(([title, detail]) => (
                <li key={title} className="rounded-xl border border-border/70 bg-white/80 p-3">
                  <h3 className="text-[13px] font-bold text-foreground">{title}</h3>
                  <p className="mt-1.5 text-[13px] leading-relaxed text-muted-foreground">{detail}</p>
                </li>
              ))}
            </ol>
          </section>

          <section className="card-warm overflow-hidden rounded-2xl">
            <SectionTitle
              title="เปรียบเทียบ chunking และ exact cosine"
              note="114 queries · @cf/baai/bge-m3 ขนาด 1,024 · local NumPy exact search ไม่ใช้ Qdrant/ANN"
            />
            <div className="nice-scroll overflow-x-auto">
              <table className="w-full min-w-[690px] text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground">
                  <tr>{['วิธีแบ่งข้อความ', 'จำนวน chunks', 'Document hit@10', 'Evidence recall@10', 'Evidence MRR@10'].map((h) => <th key={h} className="px-3 py-2.5 font-semibold">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {CHUNKING_RESULTS.map((row) => (
                    <tr key={row.method} className={row.method === 'Structure-aware' ? 'bg-accent/25' : undefined}>
                      <th className="px-3 py-2.5 font-semibold">{row.method}</th>
                      <td className="px-3 py-2.5 tabular-nums">{row.count}</td>
                      <td className="px-3 py-2.5 tabular-nums">{row.hit}</td>
                      <td className="px-3 py-2.5 tabular-nums">{row.recall}</td>
                      <td className="px-3 py-2.5 tabular-nums">{row.mrr}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="border-t border-border/60 px-4 py-3 text-[13px] leading-relaxed text-muted-foreground">
              Structure-aware รักษาหัวข้อ/section ของ CPI และ NFP และรวมย่อหน้าตามลำดับสำหรับแหล่งอื่น จึงได้ MRR สูงสุด; Adaptive ปรับขนาด chunk ตามความยาวเอกสาร จึงได้ evidence recall สูงสุด แต่หลักฐานที่ดีที่สุดอยู่ลำดับต่ำกว่า. Semantic ในการทดลองนี้แบ่งตามขอบเขตประโยค/ย่อหน้าแบบ deterministic ไม่ได้ใช้ LLM หา semantic boundary.
            </p>
          </section>

          <section className="card-warm overflow-hidden rounded-2xl">
            <SectionTitle
              title="ผล retrieval: BM25, dense, hybrid และ reranker"
              note="ชุดเดียวกัน 114 queries · เวลาเฉลี่ยรวม search/rerank ตาม run นี้ ไม่รวมการสร้างคำตอบ"
            />
            <div className="nice-scroll overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground">
                  <tr>{['วิธีค้น', 'Document hit@10', 'Evidence recall@10', 'Quote recall@10', 'MRR@10', 'เวลาเฉลี่ย'].map((h) => <th key={h} className="px-3 py-2.5 font-semibold">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {RETRIEVAL_RESULTS.map((row) => (
                    <tr key={row.method} className={row.method === 'Hybrid RRF + Jina' ? 'bg-accent/25' : undefined}>
                      <th className="px-3 py-2.5 font-semibold">{row.method}</th>
                      <td className="px-3 py-2.5 tabular-nums">{row.hit}</td>
                      <td className="px-3 py-2.5 tabular-nums">{row.recall}</td>
                      <td className="px-3 py-2.5 tabular-nums">{row.quote}</td>
                      <td className="px-3 py-2.5 tabular-nums">{row.mrr}</td>
                      <td className="px-3 py-2.5 tabular-nums">{row.latency}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="grid gap-3 p-4 md:grid-cols-2">
              <Fact label="ผลที่เลือกตาม evidence recall" value="Hybrid RRF + Jina: evidence recall เพิ่มจาก 35.5% เป็น 52.6% (+17.1 จุดเปอร์เซ็นต์), document hit เพิ่มจาก 58.8% เป็น 73.7%; Jina สำเร็จ 114/114 queries ใน run นี้" />
              <Fact label="Trade-off ที่ยอมรับ" value="เวลาเฉลี่ยเพิ่มจาก 1.90 s เป็น 6.40 s; latency นี้ไม่รวม answer generation และไม่ใช่ SLA" />
            </div>
            <p className="border-t border-border/60 px-4 py-3 text-[13px] leading-relaxed text-muted-foreground">
              Dense search สร้าง query vector ด้วย Cloudflare BGE-M3; BM25 ช่วยจับชื่อเฉพาะ ตัวเลข และวันที่; RRF รวมอันดับโดยไม่บวกคะแนนดิบต่างสเกล; Jina reranker จัดอันดับ candidate ซ้ำแล้วเลือก 10 chunks. Citation และความถูกต้องของคำตอบต้องตรวจแยกจากคุณภาพ retrieval.
            </p>
          </section>

          <section className="card-warm overflow-hidden rounded-2xl">
            <SectionTitle
              title="ผล prompt, citation และ latency"
              note="ตัวเลขจาก README ของแต่ละ run; 114 queries × 3 รอบต่อ variant. ห้ามเทียบ latency ข้าม run เป็น SLA"
            />
            <div className="nice-scroll overflow-x-auto">
              <table className="w-full min-w-[820px] text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground">
                  <tr>{['Run / variant', 'Citation ปรากฏ', 'Citation ID valid', 'Structured output valid', 'Mean', 'P95'].map((h) => <th key={h} className="px-3 py-2.5 font-semibold">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  <tr><th className="px-3 py-2.5 font-semibold">Baseline</th><td className="px-3 py-2.5">63.2%</td><td className="px-3 py-2.5">63.2%</td><td className="px-3 py-2.5">ไม่ได้รายงาน</td><td className="px-3 py-2.5">22.75 s</td><td className="px-3 py-2.5">80.12 s</td></tr>
                  <tr><th className="px-3 py-2.5 font-semibold">A2 citation preservation</th><td className="px-3 py-2.5">93.3%</td><td className="px-3 py-2.5">93.3%</td><td className="px-3 py-2.5">98.0%</td><td className="px-3 py-2.5">11.60 s</td><td className="px-3 py-2.5">16.69 s</td></tr>
                  <tr className="bg-accent/25"><th className="px-3 py-2.5 font-semibold">A2 comparison run</th><td className="px-3 py-2.5">95.9%</td><td className="px-3 py-2.5">95.9%</td><td className="px-3 py-2.5">98.2%</td><td className="px-3 py-2.5">14.58 s</td><td className="px-3 py-2.5">32.30 s</td></tr>
                  <tr><th className="px-3 py-2.5 font-semibold">A3 citation + evidence</th><td className="px-3 py-2.5">95.3%</td><td className="px-3 py-2.5">95.3%</td><td className="px-3 py-2.5">99.1%</td><td className="px-3 py-2.5">16.78 s</td><td className="px-3 py-2.5">69.78 s</td></tr>
                </tbody>
              </table>
            </div>
            <p className="border-t border-border/60 px-4 py-3 text-[13px] leading-relaxed text-muted-foreground">
              ใน A2 preservation run แรก citation-integrity อยู่ที่ 84.5% แม้ citation ID จะถูกต้อง 93.3%; การมี citation หรือ ID ที่ถูกต้องยังไม่ยืนยันว่าแหล่งข้อมูลรองรับทุก claim. A3 ได้ structured output สูงสุด แต่ latency P95 สูงกว่า A2.
            </p>
          </section>

          <div className="grid gap-3 lg:grid-cols-2">
            <section className="card-warm rounded-2xl p-4 md:p-5">
              <SectionTitle title="Vector store และสถานะการ sync" />
              <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                Qdrant collection ใช้ cosine distance กับ dense vector 1,024 มิติ; point ID สร้าง deterministic จาก chunk ID และ payload เก็บ source, URL, วันที่ และข้อความเพื่อ trace citation. ระหว่าง ingestion ฝัง batch ละ 16 และ upsert batch ละ 64 พร้อม checkpoint เพื่อ resume.
              </p>
              <div className="mt-3 rounded-xl border border-amber-300 bg-amber-50 p-3 text-[13px] leading-relaxed text-amber-950">
                ตัวเลขที่บันทึกไว้ยังขัดกัน: notebook ระบุ 19,784 points, local upsert checkpoint มี 6,080 IDs, journal มี 13,640 IDs. ยังยืนยัน sync ครบไม่ได้จนกว่าจะเทียบ exact remote IDs กับ source manifest.
              </div>
              <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                API ข้อมูลโครงการอ่าน versioned snapshot ส่วน Gold Assistant เรียก GAIB-1 runtime ที่ค้น corpus ผ่าน Qdrant จริง. Retrieval ใช้ historical corpus ไม่ใช่ข่าวสด และไม่ได้รับ portfolio ID ที่เลือกในหน้าตาราง.
              </p>
            </section>
            <section className="card-warm rounded-2xl p-4 md:p-5">
              <SectionTitle title="GAIB-1: ผลพัฒนา ไม่ใช่ release approval" />
              <dl className="mt-3 grid grid-cols-2 gap-2">
                <Fact label="Development queries / agent records" value="21 / 105 · ไม่มี errors" />
                <Fact label="Retrieval" value="Recall@10 100% · MRR 0.9302" />
                <Fact label="Output" value="JSON parse 96.19%" />
                <Fact label="Judge" value="Correctness / citation entailment 94.03%" />
                <Fact label="Critical unsupported numbers" value="0 ในชุด development นี้" />
                <Fact label="สถานะ" value="DEVELOPMENT_PASS; human semantic review ยังไม่ครบ จึงยังไม่ใช่ release approval" />
              </dl>
              <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                GAIB-1 ใช้ชุด query และ metric คนละชุดกับ retrieval 114 queries; อย่ารวมคะแนนเป็น accuracy เดียวหรือยกเป็นผลใช้งานจริงของเว็บ.
              </p>
            </section>
          </div>

          <p className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-[13px] leading-relaxed text-amber-950">
            ข้อจำกัดร่วม: Ground Truth ทั้ง 114 queries ผ่านการตรวจ source span แต่ยังรอ human semantic review; retrieval/RAG metrics จึงเป็น provisional. งาน chunking ใช้ exact NumPy cosine ไม่ได้วัด ANN; retrieval latency ไม่รวม generation; development benchmark ไม่ใช่การรับรอง production.
          </p>
          <p className="text-[12px] leading-relaxed text-muted-foreground">
            แหล่ง: README ส่วน Chunking/Embedding, Vector Store, Retrieval/RAG และ GAIB-1; embedding/embedding/retrieval_eval_v2/benchmark_summary.md; rag/rag_comparison/rag_comparison_summary.csv; rag/rag_latency_experiments/20261028T070459Z/experiment_summary.csv.
          </p>
        </section>
      )}

      {section === 'tables' && (
        <section id="project-tables-panel" role="tabpanel" aria-labelledby="project-tables-tab" tabIndex={0}>
          <ProjectDataView />
        </section>
      )}

      {section === 'journey' && (
        <ResearchJourneyView
          data={data}
          onOpenAssistant={onOpenAssistant}
          panelId="project-journey-panel"
          labelledBy="project-journey-tab"
          showHeader={false}
        />
      )}

      {section === 'agents' && (
        <MultiAgentPipelineView
          data={data}
          onOpenAssistant={onOpenAssistant}
          panelId="project-agents-panel"
          labelledBy="project-agents-tab"
          showHeader={false}
        />
      )}
    </div>
  );
}

function CorrelationPlot() {
  const rows = CORRELATIONS.map((row) => ({
    ...row,
    pearsonValue: Number(row.pearson),
    spearmanValue: Number(row.spearman),
  }));
  const xStart = 250;
  const xEnd = 690;
  const center = (xStart + xEnd) / 2;
  const halfWidth = (xEnd - xStart) / 2;
  const yPositions = [52, 98, 144];

  return (
    <div className="nice-scroll overflow-x-auto px-3 pt-3">
      <svg
        viewBox="0 0 720 184"
        className="min-w-[640px] w-full"
        role="img"
        aria-label="กราฟค่าสหสัมพันธ์ Pearson และ Spearman ของผลตอบแทนทองไทย ทอง Spot และ USD/THB"
      >
        <text x={xStart} y="18" fontSize="11" fill="#6e6552" textAnchor="middle">−1</text>
        <text x={center} y="18" fontSize="11" fill="#6e6552" textAnchor="middle">0</text>
        <text x={xEnd} y="18" fontSize="11" fill="#6e6552" textAnchor="middle">+1</text>
        <line x1={xStart} x2={xEnd} y1="25" y2="25" stroke="#e8e0cc" />
        <line x1={center} x2={center} y1="28" y2="164" stroke="#b8ad96" strokeDasharray="3 3" />
        {rows.map((row, index) => {
          const y = yPositions[index];
          const pearsonX = center + row.pearsonValue * halfWidth;
          const spearmanX = center + row.spearmanValue * halfWidth;
          return (
            <g key={row.pair}>
              <text x="0" y={y + 3} fontSize="12" fontWeight="600" fill="#2a251b">{row.pair}</text>
              <line x1={center} x2={pearsonX} y1={y - 6} y2={y - 6} stroke="#96690c" strokeWidth="7" strokeLinecap="round" />
              <circle cx={spearmanX} cy={y + 8} r="4.5" fill="#3e5f8a" />
              <text x={xEnd + 8} y={y - 3} fontSize="10" fill="#6e6552">{row.pearsonValue.toFixed(2)}</text>
              <text x={xEnd + 8} y={y + 12} fontSize="10" fill="#6e6552">{row.spearmanValue.toFixed(2)}</text>
            </g>
          );
        })}
        <line x1={xStart} x2={xEnd} y1="164" y2="164" stroke="#e8e0cc" />
        <line x1="8" x2="24" y1="177" y2="177" stroke="#96690c" strokeWidth="6" strokeLinecap="round" />
        <text x="30" y="180" fontSize="10" fill="#6e6552">Pearson</text>
        <circle cx="102" cy="177" r="4" fill="#3e5f8a" />
        <text x="111" y="180" fontSize="10" fill="#6e6552">Spearman</text>
      </svg>
    </div>
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

function SectionTitle({ title, note }: { title: string; note?: string }) {
  return (
    <header className="border-b border-border/60 px-4 py-3">
      <h3 className="text-sm font-bold">{title}</h3>
      {note && <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{note}</p>}
    </header>
  );
}

function Metric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <article className="card-warm min-w-0 rounded-xl p-3">
      <p className="text-[11px] font-semibold text-muted-foreground">{label}</p>
      <p className="mt-1 text-xl font-bold tabular-nums">{value}</p>
      <p className="mt-1 text-[10px] leading-snug text-muted-foreground">{note}</p>
    </article>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-xl border border-border/70 bg-white/80 p-3">
      <dt className="text-[11px] font-semibold text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-xs font-semibold leading-relaxed text-foreground">{value}</dd>
    </div>
  );
}
