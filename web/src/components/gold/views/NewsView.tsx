'use client';

import { useMemo, useState } from 'react';
import { Newspaper, TrendingUp, TrendingDown, Minus, Filter, ArrowUpDown } from 'lucide-react';
import { ViewHeader } from './shared';
import { formatPct } from '@/lib/gold/format';
import type { MarketPayload, NewsItem } from '@/lib/gold/payload';

type SentimentFilter = 'all' | 'bullish' | 'bearish' | 'neutral';
type SortMode = 'move' | 'date';

const SENTIMENT_META: Record<NewsItem['sentiment'], { label: string; cls: string; icon: typeof TrendingUp }> = {
  bullish: { label: 'ข่าวบวก', cls: 'bg-gain/12 text-gain', icon: TrendingUp },
  bearish: { label: 'ข่าวลบ', cls: 'bg-loss/12 text-loss', icon: TrendingDown },
  neutral: { label: 'เป็นกลาง', cls: 'bg-muted text-muted-foreground', icon: Minus },
};

const IMPACT_META: Record<NewsItem['impact'], { label: string; cls: string }> = {
  high: { label: 'ผลกระทบสูง', cls: 'bg-loss/15 text-loss' },
  medium: { label: 'ผลกระทบกลาง', cls: 'bg-gold/15 text-gold-deep' },
  low: { label: 'ผลกระทบต่ำ', cls: 'bg-muted text-muted-foreground' },
};

export function NewsView({ data }: { data: MarketPayload }) {
  const [sent, setSent] = useState<SentimentFilter>('all');
  const [impact, setImpact] = useState<'all' | NewsItem['impact']>('all');
  const [sort, setSort] = useState<SortMode>('date');

  const counts = useMemo(
    () => ({
      bullish: data.news.filter((n) => n.sentiment === 'bullish').length,
      bearish: data.news.filter((n) => n.sentiment === 'bearish').length,
      neutral: data.news.filter((n) => n.sentiment === 'neutral').length,
    }),
    [data.news],
  );

  const list = useMemo(() => {
    let items = [...data.news];
    if (sent !== 'all') items = items.filter((n) => n.sentiment === sent);
    if (impact !== 'all') items = items.filter((n) => n.impact === impact);
    items.sort((a, b) => (sort === 'move' ? a.marketMovePct - b.marketMovePct : b.date.localeCompare(a.date)));
    return items;
  }, [data.news, sent, impact, sort]);

  const bearishAvg =
    counts.bearish > 0
      ? data.news.filter((n) => n.marketMovePct < -2).reduce((a, b) => a + b.marketMovePct, 0) / Math.max(data.news.filter((n) => n.marketMovePct < -2).length, 1)
      : 0;

  return (
    <div className="space-y-5">
      <ViewHeader
        title="ข่าวและการจับคู่กับตัวเลขตลาด"
        subtitle="ข่าวและสถานการณ์เป็นข้อมูลตัวอย่าง จับคู่กับการเปลี่ยนแปลงในชุดข้อมูลย้อนหลังภายใน 5 วันทำการ"
        data={data}
      />

      {/* Summary strip */}
      <div className="grid grid-cols-3 gap-3">
        <SummaryCard icon={TrendingUp} label="ข่าวบวก" value={counts.bullish} cls="text-gain" />
        <SummaryCard icon={TrendingDown} label="ข่าวลบ" value={counts.bearish} cls="text-loss" />
        <SummaryCard icon={Minus} label="เป็นกลาง" value={counts.neutral} cls="text-muted-foreground" />
      </div>
      {counts.bearish > 0 && (
        <p className="rounded-2xl border border-loss/30 bg-white px-4 py-2.5 text-[11px] leading-relaxed text-foreground/80">
          ข่าวลบที่ราคาทองวิ่งตามเกิน -2% ใน 5 วันเฉลี่ย <b className="text-loss">{formatPct(bearishAvg)}</b> นี่คือวันที่พอร์ตถือทองหนักโดนเต็ม ๆ โดยไม่มีเวลาตั้งรับ
        </p>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-white px-3.5 py-2.5">
        <Filter className="h-3.5 w-3.5 text-muted-foreground" />
        {(
          [
            ['all', 'ทั้งหมด'],
            ['bullish', 'บวก'],
            ['bearish', 'ลบ'],
            ['neutral', 'กลาง'],
          ] as [SentimentFilter, string][]
        ).map(([k, label]) => (
          <button
            key={k}
            onClick={() => setSent(k)}
            className={`rounded-full px-3 py-1 text-[11px] font-semibold transition-colors ${
              sent === k ? 'gold-gradient text-navy-deep' : 'bg-muted/70 text-muted-foreground hover:bg-muted'
            }`}
          >
            {label}
          </button>
        ))}
        <span className="mx-1 h-4 w-px bg-border" />
        {(
          [
            ['all', 'ทุกระดับ'],
            ['high', 'ผลสูง'],
            ['medium', 'ผลกลาง'],
            ['low', 'ผลต่ำ'],
          ] as ['all' | NewsItem['impact'], string][]
        ).map(([k, label]) => (
          <button
            key={k}
            onClick={() => setImpact(k)}
            className={`rounded-full px-3 py-1 text-[11px] font-semibold transition-colors ${
              impact === k ? 'bg-navy-deep text-white' : 'bg-muted/70 text-muted-foreground hover:bg-muted'
            }`}
          >
            {label}
          </button>
        ))}
        <button
          onClick={() => setSort((s) => (s === 'date' ? 'move' : 'date'))}
          className="ml-auto inline-flex items-center gap-1 rounded-full border border-gold/40 px-3 py-1 text-[11px] font-semibold text-accent-foreground hover:bg-accent/50"
        >
          <ArrowUpDown className="h-3 w-3" /> {sort === 'date' ? 'เรียง: วันที่' : 'เรียง: ราคาวิ่งแรง'}
        </button>
      </div>

      {/* News list */}
      <ul className="space-y-3">
        {list.map((n) => {
          const sMeta = SENTIMENT_META[n.sentiment];
          const SIcon = sMeta.icon;
          const iMeta = IMPACT_META[n.impact];
          const moveCls = n.marketMovePct > 2 ? 'text-gain' : n.marketMovePct < -2 ? 'text-loss' : 'text-muted-foreground';
          return (
            <li key={n.date + n.title} className="card-warm rounded-2xl p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold ${sMeta.cls}`}>
                      <SIcon className="h-3 w-3" /> {sMeta.label}
                    </span>
                    <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${iMeta.cls}`}>{iMeta.label}</span>
                    {n.tags.map((t) => (
                      <span key={t} className="rounded-full bg-accent px-2 py-0.5 text-[11px] font-medium text-accent-foreground">
                        #{t}
                      </span>
                    ))}
                  </div>
                  <p className="text-sm font-semibold leading-snug">{n.title}</p>
                  <p className="mt-1 text-[11px] text-muted-foreground">{n.source} · {n.date}</p>
                </div>
                <div className={`shrink-0 rounded-2xl bg-muted/60 px-3.5 py-2.5 text-right ${moveCls}`}>
                  <div className="flex items-center gap-1 text-[11px] font-semibold uppercase text-muted-foreground">
                    <Newspaper className="h-3 w-3" /> ทองหลังข่าว 5 วัน
                  </div>
                  <div className="font-display text-lg font-bold leading-tight">{formatPct(n.marketMovePct)}</div>
                </div>
              </div>
            </li>
          );
        })}
        {list.length === 0 && (
          <li className="rounded-2xl border border-dashed border-border bg-white/60 p-8 text-center text-xs text-muted-foreground">
            ไม่มีข่าวที่ตรงกับตัวกรองนี้ในสถานการณ์ที่เลือก ลองเปลี่ยนตัวกรองหรือเลือกสถานการณ์อื่น
          </li>
        )}
      </ul>
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, cls }: { icon: typeof TrendingUp; label: string; value: number; cls: string }) {
  return (
    <div className="card-warm flex items-center gap-3 rounded-2xl p-4">
      <span className={`flex h-9 w-9 items-center justify-center rounded-2xl bg-white ${cls}`}>
        <Icon className="h-4 w-4" />
      </span>
      <div>
        <div className="text-[11px] text-muted-foreground">{label}</div>
        <div className={`font-display text-xl font-bold leading-none ${cls}`}>{value} รายการ</div>
      </div>
    </div>
  );
}
