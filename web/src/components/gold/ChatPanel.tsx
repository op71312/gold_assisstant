'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Send,
  X,
  Wrench,
  FileText,
  Loader2,
  Crown,
  Square,
  Sparkles,
  PanelRightClose,
} from 'lucide-react';
import { Logo } from './Logo';
import { AGENT_META, STATUS_LABEL, type AgentStatus } from './agent-meta';
import type { ChatEvent, MarketPayload } from '@/lib/gold/payload';

const QUICK_PROMPTS = [
  'ทำไมพอร์ตเราถึงขาดทุน?',
  'สรุปความเสี่ยงพอร์ตตอนนี้',
  'ควรเพิ่มทุนซื้อทองตอนนี้ไหม?',
  'เทียบพอร์ตเรากับการ DCA',
];

interface AgentRun {
  agentId: number;
  name: string;
  role: string;
  color: string;
  status: AgentStatus;
  toolName?: string;
  toolSummary?: string;
  thinking: string;
  keyFinding?: string;
  evidence?: string[];
}

interface Run {
  id: string;
  question: string;
  scenarioName: string;
  agents: AgentRun[];
  final?: string;
  notice?: string;
  done: boolean;
}

interface ChatPanelProps {
  data: MarketPayload;
  onAgentActivity: (agentId: number | null, status: AgentStatus) => void;
  onClose?: () => void;
  onCollapse?: () => void;
}

export function ChatPanel({ data, onAgentActivity, onClose, onCollapse }: ChatPanelProps) {
  const [runs, setRuns] = useState<Run[]>([]);
  const [input, setInput] = useState('');
  const [running, setRunning] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef(true);

  const scrollToBottom = useCallback(() => {
    const el = scrollRef.current;
    if (el && autoScrollRef.current) el.scrollTop = el.scrollHeight;
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [runs, scrollToBottom]);

  const handleEvent = useCallback(
    (evt: ChatEvent, runId: string, scenarioName: string) => {
      // Side effects (activity status) handled OUTSIDE the state updater.
      // Updater functions must stay pure (they may run during render).
      if (evt.type === 'agent_start') onAgentActivity(evt.agentId, 'thinking');
      else if (evt.type === 'tool_call') onAgentActivity(evt.agentId, 'tool');
      else if (evt.type === 'tool_result') onAgentActivity(evt.agentId, 'reading');
      else if (evt.type === 'agent_done') onAgentActivity(null, 'idle');

      setRuns((prev) => {
        const idx = prev.findIndex((r) => r.id === runId);
        if (idx < 0) return prev;
        const run = { ...prev[idx] };

        switch (evt.type) {
          case 'agent_start': {
            const agents = [...run.agents];
            const exists = agents.findIndex((a) => a.agentId === evt.agentId);
            const meta = {
              agentId: evt.agentId,
              name: evt.name,
              role: evt.role,
              color: evt.color,
              status: 'thinking' as AgentStatus,
              thinking: '',
            };
            if (exists >= 0) agents[exists] = meta;
            else agents.push(meta);
            run.agents = agents;
            break;
          }
          case 'tool_call': {
            run.agents = run.agents.map((a) =>
              a.agentId === evt.agentId ? { ...a, status: 'tool' as AgentStatus, toolName: evt.tool } : a,
            );
            break;
          }
          case 'tool_result': {
            run.agents = run.agents.map((a) =>
              a.agentId === evt.agentId
                ? { ...a, status: 'reading' as AgentStatus, toolSummary: evt.summary, toolName: evt.tool }
                : a,
            );
            break;
          }
          case 'thinking_delta': {
            run.agents = run.agents.map((a) =>
              a.agentId === evt.agentId ? { ...a, status: 'thinking' as AgentStatus, thinking: a.thinking + evt.text } : a,
            );
            break;
          }
          case 'agent_done': {
            run.agents = run.agents.map((a) =>
              a.agentId === evt.agentId
                ? {
                    ...a,
                    status: 'done' as AgentStatus,
                    keyFinding: evt.keyFinding,
                    evidence: evt.evidence,
                    thinking: evt.thinking || a.thinking,
                  }
                : a,
            );
            break;
          }
          case 'final_answer': {
            run.final = evt.text;
            break;
          }
          case 'analysis_notice': {
            run.notice = evt.message;
            break;
          }
          case 'done': {
            run.done = true;
            break;
          }
          default:
            break;
        }
        const next = [...prev];
        next[idx] = run;
        return next;
      });
    },
    [onAgentActivity],
  );

  const ask = useCallback(
    async (question: string) => {
      if (!question.trim() || running) return;
      const runId = `run-${Date.now()}`;
      const scenarioName = data.scenario.name;
      setRuns((prev) => [
        ...prev,
        {
          id: runId,
          question,
          scenarioName,
          agents: [],
          done: false,
        },
      ]);
      setInput('');
      setRunning(true);
      autoScrollRef.current = true;

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const res = await fetch('/api/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question, scenario: data.scenario.id }),
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`เริ่มการวิเคราะห์ไม่สำเร็จ (${res.status})`);
        if (!res.body) throw new Error('no stream');
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const parts = buf.split('\n\n');
          buf = parts.pop() ?? '';
          for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith('data:')) continue;
            try {
              const evt = JSON.parse(line.slice(5).trim()) as ChatEvent;
              handleEvent(evt, runId, scenarioName);
            } catch {
              // ignore malformed chunk
            }
          }
        }
      } catch (e) {
        if ((e as Error).name !== 'AbortError') {
          setRuns((prev) =>
            prev.map((r) =>
              r.id === runId
                ? { ...r, final: 'ขออภัยค่ะ เกิดข้อผิดพลาดในการเชื่อมต่อทีมนักวิเคราะห์ กรุณาลองถามใหม่อีกครั้ง', done: true }
                : r,
            ),
          );
        }
      } finally {
        setRunning(false);
        abortRef.current = null;
        onAgentActivity(null, 'idle');
      }
    },
    [running, data.scenario.id, data.scenario.name, handleEvent, onAgentActivity],
  );

  const cancel = () => {
    abortRef.current?.abort();
    setRunning(false);
  };

  const body = (
    <div className="flex h-full flex-col bg-cream">
      {/* Header */}
      <div className="flex items-center gap-3 bg-sidebar px-4 py-3.5 text-white">
        <span className="block shrink-0 overflow-hidden rounded-full ring-2 ring-gold/70">
          <Logo size={40} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="font-display text-sm font-bold">Gold Assistant</div>
          <div className="truncate text-[11px] text-white/60">วิเคราะห์พอร์ตด้วยทีมนักวิเคราะห์ 5 ตัว</div>
        </div>
        {onCollapse && (
          <button
            onClick={onCollapse}
            className="hidden rounded-full p-1.5 text-white/70 hover:bg-white/10 hover:text-white xl:block"
            aria-label="ย่อแผงแชต"
            title="ย่อแผงแชต"
          >
            <PanelRightClose className="h-5 w-5" />
          </button>
        )}
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-full p-1.5 text-white/70 hover:bg-white/10 hover:text-white xl:hidden"
            aria-label="ปิดแชต"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        onScroll={(e) => {
          const el = e.currentTarget;
          autoScrollRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 140;
        }}
        className="nice-scroll flex-1 space-y-4 overflow-y-auto px-4 py-4"
      >
        {/* Welcome */}
        {runs.length === 0 && (
          <div className="rounded-2xl border border-gold/40 bg-white p-4">
            <div className="mb-2 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-gold-deep" />
              <span className="font-display text-sm font-bold">สวัสดีค่ะ ทีมนักวิเคราะห์ของ Gold Assistant พร้อมแล้ว</span>
            </div>
            <p className="text-xs leading-relaxed text-foreground/80">
              ถามเรื่องพอร์ตทองของคุณได้เลย นักวิเคราะห์ทั้ง 5 ตัวจะช่วยกันคิดทีละขั้น โดยแต่ละตัวจะเรียกเครื่องมือของตัวเอง
              (ข่าว, มหภาค, สถิติ, ความเสี่ยง) แล้วให้ Lead Researcher ตรวจหลักฐานก่อนสรุปเสมอ
              ถ้าอยากเห็นกราฟทีมทำงานทีละตัว เปิดแท็บ Gold Assistant แล้วกดปุ่มเริ่มวินิจฉัย
            </p>
          </div>
        )}

        {/* Runs */}
        {runs.map((run) => (
          <div key={run.id} className="space-y-3">
            {/* Question bubble */}
            <div className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-br-md gold-gradient px-4 py-2.5 text-sm font-medium text-navy-deep">
                {run.question}
                <div className="mt-0.5 text-right text-[11px] opacity-70">บนสถานการณ์: {run.scenarioName}</div>
              </div>
            </div>

            {/* Agent cards */}
            {run.agents.map((a) => (
              <AgentCard key={a.agentId} a={a} />
            ))}

            {run.notice && (
              <p role="status" className="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-[11px] leading-relaxed text-amber-950">
                {run.notice}
              </p>
            )}

            {/* Final */}
            {run.final && (
              <div className="rounded-2xl border-2 border-gold/60 bg-white p-4">
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full gold-gradient">
                    <Crown className="h-3.5 w-3.5 text-navy-deep" />
                  </span>
                  <span className="font-display text-sm font-bold">สรุปโดย Lead Researcher</span>
                  <span className="ml-auto rounded-full bg-gain/12 px-2 py-0.5 text-[11px] font-bold text-gain">
                    ตรวจหลักฐานแล้ว
                  </span>
                </div>
                <p className="whitespace-pre-wrap text-xs leading-relaxed text-foreground/90">{run.final}</p>
              </div>
            )}
          </div>
        ))}

        {running && (
          <div className="flex items-center gap-2 rounded-full bg-muted/80 px-3 py-2 text-[11px] text-muted-foreground">
            <Loader2 className="h-3.5 w-3.5 animate-spin text-gold-deep" />
            {(runs[runs.length - 1]?.agents.length ?? 0) === 0
              ? 'กำลังเชื่อมต่อ GAIB-1 Python service; หาก backend กำลัง cold start อาจใช้เวลาสักครู่...'
              : 'ทีมนักวิเคราะห์กำลังทำงานอยู่ ดูว่าแต่ละตัวกำลังคิดอะไรได้จากด้านบน...'}
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-border bg-white px-3.5 pb-3.5 pt-3">
        <div className="nice-scroll mb-2 flex gap-1.5 overflow-x-auto pb-1">
          {QUICK_PROMPTS.map((q) => (
            <button
              key={q}
              disabled={running}
              onClick={() => ask(q)}
              className="whitespace-nowrap rounded-full border border-gold/40 bg-accent/50 px-3 py-1.5 text-[11px] font-medium text-accent-foreground transition-colors hover:bg-accent disabled:opacity-40"
            >
              {q}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(input);
          }}
          className="flex items-center gap-2"
        >
          <div className="relative flex-1">
            <Sparkles className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gold/70" />
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={running}
              placeholder={running ? 'ทีมนักวิเคราะห์กำลังตอบคำถาม...' : 'พิมพ์คำถามเกี่ยวกับพอร์ตทองของคุณ...'}
              className="h-11 w-full rounded-2xl border border-input bg-cream pl-9 pr-3 text-sm outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-gold disabled:opacity-60"
              aria-label="พิมพ์คำถามถึงทีมนักวิเคราะห์"
            />
          </div>
          {running ? (
            <button
              type="button"
              onClick={cancel}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-loss text-white transition-colors"
              aria-label="หยุดการวิเคราะห์"
            >
              <Square className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl gold-gradient text-navy-deep transition-transform disabled:opacity-40"
              aria-label="ส่งคำถาม"
            >
              <Send className="h-4 w-4" />
            </button>
          )}
        </form>
      </div>
    </div>
  );

  return body;
}

// ---------------------------------------------------------------------------
function AgentCard({ a }: { a: AgentRun }) {
  const meta = AGENT_META.find((m) => m.id === a.agentId);
  const Icon = meta?.icon ?? Sparkles;
  const done = a.status === 'done';
  const failed = a.status === 'error';

  return (
    <div
      className={`rounded-2xl border bg-white p-3.5 transition-all ${failed ? 'border-loss/40' : 'border-border'}`}
    >
      <div className="mb-2 flex items-center gap-2.5">
        <span
          className={`relative flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full ring-2 ring-offset-1 ${!done && !failed ? 'agent-active' : ''}`}
          style={{ backgroundColor: `${a.color}22`, ['--tw-ring-color' as string]: a.color }}
        >
          <Icon className="h-3.5 w-3.5" style={{ color: a.color }} />
          {meta && (
            <img
              src={meta.avatar}
              alt=""
              className="absolute inset-0 h-full w-full rounded-full object-cover"
              onError={(e) => {
                e.currentTarget.style.visibility = 'hidden';
              }}
            />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <span className="flex items-center gap-1.5 text-xs font-bold">
            <span className="rounded-md bg-accent px-1.5 py-0.5 text-[11px] font-bold text-accent-foreground">นักวิเคราะห์ {a.agentId}</span>
            {a.name}
          </span>
          <span className="block truncate text-[11px] text-muted-foreground">{a.role}</span>
        </div>
        <span
          className={`flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold ${
            done ? 'bg-gain/12 text-gain' : failed ? 'bg-loss/10 text-loss' : 'bg-accent text-accent-foreground'
          }`}
        >
          {!done && !failed && <Loader2 className="h-3 w-3 animate-spin" />}
          {STATUS_LABEL[a.status]}
        </span>
      </div>

      {a.toolName && (
        <div className="mb-2 inline-flex items-center gap-1.5 rounded-md bg-muted px-2 py-1 font-mono text-[11px] font-semibold text-foreground/80">
          <Wrench className="h-3 w-3" /> Tool: {a.toolName}
        </div>
      )}

      {(a.thinking || !done) && (
        <p className="stream-cursor text-xs leading-relaxed text-foreground/85">
          {a.thinking || <span className="text-muted-foreground">กำลังประมวลผล...</span>}
          {!done && a.thinking && <span className="cursor-dot" />}
        </p>
      )}

      {a.toolSummary && (
        <div className="mt-2 rounded-xl bg-muted/70 px-3 py-2 text-[11px] leading-relaxed text-muted-foreground">
          <span className="font-semibold text-foreground/70">ผลเครื่องมือ:</span> {a.toolSummary}
        </div>
      )}

      {done && a.keyFinding && (
        <div className="mt-2 border-l-[3px] pl-3" style={{ borderColor: a.color }}>
          <p className="text-[11px] font-semibold leading-relaxed text-foreground/90">ข้อค้นพบ: {a.keyFinding}</p>
          {a.evidence && a.evidence.length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              {a.evidence.map((ev, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 rounded-md bg-muted/60 px-1.5 py-0.5 text-[11px] text-muted-foreground"
                >
                  <FileText className="h-2.5 w-2.5" /> {ev}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
