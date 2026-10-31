'use client';

import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { AlertTriangle, Database, RefreshCw } from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface DataManifest {
  portfolio_run_id: string;
  market: {
    start_date: string;
    end_date: string;
    rows: number;
    missing_spot_rows: number;
    missing_fx_rows: number;
    imputed_values: number;
  };
  portfolios: {
    count: number;
    valuation_rows: number;
    transaction_rows: number;
    all_synthetic: boolean;
  };
}

interface MarketRow {
  date: string;
  bar_buy: number | null;
  bar_sell: number | null;
  gold_spot_clean: number | null;
  thb_usd_clean: number | null;
}

interface PortfolioRow {
  portfolio_id: string;
  cohort_start_year: number;
  portfolio_segment: string;
  behavior_scenario: string;
  initial_capital_thb: number;
  valuation_count: number;
  transaction_count: number;
  latest_valuation: {
    valuation_date: string;
    portfolio_equity_thb: number;
    cumulative_net_pnl_thb: number;
  } | null;
}

interface PortfolioDetail {
  portfolio: Pick<PortfolioRow, 'portfolio_id' | 'portfolio_segment'>;
  valuation: {
    valuation_date: string;
    portfolio_equity_thb: number;
    cumulative_net_pnl_thb: number;
    valuation_quality_flag: string;
  }[];
  transactions: {
    event_timestamp: string;
    event_type: string;
    side: string;
    execution_status: string;
    requested_quantity_bw: number;
    executed_quantity_bw: number;
    net_cash_change_thb: number;
    rejection_reason: string | null;
  }[];
}

interface PageResult<T> {
  total: number;
  rows: T[];
}

const PORTFOLIO_PAGE_SIZE = 25;

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`โหลด ${url} ไม่สำเร็จ (${response.status})`);
  return response.json() as Promise<T>;
}

function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return 'ไม่มีข้อมูล';
  return new Intl.NumberFormat('th-TH', { maximumFractionDigits: digits }).format(value);
}

function formatDate(value: string): string {
  return value.slice(0, 10);
}

function DataTable({
  headers,
  children,
}: {
  headers: string[];
  children: ReactNode;
}) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="bg-muted/50 text-xs text-muted-foreground">
          <tr>{headers.map((header) => <th key={header} className="px-3 py-2.5 font-semibold">{header}</th>)}</tr>
        </thead>
        <tbody className="divide-y divide-border">{children}</tbody>
      </table>
    </div>
  );
}

export function ProjectDataView() {
  const [manifest, setManifest] = useState<DataManifest | null>(null);
  const [marketRows, setMarketRows] = useState<MarketRow[]>([]);
  const [portfolios, setPortfolios] = useState<PortfolioRow[]>([]);
  const [portfolioTotal, setPortfolioTotal] = useState(0);
  const [portfolioOffset, setPortfolioOffset] = useState(0);
  const [selectedId, setSelectedId] = useState('');
  const [detail, setDetail] = useState<PortfolioDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchJson<DataManifest>('/api/data'),
      fetchJson<PageResult<MarketRow>>('/api/data/market?limit=10&order=desc'),
    ])
      .then(([data, market]) => {
        if (cancelled) return;
        setManifest(data);
        setMarketRows(market.rows);
        setError(null);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : 'โหลดชุดข้อมูลไม่สำเร็จ');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchJson<PageResult<PortfolioRow>>(
      `/api/data/portfolios?limit=${PORTFOLIO_PAGE_SIZE}&offset=${portfolioOffset}`,
    )
      .then((page) => {
        if (cancelled) return;
        setPortfolios(page.rows);
        setPortfolioTotal(page.total);
        setSelectedId((current) => (
          page.rows.some((portfolio) => portfolio.portfolio_id === current)
            ? current
            : page.rows[0]?.portfolio_id ?? ''
        ));
        setError(null);
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : 'โหลดรายการพอร์ตไม่สำเร็จ');
      });
    return () => { cancelled = true; };
  }, [portfolioOffset]);

  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false;
    fetchJson<PortfolioDetail>(`/api/data/portfolios/${encodeURIComponent(selectedId)}`)
      .then((record) => {
        if (!cancelled) {
          setDetail(record);
          setError(null);
        }
      })
      .catch((cause: unknown) => {
        if (!cancelled) setError(cause instanceof Error ? cause.message : 'โหลดรายละเอียดพอร์ตไม่สำเร็จ');
      });
    return () => { cancelled = true; };
  }, [selectedId]);

  if (loading && !manifest) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center gap-3 text-muted-foreground">
        <RefreshCw className="h-5 w-5 animate-spin text-gold" />
        <span>กำลังอ่านข้อมูลจริงจากชุดข้อมูลโครงการ...</span>
      </div>
    );
  }

  if (error && !manifest) {
    return <div role="alert" className="rounded-2xl border border-loss/30 bg-white p-5 text-sm text-loss">{error}</div>;
  }

  if (!manifest) return null;
  const latestValuation = detail?.valuation[detail.valuation.length - 1];

  return (
    <div className="space-y-5">
      <header className="rounded-2xl border border-border bg-white p-5 shadow-sm md:p-6">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gold/15 text-gold">
            <Database className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-lg font-bold text-foreground">ตารางข้อมูลจากชุดข้อมูลโครงการ</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              อ่านจาก Parquet ที่ export เป็น JSON ประจำรุ่น ไม่มีฐานข้อมูลและไม่มีการเติมค่าที่หาย
            </p>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="ข้อมูลตลาด" value={`${formatNumber(manifest.market.rows, 0)} แถว`} detail={`${manifest.market.start_date} ถึง ${manifest.market.end_date}`} />
          <Metric label="พอร์ตจำลอง" value={`${formatNumber(manifest.portfolios.count, 0)} พอร์ต`} detail={`run ${manifest.portfolio_run_id}`} />
          <Metric label="ประวัติประเมินพอร์ต" value={`${formatNumber(manifest.portfolios.valuation_rows, 0)} แถว`} detail="มูลค่ารายเดือน" />
          <Metric label="รายการธุรกรรมจำลอง" value={`${formatNumber(manifest.portfolios.transaction_rows, 0)} รายการ`} detail="รวมรายการที่ถูกปฏิเสธ" />
        </div>
        {manifest.portfolios.all_synthetic && (
          <p className="mt-4 flex items-start gap-2 rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-3 text-xs leading-relaxed text-amber-950">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            พอร์ตและธุรกรรมทั้งหมดเป็นข้อมูลสังเคราะห์จาก simulator ไม่ใช่บัญชีลูกค้าหรือธุรกรรมจริง
            ราคาตลาดเป็นข้อมูลย้อนหลัง ไม่ใช่ราคาสด
          </p>
        )}
        <p className="mt-3 text-xs text-muted-foreground">
          ค่าที่ไม่มีในต้นทาง: spot {formatNumber(manifest.market.missing_spot_rows, 0)} แถว · FX {formatNumber(manifest.market.missing_fx_rows, 0)} แถว · เติมค่า {formatNumber(manifest.market.imputed_values, 0)} ค่า
        </p>
      </header>

      {error && <div role="alert" className="rounded-xl border border-loss/30 bg-white p-3 text-sm text-loss">{error}</div>}

      <section className="space-y-3 rounded-2xl border border-border bg-white p-4 shadow-sm md:p-5">
        <div>
          <h2 className="font-bold text-foreground">ราคาทองย้อนหลังจากตารางตลาด</h2>
          <p className="mt-1 text-xs text-muted-foreground">10 แถวล่าสุดที่มีในไฟล์ พร้อมค่าที่อาจเป็น null ตามต้นทาง</p>
        </div>
        <DataTable headers={['วันที่', 'ทองคำแท่งรับซื้อ (บาท)', 'ทองคำแท่งขายออก (บาท)', 'Spot (USD)', 'FX (THB/USD)']}>
          {marketRows.map((row) => (
            <tr key={`${row.date}-${row.bar_buy}`} className="text-foreground">
              <td className="px-3 py-2.5">{formatDate(row.date)}</td>
              <td className="px-3 py-2.5">{formatNumber(row.bar_buy)}</td>
              <td className="px-3 py-2.5">{formatNumber(row.bar_sell)}</td>
              <td className="px-3 py-2.5">{formatNumber(row.gold_spot_clean)}</td>
              <td className="px-3 py-2.5">{formatNumber(row.thb_usd_clean, 4)}</td>
            </tr>
          ))}
        </DataTable>
      </section>

      <section className="space-y-4 rounded-2xl border border-border bg-white p-4 shadow-sm md:p-5">
        <div>
          <h2 className="font-bold text-foreground">พอร์ตจำลองและบัญชีรายการ</h2>
          <p className="mt-1 text-xs text-muted-foreground">เลือกพอร์ตเพื่ออ่านประวัติ valuation และ transaction จาก run เดียวกัน</p>
        </div>
        <label className="flex flex-col gap-1.5 text-sm font-medium sm:max-w-sm">
          เลือกพอร์ต
          <select
            value={selectedId}
            onChange={(event) => setSelectedId(event.target.value)}
            className="rounded-lg border border-border bg-white px-3 py-2 text-foreground"
          >
            {portfolios.map((portfolio) => (
              <option key={portfolio.portfolio_id} value={portfolio.portfolio_id}>
                {portfolio.portfolio_id} · {portfolio.cohort_start_year} · {portfolio.behavior_scenario}
              </option>
            ))}
          </select>
        </label>

        <DataTable headers={['รหัสพอร์ต', 'ปีเริ่มต้น', 'พฤติกรรม', 'ทุนตั้งต้น (บาท)', 'Valuation', 'ธุรกรรม']}>
          {portfolios.map((portfolio) => (
            <tr
              key={portfolio.portfolio_id}
              className={`text-foreground ${selectedId === portfolio.portfolio_id ? 'bg-gold/10' : 'hover:bg-muted/40'}`}
            >
              <td className="px-3 py-2.5 font-medium">
                <button
                  type="button"
                  aria-pressed={selectedId === portfolio.portfolio_id}
                  onClick={() => setSelectedId(portfolio.portfolio_id)}
                  className="rounded-sm text-left underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold"
                >
                  {portfolio.portfolio_id}
                </button>
              </td>
              <td className="px-3 py-2.5">{portfolio.cohort_start_year}</td>
              <td className="px-3 py-2.5">{portfolio.behavior_scenario}</td>
              <td className="px-3 py-2.5">{formatNumber(portfolio.initial_capital_thb, 0)}</td>
              <td className="px-3 py-2.5">{formatNumber(portfolio.valuation_count, 0)}</td>
              <td className="px-3 py-2.5">{formatNumber(portfolio.transaction_count, 0)}</td>
            </tr>
          ))}
        </DataTable>
        <div className="flex items-center justify-between gap-3 text-sm">
          <span className="text-muted-foreground">
            แสดง {portfolioTotal === 0 ? 0 : portfolioOffset + 1}–{Math.min(portfolioOffset + portfolios.length, portfolioTotal)} จาก {formatNumber(portfolioTotal, 0)}
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPortfolioOffset((offset) => Math.max(0, offset - PORTFOLIO_PAGE_SIZE))}
              disabled={portfolioOffset === 0}
              className="rounded-lg border border-border px-3 py-1.5 disabled:opacity-40"
            >
              ก่อนหน้า
            </button>
            <button
              type="button"
              onClick={() => setPortfolioOffset((offset) => Math.min(portfolioTotal - 1, offset + PORTFOLIO_PAGE_SIZE))}
              disabled={portfolioOffset + PORTFOLIO_PAGE_SIZE >= portfolioTotal}
              className="rounded-lg border border-border px-3 py-1.5 disabled:opacity-40"
            >
              ถัดไป
            </button>
          </div>
        </div>

        {detail && detail.portfolio.portfolio_id === selectedId && (
          <div className="space-y-4 border-t border-border pt-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="มูลค่าพอร์ตล่าสุด" value={`${formatNumber(latestValuation?.portfolio_equity_thb)} บาท`} detail={latestValuation ? formatDate(latestValuation.valuation_date) : 'ไม่มี valuation'} />
              <Metric label="กำไร/ขาดทุนสุทธิสะสม" value={`${formatNumber(latestValuation?.cumulative_net_pnl_thb)} บาท`} detail={detail.portfolio.portfolio_segment} />
              <Metric label="ข้อมูลบัญชีรายการ" value={`${formatNumber(detail.transactions.length, 0)} รายการ`} detail="แสดงรายการล่าสุด 8 รายการ" />
            </div>
            {detail.valuation.length > 1 && (
              <section aria-label="กราฟมูลค่าพอร์ตจำลองตามเวลา" className="rounded-xl border border-border/70 bg-cream/50 p-3 md:p-4">
                <h3 className="text-sm font-semibold">เส้นทางมูลค่าพอร์ตจำลอง</h3>
                <p className="mt-1 text-xs text-muted-foreground">อ่านจาก valuation ของพอร์ตที่เลือก · ข้อมูลสังเคราะห์ ไม่ใช่ผลตอบแทนจริง</p>
                <div className="mt-3 h-[220px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={detail.valuation} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
                      <CartesianGrid stroke="#e8e0cc" strokeDasharray="3 3" vertical={false} />
                      <XAxis
                        dataKey="valuation_date"
                        tickFormatter={formatDate}
                        tick={{ fontSize: 10, fill: '#6e6552' }}
                        minTickGap={32}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        tickFormatter={(value: number) => new Intl.NumberFormat('th-TH', { notation: 'compact', maximumFractionDigits: 1 }).format(value)}
                        tick={{ fontSize: 10, fill: '#6e6552' }}
                        width={52}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        labelFormatter={(value) => formatDate(String(value))}
                        formatter={(value) => [`฿${formatNumber(Number(value), 0)}`, 'มูลค่าพอร์ต']}
                        contentStyle={{ borderRadius: 10, border: '1px solid #e8e0cc', fontSize: 12 }}
                      />
                      <Line
                        type="monotone"
                        dataKey="portfolio_equity_thb"
                        name="มูลค่าพอร์ต"
                        stroke="#96690c"
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4, fill: '#96690c' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </section>
            )}
            <div>
              <h3 className="mb-2 text-sm font-semibold">Valuation ล่าสุด</h3>
              <DataTable headers={['วันที่', 'มูลค่าพอร์ต (บาท)', 'กำไร/ขาดทุนสุทธิ (บาท)', 'คุณภาพราคา']}>
                {detail.valuation.slice(-8).reverse().map((row) => (
                  <tr key={row.valuation_date} className="text-foreground">
                    <td className="px-3 py-2.5">{formatDate(row.valuation_date)}</td>
                    <td className="px-3 py-2.5">{formatNumber(row.portfolio_equity_thb)}</td>
                    <td className="px-3 py-2.5">{formatNumber(row.cumulative_net_pnl_thb)}</td>
                    <td className="px-3 py-2.5">{row.valuation_quality_flag}</td>
                  </tr>
                ))}
              </DataTable>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-semibold">ธุรกรรมล่าสุด</h3>
              <DataTable headers={['เวลา', 'ประเภท', 'ฝั่ง', 'สถานะ', 'จำนวนที่ขอ (บาททอง)', 'จำนวนที่ทำได้', 'เหตุผลที่ไม่สำเร็จ']}>
                {detail.transactions.slice(-8).reverse().map((row) => (
                  <tr key={`${row.event_timestamp}-${row.event_type}`} className="text-foreground">
                    <td className="px-3 py-2.5">{formatDate(row.event_timestamp)}</td>
                    <td className="px-3 py-2.5">{row.event_type}</td>
                    <td className="px-3 py-2.5">{row.side}</td>
                    <td className="px-3 py-2.5">{row.execution_status}</td>
                    <td className="px-3 py-2.5">{formatNumber(row.requested_quantity_bw, 4)}</td>
                    <td className="px-3 py-2.5">{formatNumber(row.executed_quantity_bw, 4)}</td>
                    <td className="px-3 py-2.5">{row.rejection_reason ?? '—'}</td>
                  </tr>
                ))}
              </DataTable>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-xl border border-border bg-cream/60 p-3.5">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-bold text-foreground">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}
