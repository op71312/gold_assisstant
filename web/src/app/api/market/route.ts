import { NextRequest, NextResponse } from 'next/server';
import { buildContext, chartSeries, allHistorySeries, INTRADAY, MONTHLY_EARLY, type Range } from '@/lib/gold/engine';
import { toolNewsSearch } from '@/lib/gold/tools';
import { strategyCompare } from '@/lib/gold/portfolio';
import { SCENARIOS } from '@/lib/gold/scenarios';
import type { NewsItem } from '@/lib/gold/types';

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const scenarioId = sp.get('scenario') ?? 'real';
  const rangeValue = sp.get('range') ?? '3M';
  const ranges: Range[] = ['1D', '1W', '1M', '3M', '6M', '1Y', 'ALL'];

  if (!SCENARIOS.some((scenario) => scenario.id === scenarioId)) {
    return NextResponse.json({ error: 'ไม่รู้จักสถานการณ์ที่เลือก' }, { status: 400 });
  }
  if (!ranges.includes(rangeValue as Range)) {
    return NextResponse.json({ error: 'ช่วงเวลาที่เลือกไม่ถูกต้อง' }, { status: 400 });
  }
  const range = rangeValue as Range;

  const ctx = buildContext(scenarioId);
  const series = range === 'ALL' ? allHistorySeries(ctx) : chartSeries(ctx, range);
  const newsTool = toolNewsSearch({ ...ctx, question: 'ทำไมพอร์ตทองของเราถึงขาดทุน' });

  // Map tool result into full NewsItem shape (tool returns move5dPct; payload contract uses marketMovePct + tags)
  const tagsByTitle = new Map(ctx.scenario.news.map((n) => [n.title, n.tags] as const));
  const news: NewsItem[] = (
    newsTool.data.news as { date: string; title: string; source: string; sentiment: NewsItem['sentiment']; impact: NewsItem['impact']; move5dPct: number }[]
  ).map((n) => ({
    date: n.date,
    title: n.title,
    source: n.source,
    sentiment: n.sentiment,
    impact: n.impact,
    tags: tagsByTitle.get(n.title) ?? [],
    marketMovePct: n.move5dPct,
  }));

  const payload = {
    coverage: {
      startDate: ctx.days[0]?.date ?? ctx.facts.lastDate,
      dailyObservations: ctx.days.length,
    },
    scenario: {
      id: ctx.scenario.id,
      name: ctx.scenario.name,
      categoryLabel: ctx.scenario.categoryLabel,
      tagColor: ctx.scenario.tagColor,
      desc: ctx.scenario.desc,
      disclaimer: ctx.scenario.disclaimer,
      signal: ctx.scenario.signal,
      showStrategyCompare: ctx.scenario.showStrategyCompare,
    },
    snapshot: ctx.snap,
    stats: {
      maxDrawdownPct: ctx.stats.maxDrawdownPct,
      maxDrawdownSpan: ctx.stats.maxDrawdownSpan,
      volAnnPct: ctx.stats.volAnnPct,
      corrPfBench: ctx.stats.corrPfBench,
      corrGoldDxy: ctx.stats.corrGoldDxy,
      monthlyReturns: ctx.stats.monthlyReturns,
      hhi: ctx.stats.hhi,
    },
    facts: ctx.facts,
    series,
    transactions: ctx.stats.txRows,
    news,
    strategyCompare: ctx.scenario.showStrategyCompare ? strategyCompare(ctx.days) : null,
    macro: ctx.scenario.macroAnchors,
    intraday: INTRADAY,
    monthly: MONTHLY_EARLY,
    spotSeries: ctx.days.slice(-365).map((d) => ({ date: d.date, spot: d.spot, fx: d.fx, barSell: d.barSell, barBuy: d.barBuy })),
  };

  return NextResponse.json(payload);
}
