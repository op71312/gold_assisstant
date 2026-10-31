'use client';

import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ReferenceLine,
} from 'recharts';
import { formatBahtShort, formatThaiDate } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

export const RANGES = ['1D', '1W', '1M', '3M', '6M', '1Y', 'ALL'] as const;
export type ChartRange = (typeof RANGES)[number];

interface PriceChartProps {
  data: MarketPayload;
  range: ChartRange;
  onRangeChange: (r: ChartRange) => void;
}

export function PriceChart({ data, range, onRangeChange }: PriceChartProps) {
  const series = useMemo(
    () =>
      data.series.map((p) => ({
        ...p,
        label: range === '1D' ? p.date : formatThaiDate(p.date),
      })),
    [data.series, range],
  );

  const first = series[0]?.value ?? 0;
  const last = series[series.length - 1]?.value ?? 0;
  const chgPct = first ? ((last - first) / first) * 100 : 0;
  // Total invested capital = current value minus total P/L (deep research: DCA segment
  // wants the average-cost anchor visible on the chart, not just in a KPI cell)
  const invested = data.snapshot.portfolioValue - data.snapshot.totalPl;

  return (
    <section aria-label="กราฟมูลค่าพอร์ต" className="card-warm rounded-2xl p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-display text-sm font-bold">มูลค่าพอร์ต</h3>
          <p className="text-xs text-muted-foreground">
            {formatBahtShort(last)} บาท · {range === '1D' ? `วันล่าสุด ${formatThaiDate(data.facts.lastDate)}` : `ช่วง ${range}`}{' '}
            <span className={chgPct >= 0 ? 'font-semibold text-gain' : 'font-semibold text-loss'}>
              {chgPct >= 0 ? '+' : ''}
              {chgPct.toFixed(2)}%
            </span>{' '}
            · เส้นประเข้ม = ถือยาวไม่แตะต้อง · เส้นทอง = ต้นทุนรวม
          </p>
        </div>
        <div className="flex rounded-full bg-muted p-1" role="tablist" aria-label="ช่วงเวลา">
          {RANGES.map((r) => (
            <button
              key={r}
              role="tab"
              aria-selected={range === r}
              onClick={() => onRangeChange(r)}
              className={`rounded-full px-2.5 py-1 text-[11px] font-semibold transition-all ${
                range === r ? 'bg-primary text-primary-foreground shadow' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="h-[260px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={series} margin={{ top: 5, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="goldFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#e9bc57" stopOpacity={0.55} />
                <stop offset="100%" stopColor="#f7e3b0" stopOpacity={0.08} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ece1c8" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: '#8b8474' }}
              interval="preserveStartEnd"
              minTickGap={40}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#8b8474' }}
              tickFormatter={(v: number) => formatBahtShort(v)}
              axisLine={false}
              tickLine={false}
              width={52}
              domain={['auto', 'auto']}
            />
            <Tooltip
              formatter={(value: number, name: string) =>
                name === 'value'
                  ? [`${value.toLocaleString('en-US')} ฿`, 'พอร์ต']
                  : [`${value.toLocaleString('en-US')} ฿`, 'ถือยาว']
              }
              labelStyle={{ fontSize: 11, fontWeight: 600 }}
              contentStyle={{
                borderRadius: 14,
                border: '1px solid #ece1c8',
                fontSize: 12,
                boxShadow: '0 4px 16px rgba(178,138,52,.12)',
              }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#d9a441"
              strokeWidth={2.2}
              fill="url(#goldFill)"
              dot={false}
              activeDot={{ r: 4, fill: '#b8860b' }}
              name="value"
            />
            <Line type="monotone" dataKey="gold" stroke="#1c2942" strokeWidth={1.4} strokeDasharray="5 4" dot={false} name="gold" opacity={0.55} />
            <ReferenceLine
              y={invested}
              stroke="#96690C"
              strokeDasharray="6 4"
              strokeWidth={1.2}
              label={{
                value: `เส้นต้นทุนรวม ${invested.toLocaleString('en-US')} ฿ (ขึ้นเหนือเส้น = กำไร)`,
                position: 'insideTopLeft',
                fontSize: 10,
                fill: '#96690C',
                fontWeight: 600,
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
