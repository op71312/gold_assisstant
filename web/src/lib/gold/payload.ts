import type {
  ChartPoint,
  IntradayPoint,
  MacroAnchor,
  MarketFacts,
  NewsItem,
  PortfolioSnapshot,
  StrategyCompareRow,
  TxRow,
} from './types';

export interface MonthlyRow {
  date: string; // YYYY-MM
  hi: number;
  lo: number;
  last_spot: number;
  last_fx: number;
}

export interface SpotPoint {
  date: string;
  spot: number; // XAU/USD
  fx: number; // THB per USD
  barSell: number; // THB per บาททอง
  barBuy: number;
}

export interface MarketPayload {
  coverage: {
    startDate: string;
    dailyObservations: number;
  };
  scenario: {
    id: string;
    name: string;
    categoryLabel: string;
    tagColor: string;
    desc: string;
    disclaimer: string;
    signal: { label: string; tone: 'risk-off' | 'risk-on' | 'mixed' };
    showStrategyCompare: boolean;
  };
  snapshot: PortfolioSnapshot;
  stats: {
    maxDrawdownPct: number;
    maxDrawdownSpan: [string, string] | null;
    volAnnPct: number;
    corrPfBench: number;
    corrGoldDxy: number;
    monthlyReturns: { month: string; ret: number }[];
    hhi: number;
  };
  facts: MarketFacts;
  series: ChartPoint[];
  transactions: TxRow[];
  news: NewsItem[];
  strategyCompare: StrategyCompareRow[] | null;
  macro: MacroAnchor[];
  intraday: IntradayPoint[];
  monthly: MonthlyRow[];
  spotSeries: SpotPoint[];
}

export type { NewsItem };

export interface GaibSource {
  citation_id?: string | null;
  title?: string | null;
  source?: string | null;
  publication_date?: string | null;
  report_period?: string | null;
  url?: string | null;
  text_excerpt?: string | null;
}

export interface GaibPipelineSummary {
  retrieval?: {
    backend?: string | null;
    metrics?: Record<string, unknown>;
    sources?: GaibSource[];
  };
  market?: {
    as_of?: string | null;
    summary?: string | null;
    records?: Record<string, unknown>[];
  };
  hmm?: Record<string, unknown>;
  risk?: {
    status?: string | null;
    records?: Record<string, unknown>[];
  };
  citationAudit?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
}

export type ChatEvent =
  | { type: 'run_start'; question: string; scenario: string; runId?: string }
  | { type: 'analysis_notice'; message: string }
  | { type: 'analysis_mode'; mode: 'connecting' | 'gaib-notebook' }
  | { type: 'agent_start'; agentId: number; name: string; role: string; color: string }
  | { type: 'tool_call'; agentId: number; tool: string }
  | { type: 'tool_result'; agentId: number; tool: string; summary: string; data: Record<string, unknown> }
  | { type: 'thinking_start'; agentId: number }
  | { type: 'thinking_delta'; agentId: number; text: string }
  | { type: 'agent_done'; agentId: number; keyFinding: string; evidence: string[]; thinking?: string; narrationMode: 'gaib-notebook'; status: 'done' | 'error' }
  | { type: 'pipeline_summary'; summary: GaibPipelineSummary }
  | { type: 'pipeline_error'; message: string }
  | { type: 'final_answer'; text: string; agentId: number }
  | { type: 'done' };
