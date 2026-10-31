import { NextRequest, NextResponse } from 'next/server';
import { loadPortfolioCatalog } from '@/lib/project-data';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function parseInteger(value: string | null, fallback: number, min: number, max: number): number | null {
  if (value === null) return fallback;
  if (!/^\d+$/.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= min && parsed <= max ? parsed : null;
}

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;
  const limit = parseInteger(params.get('limit'), 25, 1, 100);
  const offset = parseInteger(params.get('offset'), 0, 0, Number.MAX_SAFE_INTEGER);
  const yearValue = params.get('year');
  const year = yearValue === null ? null : parseInteger(yearValue, 0, 2006, 2026);
  const behavior = params.get('behavior');
  const segment = params.get('segment');

  if (limit === null || offset === null || (yearValue !== null && year === null)) {
    return NextResponse.json({ error: 'ตัวกรอง limit, offset หรือ year ไม่ถูกต้อง' }, { status: 400 });
  }
  if (behavior && !/^[a-z_]+$/.test(behavior)) {
    return NextResponse.json({ error: 'behavior ไม่ถูกต้อง' }, { status: 400 });
  }
  if (segment && !/^[a-z_]+$/.test(segment)) {
    return NextResponse.json({ error: 'segment ไม่ถูกต้อง' }, { status: 400 });
  }

  const bundle = await loadPortfolioCatalog();
  let rows = bundle.rows;
  if (year !== null) rows = rows.filter((row) => row.cohort_start_year === year);
  if (behavior) rows = rows.filter((row) => row.behavior_scenario === behavior);
  if (segment) rows = rows.filter((row) => row.portfolio_segment === segment);

  return NextResponse.json({
    source: bundle.manifest,
    synthetic: true,
    total: rows.length,
    offset,
    limit,
    rows: rows.slice(offset, offset + limit),
  });
}
