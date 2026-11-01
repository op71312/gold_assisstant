'use client';

import Image from 'next/image';
import { TrendingDown, TrendingUp, Coins, Wallet } from 'lucide-react';
import { formatBaht, formatPct } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

interface StatsRowProps {
  data: MarketPayload;
}

export function StatsRow({ data }: StatsRowProps) {
  const s = data.snapshot;
  const loss = s.totalPl < 0;

  return (
    <section aria-label="สรุปพอร์ตการลงทุน" className="card-warm rounded-2xl p-5 md:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl gold-gradient">
            <Coins className="h-6 w-6 text-navy-deep" />
          </span>
          <div>
            <h2 className="font-display text-lg font-bold leading-tight md:text-xl">พอร์ตการลงทุนทองคำ</h2>
            <p className="text-xs text-muted-foreground">Gold Portfolio · อัปเดต {formatThaiDateLast(data)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-accent px-3 py-1.5 text-[11px] font-semibold text-accent-foreground">
            ตัวเลขนี้คือกำไรกระดาษ ยังไม่ใช่เงินในมือจนกว่าจะขาย
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-[1.25fr_1fr_1fr_1fr_auto]">
        {/* Value */}
        <div>
          <p className="text-xs font-medium text-muted-foreground">มูลค่าพอร์ตวันสุดท้ายของชุดข้อมูล</p>
          <p className="mt-1 font-display text-3xl font-bold tracking-tight md:text-[34px]">{formatBaht(s.portfolioValue)}</p>
          <p className={`mt-1 flex items-center gap-1 text-sm font-semibold ${loss ? 'text-loss' : 'text-gain'}`}>
            {loss ? <TrendingDown className="h-4 w-4" /> : <TrendingUp className="h-4 w-4" />}
            {formatPct(s.totalPlPct)} ({formatBaht(s.totalPl)})
          </p>
          <p className="mt-1 text-xs text-muted-foreground">จากเงินลงทุน {formatBaht(s.deposit)}</p>
        </div>
        {/* P/L */}
        <div className="rounded-2xl bg-muted/70 p-4">
          <p className="text-xs font-medium text-muted-foreground">กำไร/ขาดทุน (รวม)</p>
          <p className={`mt-1 font-display text-2xl font-bold ${loss ? 'text-loss' : 'text-gain'}`}>{formatBaht(s.totalPl)}</p>
          <p className={`mt-1 text-xs font-semibold ${loss ? 'text-loss' : 'text-gain'}`}>{formatPct(s.totalPlPct)}</p>
          <p className="mt-2 text-[11px] leading-snug text-muted-foreground">
            ยังไม่ขาย (ยังไม่รับรู้กำไร) {formatBaht(s.unrealizedPl)} · ขายแล้ว (รับรู้แล้ว) {formatBaht(s.realizedPl)}
          </p>
        </div>
        {/* Gold */}
        <div className="rounded-2xl bg-muted/70 p-4">
          <p className="text-xs font-medium text-muted-foreground">ทองคำในพอร์ต</p>
          <p className="mt-1 font-display text-2xl font-bold">{s.goldWeightPct.toFixed(1)}%</p>
          <p className="mt-1 text-xs text-muted-foreground">({formatBaht(s.goldValueThb)})</p>
          <p className="mt-2 text-[11px] text-muted-foreground">
            {s.goldOz} oz · ต้นทุนเฉลี่ย {formatBaht(s.avgCostThbPerOz)}/oz
          </p>
        </div>
        {/* Cash */}
        <div className="rounded-2xl bg-muted/70 p-4">
          <p className="text-xs font-medium text-muted-foreground">เงินสด</p>
          <p className="mt-1 font-display text-2xl font-bold">{s.cashWeightPct.toFixed(1)}%</p>
          <p className="mt-1 text-xs text-muted-foreground">({formatBaht(s.cash)})</p>
          <p className="mt-2 flex items-center gap-1 text-[11px] text-muted-foreground">
            <Wallet className="h-3 w-3" /> ไม่ได้รับดอกเบี้ย
          </p>
        </div>
        {/* Cat */}
        <div className="relative hidden h-full min-h-[150px] w-[150px] xl:block">
          <Image
            src="/gold/cat-hero.png"
            alt="แมววิเชียรมาสงุนงมหน้าทองคำ"
            fill
            unoptimized
            className="rounded-2xl object-cover"
            sizes="150px"
          />
        </div>
      </div>
    </section>
  );
}

function formatThaiDateLast(data: MarketPayload): string {
  const d = data.facts.lastDate;
  const [y, m, day] = d.split('-');
  const months = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
  return `${parseInt(day, 10)} ${months[parseInt(m, 10) - 1]} ${parseInt(y, 10) + 543}`;
}
