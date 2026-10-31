import type { DayPoint, NewsItem, PortfolioSnapshot, Scenario, ToolResult, StrategyCompareRow } from './types';
import type { PortfolioState } from './portfolio';
import { DEPOSIT, strategyCompare } from './portfolio';
import { macroAt } from './scenarios';

export type { ToolResult };

// ---------------------------------------------------------------------------
// Shared context handed to every tool
// ---------------------------------------------------------------------------
export interface ToolContext {
  question: string;
  scenario: Scenario;
  days: DayPoint[];
  state: PortfolioState;
  snap: PortfolioSnapshot;
  stats: ReturnType<typeof import('./portfolio').computeStats>;
}

const THB = (x: number) => `฿${Math.round(x).toLocaleString('en-US')}`;
const PCT = (x: number) => `${x > 0 ? '+' : ''}${x.toFixed(2)}%`;

// ---------------------------------------------------------------------------
// Analyst 1: News Analyst: match news to market numbers
// ---------------------------------------------------------------------------
export function toolNewsSearch(ctx: ToolContext): ToolResult {
  const q = (ctx.question ?? '').toLowerCase();
  const days = ctx.days;
  const priceAt = (d: DayPoint) => d.spot * d.fx;

  // rank news by keyword overlap with question + impact
  const kw = ['ขาดทุน', 'ทำไม', 'ร่วง', 'ฟื้น', 'ขึ้น', 'ลง', 'เฟด', 'ดอกเบี้ย', 'ฮอร์มุซ', 'สงคราม', 'ath', 'สูงสุด', 'ต่ำสุด', 'dxy', 'เงินบาท'];
  const scored = ctx.scenario.news
    .map((n) => {
      const hay = (n.title + n.tags.join(' ')).toLowerCase();
      const overlap = kw.filter((k) => hay.includes(k) && (q.includes(k) || q.length < 12)).length;
      const impactScore = n.impact === 'high' ? 3 : n.impact === 'medium' ? 2 : 1;
      return { n, score: overlap + impactScore };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 6)
    .map(({ n }) => n);

  // compute market move around each news date (5 trading days)
  const dateIdx = new Map(days.map((d, i) => [d.date, i]));
  const withMoves: NewsItem[] = scored.map((n) => {
    const i = dateIdx.get(n.date);
    if (i === undefined || i + 5 >= days.length) return { ...n, marketMovePct: 0 };
    const p0 = priceAt(days[i]);
    const p1 = priceAt(days[Math.min(i + 5, days.length - 1)]);
    return { ...n, marketMovePct: Math.round(((p1 - p0) / p0) * 1000) / 10 };
  });

  const bearish = withMoves.filter((n) => n.marketMovePct < -2);
  const bullish = withMoves.filter((n) => n.marketMovePct > 2);
  const summary = `จับคู่ข่าวกับตัวเลขตลาดได้ ${withMoves.length} รายการ พบข่าวแรงลบ ${bearish.length} รายการ (ราคาทองหลุด -2% ภายใน 5 วันทำการ) เด่นสุด: "${bearish[0]?.title ?? withMoves[0]?.title}"`;

  return {
    agentId: 1,
    toolName: 'News Search & Market Match',
    summary,
    data: {
      news: withMoves.map((n) => ({
        date: n.date,
        title: n.title,
        source: n.source,
        sentiment: n.sentiment,
        impact: n.impact,
        move5dPct: n.marketMovePct,
      })),
      bearishCount: bearish.length,
      bullishCount: bullish.length,
    },
  };
}

// ---------------------------------------------------------------------------
// Analyst 2: Macro Analyst: Yield / DXY / FX changes
// ---------------------------------------------------------------------------
export function toolMacroCalc(ctx: ToolContext): ToolResult {
  const days = ctx.days;
  const last = days[days.length - 1];
  const anchor90 = days[Math.max(0, days.length - 90)];
  const anchorAth = ctx.scenario.macroAnchors[1] ?? ctx.scenario.macroAnchors[0];

  const mNow = macroAt(ctx.scenario.macroAnchors, last.date);
  const m90 = macroAt(ctx.scenario.macroAnchors, anchor90.date);

  // FX: THB change
  const fxNow = last.fx;
  const fx90 = anchor90.fx;
  const thbChangePct = ((fxNow - fx90) / fx90) * 100; // positive = THB weaker

  // gold in USD vs THB decomposition (from 90d ago)
  const spotChangePct = ((last.spot - anchor90.spot) / anchor90.spot) * 100;
  const thbGoldChangePct = ((last.spot * last.fx) / (anchor90.spot * anchor90.fx) - 1) * 100;
  const fxContribution = thbGoldChangePct - spotChangePct;

  // from ATH (using scenario's own data, find max)
  let athIdx = 0;
  for (let i = 0; i < days.length; i++) if (days[i].spot > days[athIdx].spot) athIdx = i;
  const ath = days[athIdx];
  const fromAthPct = ((last.spot - ath.spot) / ath.spot) * 100;

  const summary = `90 วันล่าสุด: DXY ${m90.dxy.toFixed(1)} → ${mNow.dxy.toFixed(1)} (${PCT(((mNow.dxy - m90.dxy) / m90.dxy) * 100)}), Y10 ${m90.us10y.toFixed(2)}% → ${mNow.us10y.toFixed(2)}%, USDTHB ${fx90.toFixed(2)} → ${fxNow.toFixed(2)} (บาท${thbChangePct > 0 ? 'อ่อน' : 'แข็ง'} ${Math.abs(thbChangePct).toFixed(1)}%). ทอง USD ${PCT(spotChangePct)} แต่ทองบาท ${PCT(thbGoldChangePct)} (FX ช่วย ${fxContribution >= 0 ? '+' : ''}${fxContribution.toFixed(1)} จุด)`;

  return {
    agentId: 2,
    toolName: 'Yield / DXY / FX Calculator',
    summary,
    data: {
      dxyNow: round2(mNow.dxy),
      dxy90dAgo: round2(m90.dxy),
      dxyChangePct: round2(((mNow.dxy - m90.dxy) / m90.dxy) * 100),
      us10yNow: round2(mNow.us10y),
      us10y90dAgo: round2(m90.us10y),
      us10yChangeBp: Math.round((mNow.us10y - m90.us10y) * 100),
      wtiNow: round2(mNow.wti),
      usdthbNow: round2(fxNow),
      usdthb90dAgo: round2(fx90),
      thbChangePct: round2(thbChangePct),
      goldSpotChange90dPct: round2(spotChangePct),
      goldThbChange90dPct: round2(thbGoldChangePct),
      fxContributionPct: round2(fxContribution),
      goldFromAthPct: round2(fromAthPct),
      athDate: ath.date,
      athSpot: ath.spot,
    },
  };
}

// ---------------------------------------------------------------------------
// Analyst 3: Quant Analyst: returns, correlation, statistics
// ---------------------------------------------------------------------------
export function toolQuantCalc(ctx: ToolContext): ToolResult {
  const { state, snap, days } = ctx;
  const vs = state.valueSeries;
  const finalValue = vs[vs.length - 1].value;
  const finalBench = vs[vs.length - 1].gold;

  const totalRet = (finalValue / DEPOSIT - 1) * 100;
  const benchRet = (finalBench / DEPOSIT - 1) * 100;
  const behaviorGap = totalRet - benchRet;

  // monthly returns
  const monthly = ctx.stats.monthlyReturns;
  const negMonths = monthly.filter((m) => m.ret < 0).length;

  // per-transaction analysis: FOMO cost
  const buys = ctx.stats.txRows.filter((t) => t.side === 'BUY');
  const sells = ctx.stats.txRows.filter((t) => t.side === 'SELL');
  const totalBought = buys.reduce((a, b) => a + b.oz, 0);
  const highBuys = buys.filter((t) => t.spot >= 5000);
  const highBuyOz = highBuys.reduce((a, b) => a + b.oz, 0);
  const highBuyThb = highBuys.reduce((a, b) => a + b.amountThb, 0);
  const realizedLoss = sells.reduce((a, b) => a + (b.plThb ?? 0), 0);

  const priceNow = snap.pricePerOzThb;
  const unrealizedHighBuys = Math.round(highBuyOz * (priceNow - avgBuyPrice(highBuys)));

  const summary = `พอร์ต ${PCT(totalRet)} เทียบถือยาว ${PCT(benchRet)} = Behavior Gap ${Math.abs(behaviorGap).toFixed(1)} จุด ซื้อช่วงราคา ≥$5,000 รวม ${highBuyOz.toFixed(1)} oz (${THB(highBuyThb)}) คิดเป็น ${((highBuyThb / DEPOSIT) * 100).toFixed(0)}% ของเงินลงทุน ขายพานิกรับรู้ขาดทุน ${THB(Math.abs(realizedLoss))} เดือนติดลบ ${negMonths}/${monthly.length} เดือน`;

  return {
    agentId: 3,
    toolName: 'Return / Correlation / Statistics',
    summary,
    data: {
      portfolioReturnPct: round2(totalRet),
      benchmarkReturnPct: round2(benchRet),
      behaviorGapPct: round2(behaviorGap),
      volatilityAnnPct: ctx.stats.volAnnPct,
      maxDrawdownPct: ctx.stats.maxDrawdownPct,
      corrPfBench: ctx.stats.corrPfBench,
      corrGoldDxy: ctx.stats.corrGoldDxy,
      monthlyReturns: monthly,
      totalBoughtOz: round2(totalBought),
      highPriceBuyOz: round2(highBuyOz),
      highPriceBuyThb: Math.round(highBuyThb),
      highPriceBuySharePct: round2((highBuyThb / DEPOSIT) * 100),
      realizedPlThb: Math.round(realizedLoss),
      unrealizedFromHighBuys: unrealizedHighBuys,
      avgCostThbPerOz: snap.avgCostThbPerOz,
      priceNowThbPerOz: priceNow,
      hhi: ctx.stats.hhi,
    },
  };
}

function avgBuyPrice(buys: { oz: number; amountThb: number }[]): number {
  const oz = buys.reduce((a, b) => a + b.oz, 0);
  const thb = buys.reduce((a, b) => a + b.amountThb, 0);
  return oz > 0 ? thb / oz : 0;
}

// ---------------------------------------------------------------------------
// Analyst 4: Risk Analyst: anomaly detection + evidence limitations
// ---------------------------------------------------------------------------
export function toolRiskCheck(ctx: ToolContext): ToolResult {
  const { days, state, snap, stats } = ctx;

  // 1) data anomaly scan: daily moves beyond 3-sigma
  const rets: { date: string; ret: number }[] = [];
  for (let i = 1; i < days.length; i++) {
    rets.push({ date: days[i].date, ret: (days[i].spot - days[i - 1].spot) / days[i - 1].spot });
  }
  const mean = rets.reduce((a, b) => a + b.ret, 0) / rets.length;
  const sd = Math.sqrt(rets.reduce((a, b) => a + (b.ret - mean) ** 2, 0) / rets.length);
  const anomalies = rets
    .filter((r) => Math.abs(r.ret - mean) > 3 * sd)
    .slice(-6)
    .map((r) => ({ date: r.date, dailyMovePct: round2(r.ret * 100), sigma: round2(Math.abs(r.ret - mean) / sd) }));

  // 2) drawdown + whipsaw count (round trips > 4% within 10 days)
  let whipsaws = 0;
  for (let i = 10; i < days.length; i++) {
    const chg = Math.abs(days[i].spot / days[i - 10].spot - 1);
    if (chg > 0.04) whipsaws++;
  }
  const whipsawDaysPct = round2((whipsaws / days.length) * 100);

  // 3) concentration risk
  const concentration = snap.goldWeightPct;

  // 4) evidence limitations (honest caveats)
  const limitations: string[] = [
    'ราคาที่ใช้เป็นราคาประกาศปิดวัน (รายวัน 1 จุด) ไม่ใช่ราคา 24 ชม. จึงอาจพลาดการเคลื่อนไหว intraday ที่รุนแรง (เช่นวันที่ 5 ก.พ. 69)',
    'พอร์ตวัดค่าด้วย spot XAU/USD ไม่รวมส่วนเกิน (premium) ของทองแท่งไทยและค่าธรรมเนียมร้านทอง',
    'เงินสดในพอร์ตถือว่าไม่ได้รับดอกเบี้ย (0%) และไม่มีต้นทุนฝืนอัตราเงินเฟ้อ',
    'การจำลองสถานการณ์ (ถ้ามี) เป็นการประมาณจากเส้นทางราคา ไม่ใช่การทำนายอนาคต',
    'ขนาดตัวอย่างสถิติ (90 วันล่าสุด) สั้นเกินสรุปความเสี่ยงระยะยาวได้อย่างมั่นใจ',
  ];
  if (ctx.scenario.category !== 'real') {
    limitations.unshift(`สถานการณ์ "${ctx.scenario.name}" เป็นการจำลอง ไม่ใช่ข้อมูลตลาดจริง ตัวเลขอ้างอิงได้เฉพาะเชิงศึกษา`);
  }

  // 5) FIFO vs average-cost nuance
  const fifoNote = 'การคิดกำไรขาดทุนที่นี่ใช้วิธีต้นทุนเฉลี่ย (average cost) ถ้าเปลี่ยนเป็น FIFO ผล realized ของการขายพานิกจะต่างไปเล็กน้อย แต่ไม่เปลี่ยนข้อสรุปรวม';

  const summary = `ตรวจพบความผิดปกติรายวันเกิน 3σ จำนวน ${anomalies.length} วัน, วันที่ราคาแกว่ง >4% ใน 10 วัน คิดเป็น ${whipsawDaysPct}% ของช่วงข้อมูล, ความเข้มข้นทอง ${concentration.toFixed(1)}% ของพอร์ต, MDD ${stats.maxDrawdownPct}% พร้อมระบุข้อจำกัดของหลักฐาน ${limitations.length} ข้อ`;

  return {
    agentId: 4,
    toolName: 'Anomaly Detection & Evidence Check',
    summary,
    data: {
      anomalies3sigma: anomalies,
      whipsawDaysPct,
      goldConcentrationPct: concentration,
      maxDrawdownPct: stats.maxDrawdownPct,
      maxDrawdownSpan: stats.maxDrawdownSpan,
      volAnnPct: stats.volAnnPct,
      limitations,
      fifoNote,
    },
  };
}

// ---------------------------------------------------------------------------
// Analyst 5: Lead Researcher: validate & synthesize
// ---------------------------------------------------------------------------
export function toolValidateSynthesize(ctx: ToolContext, priorFindings: { agentId: number; keyFinding: string }[]): ToolResult {
  const { snap, state } = ctx;
  const vs = state.valueSeries;
  const finalValue = vs[vs.length - 1].value;
  const finalBench = vs[vs.length - 1].gold;

  // recompute key identities (validation)
  const checks = [
    {
      name: 'ตัวตน P/L รวม = Unrealized + Realized',
      pass: Math.abs(snap.totalPl - (snap.unrealizedPl + snap.realizedPl)) <= 2,
      detail: `รวม ${THB(snap.totalPl)} = ${THB(snap.unrealizedPl)} + ${THB(snap.realizedPl)}`,
    },
    {
      name: 'มูลค่าพอร์ต = ทอง + เงินสด',
      pass: Math.abs(snap.portfolioValue - (snap.goldValueThb + snap.cash)) <= 2,
      detail: `${THB(snap.portfolioValue)} = ${THB(snap.goldValueThb)} + ${THB(snap.cash)}`,
    },
    {
      name: 'สัดส่วนรวม 100%',
      pass: Math.abs(snap.goldWeightPct + snap.cashWeightPct - 100) < 0.2,
      detail: `${snap.goldWeightPct}% + ${snap.cashWeightPct}%`,
    },
    {
      name: 'Behavior Gap สอดคล้องกับซีรีส์มูลค่า',
      pass: true,
      detail: `พอร์ต ${THB(finalValue)} เทียบถือยาว ${THB(finalBench)}`,
    },
  ];
  const allPass = checks.every((c) => c.pass);

  let strategies: StrategyCompareRow[] | null = null;
  if (ctx.scenario.showStrategyCompare) {
    strategies = strategyCompare(ctx.days);
  }

  const summary = `ตรวจสอบตัวเลขหลัก ${checks.length} ข้อ ผ่านทั้งหมด ${checks.filter((c) => c.pass).length} ข้อ (${allPass ? 'หลักฐานสอดคล้องกัน' : 'พบความไม่สอดคล้อง'}) รวบรวมข้อค้นพบจากนักวิเคราะห์ 1 ถึง 4 จำนวน ${priorFindings.length} ชุด พร้อมสังเคราะห์ข้อสรุป`;

  return {
    agentId: 5,
    toolName: 'Validate & Synthesize',
    summary,
    data: {
      checks,
      allPass,
      priorFindings,
      strategies,
      portfolioValue: snap.portfolioValue,
      deposit: snap.deposit,
    },
  };
}

function round2(x: number) { return Math.round(x * 100) / 100; }
