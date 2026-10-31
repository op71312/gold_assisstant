import raw from './market-data.json';
import type { ChartPoint, DayPoint, MarketFacts, RawMarketData, Scenario } from './types';
import { applyScenario, getScenario } from './scenarios';
import { computePortfolio, computeStats, snapshotOf, type PortfolioState } from './portfolio';

const data = raw as unknown as RawMarketData;
const BASE_DAYS: DayPoint[] = data.daily;

export const MARKET_FACTS: MarketFacts = data.facts;
export const INTRADAY = data.intradayLastDay;
export const MONTHLY_EARLY = data.monthlyEarly;

export interface EngineContext {
  scenario: Scenario;
  days: DayPoint[];
  state: PortfolioState;
  snap: ReturnType<typeof snapshotOf>;
  stats: ReturnType<typeof computeStats>;
  facts: MarketFacts;
}

const ctxCache = new Map<string, EngineContext>();

export function buildContext(scenarioId: string): EngineContext {
  const cached = ctxCache.get(scenarioId);
  if (cached) return cached;

  const scenario = getScenario(scenarioId);
  const days = applyScenario(BASE_DAYS, scenario);
  const state = computePortfolio(days);
  const snap = snapshotOf(state, days[days.length - 1], scenarioFacts(days).changeFromAthPct);
  const stats = computeStats(days, state, snap);
  const facts = scenarioFacts(days);

  const ctx: EngineContext = { scenario, days, state, snap, stats, facts };
  ctxCache.set(scenarioId, ctx);
  return ctx;
}

/** scenario-specific facts (ATH etc. computed from the transformed series) */
function scenarioFacts(days: DayPoint[]): MarketFacts {
  const last = days[days.length - 1];
  let athIdx = 0;
  for (let i = 0; i < days.length; i++) if (days[i].spot > days[athIdx].spot) athIdx = i;
  const ath = days[athIdx];
  const trough = days.slice(athIdx).reduce((a, b) => (b.spot < a.spot ? b : a), ath);
  const barPeak = Math.max(...days.map((d) => d.barSell));
  return {
    lastDate: last.date,
    lastSpot: last.spot,
    lastFx: last.fx,
    lastBarSell: last.barSell,
    athDate: ath.date,
    athSpot: ath.spot,
    postAthTroughDate: trough.date,
    postAthTroughSpot: trough.spot,
    postAthDropPct: round2(((trough.spot - ath.spot) / ath.spot) * 100),
    maxDrawdownPct: 0,
    maxDrawdownSpan: null,
    changeFromAthPct: round2(((last.spot - ath.spot) / ath.spot) * 100),
    barFromAthPct: round2(((last.barSell - barPeak) / barPeak) * 100),
    ytd2025FirstSpot: 0,
  };
}

// ---------------------------------------------------------------------------
// Chart series by range
// ---------------------------------------------------------------------------
export type Range = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL';

const RANGE_DAYS: Record<Exclude<Range, '1D'>, number> = {
  '1W': 7, '1M': 31, '3M': 92, '6M': 183, '1Y': 365, ALL: 100000,
};

export function chartSeries(ctx: EngineContext, range: Range): ChartPoint[] {
  const { days, state } = ctx;
  if (range === '1D') {
    // intraday approximation: apply last daily multiplier to intraday spot points
    const lastDaily = days[days.length - 1];
    const bhOz = state.valueSeries[0] ? 0 : 0; // benchmark not needed intraday
    void bhOz;
    return INTRADAY.map((p) => ({
      date: p.t,
      value: Math.round((state.cash + state.oz * p.spot * lastDaily.fx)),
      gold: Math.round(state.oz * p.spot * lastDaily.fx),
    }));
  }
  const n = RANGE_DAYS[range];
  const series = state.valueSeries.slice(-n);
  return series;
}

/** full history line for ALL range: monthly 2006-2024 (benchmark only) + daily 2025+ */
export function allHistorySeries(ctx: EngineContext): ChartPoint[] {
  const out: ChartPoint[] = [];
  const deposit = ctx.snap.deposit;
  const firstPrice = ctx.days[0].spot * ctx.days[0].fx;
  const bhOz = deposit / firstPrice;
  for (const m of MONTHLY_EARLY) {
    out.push({
      date: m.date + '-15',
      value: Math.round(m.last_spot * m.last_fx * bhOz), // hypothetical B&H
      gold: Math.round(m.last_spot * m.last_fx * bhOz),
    });
  }
  out.push(...ctx.state.valueSeries);
  return out;
}

function round2(x: number) { return Math.round(x * 100) / 100; }
