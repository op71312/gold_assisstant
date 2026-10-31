import { NextResponse } from 'next/server';
import { loadManifest, loadPortfolioYear } from '@/lib/project-data';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ portfolioId: string }> },
) {
  const { portfolioId } = await params;
  const match = /^P(20\d{2})\d{4}$/.exec(portfolioId);
  if (!match) {
    return NextResponse.json({ error: 'รหัสพอร์ตไม่ถูกต้อง' }, { status: 400 });
  }

  const cohortYear = Number(match[1]);
  if (cohortYear < 2006 || cohortYear > 2026) {
    return NextResponse.json({ error: 'ไม่พบพอร์ตที่ระบุ' }, { status: 404 });
  }

  const [bundle, manifest] = await Promise.all([
    loadPortfolioYear(cohortYear),
    loadManifest(),
  ]);
  const record = bundle.portfolios.find((item) => item.portfolio.portfolio_id === portfolioId);
  if (!record) {
    return NextResponse.json({ error: 'ไม่พบพอร์ตที่ระบุ' }, { status: 404 });
  }

  return NextResponse.json({
    synthetic: true,
    source: `thai-gold-portfolio-simulator ${manifest.portfolio_run_id}`,
    ...record,
  });
}
