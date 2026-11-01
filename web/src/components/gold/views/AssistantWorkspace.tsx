'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Square,
  Wrench,
  Brain,
  FileText,
  Crown,
  Loader2,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  ShieldX,
  ScanLine,
  Radio,
  Send,
  Info,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { AGENT_META, STATUS_LABEL, type AgentStatus } from '../agent-meta';
import { AgentGraph, type GraphAgentState } from './AgentGraph';
import { GaibRuntimeStatus } from '../GaibRuntimeStatus';
import { ViewHeader } from './shared';
import { formatPct } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';
import type { ChatEvent, GaibPipelineSummary, GaibSource } from '@/lib/gold/payload';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface WsAgent {
  agentId: number;
  name: string;
  role: string;
  color: string;
  status: AgentStatus;
  thinking: string;
  toolName?: string;
  toolSummary?: string;
  toolData?: Record<string, unknown>;
  keyFinding?: string;
  evidence?: string[];
  narrationMode?: 'gaib-notebook';
}

interface WsRun {
  id: string;
  question: string;
  scenarioName: string;
  agents: WsAgent[];
  final?: string;
  notice?: string;
  error?: string;
  pipelineSummary?: GaibPipelineSummary;
  narrationMode: 'connecting' | 'gaib-notebook';
  done: boolean;
}

interface Props {
  data: MarketPayload;
  onAgentActivity: (agentId: number | null, status: AgentStatus) => void;
  autoQuestion?: string | null;
  onAutoQuestionConsumed?: () => void;
}

const QUICK_PROMPTS = [
  'สรุปความเสี่ยงจากข้อมูลพอร์ตจำลองของโครงการ',
  'HMM ระบุภาวะตลาดทองล่าสุดในชุดข้อมูลอย่างไร?',
  'ข่าวใน corpus สนับสนุนข้อสรุปเรื่องทองข้อไหนบ้าง?',
  'ข้อจำกัดสำคัญของข้อมูลและผลวิเคราะห์มีอะไร?',
];

const TOOLS_BY_AGENT: Record<number, { name: string; desc: string }[]> = {
  1: [{ name: 'GAIB-1 RAG evidence review', desc: 'ใช้ hybrid retrieval และ reranking เพื่อหาข้อความอ้างอิงจาก corpus ของโครงการ' }],
  2: [{ name: 'GAIB-1 market snapshot analysis', desc: 'อธิบายตัวเลขจาก feature dataset โดยแยกข้อเท็จจริงออกจากความสัมพันธ์เชิงสาเหตุ' }],
  3: [{ name: 'GAIB-1 quant + Gaussian HMM', desc: 'อ่านสถิติย้อนหลังและ market regime จาก HMM พร้อมระบุข้อจำกัด' }],
  4: [{ name: 'GAIB-1 risk and accounting audit', desc: 'ตรวจ invariant, คุณภาพข้อมูล, ความเสี่ยง และข้อจำกัดของผลจำลอง' }],
  5: [{ name: 'GAIB-1 citation audit + synthesis', desc: 'ตรวจแหล่งอ้างอิงและสังเคราะห์เฉพาะข้อกล่าวอ้างที่มีหลักฐานรองรับ' }],
};

const WORKFLOW_NOTE = 'นักวิเคราะห์ 1 ถึง 4 ส่ง "ข้อค้นพบ + หลักฐาน" ให้ Lead Researcher ตรวจสอบก่อนสรุปเสมอ';

// helpers for tool data
const num = (d: Record<string, unknown> | undefined, k: string, fb = 0): number => (typeof d?.[k] === 'number' ? (d[k] as number) : fb);
const str = (d: Record<string, unknown> | undefined, k: string, fb = ''): string => (typeof d?.[k] === 'string' ? (d[k] as string) : fb);
const arr = <T,>(d: Record<string, unknown> | undefined, k: string): T[] => (Array.isArray(d?.[k]) ? (d[k] as T[]) : []);
const THB = (x: number) => `฿${Math.round(Math.abs(x)).toLocaleString('en-US')}`;

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export function AssistantWorkspace({ data, onAgentActivity, autoQuestion, onAutoQuestionConsumed }: Props) {
  const [run, setRun] = useState<WsRun | null>(null);
  const [running, setRunning] = useState(false);
  const [question, setQuestion] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const runIdRef = useRef<string>('');
  const activeCardRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const scrolledForRef = useRef<string>('');
  const graphRef = useRef<HTMLDivElement | null>(null);

  const handleEvent = useCallback(
    (evt: ChatEvent, runId: string) => {
      // side effects outside state updaters
      if (evt.type === 'agent_start') onAgentActivity(evt.agentId, 'thinking');
      else if (evt.type === 'tool_call') onAgentActivity(evt.agentId, 'tool');
      else if (evt.type === 'tool_result') onAgentActivity(evt.agentId, 'reading');
      else if (evt.type === 'agent_done') onAgentActivity(null, 'idle');

      setRun((prev) => {
        if (!prev || prev.id !== runId) return prev;
        const next: WsRun = { ...prev, agents: [...prev.agents] };

        switch (evt.type) {
          case 'agent_start': {
            const meta: WsAgent = {
              agentId: evt.agentId,
              name: evt.name,
              role: evt.role,
              color: evt.color,
              status: 'thinking',
              thinking: '',
            };
            const i = next.agents.findIndex((a) => a.agentId === evt.agentId);
            if (i >= 0) next.agents[i] = meta;
            else next.agents.push(meta);
            break;
          }
          case 'tool_call': {
            next.agents = next.agents.map((a) =>
              a.agentId === evt.agentId ? { ...a, status: 'tool' as AgentStatus, toolName: evt.tool } : a,
            );
            break;
          }
          case 'tool_result': {
            next.agents = next.agents.map((a) =>
              a.agentId === evt.agentId
                ? { ...a, status: 'reading' as AgentStatus, toolName: evt.tool, toolSummary: evt.summary, toolData: evt.data }
                : a,
            );
            break;
          }
          case 'thinking_delta': {
            next.agents = next.agents.map((a) =>
              a.agentId === evt.agentId ? { ...a, status: 'thinking' as AgentStatus, thinking: a.thinking + evt.text } : a,
            );
            break;
          }
          case 'agent_done': {
            next.agents = next.agents.map((a) =>
              a.agentId === evt.agentId
                ? {
                    ...a,
                    status: evt.status as AgentStatus,
                    keyFinding: evt.keyFinding,
                    evidence: evt.evidence,
                    thinking: evt.thinking || a.thinking,
                    narrationMode: evt.narrationMode,
                  }
                : a,
            );
            break;
          }
          case 'analysis_mode': {
            next.narrationMode = evt.mode;
            break;
          }
          case 'final_answer': {
            next.final = evt.text;
            break;
          }
          case 'analysis_notice': {
            next.notice = evt.message;
            break;
          }
          case 'pipeline_summary': {
            next.pipelineSummary = evt.summary;
            break;
          }
          case 'pipeline_error': {
            next.error = evt.message;
            next.notice = evt.message;
            break;
          }
          case 'done': {
            next.done = true;
            break;
          }
          default:
            break;
        }
        return next;
      });
    },
    [onAgentActivity],
  );

  const ask = useCallback(
    async (question: string) => {
      if (!question.trim() || running) return;
      const runId = `ws-${Date.now()}`;
      runIdRef.current = runId;
      setRun({ id: runId, question, scenarioName: 'GAIB-1 notebook', agents: [], narrationMode: 'connecting', done: false });
      setRunning(true);
      scrolledForRef.current = '';

      const controller = new AbortController();
      abortRef.current = controller;
      try {
        const res = await fetch('/api/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question }),
          signal: controller.signal,
        });
        if (!res.ok) {
          const errorBody = await res.json().catch(() => null) as { error?: string; detail?: string } | null;
          throw new Error(errorBody?.error ?? errorBody?.detail ?? `เริ่ม GAIB-1 ไม่สำเร็จ (${res.status})`);
        }
        if (!res.body) throw new Error('no stream');
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = '';
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const parts = buf.split('\n\n');
          buf = parts.pop() ?? '';
          for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith('data:')) continue;
            try {
              handleEvent(JSON.parse(line.slice(5).trim()) as ChatEvent, runId);
            } catch {
              // ignore malformed chunk
            }
          }
        }
      } catch (e) {
        if ((e as Error).name !== 'AbortError') {
          setRun((prev) =>
            prev && prev.id === runId
              ? {
                  ...prev,
                  error: (e as Error).message || 'เชื่อมต่อ GAIB-1 runtime ไม่สำเร็จ',
                  notice: (e as Error).message || 'เชื่อมต่อ GAIB-1 runtime ไม่สำเร็จ',
                  done: true,
                }
              : prev,
          );
        }
      } finally {
        setRunning(false);
        abortRef.current = null;
        onAgentActivity(null, 'idle');
      }
    },
    [running, handleEvent, onAgentActivity],
  );

  // auto question handed over from other tabs
  useEffect(() => {
    if (autoQuestion && !running) {
      void ask(autoQuestion);
      onAutoQuestionConsumed?.();
    }
  }, [autoQuestion]);

  // scroll active agent card into view, only when the knowledge graph is NOT on screen
  // (if the user is watching the graph, don't yank them down to the cards)
  useEffect(() => {
    if (!run || run.done) return;
    const active = [...run.agents].reverse().find((a) => a.status !== 'done');
    if (!active) return;
    const key = `${run.id}-${active.agentId}-${active.status}`;
    if (scrolledForRef.current === key) return;
    scrolledForRef.current = key;
    const gr = graphRef.current?.getBoundingClientRect();
    if (gr && gr.top < window.innerHeight * 0.55 && gr.bottom > window.innerHeight * 0.25) return;
    activeCardRefs.current[active.agentId]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [run]);

  const stop = () => {
    abortRef.current?.abort();
    setRunning(false);
    setRun((prev) => prev ? { ...prev, notice: 'หยุดรอผลในหน้านี้แล้ว; งานที่ส่งถึง GAIB-1 runtime อาจทำต่อจนจบ และคำขอใหม่อาจต้องรอ' } : prev);
  };

  // pipeline statuses
  const statusById = useMemo(() => {
    const m: Record<number, AgentStatus> = {};
    run?.agents.forEach((a) => (m[a.agentId] = a.status));
    return m;
  }, [run]);
  const doneCount = AGENT_META.filter((a) => statusById[a.id] === 'done' || statusById[a.id] === 'error').length;

  // knowledge-graph node states (with short stat chips for evidence edges)
  const graphAgents = useMemo(() => {
    const m: Record<number, GraphAgentState> = {};
    (run?.agents ?? []).forEach((a) => {
      let chip: string | undefined;
      if (a.status === 'done') {
        if (a.agentId === 1) chip = `หลักฐาน ${arr<string>(a.toolData, 'evidence_ids').length} รายการ`;
        else if (a.agentId === 2) chip = `Bias ${str(a.toolData, 'macro_bias', 'unknown')}`;
        else if (a.agentId === 3) {
          const regime = a.toolData?.regime_state;
          const state = typeof regime === 'object' && regime !== null
            ? str(regime as Record<string, unknown>, 'state_name', str(regime as Record<string, unknown>, 'name'))
            : str(a.toolData, 'regime_state_id');
          chip = state ? `Regime ${state}` : str(a.toolData, 'status', 'Quant result');
        } else if (a.agentId === 4) chip = `Risk ${str(a.toolData, 'go_no_go', 'review')}`;
        else if (a.agentId === 5) {
          const confidence = str(a.toolData, 'confidence');
          chip = confidence ? `ความเชื่อมั่น ${confidence}` : undefined;
        }
        if (!chip && a.keyFinding) chip = a.keyFinding.slice(0, 34) + '…';
      } else if (a.status === 'error') {
        chip = 'ผลไม่ผ่านการตรวจสอบ';
      }
      m[a.agentId] = { status: a.status, thinking: a.thinking, toolName: a.toolName, keyFinding: a.keyFinding, chip };
    });
    return m;
  }, [run]);

  const selectAgent = useCallback((id: number) => {
    setSelectedAgent(id);
    activeCardRefs.current[id]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  const findings = useMemo(
    () =>
      (run?.agents ?? [])
        .filter((a) => a.agentId <= 4 && a.keyFinding)
        .map((a) => ({ agentId: a.agentId, keyFinding: a.keyFinding as string, color: a.color, name: a.name })),
    [run],
  );

  // Answer-first: plain-Thai team conclusion + calibrated confidence (research: AI trust UX)
  const riskAgent = useMemo(() => run?.agents.find((a) => a.agentId === 4), [run]);
  const leadConfidence = useMemo(() => {
    const lead = run?.agents.find((a) => a.agentId === 5);
    return str(lead?.toolData, 'confidence').toLowerCase();
  }, [run]);
  const confidence = useMemo((): { label: string; reason: string; tone: 'gain' | 'neutral' | 'loss' } => {
    if (!run || !run.done || !run.final || run.error) return { label: '', reason: '', tone: 'neutral' };
    const successfulAgents = run.agents.filter((agent) => agent.status === 'done').length;
    if (leadConfidence === 'high' && successfulAgents === 5)
      return { label: 'ความเชื่อมั่นสูง', reason: 'Lead Researcher ให้ระดับสูง และผลทั้ง 5 ตัวผ่าน schema validation', tone: 'gain' };
    if (leadConfidence === 'low' || successfulAgents < 5)
      return { label: 'ความเชื่อมั่นต่ำ', reason: `ผลที่ผ่านการตรวจสอบ ${successfulAgents}/5 ตัว อ่านข้อจำกัดและ citation ประกอบ`, tone: 'loss' };
    return { label: 'ความเชื่อมั่นปานกลาง', reason: 'ระดับจาก Lead Researcher; ตรวจแหล่งอ้างอิงและข้อจำกัดก่อนนำไปใช้', tone: 'neutral' };
  }, [run, leadConfidence]);

  const jumpToCards = useCallback(() => {
    activeCardRefs.current[1]?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  return (
    <div id="assistant-panel" className="space-y-5">
      <ViewHeader
        title="ถาม Gold Assistant"
        subtitle="ถามเรื่องพอร์ตหรือทอง แล้วตรวจผลคำนวณ หลักฐาน และสถานะการสร้างคำตอบของ agent ทั้ง 5 ตัว"
        data={data}
        right={
          run && (
            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-bold ring-1 ${run.error ? 'bg-loss/5 text-loss ring-loss/40' : 'bg-white text-accent-foreground ring-gold/40'}`}>
              <Radio className={`h-3 w-3 ${running ? 'animate-pulse text-loss' : 'text-gain'}`} />
              {running ? 'กำลังทำงานร่วมกัน' : run.error ? 'วินิจฉัยไม่สำเร็จ' : run.done ? 'วินิจฉัยเสร็จสิ้น' : 'พร้อมทำงาน'} {doneCount}/5
            </span>
          )
        }
      />

      <GaibRuntimeStatus requestPending={running && (run?.agents.length ?? 0) === 0} />

      <section className="rounded-2xl border border-gold/40 bg-white p-4 md:p-5">
        <div className="mb-4 flex items-start gap-3 rounded-xl border border-sky-200 bg-sky-50 px-3.5 py-3 text-sky-950">
          <Info className="mt-0.5 h-5 w-5 shrink-0 text-sky-800" />
          <div className="text-[13px] leading-relaxed">
            <p className="font-bold">ใช้ GAIB-1 notebook pipeline จริง</p>
            <p className="mt-1">
              คำถามส่งผ่าน <code className="rounded bg-white/80 px-1">POST /api/agents</code> ไปยัง Python runtime ที่โหลดโค้ดจาก notebook โดยตรง: corpus ข่าว → Cloudflare embeddings + Qdrant hybrid search (BM25/RRF) + Jina reranking → market features/HMM/risk audit → ThaiLLM agents 1–5 และ citation validation.
            </p>
            <p className="mt-1">
              ใช้ข้อมูลย้อนหลังจากไฟล์ใน repository ไม่ใช่ราคาทองหรือข่าวสด; ผล portfolio audit มาจาก simulator ของโครงการ ไม่ใช่บัญชีส่วนตัวหรือ portfolio ID ที่เลือกในหน้าเว็บ.
            </p>
            <p className="mt-1">
              ถ้า notebook, secrets หรือบริการภายนอกไม่พร้อม ระบบจะแจ้งข้อผิดพลาดและไม่สร้างคำตอบ fallback แทนผล GAIB-1.
            </p>
          </div>
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const trimmed = question.trim();
            if (!trimmed || running) return;
            setQuestion('');
            void ask(trimmed);
          }}
          className="flex flex-col gap-3 sm:flex-row"
          aria-label="ถาม Gold Assistant"
        >
          <label htmlFor="assistant-question" className="sr-only">พิมพ์คำถามถึง Gold Assistant</label>
          <input
            id="assistant-question"
            type="text"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            disabled={running}
            placeholder="ถามเกี่ยวกับหลักฐานและผลวิเคราะห์ในโครงการ เช่น HMM ระบุภาวะตลาดอย่างไร?"
            className="min-h-12 min-w-0 flex-1 rounded-xl border border-input bg-cream/50 px-4 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold disabled:opacity-60"
          />
          {running ? (
            <button
              type="button"
              onClick={stop}
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-loss px-5 text-sm font-bold text-white"
            >
              <Square className="h-4 w-4" /> หยุดวิเคราะห์
            </button>
          ) : (
            <button
              type="submit"
              disabled={!question.trim()}
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl gold-gradient px-5 text-sm font-bold text-navy-deep disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send className="h-4 w-4" /> ส่งคำถาม
            </button>
          )}
        </form>
        <div className="mt-3 flex flex-wrap gap-2" aria-label="ตัวอย่างคำถาม">
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={running}
              onClick={() => void ask(prompt)}
              className="min-h-9 rounded-full border border-border bg-cream/60 px-3 py-1.5 text-xs font-medium text-foreground/80 transition-colors hover:border-gold/60 hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
            >
              {prompt}
            </button>
          ))}
        </div>
        <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
          ทีมวิเคราะห์จะตอบพร้อมหลักฐานและข้อจำกัด · คำตอบใช้ประกอบการศึกษา ไม่ใช่คำแนะนำการลงทุน
        </p>
      </section>

      {run?.notice && (
        <p role={run.error ? 'alert' : 'status'} className={`rounded-xl border px-4 py-3 text-[13px] leading-relaxed ${run.error ? 'border-loss/40 bg-loss/5 text-loss' : 'border-sky-200 bg-sky-50 text-sky-950'}`}>
          {run.notice}
        </p>
      )}

      {/* Sticky progress while the team is working: visible without scrolling to cards */}
      {run && (
        <div className="sticky top-0 z-10 -mx-1 flex flex-wrap items-center gap-2 rounded-2xl border border-gold/40 bg-cream/95 px-3.5 py-2.5 shadow-sm backdrop-blur">
          <Radio className={`h-3.5 w-3.5 shrink-0 ${running ? 'animate-pulse text-loss' : 'text-gain'}`} />
          <span className="text-[11.5px] font-bold text-foreground/85">
            {running ? 'ทีมกำลังวินิจฉัย' : run.error ? 'วินิจฉัยไม่สำเร็จ' : run.done ? 'วินิจฉัยเสร็จ' : 'พร้อมทำงาน'} {doneCount}/5
          </span>
          <NarrationBadge mode={run.narrationMode} error={Boolean(run.error)} />
          <span className="hidden min-w-0 flex-1 truncate text-[11px] text-muted-foreground sm:block">{run.question}</span>
          {!run.done && (
            <button
              onClick={jumpToCards}
              className="ml-auto inline-flex min-h-[32px] items-center gap-1 rounded-full border border-gold/40 bg-white px-3 py-1 text-[11px] font-bold text-accent-foreground hover:bg-accent/50"
            >
              <ArrowRight className="h-3 w-3" /> ดูการ์ดรายละเอียด
            </button>
          )}
        </div>
      )}

      {/* Answer-first summary: Lead's plain-Thai conclusion above everything (research:
          answer first, evidence second, uncertainty labeled, second voice visible) */}
      {run?.done && run.final && confidence.label && (
        <section className="rounded-2xl border-2 border-gold/50 bg-white p-4.5 md:p-5">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <img src={AGENT_META[4].avatar} alt="" className="h-7 w-7 rounded-full object-cover ring-2 ring-teal-500/40 ring-offset-1" />
            <span className="font-display text-base font-bold">สรุปจาก Lead Researcher</span>
            <NarrationBadge mode={run.narrationMode} />
            <span
              className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${
                confidence.tone === 'gain' ? 'bg-gain/12 text-gain' : confidence.tone === 'loss' ? 'bg-loss/12 text-loss' : 'bg-muted text-muted-foreground'
              }`}
            >
              {confidence.label}: {confidence.reason}
            </span>
            <span className="ml-auto rounded-full bg-accent px-2.5 py-1 text-[11px] font-semibold text-accent-foreground">
              ความเห็นเพื่อการศึกษา ไม่ใช่คำรับประกัน
            </span>
          </div>
          <div className="max-w-[72ch] text-[15px] leading-7 text-foreground">
            <ReactMarkdown
              components={{
                h2: ({ children }) => <h3 className="mb-2 mt-4 text-base font-bold first:mt-0">{children}</h3>,
                h3: ({ children }) => <h4 className="mb-1.5 mt-3 text-sm font-bold">{children}</h4>,
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5">{children}</ul>,
                ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5">{children}</ol>,
                li: ({ children }) => <li className="pl-1">{children}</li>,
                strong: ({ children }) => <strong className="font-bold">{children}</strong>,
              }}
            >
              {run.final}
            </ReactMarkdown>
          </div>
          {riskAgent?.keyFinding && (
            <p className="mt-2.5 rounded-xl bg-accent/40 px-3 py-2.5 text-[13px] leading-relaxed text-accent-foreground">
              <b>Risk &amp; Data Auditor:</b> {riskAgent.keyFinding}
            </p>
          )}
          <p className="mt-2.5 text-[13px] leading-relaxed text-muted-foreground">
            คำตอบอิง snapshot ย้อนหลังและ corpus ที่ระบุด้านล่าง ไม่ใช่ราคาสดหรือคำแนะนำการลงทุน
          </p>
          {run.pipelineSummary && <PipelineEvidence summary={run.pipelineSummary} />}
        </section>
      )}

      {/* Knowledge graph of the team (approved design: structure unchanged) */}
      <div ref={graphRef}>
        <AgentGraph
          agents={graphAgents}
          running={running}
          done={!!run?.done}
          error={Boolean(run?.error)}
          sourceSummary="หลักฐานร่วม: RAG corpus · market features · Gaussian HMM · simulator risk audit"
          selected={selectedAgent}
          onSelect={selectAgent}
        />
      </div>

      {/* Runs */}
      {run && (
        <>
          {/* question echo */}
          <div className="flex items-center gap-2 rounded-2xl bg-navy-deep px-4 py-3 text-white">
            <ScanLine className="h-4 w-4 shrink-0 text-gold-soft" />
            <span className="min-w-0 text-xs leading-relaxed">
              <b className="text-gold-soft">คำถาม:</b> {run.question}
              <span className="ml-2 text-white/50">· รันด้วย {run.scenarioName}</span>
            </span>
          </div>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            {AGENT_META.filter((a) => a.id <= 4).map((meta) => {
              const a = run.agents.find((x) => x.agentId === meta.id);
              return (
                <div
                  key={meta.id}
                  ref={(el) => { activeCardRefs.current[meta.id] = el; }}
                  className={`rounded-2xl transition-shadow ${selectedAgent === meta.id ? 'ring-2 ring-gold/60 ring-offset-2 ring-offset-background' : ''}`}
                >
                  <AgentWorkCard agent={a} meta={meta} />
                </div>
              );
            })}
          </div>

          {/* Lead researcher: full width */}
          <div
            ref={(el) => { activeCardRefs.current[5] = el; }}
            className={`rounded-2xl transition-shadow ${selectedAgent === 5 ? 'ring-2 ring-gold/60 ring-offset-2 ring-offset-background' : ''}`}
          >
            <LeadCard
              agent={run.agents.find((x) => x.agentId === 5)}
              meta={AGENT_META[4]}
              findings={findings}
              running={running}
              allAgentsDone={findings.length >= 4}
            />
          </div>

        </>
      )}

      {/* Empty state: explain the team & workflow */}
      {!run && (
        <>
          <section className="card-warm rounded-2xl p-5">
            <h3 className="font-display text-sm font-bold">ทีมนี้ทำงานร่วมกันอย่างไร</h3>
            <div className="mt-3 grid grid-cols-1 gap-2.5 md:grid-cols-2 xl:grid-cols-4">
              {AGENT_META.filter((a) => a.id <= 4).map((a) => (
                <div key={a.id} className="rounded-2xl bg-muted/40 p-3.5">
                  <div className="mb-1.5 flex items-center gap-2">
                    <img src={a.avatar} alt="" className="h-7 w-7 shrink-0 rounded-full object-cover ring-2 ring-offset-1" style={{ ['--tw-ring-color' as string]: a.color }} />
                    <span className="text-xs font-bold">
                      ตัวที่ {a.id} · {a.name}
                    </span>
                  </div>
                  <p className="text-[13px] leading-relaxed text-muted-foreground">{a.role}</p>
                  <div className="mt-2 rounded-xl bg-muted/60 px-2.5 py-1.5">
                    <div className="flex items-center gap-1 text-[12px] font-bold text-foreground/75">
                      <Wrench className="h-3 w-3" /> {TOOLS_BY_AGENT[a.id][0].name}
                    </div>
                    <p className="mt-0.5 text-[13px] leading-relaxed text-muted-foreground">{TOOLS_BY_AGENT[a.id][0].desc}</p>
                  </div>
                </div>
              ))}
              <div className="rounded-2xl border border-gold-deep/40 bg-accent/40 p-3.5 xl:row-span-1">
                <div className="mb-1.5 flex items-center gap-2">
                  <img src={AGENT_META[4].avatar} alt="" className="h-7 w-7 shrink-0 rounded-full object-cover ring-2 ring-gold-deep/50 ring-offset-1" />
                  <span className="text-xs font-bold">ตัวที่ 5 · Lead Researcher</span>
                </div>
                <p className="text-[13px] leading-relaxed text-muted-foreground">{AGENT_META[4].role}</p>
                <div className="mt-2 rounded-xl bg-muted/60 px-2.5 py-1.5">
                  <div className="flex items-center gap-1 text-[12px] font-bold text-foreground/75">
                    <Wrench className="h-3 w-3" /> {TOOLS_BY_AGENT[5][0].name}
                  </div>
                  <p className="mt-0.5 text-[13px] leading-relaxed text-muted-foreground">{TOOLS_BY_AGENT[5][0].desc}</p>
                </div>
              </div>
            </div>
            <p className="mt-3 flex items-center gap-1.5 text-[13px] font-semibold text-accent-foreground">
              <ArrowRight className="h-3.5 w-3.5 text-gold-deep" /> {WORKFLOW_NOTE}
            </p>
          </section>

          <section className="rounded-2xl border border-dashed border-gold/50 bg-white/60 p-8 text-center">
            <p className="text-sm font-semibold text-foreground/80">พร้อมแล้ว กดปุ่มเริ่มวินิจฉัยด้านบน หรือเลือกคำถามตัวอย่าง</p>
            <p className="mt-1 text-xs text-muted-foreground">Agent 1–4 วิเคราะห์หลักฐานพร้อมกัน แล้ว Lead Researcher ตรวจ schema/citations ก่อนสรุป</p>
          </section>
        </>
      )}
    </div>
  );
}

function NarrationBadge({ mode, error = false }: { mode: WsRun['narrationMode']; error?: boolean }) {
  const label = error ? 'GAIB-1 runtime · error' : {
    connecting: 'กำลังเชื่อม GAIB-1 runtime',
    'gaib-notebook': 'GAIB-1 notebook · ThaiLLM',
  }[mode];
  const style = error
    ? 'border-loss/40 bg-loss/5 text-loss'
    : mode === 'gaib-notebook'
      ? 'border-sky-200 bg-sky-50 text-sky-900'
      : 'border-border bg-muted text-muted-foreground';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[12px] font-semibold ${style}`} role="status">
      <span className="h-2 w-2 rounded-full bg-current" aria-hidden="true" />
      {label}
    </span>
  );
}

function PipelineEvidence({ summary }: { summary: GaibPipelineSummary }) {
  const sources = summary.retrieval?.sources ?? [];
  const metrics = summary.metrics ?? {};
  const retrievalMetrics = summary.retrieval?.metrics ?? {};
  const marketAsOf = str(summary.market, 'as_of', 'ไม่ระบุ');
  const hmmStatus = str(summary.hmm, 'status', 'ไม่พร้อม');
  const hmmState = str(summary.hmm, 'latest_state', 'ไม่ระบุ');
  const backend = summary.retrieval?.backend ?? 'ไม่ระบุ';
  const citationAudit = summary.citationAudit ?? {};
  const citationStatus = citationAudit.valid === true
    ? 'ผ่าน'
    : citationAudit.valid === false
      ? 'พบข้อจำกัด'
      : str(citationAudit, 'status', 'ดูรายงาน Lead Researcher');

  return (
    <div className="mt-4 border-t border-border pt-3">
      <h3 className="text-sm font-bold text-foreground">ที่มาของคำตอบในรอบนี้</h3>
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1.5 text-[13px] leading-relaxed text-foreground/90">
        <span><b>RAG:</b> {backend} · {sources.length} แหล่ง</span>
        <span><b>Market:</b> ณ {marketAsOf}</span>
        <span><b>HMM:</b> {hmmStatus} · state {hmmState}</span>
        <span><b>Citation audit:</b> {citationStatus}</span>
        {typeof metrics.total_wall_ms === 'number' && <span><b>เวลา:</b> {(metrics.total_wall_ms / 1000).toFixed(1)} วินาที</span>}
        {typeof retrievalMetrics.retrieval_status === 'string' && <span><b>Retrieval:</b> {retrievalMetrics.retrieval_status}</span>}
      </div>
      {summary.market?.summary && (
        <p className="mt-2 max-w-[72ch] text-[13px] leading-relaxed text-muted-foreground">{summary.market.summary}</p>
      )}
      {sources.length > 0 ? (
        <ol className="mt-3 divide-y divide-border/70">
          {sources.map((source, index) => {
            const href = safeSourceUrl(source);
            return (
              <li key={`${source.citation_id ?? 'source'}-${index}`} className="py-2 first:pt-0">
                <div className="flex items-start gap-2">
                  <span className="shrink-0 rounded bg-accent px-1.5 py-0.5 font-mono text-[12px] font-bold text-accent-foreground">
                    [{source.citation_id ?? `S${index + 1}`}]
                  </span>
                  <div className="min-w-0">
                    {href ? (
                      <a href={href} target="_blank" rel="noreferrer" className="text-[13px] font-semibold text-foreground underline decoration-gold/60 underline-offset-2 hover:decoration-gold-deep">
                        {source.title || source.source || 'เปิดแหล่งข้อมูล'}
                      </a>
                    ) : (
                      <p className="text-[13px] font-semibold text-foreground">{source.title || source.source || 'แหล่งข้อมูล'}</p>
                    )}
                    <p className="text-[12px] text-muted-foreground">
                      {[source.source, source.publication_date, source.report_period].filter(Boolean).join(' · ') || 'ไม่มี metadata วันที่/แหล่งที่มา'}
                    </p>
                    {source.text_excerpt && <p className="mt-1 max-w-[72ch] text-[13px] leading-relaxed text-foreground/85">{source.text_excerpt}</p>}
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        <p className="mt-2 text-[13px] text-muted-foreground">รอบนี้ไม่มี RAG source ที่ผ่านการคัดเลือก</p>
      )}
    </div>
  );
}

function safeSourceUrl(source: GaibSource): string | null {
  if (!source.url) return null;
  try {
    const url = new URL(source.url);
    return url.protocol === 'https:' || url.protocol === 'http:' ? url.toString() : null;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Agent work card (agents 1 to 4)
// ---------------------------------------------------------------------------
function AgentWorkCard({ agent, meta }: { agent: WsAgent | undefined; meta: (typeof AGENT_META)[number] }) {
  const Icon = meta.icon;
  const exists = !!agent;
  const st = agent?.status ?? 'idle';
  const isDone = st === 'done';
  const isFailed = st === 'error';
  const isActive = exists && !isDone && !isFailed;

  return (
    <section
      className={`h-full rounded-2xl border bg-white p-4 transition-all ${
        isActive ? 'border-gold/60 ring-2 ring-gold/25' : isFailed ? 'border-loss/40' : isDone ? 'border-border' : 'border-dashed border-border opacity-70'
      }`}
    >
      {/* header */}
      <div className="mb-3 flex items-center gap-2.5">
        <span className={`relative shrink-0 ${isActive ? 'agent-active rounded-full' : ''}`}>
          <span
            className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-full ring-2 ring-offset-1"
            style={{ backgroundColor: `${meta.color}22`, ['--tw-ring-color' as string]: meta.color }}
          >
            <Icon className="h-4 w-4" style={{ color: meta.color }} />
            <img
              src={meta.avatar}
              alt=""
              className="absolute inset-0 h-full w-full rounded-full object-cover"
              onError={(e) => {
                e.currentTarget.style.visibility = 'hidden';
              }}
            />
          </span>
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-navy-deep text-[11px] font-bold text-gold-soft ring-1 ring-gold/50">
            {meta.id}
          </span>
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 text-[13px] font-bold leading-tight">
            {meta.name}
          </div>
          <div className="truncate text-[12px] text-muted-foreground">{meta.role}</div>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold ${
            isDone ? 'bg-gain/12 text-gain' : isFailed ? 'bg-loss/10 text-loss' : isActive ? 'bg-accent text-accent-foreground' : 'bg-muted text-muted-foreground'
          }`}
        >
          {isActive && <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />}
          {isDone ? '✓ ' : isFailed ? '× ' : ''}
          {STATUS_LABEL[st]}
        </span>
      </div>
      {agent?.narrationMode && <div className="mb-3"><NarrationBadge mode={agent.narrationMode} /></div>}

      {!exists && <p className="text-[13px] text-muted-foreground">ยังไม่ถึงรอบของตัวนี้ จะเริ่มทำงานตามลำดับทีละขั้น</p>}

      {exists && (
        <div className="space-y-2.5">
          {/* step 1: thinking */}
          {(agent.thinking || st === 'thinking') && !(meta.id === 5 && isDone) && (
            <StepBlock
              n={1}
              icon={<Brain className="h-3 w-3" />}
              title="กำลังคิด"
              active={st === 'thinking'}
              color={meta.color}
            >
              <p className="whitespace-pre-wrap text-[14px] leading-7 text-foreground">
                {agent.thinking || <span className="text-muted-foreground">กำลังประมวลผล...</span>}
                {st === 'thinking' && agent.thinking && <span className="cursor-dot" />}
              </p>
            </StepBlock>
          )}

          {/* step 2: tool call */}
          {agent.toolName && (
            <StepBlock
              n={2}
              icon={<Wrench className="h-3 w-3" />}
              title="เรียกเครื่องมือ"
              active={st === 'tool'}
              color={meta.color}
            >
              <div className="inline-flex items-center gap-1.5 rounded-md bg-muted px-2 py-1 font-mono text-[11px] font-semibold text-foreground/80">
                <Wrench className="h-3 w-3" /> {agent.toolName}
              </div>
            </StepBlock>
          )}

          {/* step 3: tool result (rich data) */}
          {agent.toolSummary && (
            <StepBlock
              n={3}
              icon={<FileText className="h-3 w-3" />}
              title="ผลจากเครื่องมือ"
              active={st === 'reading'}
              color={meta.color}
            >
              <p className="text-[13px] leading-relaxed text-foreground/90">{agent.toolSummary}</p>
              <div className="mt-2">
                <ToolData agentId={meta.id} data={agent.toolData} color={meta.color} />
              </div>
            </StepBlock>
          )}

          {/* step 4: finding */}
          {(isDone || isFailed) && agent.keyFinding && (
            <StepBlock n={4} icon={isFailed ? <ShieldX className="h-3 w-3" /> : <CheckCircle2 className="h-3 w-3" />} title={isFailed ? 'ผลไม่ผ่านการตรวจสอบ' : 'ข้อค้นพบสำคัญ'} active={false} color={meta.color}>
              <p className="border-l-[3px] pl-3 text-[14px] font-semibold leading-relaxed text-foreground" style={{ borderColor: meta.color }}>
                {agent.keyFinding}
              </p>
              {agent.evidence && agent.evidence.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {agent.evidence.map((ev, i) => (
                    <span key={i} className="inline-flex items-center gap-1 rounded-md bg-muted/80 px-2 py-1 text-[12px] text-muted-foreground">
                      <FileText className="h-2.5 w-2.5" /> {ev}
                    </span>
                  ))}
                </div>
              )}
              <p className="mt-2 flex items-center gap-1 text-[12px] font-bold text-muted-foreground">
                <ArrowRight className="h-3 w-3" style={{ color: meta.color }} /> ส่งข้อค้นพบนี้ให้ Lead Researcher ตรวจสอบ
              </p>
            </StepBlock>
          )}
        </div>
      )}
    </section>
  );
}

function StepBlock({
  n,
  icon,
  title,
  active,
  color,
  children,
}: {
  n: number;
  icon: React.ReactNode;
  title: string;
  active: boolean;
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div className="relative border-l pb-4 pl-4 last:pb-0" style={{ borderColor: active ? color : 'var(--border)' }}>
      <span
        className="absolute -left-[7px] top-0 h-3.5 w-3.5 rounded-full border-2 bg-white"
        style={{ borderColor: active ? color : '#cfc5aa' }}
        aria-hidden
      />
      <div className="flex items-center gap-1.5 text-[13px] font-semibold text-muted-foreground">
        <span className="tabular-nums text-foreground/50">0{n}</span>
        {icon} {title}
        {active && <Loader2 className="h-3 w-3 animate-spin text-gold-deep" />}
      </div>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Lead Researcher card (agent 5): shows collaboration, findings from 1 to 4
// ---------------------------------------------------------------------------
function LeadCard({
  agent,
  meta,
  findings,
  running,
  allAgentsDone,
}: {
  agent: WsAgent | undefined;
  meta: (typeof AGENT_META)[number];
  findings: { agentId: number; keyFinding: string; color: string; name: string }[];
  running: boolean;
  allAgentsDone: boolean;
}) {
  const Icon = meta.icon;
  const exists = !!agent;
  const st = agent?.status ?? 'idle';
  const isDone = st === 'done';
  const isFailed = st === 'error';
  const isActive = exists && !isDone && !isFailed;
  const checks = agent ? arr<{ name: string; pass: boolean; detail: string }>(agent.toolData, 'checks') : [];
  const leadFindings = agent ? arr<{ agentId: number; keyFinding: string }>(agent.toolData, 'priorFindings') : [];

  return (
    <section
      className={`rounded-2xl border bg-white p-4 transition-all ${
        isActive ? 'border-gold/60 ring-2 ring-gold/25' : isFailed ? 'border-loss/40' : isDone ? 'border-gold-deep/40' : 'border-dashed border-border opacity-80'
      }`}
    >
      <div className="mb-3 flex items-center gap-2.5">
        <span className={`relative shrink-0 ${isActive ? 'agent-active rounded-full' : ''}`}>
          <span
            className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-full ring-2 ring-offset-1"
            style={{ backgroundColor: `${meta.color}22`, ['--tw-ring-color' as string]: meta.color }}
          >
            <Icon className="h-4 w-4" style={{ color: meta.color }} />
            <img
              src={meta.avatar}
              alt=""
              className="absolute inset-0 h-full w-full rounded-full object-cover"
              onError={(e) => {
                e.currentTarget.style.visibility = 'hidden';
              }}
            />
          </span>
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-navy-deep text-[11px] font-bold text-gold-soft ring-1 ring-gold/50">
            {meta.id}
          </span>
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-[13px] font-bold leading-tight">{meta.name}</div>
          <div className="truncate text-[11px] text-muted-foreground">{meta.role}</div>
        </div>
        <span
          className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold ${
            isDone ? 'bg-gain/12 text-gain' : isFailed ? 'bg-loss/10 text-loss' : isActive ? 'bg-accent text-accent-foreground' : 'bg-muted text-muted-foreground'
          }`}
        >
          {isActive && <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />}
          {isDone ? '✓ ' : isFailed ? '× ' : ''}
          {STATUS_LABEL[st]}
        </span>
      </div>
      {agent?.narrationMode && <div className="mb-3"><NarrationBadge mode={agent.narrationMode} /></div>}

      {/* Collaboration: evidence received from agents 1 to 4 */}
      <div className="mb-3 border-b border-border pb-3">
        <div className="mb-2 flex items-center gap-1.5 text-[13px] font-semibold text-muted-foreground">
          <ArrowRight className="h-3 w-3" /> หลักฐานที่ได้รับจากนักวิเคราะห์ 1 ถึง 4 ({findings.length}/4 ชุด)
        </div>
        {findings.length === 0 ? (
          <p className="text-[13px] text-muted-foreground">
            {running ? 'กำลังรอข้อค้นพบจากนักวิเคราะห์ทั้ง 4 ตัว...' : 'ยังไม่มีหลักฐาน Lead Researcher จะเริ่มทำงานหลังนักวิเคราะห์ 1 ถึง 4 ส่งข้อค้นพบครบ'}
          </p>
        ) : (
          <ul className="divide-y divide-border/60">
            {findings.map((f) => (
              <li key={f.agentId} className="flex items-start gap-2 py-1.5 first:pt-0">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white" style={{ backgroundColor: f.color }}>
                  {f.agentId}
                </span>
                <span className="min-w-0 text-[13px] leading-relaxed text-foreground/90">
                  <b className="whitespace-nowrap">{f.name}:</b> {f.keyFinding}
                </span>
              </li>
            ))}
          </ul>
        )}
        {allAgentsDone && !exists && running && (
          <p className="mt-1.5 text-[13px] font-bold text-gain">✓ ครบ 4 ชุดแล้ว กำลังส่งต่อให้ Lead Researcher สรุปผล</p>
        )}
      </div>

      {!exists && <p className="text-[13px] text-muted-foreground">ตัวนี้จะทำงานเป็น "ตัวสุดท้าย" ตรวจสอบผลคำนวณของทุกตัวก่อนสรุปเสมอ</p>}

      {exists && (
        <div className="space-y-2.5">
          {(agent.thinking || st === 'thinking') && !isDone && (
            <StepBlock n={1} icon={<Brain className="h-3 w-3" />} title="กำลังคิด" active={st === 'thinking'} color={meta.color}>
              <p className="whitespace-pre-wrap text-[14px] leading-7 text-foreground">
                {agent.thinking || <span className="text-muted-foreground">กำลังประมวลผล...</span>}
                {st === 'thinking' && agent.thinking && <span className="cursor-dot" />}
              </p>
            </StepBlock>
          )}

          {agent.toolName && (
            <StepBlock n={2} icon={<Wrench className="h-3 w-3" />} title="เรียกเครื่องมือ" active={st === 'tool'} color={meta.color}>
              <div className="inline-flex items-center gap-1.5 rounded-md bg-muted px-2 py-1 font-mono text-[11px] font-semibold text-foreground/80">
                <Wrench className="h-3 w-3" /> {agent.toolName}
              </div>
            </StepBlock>
          )}

          {agent.toolSummary && (
            <StepBlock n={3} icon={<FileText className="h-3 w-3" />} title="ผลการตรวจสอบ" active={st === 'reading'} color={meta.color}>
              <p className="text-[13px] leading-relaxed text-foreground/90">{agent.toolSummary}</p>
              {checks.length > 0 && (
                <ul className="mt-2 divide-y divide-border/60">
                  {checks.map((c, i) => (
                    <li key={i} className="flex items-start gap-2 py-2 first:pt-0">
                      {c.pass ? (
                        <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-gain" />
                      ) : (
                        <ShieldX className="mt-0.5 h-3.5 w-3.5 shrink-0 text-loss" />
                      )}
                      <span className="min-w-0 text-[13px] leading-relaxed">
                        <b className="block text-foreground/85">{c.name}</b>
                        <span className="text-muted-foreground">{c.detail}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {/* findings re-check list (from tool data) */}
              {leadFindings.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {leadFindings.map((f) => (
                    <span key={f.agentId} className="inline-flex items-center gap-1 rounded-md bg-gain/10 px-2 py-1 text-[12px] font-semibold text-gain">
                      <CheckCircle2 className="h-2.5 w-2.5" /> รับข้อค้นพบตัวที่ {f.agentId} แล้ว
                    </span>
                  ))}
                </div>
              )}
              {agent.toolData && <div className="mt-2"><ToolData agentId={5} data={agent.toolData} color={meta.color} /></div>}
            </StepBlock>
          )}

          {(isDone || isFailed) && agent.keyFinding && (
            <StepBlock n={4} icon={isFailed ? <ShieldX className="h-3 w-3" /> : <CheckCircle2 className="h-3 w-3" />} title={isFailed ? 'ผลไม่ผ่านการตรวจสอบ' : 'ผลการตรวจสอบสุดท้าย'} active={false} color={meta.color}>
              <p className="border-l-[3px] pl-3 text-[14px] font-semibold leading-relaxed text-foreground" style={{ borderColor: meta.color }}>
                {agent.keyFinding}
              </p>
            </StepBlock>
          )}
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Rich tool-data renderers per agent
// ---------------------------------------------------------------------------
function ToolData({ agentId, data, color }: { agentId: number; data: Record<string, unknown> | undefined; color: string }) {
  if (!data) return null;
  if (typeof data._gaib === 'object' && data._gaib !== null) return <GaibAgentData data={data} />;
  if (agentId === 1) return <NewsToolData data={data} />;
  if (agentId === 2) return <MacroToolData data={data} />;
  if (agentId === 3) return <QuantToolData data={data} color={color} />;
  if (agentId === 4) return <RiskToolData data={data} color={color} />;
  return null;
}

const FIELD_LABELS: Record<string, string> = {
  accounting_assessment: 'ผลประเมินบัญชี',
  abstention_reason: 'เหตุผลที่งดสรุป',
  agent_agreement: 'ประเด็นที่เห็นตรงกัน',
  agent_disagreements: 'ประเด็นที่เห็นต่าง',
  as_of: 'ข้อมูล ณ วันที่',
  cautions: 'ข้อควรระวัง',
  checks: 'รายการตรวจสอบ',
  confidence: 'ระดับความเชื่อมั่น',
  critical_risks: 'ความเสี่ยงสำคัญ',
  data_gaps: 'ช่องว่างของข้อมูล',
  data_provenance: 'ที่มาข้อมูล',
  evidence_based_findings: 'ข้อค้นพบพร้อมหลักฐาน',
  evidence_ids: 'รหัสหลักฐาน',
  event_date: 'วันที่เหตุการณ์',
  executive_summary: 'สรุปผู้บริหาร',
  feature_inputs: 'ตัวแปรที่ใช้',
  go_no_go: 'ผลประเมินความเสี่ยง',
  hmm_interpretation: 'การตีความ HMM',
  limitations: 'ข้อจำกัด',
  macro_bias: 'ทิศทางมหภาค',
  macro_channels: 'กลไกมหภาค',
  missing_evidence: 'หลักฐานที่ยังขาด',
  non_causal_caveat: 'ข้อควรระวังเรื่องเหตุและผล',
  observed_market_facts: 'ข้อเท็จจริงจากตลาด',
  possible_market_channel: 'ช่องทางที่อาจส่งผลต่อตลาด',
  price_bias: 'มุมมองต่อทิศทางราคา',
  quantified_findings: 'ข้อค้นพบเชิงตัวเลข',
  recommendation_for_next_test: 'การทดสอบถัดไป',
  regime_confidence: 'ความเชื่อมั่นของ regime',
  regime_state: 'ภาวะตลาดจาก HMM',
  reported_fact: 'ข้อเท็จจริงจากรายงาน',
  risk_flags: 'ธงความเสี่ยง',
  statistics: 'สถิติ',
  status: 'สถานะ',
  synthetic_data_caveat: 'ข้อจำกัดข้อมูลจำลอง',
};

function fieldLabel(key: string): string {
  return FIELD_LABELS[key] ?? key.replace(/_/g, ' ').replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());
}

function GaibAgentData({ data }: { data: Record<string, unknown> }) {
  const runtime = data._gaib as Record<string, unknown>;
  const fields = Object.entries(data).filter(([key, value]) => key !== '_gaib' && key !== 'error' && value !== null && value !== '');
  const passed = runtime.status === 'success' || runtime.status === 'recovered';
  const schemaValid = runtime.schemaValid === true;

  return (
    <div className="space-y-2">
      <div className={`flex flex-wrap gap-x-4 gap-y-1 rounded-lg px-3 py-2 text-[12px] font-semibold ${passed && schemaValid ? 'bg-gain/10 text-gain' : 'bg-loss/10 text-loss'}`}>
        <span>{passed ? 'Agent call สำเร็จ' : `สถานะ: ${String(runtime.status ?? 'error')}`}</span>
        <span>JSON {runtime.jsonValid ? 'ผ่าน' : 'ไม่ผ่าน'}</span>
        <span>Schema {schemaValid ? 'ผ่าน' : 'ไม่ผ่าน'}</span>
        {typeof runtime.latencyMs === 'number' && <span>{runtime.latencyMs.toFixed(0)} ms</span>}
        {typeof runtime.attempts === 'number' && <span>{runtime.attempts} attempts</span>}
      </div>
      {fields.length > 0 ? (
        <dl className="divide-y divide-border/60">
          {fields.map(([key, value]) => (
            <div key={key} className="grid gap-1 py-2 first:pt-0 sm:grid-cols-[minmax(9rem,0.35fr)_minmax(0,1fr)] sm:gap-3">
              <dt className="text-[12px] font-bold text-muted-foreground">{fieldLabel(key)}</dt>
              <dd className="min-w-0 break-words text-[13px] leading-relaxed text-foreground">
                <StructuredValue value={value} field={key} />
              </dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-[13px] text-muted-foreground">ไม่มี structured output ที่ผ่านการตรวจสอบ</p>
      )}
    </div>
  );
}

function StructuredValue({ value, field, depth = 0 }: { value: unknown; field?: string; depth?: number }): React.ReactNode {
  if (value === null || value === undefined || value === '') return <span className="text-muted-foreground">ไม่มีข้อมูล</span>;
  if (typeof value === 'string') return <span>{value}</span>;
  if (typeof value === 'number') return <span className="tabular-nums">{value.toLocaleString('th-TH', { maximumFractionDigits: 4 })}</span>;
  if (typeof value === 'boolean') return <span>{value ? 'ใช่' : 'ไม่ใช่'}</span>;
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-muted-foreground">ไม่มีรายการ</span>;
    if (field?.includes('evidence') && value.every((item) => typeof item === 'string')) {
      return (
        <span className="flex flex-wrap gap-1">
          {value.slice(0, 12).map((item, index) => (
            <span key={`${String(item)}-${index}`} className="rounded bg-accent px-1.5 py-0.5 font-mono text-[11px] font-bold text-accent-foreground">{String(item)}</span>
          ))}
        </span>
      );
    }
    return (
      <ul className="space-y-1">
        {value.slice(0, 6).map((item, index) => (
          <li key={index} className="rounded-md bg-muted/40 px-2 py-1.5">
            <StructuredValue value={item} depth={depth + 1} />
          </li>
        ))}
        {value.length > 6 && <li className="text-[12px] text-muted-foreground">และอีก {value.length - 6} รายการ</li>}
      </ul>
    );
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>).filter(([, item]) => item !== null && item !== '');
    if (depth >= 2) return <span>{entries.map(([key, item]) => `${fieldLabel(key)}: ${String(item)}`).join(' · ')}</span>;
    return (
      <dl className="space-y-1">
        {entries.slice(0, 6).map(([key, item]) => (
          <div key={key} className="grid gap-x-2 sm:grid-cols-[minmax(7rem,0.35fr)_minmax(0,1fr)]">
            <dt className="font-semibold text-muted-foreground">{fieldLabel(key)}</dt>
            <dd><StructuredValue value={item} field={key} depth={depth + 1} /></dd>
          </div>
        ))}
        {entries.length > 6 && <div className="text-[12px] text-muted-foreground">และอีก {entries.length - 6} fields</div>}
      </dl>
    );
  }
  return <span>{String(value)}</span>;
}

function NewsToolData({ data }: { data: Record<string, unknown> }) {
  const news = arr<{ date: string; title: string; source: string; sentiment: string; impact: string; move5dPct: number }>(data, 'news');
  const bearish = num(data, 'bearishCount');
  const bullish = num(data, 'bullishCount');
  return (
    <div>
      <div className="mb-1.5 flex gap-1.5">
        <span className="rounded-full bg-loss/12 px-2 py-1 text-[12px] font-bold text-loss">ลบแรง {bearish}</span>
        <span className="rounded-full bg-gain/12 px-2 py-1 text-[12px] font-bold text-gain">บวกแรง {bullish}</span>
      </div>
      <ul className="divide-y divide-border/60">
        {news.slice(0, 6).map((n, i) => (
          <li key={i} className="flex items-center justify-between gap-2 py-1.5 first:pt-0">
            <span className="min-w-0">
              <span className="block truncate text-[13px] font-semibold leading-snug">{n.title}</span>
              <span className="text-[12px] text-muted-foreground">{n.date} · {n.source}</span>
            </span>
            <span className={`shrink-0 font-mono text-[12px] font-bold ${n.move5dPct > 2 ? 'text-gain' : n.move5dPct < -2 ? 'text-loss' : 'text-muted-foreground'}`}>
              {formatPct(n.move5dPct)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MacroToolData({ data }: { data: Record<string, unknown> }) {
  const cells: { label: string; value: string; sub?: string; tone?: 'gain' | 'loss' | 'neutral' }[] = [
    { label: 'DXY', value: `${num(data, 'dxy90dAgo').toFixed(1)} → ${num(data, 'dxyNow').toFixed(1)}`, sub: formatPct(num(data, 'dxyChangePct')), tone: num(data, 'dxyChangePct') > 0 ? 'loss' : 'gain' },
    { label: 'US 10Y', value: `${num(data, 'us10y90dAgo').toFixed(2)}% → ${num(data, 'us10yNow').toFixed(2)}%`, sub: `${num(data, 'us10yChangeBp') > 0 ? '+' : ''}${num(data, 'us10yChangeBp')} bps`, tone: num(data, 'us10yChangeBp') > 0 ? 'loss' : 'gain' },
    { label: 'USD/THB', value: `${num(data, 'usdthb90dAgo').toFixed(2)} → ${num(data, 'usdthbNow').toFixed(2)}`, sub: `บาท${num(data, 'thbChangePct') > 0 ? 'อ่อน' : 'แข็ง'} ${Math.abs(num(data, 'thbChangePct')).toFixed(1)}%` },
    { label: 'WTI', value: `$${num(data, 'wtiNow').toFixed(1)}`, sub: 'ราคาน้ำมันล่าสุด' },
    { label: 'ทอง USD (90 วัน)', value: formatPct(num(data, 'goldSpotChange90dPct')), tone: num(data, 'goldSpotChange90dPct') >= 0 ? 'gain' : 'loss' },
    { label: 'ทองบาท (90 วัน)', value: formatPct(num(data, 'goldThbChange90dPct')), sub: `FX ช่วย ${formatPct(num(data, 'fxContributionPct'))}`, tone: num(data, 'goldThbChange90dPct') >= 0 ? 'gain' : 'loss' },
    { label: 'ห่างจากจุดสูงสุด', value: formatPct(num(data, 'goldFromAthPct')), sub: `ATH $${num(data, 'athSpot').toLocaleString('en-US')} · ${str(data, 'athDate')}`, tone: 'loss' },
  ];
  return (
    <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4">
      {cells.map((c, i) => (
        <div key={i} className="rounded-lg bg-muted/60 px-2.5 py-1.5">
          <div className="text-[12px] font-semibold text-muted-foreground">{c.label}</div>
          <div className={`text-[13px] font-bold leading-snug ${c.tone === 'gain' ? 'text-gain' : c.tone === 'loss' ? 'text-loss' : 'text-foreground'}`}>{c.value}</div>
          {c.sub && <div className="text-[12px] text-muted-foreground">{c.sub}</div>}
        </div>
      ))}
    </div>
  );
}

function QuantToolData({ data, color }: { data: Record<string, unknown>; color: string }) {
  const monthly = arr<{ month: string; ret: number }>(data, 'monthlyReturns').slice(-6);
  return (
    <div>
      <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4">
        <QCell label="พอร์ต (รวม)" value={formatPct(num(data, 'portfolioReturnPct'))} tone={num(data, 'portfolioReturnPct') >= 0 ? 'gain' : 'loss'} />
        <QCell label="ถือยาว" value={formatPct(num(data, 'benchmarkReturnPct'))} tone={num(data, 'benchmarkReturnPct') >= 0 ? 'gain' : 'loss'} />
        <QCell label="Behavior Gap" value={`${Math.abs(num(data, 'behaviorGapPct')).toFixed(1)} จุด`} tone="loss" />
        <QCell label="Vol ต่อปี" value={`${num(data, 'volatilityAnnPct').toFixed(1)}%`} />
        <QCell label="ซื้อช่วงแพง (≥$5,000)" value={`${num(data, 'highPriceBuySharePct').toFixed(0)}% ของเงิน`} sub={THB(num(data, 'highPriceBuyThb'))} tone="loss" />
        <QCell label="ขายพานิก (ขาดทุน)" value={THB(num(data, 'realizedPlThb'))} tone="loss" />
        <QCell label="ต้นทุนเฉลี่ย" value={`${THB(num(data, 'avgCostThbPerOz'))}/oz`} sub={`ปัจจุบัน ${THB(num(data, 'priceNowThbPerOz'))}`} />
        <QCell label="MDD" value={formatPct(num(data, 'maxDrawdownPct'))} tone="loss" />
      </div>
      {monthly.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {monthly.map((m, i) => (
            <span
              key={i}
              className={`rounded-md px-2 py-1 font-mono text-[12px] font-bold ${m.ret >= 0 ? 'bg-gain/10 text-gain' : 'bg-loss/10 text-loss'}`}
            >
              {m.month} {formatPct(m.ret)}
            </span>
          ))}
        </div>
      )}
      <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground" style={{ borderLeft: `2px solid ${color}`, paddingLeft: 8 }}>
        การซื้อ {num(data, 'totalBoughtOz').toFixed(1)} oz รวมมี {num(data, 'highPriceBuyOz').toFixed(1)} oz ที่ซื้อช่วงราคาสูง ส่วนนี้คือแรงกดผลตอบแทนหลักของพอร์ต
      </p>
    </div>
  );
}

function RiskToolData({ data, color }: { data: Record<string, unknown>; color: string }) {
  const anomalies = arr<{ date: string; dailyMovePct: number; sigma: number }>(data, 'anomalies3sigma');
  const limits = arr<string>(data, 'limitations');
  return (
    <div>
      <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4">
        <QCell label="Anomaly เกิน 3σ" value={`${anomalies.length} วัน`} tone={anomalies.length > 0 ? 'loss' : undefined} />
        <QCell label="วันแกว่งแรง >4%/10วัน" value={`${num(data, 'whipsawDaysPct').toFixed(1)}%`} tone="loss" />
        <QCell label="รวมศูนย์ทอง" value={`${num(data, 'goldConcentrationPct').toFixed(1)}%`} tone="loss" />
        <QCell label="ข้อจำกัดหลักฐาน" value={`${limits.length} ข้อ`} />
      </div>
      {anomalies.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1">
          {anomalies.map((a, i) => (
            <span key={i} className="rounded-md bg-loss/10 px-2 py-1 font-mono text-[12px] font-bold text-loss">
              {a.date} {formatPct(a.dailyMovePct)} ({a.sigma}σ)
            </span>
          ))}
        </div>
      )}
      {limits.length > 0 && (
        <ul className="mt-2 space-y-1 text-[13px] leading-relaxed text-muted-foreground" style={{ borderLeft: `2px solid ${color}`, paddingLeft: 8 }}>
          {limits.slice(0, 3).map((l, i) => (
            <li key={i}>• {l}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function QCell({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: 'gain' | 'loss' }) {
  return (
    <div className="rounded-lg bg-muted/60 px-2.5 py-2">
      <div className="text-[12px] font-semibold text-muted-foreground">{label}</div>
      <div className={`text-[14px] font-bold leading-snug ${tone === 'gain' ? 'text-gain' : tone === 'loss' ? 'text-loss' : 'text-foreground'}`}>{value}</div>
      {sub && <div className="text-[13px] text-muted-foreground">{sub}</div>}
    </div>
  );
}
