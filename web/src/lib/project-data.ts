import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { gunzip } from 'node:zlib';
import { promisify } from 'node:util';

export interface ProjectDataManifest {
  schema_version: number;
  portfolio_run_id: string;
  market: {
    source: string;
    start_date: string;
    end_date: string;
    rows: number;
    missing_spot_rows: number;
    missing_fx_rows: number;
    imputed_values: number;
    sha256: string;
  };
  portfolios: {
    source_tables: string[];
    count: number;
    valuation_rows: number;
    transaction_rows: number;
    all_synthetic: boolean;
    sha256: Record<string, string>;
  };
}

export interface ProjectDataRow {
  [column: string]: string | number | boolean | null;
}

export interface ProjectDataBundle<T> {
  manifest: Record<string, unknown>;
  rows: T[];
}

export interface PortfolioYearBundle {
  cohort_year: number;
  portfolios: {
    portfolio: ProjectDataRow;
    valuation: ProjectDataRow[];
    transactions: ProjectDataRow[];
  }[];
}

const dataRoot = path.join(process.cwd(), 'data');
const cache = new Map<string, Promise<unknown>>();
const gunzipAsync = promisify(gunzip);

async function loadJson<T>(relativePath: string): Promise<T> {
  let pending = cache.get(relativePath) as Promise<T> | undefined;
  if (!pending) {
    pending = readFile(path.join(dataRoot, relativePath)).then(async (contents) => {
      const text = relativePath.endsWith('.gz')
        ? (await gunzipAsync(contents)).toString('utf8')
        : contents.toString('utf8');
      return JSON.parse(text) as T;
    });
    cache.set(relativePath, pending);
    pending.catch(() => cache.delete(relativePath));
  }
  return pending;
}

export const loadManifest = () => loadJson<ProjectDataManifest>('manifest.json');
export const loadMarketHistory = () => loadJson<ProjectDataBundle<ProjectDataRow>>('market-history.json.gz');
export const loadPortfolioCatalog = () => loadJson<ProjectDataBundle<ProjectDataRow>>('portfolio-catalog.json.gz');

export function loadPortfolioYear(year: number) {
  return loadJson<PortfolioYearBundle>(path.join('portfolio-years', `${year}.json.gz`));
}
