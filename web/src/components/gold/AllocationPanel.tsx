'use client';

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { ShieldAlert, Scale } from 'lucide-react';
import { formatBaht, formatPct } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

export function AllocationPanel({ data }: { data: MarketPayload }) {
  const s = data.snapshot;
  const donut = [
    { name: 'ทองคำ', value: s.goldWeightPct, color: '#d9a441' },
    { name: 'เงินสด', value: s.cashWeightPct, color: '#7fb8a4' },
  ];

  return (
    <div className="flex flex-col gap-4">
      {/* Donut */}
      <section aria-label="สัดส่วนการลงทุน" className="card-warm rounded-2xl p-5">
        <h3 className="mb-1 font-display text-sm font-bold">สัดส่วนการลงทุน</h3>
        <div className="relative h-[150px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={donut}
                dataKey="value"
                innerRadius={48}
                outerRadius={66}
                paddingAngle={3}
                strokeWidth={0}
                startAngle={90}
                endAngle={-270}
              >
                {donut.map((d) => (
                  <Cell key={d.name} fill={d.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(v: number, n: string) => [`${v.toFixed(1)}%`, n]}
                contentStyle={{ borderRadius: 12, border: '1px solid #ece1c8', fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-display text-xl font-bold">{s.goldWeightPct.toFixed(1)}%</span>
            <span className="text-[11px] text-muted-foreground">ทองคำ</span>
          </div>
        </div>
        <ul className="mt-1 space-y-1.5">
          {donut.map((d) => (
            <li key={d.name} className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 font-medium">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                {d.name}
              </span>
              <span className="font-semibold">{d.value.toFixed(1)}%</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Details */}
      <section aria-label="ข้อมูลพอร์ตโดยละเอียด" className="card-warm rounded-2xl p-5">
        <h3 className="mb-3 font-display text-sm font-bold">ข้อมูลพอร์ตโดยละเอียด</h3>
        <dl className="space-y-2.5 text-xs">
          <Row label="จำนวนทองคำสุทธิ" value={`${s.goldOz} oz`} />
          <Row label="ต้นทุนเฉลี่ยต่อออนซ์" value={formatBaht(s.avgCostThbPerOz)} />
          <Row label="มูลค่าทองต่อออนซ์ (บาท)" value={formatBaht(s.pricePerOzThb)} />
          <Row label="ราคาทองแท่งไทย (ขายออก)" value={`${s.barPriceNow.toLocaleString('en-US')} ฿/บาททอง`} />
          <Row label="ราคา Spot (USD/oz)" value={`$${s.spotNow.toLocaleString('en-US')}`} />
          <Row label="อัตราแลกเปลี่ยน" value={`${s.fxNow.toFixed(2)} ฿/USD`} />
        </dl>
      </section>

      {/* Signal */}
      <section aria-label="สัญญาณตลาดล่าสุด" className="card-warm rounded-2xl p-5">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-display text-sm font-bold">สัญญาณตลาดล่าสุด</h3>
          <span
            className={`rounded-full px-3 py-1 text-[11px] font-bold text-white ${
              data.scenario.signal.tone === 'risk-off' ? 'bg-loss' : data.scenario.signal.tone === 'risk-on' ? 'bg-gain' : 'bg-chart-4'
            }`}
          >
            {data.scenario.signal.label}
          </span>
        </div>
        <p className="text-xs leading-relaxed text-muted-foreground">
          ความผันผวนพอร์ต {data.stats.volAnnPct}%/ปี · MDD {data.stats.maxDrawdownPct}% · ความสัมพันธ์ทอง-DXY {data.stats.corrGoldDxy}
        </p>
        <div className="mt-3 flex items-start gap-2 rounded-2xl bg-accent/70 p-3">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-gold-deep" />
          <p className="text-[11px] leading-relaxed text-accent-foreground">
            ตลาดผันผวนช่วงปรับฐาน ตรวจสอบสัดส่วนความเสี่ยงก่อนตัดสินใจเพิ่มน้ำหนักทอง
          </p>
        </div>
      </section>

      {/* Strategy compare (behavior scenario only) */}
      {data.strategyCompare && (
        <section aria-label="เปรียบเทียบกลยุทธ์" className="card-warm rounded-2xl p-5">
          <h3 className="mb-1 flex items-center gap-1.5 font-display text-sm font-bold">
            <Scale className="h-4 w-4 text-gold-deep" /> เปรียบเทียบ 3 กลยุทธ์
          </h3>
          <p className="mb-3 text-[11px] text-muted-foreground">เงินลงทุนเดียวกัน ราคาเดียวกัน คนละพฤติกรรม</p>
          <ul className="space-y-2">
            {data.strategyCompare.map((r) => (
              <li
                key={r.name}
                className={`rounded-2xl border p-3 ${r.highlight ? 'border-gold bg-accent/60' : 'border-transparent bg-muted/50'}`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold">{r.name}</span>
                  <span className={`font-display text-sm font-bold ${r.pl < 0 ? 'text-loss' : 'text-gain'}`}>
                    {formatPct(r.plPct)}
                  </span>
                </div>
                <div className="mt-1 flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>มูลค่า {formatBaht(r.finalValue)}</span>
                  <span className={r.pl < 0 ? 'text-loss' : 'text-gain'}>{formatBaht(r.pl, true)}</span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-2 last:border-0 last:pb-0">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-semibold">{value}</dd>
    </div>
  );
}
