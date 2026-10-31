'use client';

import { ArrowUpRight, ArrowDownRight, CheckCircle2, ArrowRight } from 'lucide-react';
import { formatBaht, formatThaiDate } from '@/lib/gold/format';
import type { MarketPayload } from '@/lib/gold/payload';

export function TransactionsTable({ data }: { data: MarketPayload }) {
  const rows = [...data.transactions].reverse().slice(0, 8);

  return (
    <section aria-label="รายการธุรกรรมล่าสุด" className="card-warm rounded-2xl p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display text-sm font-bold">รายการธุรกรรมล่าสุด</h3>
        <button className="flex items-center gap-1 text-xs font-semibold text-gold-deep hover:underline">
          ดูรายการทั้งหมด <ArrowRight className="h-3 w-3" />
        </button>
      </div>

      <div className="nice-scroll overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-xs">
          <thead>
            <tr className="border-b border-border text-[11px] uppercase tracking-wide text-muted-foreground">
              <th className="py-2 pr-3 font-medium">วันที่</th>
              <th className="py-2 pr-3 font-medium">ประเภท</th>
              <th className="py-2 pr-3 font-medium">รายการ</th>
              <th className="py-2 pr-3 text-right font-medium">จำนวน</th>
              <th className="py-2 pr-3 text-right font-medium">ราคารวม (฿)</th>
              <th className="py-2 pr-3 text-right font-medium">ผล (฿)</th>
              <th className="py-2 text-right font-medium">สถานะ</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.id} className="border-b border-border/50 last:border-0 hover:bg-muted/50">
                <td className="py-2.5 pr-3 font-medium">{formatThaiDate(t.date)}</td>
                <td className="py-2.5 pr-3">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-bold ${
                      t.side === 'BUY' ? 'bg-gain/12 text-gain' : 'bg-loss/12 text-loss'
                    }`}
                  >
                    {t.side === 'BUY' ? <ArrowDownRight className="h-3 w-3" /> : <ArrowUpRight className="h-3 w-3" />}
                    {t.side === 'BUY' ? 'ซื้อ' : 'ขาย'}
                  </span>
                </td>
                <td className="py-2.5 pr-3">
                  <span className="font-medium">ทองคำ (XAUSUSD)</span>
                  <span className="block max-w-[220px] truncate text-[11px] text-muted-foreground">{t.note}</span>
                </td>
                <td className={`py-2.5 pr-3 text-right font-semibold ${t.side === 'BUY' ? 'text-gain' : 'text-loss'}`}>
                  {t.side === 'BUY' ? '+' : '-'}
                  {t.oz.toFixed(2)} oz
                </td>
                <td className="py-2.5 pr-3 text-right">{t.amountThb.toLocaleString('en-US')}</td>
                <td className={`py-2.5 pr-3 text-right font-semibold ${(t.plThb ?? 0) < 0 ? 'text-loss' : 'text-gain'}`}>
                  {t.plThb === null ? '-' : formatBaht(t.plThb, true)}
                </td>
                <td className="py-2.5 text-right">
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-gain">
                    <CheckCircle2 className="h-3 w-3" /> สำเร็จ
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
