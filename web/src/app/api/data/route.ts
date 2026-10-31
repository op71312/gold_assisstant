import { NextResponse } from 'next/server';
import { loadManifest } from '@/lib/project-data';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  const manifest = await loadManifest();
  return NextResponse.json({
    storage: 'versioned-static-json',
    database: false,
    portfolio_run_id: manifest.portfolio_run_id,
    market: manifest.market,
    portfolios: manifest.portfolios,
  });
}
