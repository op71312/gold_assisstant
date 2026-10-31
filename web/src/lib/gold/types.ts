export interface DayPoint {
  date: string; // YYYY-MM-DD
  spot: number; // XAU/USD per oz
  fx: number; // THB per USD
  barSell: number; // Thai bar price (customer buy), THB per บาททอง
  barBuy: number;
}

export interface IntradayPoint {
  t: string; // HH:MM
  spot: number;
  barSell: number;
}

export interface MarketFacts {
  lastDate: string;
  lastSpot: number;
  lastFx: number;
  lastBarSell: number;
  athDate: string;
  athSpot: number;
  postAthTroughDate: string;
  postAthTroughSpot: number;
  postAthDropPct: number;
  maxDrawdownPct: number;
  maxDrawdownSpan: [string, string] | null;
  changeFromAthPct: number;
  barFromAthPct: number;
  ytd2025FirstSpot: number;
}

export interface RawMarketData {
  daily: DayPoint[];
  intradayLastDay: IntradayPoint[];
  monthlyEarly: { date: string; hi: number; lo: number; last_spot: number; last_fx: number }[];
  facts: MarketFacts;
}

export interface Tx {
  id: string;
  date: string;
  side: 'BUY' | 'SELL';
  oz: number;
  spot: number; // USD/oz executed
  fx: number; // THB/USD executed
  note: string;
}

export interface NewsItem {
  date: string;
  title: string;
  source: string;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  impact: 'high' | 'medium' | 'low';
  tags: string[];
  marketMovePct: number; // gold % move within 5 trading days after
}

export interface MacroAnchor {
  date: string;
  dxy: number;
  us10y: number; // %
  wti: number; // $
}

export type ScenarioCategory = 'real' | 'macro' | 'geo' | 'behavior';

export interface Scenario {
  id: string;
  name: string;
  category: ScenarioCategory;
  categoryLabel: string;
  tagColor: string; // tailwind-friendly hex
  shortDesc: string;
  desc: string;
  disclaimer: string;
  signal: { label: string; tone: 'risk-off' | 'risk-on' | 'mixed' };
  news: NewsItem[];
  macroAnchors: MacroAnchor[];
  /** transform spot/fx for dates >= startDate (deterministic) */
  transform?: (date: string, i: number, spot: number, fx: number) => { spot: number; fx: number };
  transformStart: string; // apply transform from this date
  showStrategyCompare: boolean;
}

export interface PortfolioSnapshot {
  deposit: number;
  cash: number;
  goldOz: number;
  avgCostThbPerOz: number;
  goldValueThb: number;
  portfolioValue: number;
  totalPl: number;
  totalPlPct: number;
  unrealizedPl: number;
  realizedPl: number;
  goldWeightPct: number;
  cashWeightPct: number;
  spotNow: number;
  fxNow: number;
  barPriceNow: number;
  pricePerOzThb: number;
  changeFromAthPct: number;
}

export interface ChartPoint {
  date: string;
  value: number; // portfolio THB
  gold: number; // benchmark buy&hold THB (same deposit)
}

export interface TxRow {
  id: string;
  date: string;
  side: 'BUY' | 'SELL';
  oz: number;
  spot: number;
  thbPerOz: number;
  amountThb: number;
  plThb: number | null; // realized for SELL, unrealized-marked for BUY
  status: string;
  note: string;
}

export interface StrategyCompareRow {
  name: string;
  finalValue: number;
  pl: number;
  plPct: number;
  invested: number;
  note: string;
  highlight?: boolean;
}

export interface AgentFinding {
  agentId: number;
  keyFinding: string;
  evidence: string[];
}

export interface ToolResult {
  agentId: number;
  toolName: string;
  summary: string;
  data: Record<string, unknown>;
}
