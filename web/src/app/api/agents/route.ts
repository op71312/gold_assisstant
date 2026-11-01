import { NextResponse } from 'next/server';
import { z } from 'zod';

export const runtime = 'nodejs';
export const maxDuration = 300;

const requestSchema = z.object({
  question: z.string().trim().min(1, 'กรุณาพิมพ์คำถาม').max(500, 'คำถามยาวเกิน 500 ตัวอักษร'),
  scenario: z.string().optional(),
});

function runtimeUrl(): string | null {
  const configured = process.env.GAIB_RUNTIME_URL?.trim();
  if (!configured) return null;

  try {
    const url = new URL(/^[a-z][a-z\d+.-]*:\/\//i.test(configured) ? configured : `https://${configured}`);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) return null;
    return url.toString().replace(/\/+$/, '');
  } catch {
    return null;
  }
}

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'รูปแบบคำขอไม่ถูกต้อง' }, { status: 400 });
  }

  const parsed = requestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message ?? 'ข้อมูลคำขอไม่ถูกต้อง' }, { status: 400 });
  }

  const upstreamUrl = runtimeUrl();
  const serviceToken = process.env.GAIB_SERVICE_TOKEN?.trim();
  if (!upstreamUrl || !serviceToken) {
    const missing: string[] = [];
    if (!upstreamUrl) missing.push('GAIB_RUNTIME_URL (Vercel service binding)');
    if (!serviceToken) missing.push('GAIB_SERVICE_TOKEN');
    return NextResponse.json(
      { error: `GAIB-1 runtime ยังไม่ได้ตั้งค่า: ${missing.join(' และ ')}` },
      { status: 503 },
    );
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${upstreamUrl}/api/agents`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${serviceToken}`,
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({ question: parsed.data.question }),
      cache: 'no-store',
      signal: request.signal,
    });
  } catch {
    return NextResponse.json(
      { error: 'เชื่อมต่อ GAIB-1 Python runtime ไม่ได้ ตรวจสอบสถานะบริการแล้วลองใหม่' },
      { status: 502 },
    );
  }

  const headers = new Headers({
    'Cache-Control': 'no-cache, no-transform',
    'X-Accel-Buffering': 'no',
  });
  const contentType = upstream.headers.get('content-type');
  if (contentType) headers.set('Content-Type', contentType);

  return new Response(upstream.body, {
    status: upstream.status,
    headers,
  });
}
