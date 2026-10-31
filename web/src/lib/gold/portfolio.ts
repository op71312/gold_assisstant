import type { Tx, DayPoint, ChartPoint, TxRow, PortfolioSnapshot, StrategyCompareRow } from './types';
import { macroAt, SCENARIOS } from './scenarios';

// ---------------------------------------------------------------------------
// Portfolio: real executed trades (prices from the real announcement dataset)
// Deposit: ฿1,800,000 on 2025-11-14. Gold unit: troy oz (XAU spot × USDTHB).
// ---------------------------------------------------------------------------
export const DEPOSIT = 1_800_000;
export const DEPOSIT_DATE = '2025-11-14';

export const TRANSACTIONS: Tx[] = [
  { id: 'T1', date: '2025-11-14', side: 'BUY', oz: 1.5, spot: 4171.0, fx: 32.40, note: 'เริ่มต้นลงทุน ซื้อจากกราฟขาขึ้น' },
  { id: 'T2', date: '2025-12-10', side: 'BUY', oz: 1.0, spot: 4198.0, fx: 31.83, note: 'เพิ่มน้ำหนักตามแรงเชียร์กระแสทอง' },
  { id: 'T3', date: '2026-01-12', side: 'BUY', oz: 2.0, spot: 4586.0, fx: 31.22, note: 'FOMO ราคากำลังวิ่งเข้าจุดสูงสุด' },
  { id: 'T4', date: '2026-01-29', side: 'BUY', oz: 2.0, spot: 5516.0, fx: 31.22, note: 'ซื้อวันทำ ATH จุดสูงสุดตลอดกาล' },
  { id: 'T5', date: '2026-02-20', side: 'BUY', oz: 1.0, spot: 5025.0, fx: 31.19, note: 'เฉลี่ยลงหลังเห็นย่อ คิดว่าวงจรขาขึ้นกลับมา' },
  { id: 'T6', date: '2026-03-27', side: 'SELL', oz: 0.5, spot: 4432.0, fx: 32.90, note: 'ใจไม่ถึง ขายพานิกรอบแรก' },
  { id: 'T7', date: '2026-04-13', side: 'BUY', oz: 1.0, spot: 4714.0, fx: 32.24, note: 'กลับมาซื้อรอบที่ประกาศปิดล้อมท่าเรือ' },
  { id: 'T8', date: '2026-06-30', side: 'SELL', oz: 1.0, spot: 4023.0, fx: 33.23, note: 'ทนขาลงไม่ไหว ขายพานิกรอบสองใกล้จุดต่ำสุด' },
  { id: 'T9', date: '2026-08-14', side: 'BUY', oz: 1.5, spot: 4354.0, fx: 33.16, note: 'ซื้อกลับเมื่อราคาเด้งกลับ' },
  { id: 'T10', date: '2026-09-30', side: 'BUY', oz: 0.5, spot: 4188.0, fx: 33.57, note: 'เก็บเพิ่มเมื่อราคาอึดอัด' },
];

export const CASH_INTEREST_PCT = 0; // cash earns nothing (noted by Risk Analyst)

const thbPerOz = (spot: number, fx: number) => spot * fx;
const txAmount = (t: Tx) => t.oz * t.spot * t.fx;

export function dateOf(d: DayPoint) { return d.date; }

// ---------------------------------------------------------------------------
// Core portfolio state machine (average-cost method)
// ---------------------------------------------------------------------------
export interface PortfolioState {
  cash: number;
  oz: number;
  avgCost: number; // THB per oz
  realized: number; // cumulative realized P/L THB
  valueSeries: ChartPoint[]; // portfolio + B&H benchmark
  txRows: TxRow[];
  ozSeries: { date: string; oz: number }[];
}

export function computePortfolio(days: DayPoint[], deposit = DEPOSIT): PortfolioState {
  const byDate = new Map(days.map((d) => [d.date, d]));
  const sorted = [...days].sort((a, b) => a.date.localeCompare(b.date));
  const txByDate = new Map<string, Tx[]>();
  for (const t of TRANSACTIONS) {
    const arr = txByDate.get(t.date) ?? [];
    arr.push(t);
    txByDate.set(t.date, arr);
  }

  let cash = 0;
  let oz = 0;
  let avgCost = 0;
  let realized = 0;
  const valueSeries: ChartPoint[] = [];
  const ozSeries: { date: string; oz: number }[] = [];
  const txRows: TxRow[] = [];

  const bhOz = deposit / thbPerOz(TRANSACTIONS[0].spot, TRANSACTIONS[0].fx);

  for (const d of sorted) {
    if (d.date < DEPOSIT_DATE) continue;

    // initial deposit
    if (d.date === DEPOSIT_DATE) {
      cash += deposit;
    }

    const txs = txByDate.get(d.date);
    if (txs) {
      for (const t of txs) {
        const price = thbPerOz(t.spot, t.fx);
        const amt = txAmount(t);
        let pl = 0;
        if (t.side === 'BUY') {
          const newOz = oz + t.oz;
          avgCost = newOz > 0 ? (avgCost * oz + price * t.oz) / newOz : price;
          oz = newOz;
          cash -= amt;
        } else {
          pl = (price - avgCost) * t.oz;
          realized += pl;
          oz -= t.oz;
          cash += amt;
        }
        txRows.push({
          id: t.id,
          date: t.date,
          side: t.side,
          oz: t.oz,
          spot: t.spot,
          thbPerOz: Math.round(price),
          amountThb: Math.round(amt),
          plThb: t.side === 'SELL' ? Math.round(pl) : null,
          status: 'สำเร็จ',
          note: t.note,
        });
      }
    }

    const value = cash + oz * thbPerOz(d.spot, d.fx);
    valueSeries.push({ date: d.date, value: Math.round(value), gold: Math.round(bhOz * thbPerOz(d.spot, d.fx)) });
    ozSeries.push({ date: d.date, oz: Math.round(oz * 100) / 100 });
  }

  const last = sorted[sorted.length - 1];
  const priceNow = thbPerOz(last.spot, last.fx);

  return {
    cash: Math.round(cash),
    oz: Math.round(oz * 100) / 100,
    avgCost: Math.round(avgCost),
    realized: Math.round(realized),
    valueSeries,
    txRows,
    ozSeries,
  };
}

// ---------------------------------------------------------------------------
// Snapshot + stats
// ---------------------------------------------------------------------------
export function snapshotOf(state: PortfolioState, lastDay: DayPoint, changeFromAthPct: number): PortfolioSnapshot {
  const priceNow = lastDay.spot * lastDay.fx;
  const goldValue = state.oz * priceNow;
  const portfolioValue = goldValue + state.cash;
  const totalPl = portfolioValue - DEPOSIT;
  return {
    deposit: DEPOSIT,
    cash: state.cash,
    goldOz: state.oz,
    avgCostThbPerOz: state.avgCost,
    goldValueThb: Math.round(goldValue),
    portfolioValue: Math.round(portfolioValue),
    totalPl: Math.round(totalPl),
    totalPlPct: round2((totalPl / DEPOSIT) * 100),
    unrealizedPl: Math.round(totalPl - state.realized),
    realizedPl: state.realized,
    goldWeightPct: round2((goldValue / portfolioValue) * 100),
    cashWeightPct: round2((state.cash / portfolioValue) * 100),
    spotNow: lastDay.spot,
    fxNow: lastDay.fx,
    barPriceNow: lastDay.barSell,
    pricePerOzThb: Math.round(priceNow),
    changeFromAthPct,
  };
}

export function computeStats(days: DayPoint[], state: PortfolioState, snap: PortfolioSnapshot) {
  const vs = state.valueSeries;
  // max drawdown of portfolio value
  let peak = -Infinity;
  let mdd = 0;
  let mddSpan: [string, string] | null = null;
  let curPeakDate = vs[0]?.date ?? '';
  for (const p of vs) {
    if (p.value > peak) { peak = p.value; curPeakDate = p.date; }
    const dd = (p.value - peak) / peak;
    if (dd < mdd) { mdd = dd; mddSpan = [curPeakDate, p.date]; }
  }

  // daily returns & volatility (last 90 days)
  const tail = vs.slice(-90);
  const rets: number[] = [];
  for (let i = 1; i < tail.length; i++) rets.push((tail[i].value - tail[i - 1].value) / tail[i - 1].value);
  const mean = rets.reduce((a, b) => a + b, 0) / (rets.length || 1);
  const variance = rets.reduce((a, b) => a + (b - mean) ** 2, 0) / (rets.length || 1);
  const volAnn = Math.sqrt(variance) * Math.sqrt(252) * 100;

  // correlation portfolio vs benchmark (last 90d)
  const benchRets: number[] = [];
  for (let i = 1; i < tail.length; i++) benchRets.push((tail[i].gold - tail[i - 1].gold) / tail[i - 1].gold);
  const corrPfBench = correlation(rets, benchRets);

  // correlation gold spot vs DXY (last 90d, real dxy path)
  const gtail = days.slice(-90);
  const gRets: number[] = [];
  const dxyRets: number[] = [];
  for (let i = 1; i < gtail.length; i++) {
    gRets.push((gtail[i].spot - gtail[i - 1].spot) / gtail[i - 1].spot);
    const dxyPrev = macroAt2(gtail[i - 1].date).dxy;
    const dxyCur = macroAt2(gtail[i].date).dxy;
    dxyRets.push((dxyCur - dxyPrev) / dxyPrev);
  }
  const corrGoldDxy = correlation(gRets, dxyRets);

  // monthly returns of portfolio (last 8 months)
  const byMonth = new Map<string, { first: number; last: number }>();
  for (const p of vs) {
    const k = p.date.slice(0, 7);
    const m = byMonth.get(k) ?? { first: p.value, last: p.value };
    m.last = p.value;
    byMonth.set(k, m);
  }
  const monthly: { month: string; ret: number }[] = [];
  const keys = [...byMonth.keys()].sort();
  for (let i = 1; i < keys.length; i++) {
    const prev = byMonth.get(keys[i - 1])!;
    const cur = byMonth.get(keys[i])!;
    monthly.push({ month: keys[i], ret: round2(((cur.last - prev.last) / prev.last) * 100) });
  }

  // per-tx P/L (average-cost marking), enrich txRows
  const enriched = state.txRows.map((r) => {
    if (r.plThb !== null) return r;
    const d = days.find((x) => x.date === r.date);
    const priceNow = (d?.spot ?? 0) * (d?.fx ?? 1);
    return { ...r, plThb: Math.round((priceNow - r.thbPerOz) * r.oz) };
  });

  return {
    maxDrawdownPct: round2(mdd * 100),
    maxDrawdownSpan: mddSpan,
    volAnnPct: round2(volAnn),
    corrPfBench: round2(corrPfBench),
    corrGoldDxy: round2(corrGoldDxy),
    monthlyReturns: monthly.slice(-8),
    txRows: enriched,
    hhi: round2((Math.pow(snap.goldWeightPct / 100, 2) + Math.pow(snap.cashWeightPct / 100, 2)) * 10000) / 10000,
  };
}

function macroAt2(date: string) {
  return macroAt(SCENARIOS[0].macroAnchors, date);
}

function correlation(a: number[], b: number[]): number {
  const n = Math.min(a.length, b.length);
  if (n < 3) return 0;
  const ma = a.reduce((x, y) => x + y, 0) / n;
  const mb = b.reduce((x, y) => x + y, 0) / n;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < n; i++) {
    num += (a[i] - ma) * (b[i] - mb);
    da += (a[i] - ma) ** 2;
    db += (b[i] - mb) ** 2;
  }
  const den = Math.sqrt(da * db);
  return den === 0 ? 0 : num / den;
}

// ---------------------------------------------------------------------------
// Strategy comparison (behavior scenario)
// ---------------------------------------------------------------------------
export function strategyCompare(days: DayPoint[]): StrategyCompareRow[] {
  const sorted = days.filter((d) => d.date >= DEPOSIT_DATE);
  const byDate = new Map(sorted.map((d) => [d.date, d]));
  const price = (d: DayPoint) => d.spot * d.fx;

  // 1) Actual (the real trades)
  const actual = computePortfolio(days);
  const actualVal = actual.cash + actual.oz * price(sorted[sorted.length - 1]);

  // 2) DCA: ฿150,000 on the 14th of each month (or first trading day after)
  const dcaMonthly = 150_000;
  let dcaCash = 0, dcaOz = 0, dcaInvested = 0;
  const months = new Set<string>();
  for (const d of sorted) months.add(d.date.slice(0, 7));
  const monthList = [...months].sort();
  for (const m of monthList) {
    const target = `${m}-14`;
    let txDay = sorted.find((d) => d.date >= target && d.date.slice(0, 7) === m);
    if (!txDay) txDay = sorted.find((d) => d.date.slice(0, 7) === m);
    if (!txDay) continue;
    dcaCash += dcaMonthly;
    dcaInvested += dcaMonthly;
    const buyOz = dcaMonthly / price(txDay);
    dcaOz += buyOz;
    dcaCash -= dcaMonthly; // all converted to gold immediately
  }
  const dcaVal = dcaOz * price(sorted[sorted.length - 1]) + dcaCash;

  // 3) Buy & hold lump sum
  const bhOz = DEPOSIT / price(sorted[0]);
  const bhVal = bhOz * price(sorted[sorted.length - 1]);

  return [
    {
      name: 'พอร์ตจริง (ซื้อขายตามอารมณ์)',
      finalValue: Math.round(actualVal),
      pl: Math.round(actualVal - DEPOSIT),
      plPct: round2(((actualVal - DEPOSIT) / DEPOSIT) * 100),
      invested: DEPOSIT,
      note: 'FOMO ช่วงราคาสูง + ขายพานิกช่วงราคาต่ำ 2 รอบ',
      highlight: true,
    },
    {
      name: 'DCA เดือนละ ฿150,000',
      finalValue: Math.round(dcaVal),
      pl: Math.round(dcaVal - dcaInvested),
      plPct: round2(((dcaVal - dcaInvested) / dcaInvested) * 100),
      invested: Math.round(dcaInvested),
      note: 'ฝากเงินและซื้อทองทุกวันที่ 14 ของเดือน ไม่สนใจราคา',
    },
    {
      name: 'ถือยาว (ซื้อครั้งเดียววันแรก)',
      finalValue: Math.round(bhVal),
      pl: Math.round(bhVal - DEPOSIT),
      plPct: round2(((bhVal - DEPOSIT) / DEPOSIT) * 100),
      invested: DEPOSIT,
      note: 'เอาเงินก้อนเดียวซื้อตั้งแต่ 14 พ.ย. 68 แล้วไม่แตะต้อง',
    },
  ];
}

function round2(x: number) { return Math.round(x * 100) / 100; }
