'use client';

import { Sigma, TrendingDown, Layers, Gauge, GitCompareArrows } from 'lucide-react';
import { ViewHeader, ReturnBars, DrawdownChart, StatCell } from './shared';
import { formatBaht, formatPct } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

export function AnalysisView({ data }: { data: MarketPayload }) {
  const stats = data.stats;
  const snap = data.snapshot;

  // Drawdown series of the portfolio (client-side from value series)
  const dd: number[] = [];
  let peak = -Infinity;
  for (const p of data.series) {
    peak = Math.max(peak, p.value);
    dd.push(((p.value - peak) / peak) * 100);
  }
  const finalValue = data.series[data.series.length - 1]?.value ?? snap.portfolioValue;
  const benchFinal = data.series[data.series.length - 1]?.gold ?? snap.deposit;
  const benchRet = (benchFinal / snap.deposit - 1) * 100;
  const gapPct = snap.totalPlPct - benchRet;
  const negMonths = stats.monthlyReturns.filter((m) => m.ret < 0).length;
  const best = [...stats.monthlyReturns].sort((a, b) => b.ret - a.ret)[0];
  const worst = [...stats.monthlyReturns].sort((a, b) => a.ret - b.ret)[0];
  const strat = data.strategyCompare;

  return (
    <div className="space-y-5">
      <ViewHeader
        title="วิเคราะห์พอร์ตเชิงลึก"
        subtitle="ผลตอบแทนรายเดือน, ความเสี่ยง, Behavior Gap และการเทียบกลยุทธ์ คำนวณจากข้อมูลจริงในสถานการณ์ที่เลือก"
        data={data}
      />

      {/* Stat grid (each number carries a one-line plain-Thai gloss) */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCell label="ผลตอบแทนพอร์ต (รวม)" value={formatPct(snap.totalPlPct)} tone={snap.totalPlPct >= 0 ? 'gain' : 'loss'} delta={formatBaht(snap.totalPl)} note="กำไรหรือขาดทุนทั้งพอร์ต นับถึงวันล่าสุด" />
        <StatCell label="ถือยาวแบบไม่แตะ (เบนช์มาร์ก)" value={formatPct(benchRet)} tone={benchRet >= 0 ? 'gain' : 'loss'} delta={formatBaht(benchFinal)} note="ถ้าซื้อครั้งแรกแล้วไม่แตะเลยจะเป็นเท่านี้" />
        <StatCell label="Behavior Gap" value={formatPct(gapPct)} tone={Math.abs(gapPct) < 1 ? 'neutral' : 'loss'} delta="ราคาของการตัดสินใจซื้อ-ขาย" note="ส่วนที่พลาดไปเพราะซื้อ-ขายเอง เทียบกับการถือยาว" />
        <StatCell label="ความผันผวนต่อปี" value={`${stats.volAnnPct.toFixed(1)}%`} tone="neutral" delta={`HHI รวมศูนย์ ${stats.hhi.toFixed(2)}`} note="ราคาแกว่งกว้างแค่ไหนต่อปี ยิ่งสูงยิ่งหลอน" />
      </div>

      {/* Monthly returns */}
      <section className="card-warm rounded-2xl p-5">
        <div className="mb-2 flex items-center gap-2">
          <Sigma className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">ผลตอบแทนรายเดือนของพอร์ต</h3>
          <span className="ml-auto text-[11px] text-muted-foreground">
            ติดลบ {negMonths}/{stats.monthlyReturns.length} เดือน
            {best && <> · ดีสุด <b className="text-gain">{best.month} {formatPct(best.ret)}</b></>}
            {worst && <> · แย่สุด <b className="text-loss">{worst.month} {formatPct(worst.ret)}</b></>}
          </span>
        </div>
        <ReturnBars data={stats.monthlyReturns} height={160} />
      </section>

      {/* Drawdown + risk */}
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.5fr_1fr]">
        <section className="card-warm rounded-2xl p-5">
          <div className="mb-2 flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-loss" />
            <h3 className="font-display text-sm font-bold">ความลึกของการขาดทุน (Drawdown)</h3>
          </div>
          <DrawdownChart values={dd} height={140} />
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
            วูบลึกสุด <b className="text-loss">{formatPct(stats.maxDrawdownPct)}</b>
            {stats.maxDrawdownSpan && (
              <> ช่วง {stats.maxDrawdownSpan[0]} → {stats.maxDrawdownSpan[1]} คือช่วงที่พอร์ตห่างจากจุดสูงสุดมากที่สุด ถ้าขายในจุดนี้จะเปลี่ยนขาดทุนกระดาษเป็นขาดทุนจริง</>
            )}
          </p>
        </section>

        <section className="card-warm rounded-2xl p-5">
          <div className="mb-3 flex items-center gap-2">
            <Gauge className="h-4 w-4 text-gold-deep" />
            <h3 className="font-display text-sm font-bold">สถิติความเสี่ยงหลัก</h3>
          </div>
          <ul className="space-y-2 text-xs">
            <RiskRow label="Max Drawdown (วูบลึกสุด)" value={formatPct(stats.maxDrawdownPct)} tone="loss" note="จากจุดสูงสุด พอร์ตเคยหายไปมากที่สุดเท่านี้" />
            <RiskRow label="Volatility (ความผันผวนต่อปี)" value={`${stats.volAnnPct.toFixed(1)}%`} note="ราคาวันต่อวันแกว่งกว้างแค่ไหน" />
            <RiskRow label="corr(พอร์ต, ทองถือยาว)" value={stats.corrPfBench.toFixed(2)} note="1.00 = พอร์ตขยับตามการถือทองยาวทุกอย่าง" />
            <RiskRow label="corr(ทอง, DXY)" value={stats.corrGoldDxy.toFixed(2)} note="ค่าติดลบ = ดอลลาร์แข็งกดทอง" />
            <RiskRow label="รวมศูนย์ทอง (HHI)" value={stats.hhi.toFixed(2)} note="ยิ่งสูงยิ่งพึ่งสินทรัพย์เดียว" />
            <RiskRow label="น้ำหนักทองปัจจุบัน" value={`${snap.goldWeightPct.toFixed(1)}%`} />
          </ul>
        </section>
      </div>

      {/* Strategy compare */}
      {strat && strat.length > 0 && (
        <section className="card-warm rounded-2xl p-5">
          <div className="mb-3 flex items-center gap-2">
            <GitCompareArrows className="h-4 w-4 text-gold-deep" />
            <h3 className="font-display text-sm font-bold">เทียบกลยุทธ์: ถ้าทำแบบอื่นจะเป็นอย่างไร</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-xs">
              <thead>
                <tr className="border-b border-border text-[11px] uppercase tracking-wide text-muted-foreground">
                  <th className="py-2 pr-3 font-semibold">กลยุทธ์</th>
                  <th className="py-2 pr-3 text-right font-semibold">มูลค่าสุดท้าย</th>
                  <th className="py-2 pr-3 text-right font-semibold">กำไร/ขาดทุน</th>
                  <th className="py-2 pr-3 text-right font-semibold">%</th>
                  <th className="py-2 font-semibold">หมายเหตุ</th>
                </tr>
              </thead>
              <tbody>
                {strat.map((s) => (
                  <tr
                    key={s.name}
                    className={`border-b border-border/60 last:border-0 ${s.highlight ? 'bg-accent/60 font-semibold' : ''}`}
                  >
                    <td className="py-2.5 pr-3">
                      {s.name}
                      {s.highlight && <span className="ml-1.5 rounded-full bg-gain/15 px-1.5 py-0.5 text-[11px] font-bold text-gain">แนะนำ</span>}
                    </td>
                    <td className="py-2.5 pr-3 text-right">{formatBaht(s.finalValue)}</td>
                    <td className={`py-2.5 pr-3 text-right ${s.pl >= 0 ? 'text-gain' : 'text-loss'}`}>{formatBaht(s.pl)}</td>
                    <td className={`py-2.5 pr-3 text-right ${s.plPct >= 0 ? 'text-gain' : 'text-loss'}`}>{formatPct(s.plPct)}</td>
                    <td className="py-2.5 text-[11px] text-muted-foreground">{s.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Reading guide: short bullets instead of a wall of text */}
      <section className="rounded-2xl border border-gold/40 bg-accent/50 p-4">
        <div className="flex items-start gap-2.5">
          <Layers className="mt-0.5 h-4 w-4 shrink-0 text-gold-deep" />
          <div className="text-xs leading-relaxed text-accent-foreground">
            <p className="font-semibold">อ่านตัวเลขชุดนี้อย่างไร</p>
            <ul className="mt-1 space-y-0.5">
              <li>• Behavior Gap กว้าง = จังหวะซื้อ-ขายของเรากำลังกัดผลตอบแทน ไม่ใช่ทองไม่ดี</li>
              <li>• HHI และน้ำหนักทองสูง = พอร์ตไวต่อวงจรดอลลาร์/ดอกเบี้ยเป็นพิเศษ</li>
              <li>• ทุกตัวเลขคำนวณจากราคาประกาศรายวันของสถานการณ์ที่เลือกเท่านั้น</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}

function RiskRow({ label, value, tone, note }: { label: string; value: string; tone?: 'loss'; note?: string }) {
  return (
    <li className="flex items-center justify-between gap-2 rounded-xl bg-muted/60 px-3 py-2">
      <span className="min-w-0">
        <span className="block font-semibold text-foreground/85">{label}</span>
        {note && <span className="block text-[11px] leading-snug text-muted-foreground">{note}</span>}
      </span>
      <span className={`shrink-0 font-display text-sm font-bold ${tone === 'loss' ? 'text-loss' : 'text-foreground'}`}>{value}</span>
    </li>
  );
}
