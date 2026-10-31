'use client';

import { useState } from 'react';
import { Newspaper, Database } from 'lucide-react';
import { NewsView } from './NewsView';
import { MarketView } from './MarketView';
import type { MarketPayload } from '@/lib/gold/payload';

/**
 * Merged "ข่าว & ตลาด" tab: one nav item, two sub-sections behind a pill switcher.
 * Reduces 8 top-level tabs to 7 with a clearer grouping (UX redesign 2026-10-28).
 */
export function NewsMarketView({ data, initialTab = 'news' }: { data: MarketPayload; initialTab?: 'news' | 'market' }) {
  const [tab, setTab] = useState<'news' | 'market'>(initialTab);

  return (
    <div className="space-y-5">
      <div className="inline-flex rounded-full bg-muted p-1" role="tablist" aria-label="สลับข่าว / ข้อมูลตลาด">
        <button
          role="tab"
          aria-selected={tab === 'news'}
          onClick={() => setTab('news')}
          className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-bold transition-all ${
            tab === 'news' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Newspaper className="h-3.5 w-3.5" /> ข่าว & จับคู่ราคา
        </button>
        <button
          role="tab"
          aria-selected={tab === 'market'}
          onClick={() => setTab('market')}
          className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-bold transition-all ${
            tab === 'market' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Database className="h-3.5 w-3.5" /> ข้อมูลตลาด
        </button>
      </div>

      {tab === 'news' ? <NewsView data={data} /> : <MarketView data={data} />}
    </div>
  );
}
