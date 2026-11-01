'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { CheckCircle2, CircleAlert, LoaderCircle, RefreshCw } from 'lucide-react';

type RuntimeStatus = 'checking' | 'not_configured' | 'starting' | 'unavailable' | 'ready';

type StatusPayload = {
  status?: Exclude<RuntimeStatus, 'checking'>;
  message?: string;
};

const RETRY_DELAY_MS = 15_000;
const MAX_AUTOMATIC_RETRIES = 4;

export function GaibRuntimeStatus({ requestPending = false }: { requestPending?: boolean }) {
  const [status, setStatus] = useState<RuntimeStatus>('checking');
  const [message, setMessage] = useState('กำลังตรวจสถานะ GAIB-1 Python service');
  const [checking, setChecking] = useState(false);
  const retriesRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const checkStatus = useCallback(async (manual = false) => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (manual) retriesRef.current = 0;
    setChecking(true);

    let nextStatus: RuntimeStatus = 'unavailable';
    try {
      const response = await fetch('/api/gaib-status', { cache: 'no-store' });
      const payload = await response.json() as StatusPayload;
      nextStatus = payload.status ?? 'unavailable';
      setMessage(payload.message ?? 'ไม่ได้รับรายละเอียดสถานะจาก backend');
    } catch {
      setMessage('ตรวจสถานะจาก Vercel ไม่สำเร็จ ตรวจการเชื่อมต่อแล้วลองอีกครั้ง');
    } finally {
      setStatus(nextStatus);
      setChecking(false);
    }

    if ((nextStatus === 'starting' || nextStatus === 'unavailable') && retriesRef.current < MAX_AUTOMATIC_RETRIES) {
      retriesRef.current += 1;
      timerRef.current = setTimeout(() => {
        void checkStatus();
      }, RETRY_DELAY_MS);
    }
  }, []);

  useEffect(() => {
    void checkStatus();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [checkStatus]);

  const ready = status === 'ready';
  const pending = status === 'checking' || checking;
  const tone = ready
    ? 'border-gain/30 bg-gain/5 text-gain'
    : status === 'starting' || pending
      ? 'border-amber-300 bg-amber-50 text-amber-950'
      : 'border-loss/30 bg-loss/5 text-loss';
  const Icon = ready ? CheckCircle2 : pending ? LoaderCircle : CircleAlert;

  return (
    <section
      className={`flex flex-col gap-3 rounded-xl border px-3.5 py-3 sm:flex-row sm:items-center ${tone}`}
      role="status"
      aria-live="polite"
      aria-label="สถานะ GAIB-1 Python runtime"
    >
      <Icon className={`h-5 w-5 shrink-0 ${pending ? 'animate-spin' : ''}`} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold">
          {ready ? 'GAIB-1 Python service พร้อมรับคำขอ' : status === 'starting' || pending ? 'กำลังเชื่อมต่อกับ Python service' : 'GAIB-1 Python service ยังไม่พร้อม'}
        </p>
        <p className="mt-0.5 text-xs leading-relaxed">{message}</p>
        <p className="mt-1 text-[11px] opacity-80">
          Health check ยืนยันเฉพาะ process และ service token ไม่ได้รับรองว่า provider AI ทุกตัวพร้อมใช้งาน
          {requestPending ? ' · กำลังรอ event แรกจาก pipeline; หากเป็น cold start อาจใช้เวลาสักครู่' : ''}
        </p>
      </div>
      <button
        type="button"
        onClick={() => void checkStatus(true)}
        disabled={checking}
        className="inline-flex min-h-9 shrink-0 items-center justify-center gap-1.5 rounded-lg border border-current/20 bg-white/70 px-3 text-xs font-semibold disabled:cursor-wait disabled:opacity-60"
      >
        <RefreshCw className={`h-3.5 w-3.5 ${checking ? 'animate-spin' : ''}`} />
        ตรวจอีกครั้ง
      </button>
    </section>
  );
}
