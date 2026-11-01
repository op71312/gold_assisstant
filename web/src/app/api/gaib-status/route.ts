import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 15;

type RuntimeHealth = {
  status?: unknown;
  serviceAuthConfigured?: unknown;
};

function statusResponse(
  status: 'not_configured' | 'starting' | 'unavailable' | 'ready',
  message: string,
) {
  return NextResponse.json(
    { status, message, checkedAt: new Date().toISOString() },
    { headers: { 'Cache-Control': 'no-store, max-age=0' } },
  );
}

export async function GET() {
  const configuredUrl = process.env.GAIB_RUNTIME_URL?.trim();
  const serviceToken = process.env.GAIB_SERVICE_TOKEN?.trim();
  if (!configuredUrl || !serviceToken) {
    return statusResponse('not_configured', 'ยังไม่ได้ตั้งค่า GAIB runtime หรือ service token');
  }

  let healthUrl: URL;
  try {
    healthUrl = new URL(/^[a-z][a-z\d+.-]*:\/\//i.test(configuredUrl) ? configuredUrl : `https://${configuredUrl}`);
  } catch {
    return statusResponse('not_configured', 'GAIB_RUNTIME_URL มีรูปแบบไม่ถูกต้อง');
  }
  if (!['http:', 'https:'].includes(healthUrl.protocol) || healthUrl.username || healthUrl.password) {
    return statusResponse('not_configured', 'GAIB_RUNTIME_URL มีรูปแบบไม่ถูกต้อง');
  }
  healthUrl.pathname = `${healthUrl.pathname.replace(/\/+$/, '')}/health`;
  healthUrl.search = '';
  healthUrl.hash = '';

  try {
    const response = await fetch(healthUrl, {
      cache: 'no-store',
      signal: AbortSignal.timeout(8_000),
    });
    if (response.status === 503) {
      return statusResponse('starting', 'Render กำลังเริ่มบริการ หรือยังตอบ health check ไม่ได้');
    }
    if (!response.ok) {
      return statusResponse('unavailable', `Render health check ตอบกลับ HTTP ${response.status}`);
    }

    const health = await response.json() as RuntimeHealth;
    if (health.status !== 'ok') {
      return statusResponse('unavailable', 'GAIB runtime ยังไม่พร้อมให้บริการ');
    }
    if (health.serviceAuthConfigured !== true) {
      return statusResponse('not_configured', 'ยังไม่ได้ตั้ง GAIB_SERVICE_TOKEN ใน Render backend');
    }
    return statusResponse('ready', 'Render backend ตอบ health check และตั้งค่า service token แล้ว');
  } catch (error) {
    if (error instanceof Error && (error.name === 'TimeoutError' || error.name === 'AbortError')) {
      return statusResponse('starting', 'Render ใช้เวลาตอบนาน อาจกำลัง cold start; ลองตรวจอีกครั้ง');
    }
    return statusResponse('unavailable', 'ติดต่อ Render backend ไม่ได้ ตรวจสถานะและ logs ใน Render');
  }
}
