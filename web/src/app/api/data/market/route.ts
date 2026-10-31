import { NextRequest, NextResponse } from 'next/server';
import { loadMarketHistory } from '@/lib/project-data';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function parseDate(value: string | null): string | null | undefined {
  if (value === null) return undefined;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (Number.isNaN(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== value) return null;
  return value;
}

function parseInteger(value: string | null, fallback: number, min: number, max: number): number | null {
  if (value === null) return fallback;
  if (!/^\d+$/.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed >= min && parsed <= max ? parsed : null;
}

export async function GET(req: NextRequest) {
  const params = req.nextUrl.searchParams;
  const from = parseDate(params.get('from'));
  const to = parseDate(params.get('to'));
  const limit = parseInteger(params.get('limit'), 100, 1, 500);
  const offset = parseInteger(params.get('offset'), 0, 0, Number.MAX_SAFE_INTEGER);
  const order = params.get('order') ?? 'desc';

  if (from === null || to === null) {
    return NextResponse.json({ error: 'วันที่ต้องอยู่ในรูปแบบ YYYY-MM-DD' }, { status: 400 });
  }
  if (order !== 'asc' && order !== 'desc') {
    return NextResponse.json({ error: 'order ต้องเป็น asc หรือ desc' }, { status: 400 });
  }
  if (limit === null || offset === null) {
    return NextResponse.json({ error: 'limit ต้องอยู่ระหว่าง 1–500 และ offset ต้องเป็นจำนวนเต็มไม่ติดลบ' }, { status: 400 });
  }
  if (from && to && from > to) {
    return NextResponse.json({ error: 'from ต้องไม่อยู่หลัง to' }, { status: 400 });
  }

  const bundle = await loadMarketHistory();
  const rows = bundle.rows.filter((row) => {
    const date = String(row.date).slice(0, 10);
    return (!from || date >= from) && (!to || date <= to);
  });
  if (order === 'desc') rows.reverse();

  return NextResponse.json({
    source: bundle.manifest,
    total: rows.length,
    offset,
    limit,
    rows: rows.slice(offset, offset + limit),
  });
}
