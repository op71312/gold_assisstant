'use client';

import { useState } from 'react';
import { Globe2, Coins, DollarSign, CalendarClock, Clock3, Landmark } from 'lucide-react';
import { ViewHeader, Sparkline, StatCell } from './shared';
import { formatPct, formatThaiDate } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

const RANGES = [
  { id: '1M', days: 31 },
  { id: '3M', days: 92 },
  { id: '6M', days: 183 },
  { id: '1Y', days: 365 },
] as const;

export function MarketView({ data }: { data: MarketPayload }) {
  const [range, setRange] = useState<(typeof RANGES)[number]['id']>('3M');
  const facts = data.facts;
  const all = data.spotSeries;
  const days = RANGES.find((r) => r.id === range)?.days ?? 92;
  const slice = all.slice(-days);
  const thbSeries = slice.map((p) => p.spot * p.fx);
  const first = slice[0];
  const last = slice[slice.length - 1];
  const chgPct = first ? ((last.spot - first.spot) / first.spot) * 100 : 0;
  const thbChgPct = first ? (thbSeries[thbSeries.length - 1] / thbSeries[0] - 1) * 100 : 0;

  const monthly = [...data.monthly].slice(-12).reverse();
  const intraday = data.intraday;

  return (
    <div className="space-y-5">
      <ViewHeader
        title="ข้อมูลตลาดทองคำ"
        subtitle="ราคา Spot XAU/USD, ค่าเงินบาท, ราคาทองแท่งในไทย และตัวแปรมหภาค (DXY / ดอกเบี้ย / น้ำมัน) ประกอบการวินิจฉัยของทีมนักวิเคราะห์"
        data={data}
      />

      {/* Top stats (plain-Thai gloss under every anchor number) */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCell label="Spot XAU/USD (ทองโลก)" value={`$${facts.lastSpot.toLocaleString('en-US')}`} delta={`ห่าง ATH ${formatPct(facts.changeFromAthPct)}`} tone={facts.changeFromAthPct >= 0 ? 'gain' : 'loss'} note="ราคาตลาดโลกดอลลาร์ ยังไม่รวมค่าเงินบาท" />
        <StatCell label="USD/THB (ค่าเงินบาท)" value={facts.lastFx.toFixed(2)} delta="บาทอ่อน = ทองบาทแพงขึ้น" tone="neutral" note="บาทอ่อนทำให้ทองไทยแพงขึ้นแม้ทองโลกนิ่ง" />
        <StatCell label="ทองแท่งร้านค้า (ขายออก)" value={`${facts.lastBarSell.toLocaleString('en-US')} ฿`} delta={`ห่างจุดสูงสุด ${formatPct(facts.barFromAthPct)}`} tone="neutral" note="ราคาที่ร้านขายให้คุณต่อ 1 บาททอง" />
        <StatCell label="จุดสูงสุดในชุดข้อมูล (ATH)" value={`$${facts.athSpot.toLocaleString('en-US')}`} delta={formatThaiDate(facts.athDate)} tone="neutral" note="ราคาสูงสุดที่เคยไปถึงในช่วงข้อมูล" />
      </div>
      <p className="-mt-2 px-1 text-[11px] text-muted-foreground">ข้อมูลย้อนหลังถึง {formatThaiDate(facts.lastDate)} · ไม่ใช่ฟีดราคาแบบสด</p>

      {/* Spot chart */}
      <section className="card-warm rounded-2xl p-5">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Coins className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">ราคาทองคำ (บาท/ออนซ์ = spot × FX)</h3>
          <div className="ml-auto flex gap-1.5">
            {RANGES.map((r) => (
              <button
                key={r.id}
                onClick={() => setRange(r.id)}
                className={`rounded-full px-3 py-1 text-[11px] font-bold transition-colors ${
                  range === r.id ? 'gold-gradient text-navy-deep' : 'bg-muted/70 text-muted-foreground hover:bg-muted'
                }`}
              >
                {r.id}
              </button>
            ))}
          </div>
        </div>
        <Sparkline values={thbSeries} height={150} stroke="#D9A441" fill="rgba(217,164,65,0.18)" />
        <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
          <span>{formatThaiDate(first?.date ?? '')} → {formatThaiDate(last?.date ?? '')}</span>
          <span>
            USD {formatPct(chgPct)} · บาท {formatPct(thbChgPct)}
            <span className="ml-2 rounded-full bg-muted px-2 py-0.5">ส่วนต่าง FX {(thbChgPct - chgPct).toFixed(1)} จุด</span>
          </span>
        </div>
      </section>

      {/* Macro + intraday */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.3fr_1fr]">
        <section className="card-warm rounded-2xl p-5">
          <div className="mb-3 flex items-center gap-2">
            <Landmark className="h-4 w-4 text-gold-deep" />
            <h3 className="font-display text-sm font-bold">ตัวแปรมหภาค (Macro Anchors)</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[420px] text-left text-xs">
              <thead>
                <tr className="border-b border-border text-[11px] uppercase tracking-wide text-muted-foreground">
                  <th className="py-2 pr-3 font-semibold">วันที่</th>
                  <th className="py-2 pr-3 text-right font-semibold">DXY</th>
                  <th className="py-2 pr-3 text-right font-semibold">US 10Y (%)</th>
                  <th className="py-2 text-right font-semibold">WTI ($)</th>
                </tr>
              </thead>
              <tbody>
                {data.macro.map((m, i) => {
                  const prev = data.macro[i - 1];
                  const dxyChg = prev ? ((m.dxy - prev.dxy) / prev.dxy) * 100 : null;
                  return (
                    <tr key={m.date} className="border-b border-border/60 last:border-0">
                      <td className="py-2.5 pr-3 font-medium">{formatThaiDate(m.date)}</td>
                      <td className="py-2.5 pr-3 text-right">
                        {m.dxy.toFixed(2)}
                        {dxyChg !== null && (
                          <span className={`ml-1.5 text-[11px] font-semibold ${dxyChg > 0 ? 'text-loss' : 'text-gain'}`}>{formatPct(dxyChg)}</span>
                        )}
                      </td>
                      <td className="py-2.5 pr-3 text-right">{m.us10y.toFixed(2)}</td>
                      <td className="py-2.5 text-right">{m.wti.toFixed(1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-2.5 flex items-start gap-1.5 text-[11px] leading-relaxed text-muted-foreground">
            <Globe2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            กฎมือใหม่: ดอลลาร์แข็ง (DXY ขึ้น) + ดอกเบี้ยสูง = กดทอง · ความตึงเครียดด้านพลังงาน (WTI พุ่ง) มักหนุนทองในฐานะสินทรัพย์กันเงินเฟ้อ
          </p>
        </section>

        <section className="card-warm rounded-2xl p-5">
          <div className="mb-3 flex items-center gap-2">
            <Clock3 className="h-4 w-4 text-gold-deep" />
            <h3 className="font-display text-sm font-bold">ข้อมูลระหว่างวันตัวอย่าง (Intraday)</h3>
          </div>
          <ul className="nice-scroll max-h-[260px] space-y-1.5 overflow-y-auto pr-1">
            {intraday.map((p, i) => {
              const prev = intraday[i - 1];
              const d = prev ? ((p.spot - prev.spot) / prev.spot) * 100 : 0;
              return (
                <li key={p.t} className="flex items-center justify-between rounded-xl bg-muted/60 px-3 py-2 text-xs">
                  <span className="font-mono text-[11px] text-muted-foreground">{p.t}</span>
                  <span className="font-semibold">${p.spot.toFixed(1)}</span>
                  <span className="font-semibold text-foreground/85">{p.barSell.toLocaleString('en-US')} ฿</span>
                  <span className={`w-14 text-right text-[11px] font-bold ${(d ?? 0) > 0 ? 'text-gain' : (d ?? 0) < 0 ? 'text-loss' : 'text-muted-foreground'}`}>
                    {(d ?? 0) !== 0 ? formatPct(d) : '-'}
                  </span>
                </li>
              );
            })}
          </ul>
          <p className="mt-2 flex items-center gap-1.5 text-[11px] text-muted-foreground">
            <CalendarClock className="h-3 w-3" /> จำลองจากวันทำการล่าสุดในชุดข้อมูล ({formatThaiDate(facts.lastDate)})
          </p>
        </section>
      </div>

      {/* Monthly table */}
      <section className="card-warm rounded-2xl p-5">
        <div className="mb-3 flex items-center gap-2">
          <DollarSign className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">ราคาทองรายเดือน (สูง-ต่ำ-ปิด) 12 เดือนล่าสุด</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-xs">
            <thead>
              <tr className="border-b border-border text-[11px] uppercase tracking-wide text-muted-foreground">
                <th className="py-2 pr-3 font-semibold">เดือน</th>
                <th className="py-2 pr-3 text-right font-semibold">สูงสุด ($)</th>
                <th className="py-2 pr-3 text-right font-semibold">ต่ำสุด ($)</th>
                <th className="py-2 pr-3 text-right font-semibold">ปิด ($)</th>
                <th className="py-2 pr-3 text-right font-semibold">USD/THB</th>
                <th className="py-2 text-right font-semibold">ปิดเป็นบาท/oz</th>
              </tr>
            </thead>
            <tbody>
              {monthly.map((m) => {
                const thb = m.last_spot * m.last_fx;
                const prev = monthly[monthly.indexOf(m) + 1];
                const chg = prev ? ((m.last_spot - prev.last_spot) / prev.last_spot) * 100 : null;
                return (
                  <tr key={m.date} className="border-b border-border/60 last:border-0">
                    <td className="py-2.5 pr-3 font-medium">{formatThaiDate(m.date)}</td>
                    <td className="py-2.5 pr-3 text-right">{m.hi.toLocaleString('en-US')}</td>
                    <td className="py-2.5 pr-3 text-right">{m.lo.toLocaleString('en-US')}</td>
                    <td className="py-2.5 pr-3 text-right font-semibold">
                      {m.last_spot.toLocaleString('en-US')}
                      {chg !== null && (
                        <span className={`ml-1.5 text-[11px] font-bold ${chg > 0 ? 'text-gain' : 'text-loss'}`}>{formatPct(chg)}</span>
                      )}
                    </td>
                    <td className="py-2.5 pr-3 text-right">{m.last_fx.toFixed(2)}</td>
                    <td className="py-2.5 text-right font-semibold text-gold-deep">{Math.round(thb).toLocaleString('en-US')}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
