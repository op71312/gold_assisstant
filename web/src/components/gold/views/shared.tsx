'use client';

import type { ReactNode } from 'react';
import { FlaskConical } from 'lucide-react';
import type { MarketPayload } from '@/lib/gold/payload';

// ---------------------------------------------------------------------------
// View header with scenario chip
// ---------------------------------------------------------------------------
export function ViewHeader({
  title,
  subtitle,
  data,
  right,
}: {
  title: string;
  subtitle: string;
  data: MarketPayload;
  right?: ReactNode;
}) {
  const s = data.scenario;
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
      <div className="min-w-0 flex-1">
        <h1 className="font-display text-lg font-bold leading-snug md:text-2xl md:leading-tight">{title}</h1>
        <p className="mt-0.5 text-xs text-muted-foreground md:text-[13px]">{subtitle}</p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {right}
        <span
          className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold text-white"
          style={{ backgroundColor: s.tagColor }}
        >
          <FlaskConical className="h-3 w-3" /> {s.name}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stat cell
// ---------------------------------------------------------------------------
export function StatCell({
  label,
  value,
  delta,
  tone,
  note,
}: {
  label: string;
  value: string;
  delta?: string;
  tone?: 'gain' | 'loss' | 'neutral';
  /** one-line plain-Thai gloss under the number (tap-to-explain is built in) */
  note?: string;
}) {
  const toneCls = tone === 'gain' ? 'text-gain' : tone === 'loss' ? 'text-loss' : 'text-foreground';
  const deltaCls = tone === 'gain' ? 'text-gain' : tone === 'loss' ? 'text-loss' : 'text-muted-foreground';
  return (
    <div className="rounded-2xl border border-border bg-white p-3.5">
      <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={`mt-1 font-display text-lg font-bold leading-tight ${toneCls}`}>{value}</div>
      {delta && <div className={`mt-0.5 text-[11px] font-semibold ${deltaCls}`}>{delta}</div>}
      {note && <div className="mt-1 border-t border-border/70 pt-1.5 text-[11px] leading-snug text-muted-foreground">{note}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sparkline (line) SVG
// ---------------------------------------------------------------------------
export function Sparkline({
  values,
  height = 64,
  stroke = '#D9A441',
  fill = 'rgba(217,164,65,0.16)',
  className = '',
}: {
  values: number[];
  height?: number;
  stroke?: string;
  fill?: string;
  className?: string;
}) {
  if (values.length < 2) return <div style={{ height }} className={className} />;
  const W = 300;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * W;
    const y = height - 6 - ((v - min) / span) * (height - 12);
    return [x, y] as const;
  });
  const line = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  const area = `${line} L${W},${height} L0,${height} Z`;
  return (
    <svg viewBox={`0 0 ${W} ${height}`} preserveAspectRatio="none" className={`w-full ${className}`} style={{ height }} aria-hidden>
      <path d={area} fill={fill} />
      <path d={line} fill="none" stroke={stroke} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Bar chart SVG (monthly returns): green/red bars with zero line
// ---------------------------------------------------------------------------
export function ReturnBars({ data, height = 150 }: { data: { month: string; ret: number }[]; height?: number }) {
  if (!data.length) return null;
  const W = 640;
  const H = height;
  const pad = { t: 10, b: 18 };
  const maxAbs = Math.max(...data.map((d) => Math.abs(d.ret)), 1);
  const minRet = Math.min(...data.map((d) => d.ret));
  const maxRet = Math.max(...data.map((d) => d.ret));
  const scale = Math.max(maxRet, -minRet) || maxAbs;
  const zero = pad.t + ((-minRet / scale) / ((maxRet - minRet) / scale || 1)) * (H - pad.t - pad.b) || H / 2;
  const half = (H - pad.t - pad.b) / 2;
  const midY = pad.t + (H - pad.t - pad.b) / 2;
  const bw = (W - 16) / data.length;
  const zeroY = maxRet > 0 && minRet < 0 ? midY : minRet >= 0 ? H - pad.b : pad.t;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height }} role="img" aria-label="ผลตอบแทนรายเดือน">
      {data.map((d, i) => {
        const h = (Math.abs(d.ret) / scale) * half * 2;
        const x = 8 + i * bw + bw * 0.18;
        const w = bw * 0.64;
        const y = d.ret >= 0 ? zeroY - h : zeroY;
        return (
          <g key={d.month + i}>
            <rect x={x} y={y} width={w} height={Math.max(h, 1.5)} rx={2} fill={d.ret >= 0 ? '#1F7A4D' : '#C23A3F'} />
            {data.length <= 14 && (
              <text x={x + w / 2} y={H - 5} textAnchor="middle" fontSize={9} fill="#8a8578">
                {d.month}
              </text>
            )}
          </g>
        );
      })}
      <line x1={0} x2={W} y1={zeroY} y2={zeroY} stroke="#c9c2b2" strokeWidth={1} strokeDasharray="3 3" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Drawdown area chart SVG (values already in % below running max)
// ---------------------------------------------------------------------------
export function DrawdownChart({ values, height = 130 }: { values: number[]; height?: number }) {
  if (values.length < 2) return null;
  const W = 640;
  const H = height;
  const min = Math.min(...values, -1);
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * W;
    const y = 6 + (Math.min(v, 0) / (min || -1)) * (H - 22);
    return [x, y] as const;
  });
  const line = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="w-full" style={{ height }} role="img" aria-label="กราฟ drawdown">
      <path d={`${line} L${W},${H - 16} L0,${H - 16} Z`} fill="rgba(194,58,63,0.15)" />
      <path d={line} fill="none" stroke="#C23A3F" strokeWidth={1.8} />
      <line x1={0} x2={W} y1={6} y2={6} stroke="#c9c2b2" strokeWidth={1} strokeDasharray="3 3" />
    </svg>
  );
}
