'use client';

import { TrendingDown, TrendingUp, Minus, ExternalLink } from 'lucide-react';
import { formatThaiDate } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

export function NewsList({ data }: { data: MarketPayload }) {
  return (
    <section aria-label="ข่าวที่เกี่ยวข้องกับพอร์ต" className="card-warm rounded-2xl p-5">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="font-display text-sm font-bold">ข่าวที่นักวิเคราะห์จับคู่กับตัวเลขตลาด</h3>
        <span className="rounded-full bg-accent px-2.5 py-0.5 text-[11px] font-semibold text-accent-foreground">
          ใช้เครื่องมือ News Search
        </span>
      </div>
      <p className="mb-3 text-xs text-muted-foreground">เรียงตามน้ำหนักผลกระทบต่อราคาทองในสถานการณ์ &ldquo;{data.scenario.name}&rdquo;</p>

      <ul className="nice-scroll max-h-[300px] space-y-2.5 overflow-y-auto pr-1">
        {data.news.map((n, i) => (
          <li key={i} className="rounded-2xl bg-muted/40 p-3 transition-colors hover:bg-muted/70">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-semibold text-muted-foreground">{formatThaiDate(n.date)}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-bold text-white ${
                  n.sentiment === 'bearish' ? 'bg-loss' : n.sentiment === 'bullish' ? 'bg-gain' : 'bg-muted-foreground'
                }`}
              >
                {n.sentiment === 'bearish' ? 'ลบ' : n.sentiment === 'bullish' ? 'บวก' : 'กลาง'}
              </span>
              {n.impact === 'high' && (
                <span className="rounded-full bg-accent px-2 py-0.5 text-[11px] font-bold text-accent-foreground">ผลกระทบสูง</span>
              )}
              <span
                className={`ml-auto flex items-center gap-0.5 text-[11px] font-bold ${
                  n.marketMovePct < 0 ? 'text-loss' : n.marketMovePct > 0 ? 'text-gain' : 'text-muted-foreground'
                }`}
              >
                {n.marketMovePct < 0 ? (
                  <TrendingDown className="h-3 w-3" />
                ) : n.marketMovePct > 0 ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <Minus className="h-3 w-3" />
                )}
                ทอง 5 วันหลังข่าว {n.marketMovePct > 0 ? '+' : ''}
                {n.marketMovePct}%
              </span>
            </div>
            <p className="text-xs font-medium leading-relaxed">{n.title}</p>
            <p className="mt-1 flex items-center gap-1 text-[11px] text-muted-foreground">
              <ExternalLink className="h-2.5 w-2.5" /> {n.source}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
