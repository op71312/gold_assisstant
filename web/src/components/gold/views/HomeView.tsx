'use client';

import Image from 'next/image';
import {
  ArrowRight,
  Wallet,
  MessageCircleMore,
  Landmark,
  ArrowDownRight,
  ArrowUpRight,
  Scale,
  Info,
} from 'lucide-react';
import { AGENT_META } from '../agent-meta';
import { ViewHeader, Sparkline } from './shared';
import { formatBaht, formatPct, formatThaiDate } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

interface HomeViewProps {
  data: MarketPayload;
  onGoTab: (id: string) => void;
  onAskSample: (q: string) => void;
}

/**
 * Home = 5-second answer screen (deep research: all 8 items).
 * Answers in one glance: มูลค่าเท่าไหร่ / ขึ้น-ลงแค่ไหน / อะไรเปลี่ยน / ควรทำอะไร,
 * anchored on the Thai shop board (ขายออก-รับซื้อ) with spread truth
 * and a plain-Thai "why" sentence. No jargon on the primary path.
 */
export function HomeView({ data, onGoTab, onAskSample }: HomeViewProps) {
  const snap = data.snapshot;
  const stats = data.stats;
  const facts = data.facts;
  const plTone = snap.totalPl >= 0 ? 'gain' : 'loss';
  const hour = new Date().getHours();
  const greet = hour < 12 ? 'สวัสดีตอนเช้า' : hour < 18 ? 'สวัสดีตอนบ่าย' : 'สวัสดีตอนเย็น';

  const seriesValues = data.series.map((p) => p.value);
  const invested = snap.portfolioValue - snap.totalPl;

  // Board price: both sides of the spread from the latest spot series row
  const lastSpotRow = data.spotSeries[data.spotSeries.length - 1];
  const barSell = lastSpotRow?.barSell ?? snap.barPriceNow;
  const barBuy = lastSpotRow?.barBuy ?? Math.round(snap.barPriceNow * 0.995);

  // "ถ้าขายวันนี้" sell-back estimate at the buyback side (spread truth)
  const sellBackEst = snap.goldOz * snap.pricePerOzThb * (barBuy / Math.max(barSell, 1));
  const spreadPerBaht = barSell - barBuy;

  // What changed: top market-moving news + macro anchor move
  const topNews = [...data.news].sort((a, b) => a.marketMovePct - b.marketMovePct).slice(0, 2);
  const macroLast = data.macro[data.macro.length - 1];
  const macroPrev = data.macro[data.macro.length - 2];
  const dxyMove = macroLast && macroPrev ? ((macroLast.dxy - macroPrev.dxy) / macroPrev.dxy) * 100 : null;

  // Plain-Thai "why" sentence, derived from the selected scenario + facts
  const whySentence = buildWhySentence(data, dxyMove);

  return (
    <div className="space-y-5">
      <ViewHeader title={`${greet} Gold Lover`} subtitle="คำตอบครบในหน้าเดียว: มูลค่า ขึ้น-ลง อะไรเปลี่ยน และควรทำอะไร" data={data} />

      {/* Answer card: the 4 questions in one glance */}
      <section className="card-warm rounded-2xl p-5 md:p-6">
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1.15fr_1fr]">
          <div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Wallet className="h-4 w-4 text-gold-deep" /> พอร์ตตัวอย่าง ณ วันล่าสุดในข้อมูล
            </div>
            <div className="mt-1 flex flex-wrap items-end gap-3">
              <span className="font-display text-3xl font-bold leading-none md:text-4xl">
                {formatBaht(snap.portfolioValue)}
              </span>
              <span
                className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${
                  plTone === 'gain' ? 'bg-gain/12 text-gain' : 'bg-loss/12 text-loss'
                }`}
              >
                {plTone === 'gain' ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
                {formatPct(snap.totalPlPct)} ({formatBaht(snap.totalPl)})
              </span>
            </div>
            <p className="mt-1.5 text-xs text-muted-foreground">
              เริ่มจากเงินลงทุน {formatBaht(invested)} · อัปเดตล่าสุด {formatThaiDate(facts.lastDate)}
            </p>

            {/* Plain-Thai why: answer first, evidence on tap */}
            <div className="mt-3 rounded-2xl bg-accent/50 px-3.5 py-3">
              <p className="text-[13px] font-semibold leading-relaxed text-accent-foreground">{whySentence}</p>
              <p className="mt-1 text-[11px] text-muted-foreground">
                สรุปจากทีมนักวิเคราะห์ 5 ตัว · ความเห็นเพื่อการศึกษา ไม่ใช่คำรับประกัน
              </p>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <button
                onClick={() => onAskSample('ทำไมพอร์ตเราถึงขาดทุน?')}
                className="inline-flex min-h-[44px] items-center gap-2 rounded-2xl gold-gradient px-4 py-2.5 text-sm font-bold text-navy-deep shadow transition-transform hover:scale-[1.02]"
              >
                <MessageCircleMore className="h-4 w-4" /> ให้ทีมช่วยวินิจฉัยพอร์ต
              </button>
              <button
                onClick={() => onGoTab('portfolio')}
                className="inline-flex min-h-[44px] items-center gap-1.5 rounded-2xl border border-gold/50 bg-white px-4 py-2.5 text-sm font-semibold text-accent-foreground transition-colors hover:bg-accent/50"
              >
                ดูรายละเอียดพอร์ต <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="rounded-2xl bg-muted/50 p-4">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-foreground/80">มูลค่าพอร์ตช่วงล่าสุด</span>
              <span className="text-muted-foreground">
                {formatBaht(seriesValues[0] ?? 0)} → {formatBaht(snap.portfolioValue)}
              </span>
            </div>
            <Sparkline
              values={seriesValues}
              height={92}
              stroke={plTone === 'gain' ? '#1F7A4D' : '#C23A3F'}
              fill={plTone === 'gain' ? 'rgba(31,122,77,0.14)' : 'rgba(194,58,63,0.14)'}
              className="mt-2"
            />
            <p className="mt-2 text-[11px] text-muted-foreground">
              ความผันผวนต่อปี {stats.volAnnPct.toFixed(1)}% · ห่างจุดสูงสุด {formatPct(facts.changeFromAthPct)}
            </p>
          </div>
        </div>
      </section>

      {/* Shop board + spread truth: the anchor of Thai gold world */}
      <section className="card-warm rounded-2xl p-5">
        <div className="mb-3 flex items-center gap-2">
          <Landmark className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">ป้ายราคาทองแท่งในชุดข้อมูล (บาททองคำ)</h3>
          <span className="ml-auto text-[11px] text-muted-foreground">ไม่ใช่ราคาสด</span>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <BoardCell label="ร้านขายให้คุณ (ขายออก)" value={barSell} tone="ink" />
          <BoardCell label="ร้านรับซื้อจากคุณ (รับซื้อ)" value={barBuy} tone="ink" />
          <BoardCell label="Spot โลก ($/oz)" value={Math.round(snap.spotNow)} tone="muted" prefix="$" />
          <BoardCell label="ค่าเงิน (บาท/USD)" value={Number(snap.fxNow.toFixed(2))} tone="muted" />
        </div>
        <div className="mt-3 flex flex-col gap-2 rounded-2xl bg-muted/60 px-3.5 py-3 text-[13px] leading-relaxed sm:flex-row sm:items-center sm:justify-between">
          <p className="font-semibold text-foreground/90">
            <Scale className="mr-1.5 inline h-4 w-4 text-gold-deep" />
            ถ้าขายทอง ({snap.goldOz.toFixed(2)} oz) ตามราคาล่าสุดในชุดข้อมูล จะได้ประมาณ <b className="text-gold-deep">{formatBaht(sellBackEst)}</b>
          </p>
          <p className="text-[11px] text-muted-foreground">
            ต่ำกว่าราคาที่ร้านขาย {spreadPerBaht.toLocaleString('en-US')} บาท/บาททอง จากส่วนต่างร้าน (รับซื้อต่ำกว่าขายออกเสมอ)
          </p>
        </div>
      </section>

      {/* What changed + suggested next */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.4fr_1fr]">
        <section className="card-warm rounded-2xl p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-display text-sm font-bold">อะไรเปลี่ยนบ้างตอนนี้</h3>
            <button onClick={() => onGoTab('news')} className="text-[11px] font-semibold text-gold-deep hover:underline">
              ดูข่าวทั้งหมด →
            </button>
          </div>
          <ul className="divide-y divide-border">
            {dxyMove !== null && (
              <li className="flex items-center justify-between gap-3 py-2.5 first:pt-0">
                <p className="min-w-0 text-[13px] font-semibold leading-snug">
                  ค่าเงินดอลลาร์ {dxyMove >= 0 ? 'แข็งค่าขึ้น' : 'อ่อนค่าลง'} {Math.abs(dxyMove).toFixed(1)}% ตั้งแต่รอบก่อน
                  <span className="block text-[11px] font-normal text-muted-foreground">ดอลลาร์แข็งมักกดทอง · อ่อนมักหนุนทอง</span>
                </p>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-bold ${dxyMove > 0 ? 'bg-loss/12 text-loss' : 'bg-gain/12 text-gain'}`}>
                  DXY {dxyMove > 0 ? '+' : ''}{dxyMove.toFixed(1)}%
                </span>
              </li>
            )}
            {topNews.map((n) => (
              <li key={n.date + n.title} className="py-2.5 first:pt-0">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[13px] font-semibold leading-snug">{n.title}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">{n.source} · {formatThaiDate(n.date)}</p>
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-bold ${
                      n.marketMovePct > 2 ? 'bg-gain/12 text-gain' : n.marketMovePct < -2 ? 'bg-loss/12 text-loss' : 'bg-muted text-muted-foreground'
                    }`}
                  >
                    ทอง {formatPct(n.marketMovePct)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="card-warm rounded-2xl p-5">
          <div className="mb-2 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-lg gold-gradient text-[11px] font-bold text-navy-deep">5</span>
            <h3 className="font-display text-sm font-bold">ทีมนักวิเคราะห์ 5 ตัวช่วยอะไรได้</h3>
          </div>
          <ul className="divide-y divide-border">
            {AGENT_META.map((a) => (
              <li key={a.id} className="flex items-center gap-2.5 py-2 first:pt-0">
                <img
                  src={a.avatar}
                  alt=""
                  className="h-9 w-9 shrink-0 rounded-full object-cover ring-2 ring-offset-1"
                  style={{ backgroundColor: `${a.color}22`, ['--tw-ring-color' as string]: a.color }}
                />
                <span className="min-w-0">
                  <span className="block text-xs font-semibold">{a.name}</span>
                  <span className="block text-[11px] leading-snug text-muted-foreground">{a.takeaway}</span>
                </span>
              </li>
            ))}
          </ul>
          <button
            onClick={() => onGoTab('assistant')}
            className="mt-3 min-h-[44px] w-full rounded-2xl border border-gold/50 bg-accent/60 py-2.5 text-xs font-bold text-accent-foreground transition-colors hover:bg-accent"
          >
            เปิดห้องทำงานดูทั้ง 5 ตัวทำงานร่วมกัน
          </button>
        </section>
      </div>

      {/* Trust strip: visible disclaimer on the money screen */}
      <p className="flex items-start gap-1.5 px-1 text-[11px] leading-relaxed text-muted-foreground">
        <Info className="mt-0.5 h-3 w-3 shrink-0" />
        ข้อมูลทั้งหมดเป็นการจำลองเพื่อการศึกษาจากชุดข้อมูลราคาจริง คำวิเคราะห์ของทีมเป็นความเห็น ไม่ใช่คำแนะนำการลงทุน ตรวจสอบก่อนตัดสินใจเสมอ
      </p>
    </div>
  );
}

function BoardCell({ label, value, tone, prefix }: { label: string; value: number; tone: 'ink' | 'muted'; prefix?: string }) {
  return (
    <div className={`rounded-2xl px-3 py-2.5 ${tone === 'ink' ? 'bg-white ring-1 ring-border' : 'bg-muted/50'}`}>
      <div className="text-[11px] font-medium leading-snug text-muted-foreground">{label}</div>
      <div className="mt-0.5 font-display text-xl font-bold tabular-nums leading-tight md:text-2xl">
        {prefix}
        {value.toLocaleString('en-US')}
      </div>
    </div>
  );
}

/** ประโยค "ทำไมถึงเป็นแบบนี้" ภาษาคน ประกอบจากข้อมูลของสถานการณ์ที่เลือก */
function buildWhySentence(data: MarketPayload, dxyMove: number | null): string {
  const snap = data.snapshot;
  const losing = snap.totalPl < 0;
  const fromAth = Math.abs(data.facts.changeFromAthPct);
  const fxPart = dxyMove === null ? '' : dxyMove > 0 ? ' ดอลลาร์ล่าสุดแข็งค่าขึ้น ซึ่งมักกดราคาทอง' : ' ดอลลาร์ล่าสุดอ่อนค่า ซึ่งมักหนุนราคาทอง';

  if (!losing) {
    return `พอร์ตของคุณกำไรอยู่ ${formatPct(snap.totalPlPct)} มาจากราคาทองบวกเป็นหลัก${fxPart} ทีมนักวิเคราะห์ช่วยดูว่าควรถือต่อหรือทำกำไรบางส่วน`;
  }
  if (fromAth >= 10) {
    return `พอร์ตขาดทุน ${formatPct(snap.totalPlPct)} เพราะราคาทองย่อจากจุดสูงสุดไป ${fromAth.toFixed(0)}% ตามตัวเลขจริงในชุดข้อมูล${fxPart} ลองให้ทีมช่วยวิเคราะห์ว่าจังหวะซื้อ-ขายที่ผ่านมากัดกำไรแค่ไหน`;
  }
  return `พอร์ตขาดทุน ${formatPct(snap.totalPlPct)} ส่วนใหญ่มาจากจังหวะซื้อขายและส่วนต่างร้าน มากกว่าทิศทางราคาทองเอง${fxPart} ให้ทีมช่วยชี้จุดที่กัดกำไรมากที่สุด`;
}
