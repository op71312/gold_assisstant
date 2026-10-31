'use client';

import { useEffect, useRef } from 'react';
import { Coins, Loader2, CheckCircle2, Radio, FileText, MousePointerClick } from 'lucide-react';
import { AGENT_META, EVIDENCE_LABEL, STATUS_LABEL, type AgentStatus } from '../agent-meta';

// ---------------------------------------------------------------------------
// Gold Assistant team diagram, designed with the diagram-design principles:
//   · fan-in pattern: 4 analysts on one row, evidence flows down into Lead
//   · density 4/10 (every node earns its place, decoration deleted)
//   · semantic roles: paper / ink / muted / accent(gold, reserved) / hairline
//   · no shadows, hairline strokes, flat editorial surface
//   · accessible SVG (role=img + title/desc), reduced-motion safe
// SVG layer draws edges + travelling dots; HTML layer draws nodes (same box).
// ---------------------------------------------------------------------------

export interface GraphAgentState {
  status: AgentStatus;
  thinking: string;
  toolName?: string;
  keyFinding?: string;
  chip?: string;
}

interface Props {
  agents: Record<number, GraphAgentState>;
  running: boolean;
  done: boolean;
  error: boolean;
  sourceSummary: string;
  selected: number | null;
  onSelect: (id: number) => void;
}

const W = 1000;
const H = 640;

// one projection: node centres on the canvas grid
const SPOTS: Record<number, { x: number; y: number }> = {
  1: { x: 125, y: 152 },
  2: { x: 375, y: 152 },
  3: { x: 625, y: 152 },
  4: { x: 875, y: 152 },
  5: { x: 500, y: 404 },
};
const OUT = { x: 500, y: 566 };

const pos = (x: number, y: number) => ({ left: `${(x / W) * 100}%`, top: `${(y / H) * 100}%` });

// evidence edges: analyst bottom → Lead top (gentle S-curves, one per analyst)
const EDGE_IN: Record<number, string> = {
  1: 'M 125 244 C 125 292, 415 272, 428 307',
  2: 'M 375 244 C 375 280, 465 268, 470 307',
  3: 'M 625 244 C 625 280, 535 268, 530 307',
  4: 'M 875 244 C 875 292, 585 272, 572 307',
};
const EDGE_OUT = 'M 500 508 L 500 538';

const HAIRLINE = '#ddd2b8';

function isBusy(st?: AgentStatus) {
  return !!st && st !== 'idle' && st !== 'done' && st !== 'error';
}

export function AgentGraph({ agents, running, done, error, sourceSummary, selected, onSelect }: Props) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const lead = agents[5];
  const doneCount = [1, 2, 3, 4, 5].filter((id) => ['done', 'error'].includes(agents[id]?.status ?? '')).length;
  const failedCount = [1, 2, 3, 4, 5].filter((id) => agents[id]?.status === 'error').length;
  const leadSt = lead?.status ?? 'idle';
  const leadDone = leadSt === 'done';
  const leadActive = !!lead && !leadDone && leadSt !== 'error';

  // center the canvas horizontally on first paint (mobile: canvas is wider than viewport)
  useEffect(() => {
    const el = scrollRef.current;
    if (el && el.scrollWidth > el.clientWidth) {
      el.scrollLeft = (el.scrollWidth - el.clientWidth) / 2;
    }
  }, []);

  return (
    <section className="card-warm overflow-hidden rounded-2xl">
      {/* ---- header: title + run status ---- */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-3">
        <Radio className={`h-4 w-4 shrink-0 ${running || error ? 'text-loss' : done ? 'text-gain' : 'text-gold-deep'}`} />
        <div className="min-w-0 flex-1">
          <h3 className="font-display text-[15px] font-bold leading-tight">แผนผังการทำงานของทีมนักวิเคราะห์ 5 ตัว</h3>
          <p className="text-xs text-muted-foreground">Agent 1–4 วิเคราะห์หลักฐาน · Lead Researcher ตรวจ citations และสังเคราะห์</p>
        </div>
        <span
          className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-bold ${
            running || error ? 'bg-loss/10 text-loss' : done ? 'bg-gain/10 text-gain' : 'bg-muted text-muted-foreground'
          }`}
        >
          {running ? 'กำลังทำงาน' : error ? 'ไม่สำเร็จ' : done ? failedCount ? `จบรอบ · ผิดพลาด ${failedCount}` : 'เสร็จสิ้น' : 'พร้อมทำงาน'} {doneCount}/5
        </span>
        <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full gold-gradient transition-all duration-500" style={{ width: `${(doneCount / 5) * 100}%` }} />
        </div>
      </div>

      {/* ---- shared evidence source strip ---- */}
      <div className="flex justify-center border-b border-border/70 bg-muted/40 px-3 py-2.5">
        <span className="inline-flex max-w-full items-center gap-2 text-[13px] font-semibold text-foreground">
          <Coins className="h-4 w-4 shrink-0 text-gold-deep" />
          <span className="truncate">{sourceSummary}</span>
        </span>
      </div>

      {/* ---- canvas ---- */}
      <div ref={scrollRef} className="nice-scroll overflow-x-auto bg-cream">
        <div className="relative mx-auto aspect-[1000/640] w-full min-w-[900px] max-w-[1000px]">
          {/* accessible SVG edge layer */}
          <svg viewBox={`0 0 ${W} ${H}`} className="pointer-events-none absolute inset-0 h-full w-full" role="img" aria-labelledby="gd-title gd-desc">
            <title id="gd-title">แผนผังทีมนักวิเคราะห์ 5 ตัว</title>
            <desc id="gd-desc">
              นักวิเคราะห์ 4 ตัว (ข่าว แมโคร สถิติ ความเสี่ยง) ส่งหลักฐานลงสู่ Lead Researcher ที่อยู่ด้านล่าง แล้วสรุปเป็นผลลัพธ์เดียว
            </desc>
            <defs>
              {AGENT_META.map((a) => (
                <marker key={a.id} id={`gd-arrow-${a.id}`} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
                  <path d="M 0 1 L 9 5 L 0 9 z" fill={a.id === 5 ? '#96690c' : a.color} opacity={0.85} />
                </marker>
              ))}
              <marker id="gd-arrow-out" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#96690c" />
              </marker>
            </defs>

            {/* evidence → Lead: hairline at rest, agent colour when it flows */}
            {[1, 2, 3, 4].map((id) => {
              const meta = AGENT_META[id - 1];
              const st = agents[id]?.status ?? 'idle';
              const aDone = st === 'done';
              const aFailed = st === 'error';
              const active = isBusy(st);
              const d = EDGE_IN[id];
              return (
                <g key={`e${id}`}>
                  <path
                    d={d}
                    fill="none"
                    stroke={aFailed ? '#b42318' : aDone || active ? meta.color : HAIRLINE}
                    strokeWidth={active ? 2 : 1.5}
                    strokeDasharray={active ? '5 5' : undefined}
                    strokeLinecap="round"
                    className={active ? 'graph-dash' : undefined}
                    opacity={aDone ? 0.55 : active ? 0.9 : 1}
                    markerEnd={`url(#gd-arrow-${id})`}
                  />
                  {/* travelling evidence dot, only while the team is mid-run */}
                  {aDone && !done && (
                    <circle r={4.5} fill={meta.color} stroke="#fff" strokeWidth={1.2} key={`d${running ? 'r' : 's'}${id}`}>
                      <animateMotion dur="1.6s" repeatCount="indefinite" path={d} />
                    </circle>
                  )}
                </g>
              );
            })}

            {/* Lead → final result */}
            <path
              d={EDGE_OUT}
              fill="none"
              stroke={leadDone || leadActive ? '#96690c' : HAIRLINE}
              strokeWidth={leadActive ? 2 : 1.5}
              strokeDasharray={leadActive ? '5 5' : undefined}
              strokeLinecap="round"
              className={leadActive ? 'graph-dash' : undefined}
              opacity={leadDone ? 0.8 : leadActive ? 0.9 : 1}
              markerEnd="url(#gd-arrow-out)"
            />
          </svg>

          {/* ---- analyst nodes (top row) ---- */}
          {[1, 2, 3, 4].map((id) => {
            const meta = AGENT_META[id - 1];
            return <AnalystNode key={id} id={id} meta={meta} state={agents[id]} selected={selected === id} onSelect={onSelect} />;
          })}

          {/* ---- Lead Researcher (fan-in hub) ---- */}
          <LeadNode meta={AGENT_META[4]} state={lead} selected={selected === 5} onSelect={onSelect} agents={agents} />

          {/* ---- final output pill ---- */}
          <div className="absolute -translate-x-1/2 -translate-y-1/2" style={pos(OUT.x, OUT.y)}>
            <button
              type="button"
              onClick={() => onSelect(5)}
              aria-pressed={leadDone}
              className={`flex items-center gap-2 rounded-full border px-4 py-2 text-[13px] font-bold transition-colors ${
                leadDone ? 'border-gain/50 bg-white text-gain' : leadSt === 'error' ? 'border-loss/50 bg-white text-loss' : leadActive ? 'border-gold-deep/60 bg-white text-gold-deep' : 'border-border bg-white text-muted-foreground'
              }`}
            >
              {leadDone ? <CheckCircle2 className="h-4 w-4" /> : leadSt === 'error' ? <FileText className="h-4 w-4" /> : leadActive ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              {leadDone ? 'ข้อสรุปพร้อมแล้ว ดูด้านล่าง' : leadSt === 'error' ? 'ผลไม่ผ่านการตรวจสอบ' : 'ผลลัพธ์ที่ผ่านการตรวจสอบ'}
            </button>
          </div>
        </div>
      </div>

      {/* ---- legend: one quiet line ---- */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-border px-4 py-3 text-xs font-medium text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gold-deep/70" /> กำลังทำงาน
        </span>
        <span className="flex items-center gap-1.5">
          <svg width="22" height="8" aria-hidden="true">
            <line x1="0" y1="4" x2="22" y2="4" stroke="#b4690e" strokeWidth="1.8" />
          </svg>
          เส้นสี = หลักฐานที่ส่งเข้า Lead
        </span>
        <span className="flex items-center gap-1.5">
          <MousePointerClick className="h-3 w-3" /> แตะการ์ดเพื่อดูรายละเอียดของแต่ละตัว
        </span>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Analyst node: cat avatar + name + status + one live line + evidence tag
// ---------------------------------------------------------------------------
function AnalystNode({
  id,
  meta,
  state,
  selected,
  onSelect,
}: {
  id: number;
  meta: (typeof AGENT_META)[number];
  state?: GraphAgentState;
  selected: boolean;
  onSelect: (id: number) => void;
}) {
  const st = state?.status ?? 'idle';
  const spot = SPOTS[id];

  return (
    <button
      type="button"
      onClick={() => onSelect(id)}
      aria-label={`${meta.name} · ${STATUS_LABEL[st]}`}
      aria-pressed={selected}
      className={`absolute w-[222px] -translate-x-1/2 -translate-y-1/2 rounded-2xl border bg-white p-3.5 text-left transition-colors ${
        selected ? 'ring-2 ring-gold ring-offset-2 ring-offset-cream' : ''
      } ${st === 'idle' ? 'border-dashed border-input' : st === 'error' ? 'border-loss/60' : isBusy(st) ? '' : 'border-border'}`}
      style={{ ...pos(spot.x, spot.y), ...(isBusy(st) ? { borderColor: meta.color } : {}) }}
    >
      <NodeBody id={id} meta={meta} state={state} />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Lead node: the fan-in hub
// ---------------------------------------------------------------------------
function LeadNode({
  meta,
  state,
  selected,
  onSelect,
  agents,
}: {
  meta: (typeof AGENT_META)[number];
  state?: GraphAgentState;
  selected: boolean;
  onSelect: (id: number) => void;
  agents: Record<number, GraphAgentState>;
}) {
  const st = state?.status ?? 'idle';
  const evidenceCount = [1, 2, 3, 4].filter((i) => ['done', 'error'].includes(agents[i]?.status ?? '')).length;

  return (
    <button
      type="button"
      onClick={() => onSelect(5)}
      aria-label={`${meta.name} · ${STATUS_LABEL[st]}`}
      aria-pressed={selected}
      className={`absolute w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-2xl border bg-white p-4 text-left transition-colors ${
        selected ? 'ring-2 ring-gold ring-offset-2 ring-offset-cream' : ''
      } ${st === 'idle' ? 'border-dashed border-input' : st === 'error' ? 'border-loss/60' : isBusy(st) ? 'border-gold-deep' : 'border-gold-deep/50'}`}
      style={pos(SPOTS[5].x, SPOTS[5].y)}
    >
      <NodeBody id={5} meta={meta} state={state} evidenceCount={evidenceCount} />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Shared node body: deleted everything that did not earn its place
// ---------------------------------------------------------------------------
function NodeBody({
  id,
  meta,
  state,
  evidenceCount,
}: {
  id: number;
  meta: (typeof AGENT_META)[number];
  state?: GraphAgentState;
  evidenceCount?: number;
}) {
  const st = state?.status ?? 'idle';
  const isDone = st === 'done';
  const isError = st === 'error';
  const active = isBusy(st);
  const lead = id === 5;

  return (
    <>
      {/* identity row */}
      <div className="flex items-center gap-2">
        <span className={`relative shrink-0 ${active ? 'agent-active rounded-full' : ''}`}>
          <span
            className="relative flex items-center justify-center overflow-hidden rounded-full ring-1"
            style={{ width: lead ? 58 : 50, height: lead ? 58 : 50, backgroundColor: `${meta.color}14`, ['--tw-ring-color' as string]: `${meta.color}55` }}
          >
            <img
              src={meta.avatar}
              alt=""
              className="absolute inset-0 h-full w-full rounded-full object-cover"
              onError={(e) => {
                e.currentTarget.style.visibility = 'hidden';
              }}
            />
          </span>
          {(isDone || isError) && (
            <span className={`absolute -bottom-1 -left-1 flex h-4 w-4 items-center justify-center rounded-full bg-white ${isError ? 'ring-1 ring-loss/50' : 'ring-1 ring-gain/50'}`}>
              {isError ? <FileText className="h-3 w-3 text-loss" /> : <CheckCircle2 className="h-3 w-3 text-gain" />}
            </span>
          )}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[15px] font-bold leading-tight text-foreground">{meta.name}</span>
          <span className="mt-1 flex items-center gap-1.5 text-[12.5px] leading-tight">
            <span
              className={`h-1.5 w-1.5 shrink-0 rounded-full ${st === 'idle' ? 'bg-input' : isDone ? 'bg-gain' : isError ? 'bg-loss' : ''}`}
              style={!st || st === 'idle' || isDone || isError ? undefined : { backgroundColor: meta.color }}
            />
            <span className={isDone ? 'font-semibold text-gain' : isError ? 'font-semibold text-loss' : active ? 'font-semibold' : 'text-muted-foreground'} style={active ? { color: meta.color } : undefined}>
              {STATUS_LABEL[st]}
            </span>
          </span>
        </span>
        {/* editorial numbering */}
        <span className="shrink-0 self-start text-xs font-semibold tabular-nums text-muted-foreground/80">{String(id).padStart(2, '0')}</span>
      </div>

      {/* live line: thinking / result */}
      <p className={`mt-2.5 border-t border-border pt-2.5 leading-snug ${lead ? 'min-h-[52px]' : 'min-h-[46px]'} line-clamp-2 text-[13.5px] ${
        st === 'idle' ? 'text-muted-foreground' : 'text-foreground'
      }`}>
        <NodeText id={id} meta={meta} state={state} />
      </p>

      {/* evidence tag: what this node hands over (the edge meaning) */}
      <div className="mt-1.5 flex items-center justify-between gap-2">
        {lead ? (
          <span className="flex items-center gap-1.5 text-[12.5px] text-muted-foreground">
            หลักฐานที่ได้รับ
            <span className="flex items-center gap-1">
              {[1, 2, 3, 4].map((i) => (
                <span
                  key={i}
                  className={`h-2 w-2 rounded-full ${i <= (evidenceCount ?? 0) ? '' : 'bg-input'}`}
                  style={i <= (evidenceCount ?? 0) ? { backgroundColor: AGENT_META[i - 1].color } : undefined}
                />
              ))}
            </span>
            <b className="tabular-nums text-foreground/80">{evidenceCount ?? 0}/4</b>
          </span>
        ) : (
          <span className={`flex min-w-0 items-center gap-1.5 text-[12.5px] ${isDone ? 'text-foreground/85' : 'text-muted-foreground'}`}>
            <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: isDone || active ? meta.color : '#d8cfb8' }} />
            <span className="truncate">
              {EVIDENCE_LABEL[id]}
              {isDone && state?.chip ? ` · ${state.chip}` : ''}
            </span>
          </span>
        )}
      </div>
    </>
  );
}

function NodeText({ id, meta, state }: { id: number; meta: (typeof AGENT_META)[number]; state?: GraphAgentState }) {
  const st = state?.status ?? 'idle';

  if (!state || st === 'idle') {
    return (
      <>
        {id === 1
          ? 'ตัวแรกของทีม เริ่มค้นข่าวทันทีที่กดเริ่มวินิจฉัย'
          : id === 5
            ? 'รอหลักฐานจากนักวิเคราะห์ 1 ถึง 4 ก่อนตรวจและสรุปผล'
            : `รอลำดับ เริ่มหลังตัวที่ ${id - 1} ส่งบริบทให้`}
      </>
    );
  }
  if (st === 'tool') {
    return <span className="font-semibold" style={{ color: meta.color }}>กำลังเรียก {state.toolName ?? meta.tool}…</span>;
  }
  if (st === 'reading') {
    return <span>อ่านผลจาก {state.toolName ?? 'เครื่องมือ'} และคัดตัวเลขสำคัญ…</span>;
  }
  if (st === 'done') {
    return <span className="line-clamp-2">{state.keyFinding ?? state.thinking}</span>;
  }
  return (
    <>
      {state.thinking || 'กำลังประมวลผล…'}
      {state.thinking && <span className="ml-0.5 inline-block h-3 w-[4px] animate-pulse rounded-sm bg-gold-deep align-middle" />}
    </>
  );
}
