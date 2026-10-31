'use client';

import { useEffect, useState } from 'react';
import { Settings2, Database, BellRing, SlidersHorizontal, Info, Save } from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { ViewHeader } from './shared';
import { SCENARIOS } from '@/lib/gold/scenarios';
import type { MarketPayload } from '@/lib/gold/payload';

interface Props {
  data: MarketPayload;
  defaultScenario: string;
  onDefaultScenarioChange: (id: string) => void;
  fontScale: 'base' | 'lg' | 'xl';
  onFontScaleChange: (fs: 'base' | 'lg' | 'xl') => void;
}

interface Prefs {
  autoOpenChat: boolean;
  showThinkingDetail: boolean;
  notifyPriceAlert: boolean;
  notifyNewsAlert: boolean;
  compactTable: boolean;
}

const DEFAULT_PREFS: Prefs = {
  autoOpenChat: true,
  showThinkingDetail: true,
  notifyPriceAlert: true,
  notifyNewsAlert: false,
  compactTable: false,
};

function readPrefs(): Prefs {
  try {
    const raw = localStorage.getItem('ga-prefs');
    if (raw) return { ...DEFAULT_PREFS, ...(JSON.parse(raw) as Partial<Prefs>) };
  } catch {
    // ignore
  }
  return DEFAULT_PREFS;
}

export function SettingsView({ data, defaultScenario, onDefaultScenarioChange, fontScale, onFontScaleChange }: Props) {
  const [prefs, setPrefs] = useState<Prefs>(DEFAULT_PREFS);
  const [savedTick, setSavedTick] = useState(0);
  const facts = data.facts;

  useEffect(() => {
    const t = setTimeout(() => setPrefs(readPrefs()), 0);
    return () => clearTimeout(t);
  }, []);

  const update = (patch: Partial<Prefs>) => {
    const next = { ...prefs, ...patch };
    setPrefs(next);
    try {
      localStorage.setItem('ga-prefs', JSON.stringify(next));
    } catch {
      // ignore
    }
    setSavedTick((t) => t + 1);
  };

  return (
    <div className="space-y-5">
      <ViewHeader
        title="ตั้งค่า"
        subtitle="ปรับพฤติกรรมการแสดงผล โหมดจำลองเริ่มต้น และการแจ้งเตือน (บันทึกในเครื่องของคุณ)"
        data={data}
        right={
          savedTick > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-gain/12 px-2.5 py-1 text-[11px] font-bold text-gain">
              <Save className="h-3 w-3" /> บันทึกแล้ว
            </span>
          )
        }
      />

      {/* Simulation default */}
      <section className="card-warm rounded-2xl p-5">
        <div className="mb-3 flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">โหมดจำลองเริ่มต้นเมื่อเปิดเว็บ</h3>
        </div>
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
          {SCENARIOS.map((s) => {
            const isActive = defaultScenario === s.id;
            return (
              <button
                key={s.id}
                onClick={() => {
                  onDefaultScenarioChange(s.id);
                  setSavedTick((t) => t + 1);
                }}
                className={`rounded-2xl border p-3 text-left transition-all ${
                  isActive ? 'border-gold bg-accent' : 'border-border bg-white hover:border-gold/50'
                }`}
              >
                <span className="mb-1 inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold text-white" style={{ backgroundColor: s.tagColor }}>
                  {s.categoryLabel}
                </span>
                <p className="text-[13px] font-semibold leading-snug">{s.name}</p>
              </button>
            );
          })}
        </div>
        <p className="mt-2.5 text-[11px] text-muted-foreground">
          ทุกแท็บ (พอร์ต, วิเคราะห์, ข่าว, ข้อมูลตลาด) จะใช้ข้อมูลจำลองตามสถานการณ์ที่เลือก และทีมนักวิเคราะห์ 5 ตัวจะวินิจฉัยบนข้อมูลชุดเดียวกัน
        </p>
      </section>

      {/* Text size: older users / low-vision control (deep research: seniors segment) */}
      <section className="card-warm rounded-2xl p-5">
        <div className="mb-3 flex items-center gap-2">
          <Settings2 className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">ขนาดตัวอักษร</h3>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {(
            [
              ['base', 'ปกติ', 'A'],
              ['lg', 'ใหญ่', 'A+'],
              ['xl', 'ใหญ่มาก', 'A++'],
            ] as ['base' | 'lg' | 'xl', string, string][]
          ).map(([id, label, badge]) => (
            <button
              key={id}
              onClick={() => onFontScaleChange(id)}
              aria-pressed={fontScale === id}
              className={`inline-flex min-h-[44px] items-center gap-2 rounded-2xl border px-4 py-2 transition-colors ${
                fontScale === id ? 'border-gold bg-accent text-accent-foreground' : 'border-border bg-white text-foreground/75 hover:border-gold/50'
              }`}
            >
              <span className={`font-display font-bold ${id === 'base' ? 'text-sm' : id === 'lg' ? 'text-base' : 'text-lg'}`}>{badge}</span>
              {label}
            </button>
          ))}
          <p className="text-[11px] text-muted-foreground">ขยายเฉพาะเนื้อหาหลัก เมนูและแผงด้านข้างคงขนาดเดิม</p>
        </div>
      </section>

      {/* Display prefs */}
      <section className="card-warm rounded-2xl p-5">
        <div className="mb-3 flex items-center gap-2">
          <Settings2 className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">การแสดงผลและพฤติกรรม</h3>
        </div>
        <ul className="space-y-1">
          <PrefRow
            title="เปิดแผง Gold Assistant อัตโนมัติบนจอกว้าง"
            desc="ถ้าปิด แผงแชตจะย่อเป็นแถบด้านขวาจนกว่าจะกดขยายเอง"
            checked={prefs.autoOpenChat}
            onChange={(v) => update({ autoOpenChat: v })}
          />
          <PrefRow
            title="แสดงความคิดแบบละเอียดของนักวิเคราะห์"
            desc="เปิดเพื่อให้ห้องทำงานแสดงทุกขั้นตอน: คิด → เรียกเครื่องมือ → อ่านผล → ข้อค้นพบ"
            checked={prefs.showThinkingDetail}
            onChange={(v) => update({ showThinkingDetail: v })}
          />
          <PrefRow
            title="ตารางธุรกรรมแบบกระชับ"
            desc="ซ่อนคอลัมน์รอง เหลือวันที่ ฝั่งซื้อ-ขาย และจำนวนเงิน"
            checked={prefs.compactTable}
            onChange={(v) => update({ compactTable: v })}
          />
        </ul>
      </section>

      {/* Notifications (mock) */}
      <section className="card-warm rounded-2xl p-5">
        <div className="mb-3 flex items-center gap-2">
          <BellRing className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">การแจ้งเตือน (สาธิต)</h3>
        </div>
        <ul className="space-y-1">
          <PrefRow
            title="แจ้งเตือนราคาทองแตะระดับที่ตั้งไว้"
            desc="ตัวอย่าง: แจ้งเมื่อทองแท่งแตะ 65,000 ฿/บาททอง (ในดีโมนี้ยังไม่ส่งจริง)"
            checked={prefs.notifyPriceAlert}
            onChange={(v) => update({ notifyPriceAlert: v })}
          />
          <PrefRow
            title="แจ้งข่าว impact สูงทันที"
            desc="ข่าวระดับ 'ผลกระทบสูง' จะเด้งเข้ากระดิ่งด้านบน"
            checked={prefs.notifyNewsAlert}
            onChange={(v) => update({ notifyNewsAlert: v })}
          />
        </ul>
      </section>

      {/* About data */}
      <section className="rounded-2xl border border-gold/40 bg-accent/40 p-5">
        <div className="mb-2.5 flex items-center gap-2">
          <Database className="h-4 w-4 text-gold-deep" />
          <h3 className="font-display text-sm font-bold">เกี่ยวกับข้อมูลที่ใช้</h3>
        </div>
        <ul className="space-y-1.5 text-xs leading-relaxed text-accent-foreground/90">
          <li>• ชุดข้อมูลราคาทองประกาศรายวันของไทย {formatThaiDate('2006-05-01')} ถึง {formatThaiDate(facts.lastDate)} (ราคาแท่ง 96.5% บาททองละ 15.244 กรัม)</li>
          <li>• ตัวแปรมหภาค (DXY, US 10Y, WTI) เป็นค่าอ้างอิงจุดสำคัญของแต่ละสถานการณ์ ใช้เพื่ออธิบายกลไก ไม่ใช่ feed สด</li>
          <li>• พอร์ตผู้ใช้เป็นการจำลองเชิงสาธิต (เงินลงทุนตั้งต้น 500,000 ฿) คำนวณด้วยต้นทุนเฉลี่ยถ่วงน้ำหนัก ไม่รวมส่วนเกินร้านทองและภาษี</li>
          <li>• ทั้งหมดมีไว้เพื่อการศึกษา ไม่ใช่คำแนะนำการลงทุน</li>
        </ul>
        <p className="mt-2.5 flex items-start gap-1.5 text-[11px] italic text-muted-foreground">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" /> การตั้งค่าทั้งหมดเก็บใน localStorage ของเบราว์เซอร์นี้เท่านั้น ไม่มีการส่งขึ้นเซิร์ฟเวอร์
        </p>
      </section>
    </div>
  );
}

function PrefRow({ title, desc, checked, onChange }: { title: string; desc: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <li className="flex items-center justify-between gap-4 rounded-2xl bg-muted/40 px-4 py-3">
      <span className="min-w-0">
        <span className="block text-[13px] font-semibold">{title}</span>
        <span className="block text-[11px] leading-relaxed text-muted-foreground">{desc}</span>
      </span>
      <Switch checked={checked} onCheckedChange={onChange} aria-label={title} />
    </li>
  );
}

function formatThaiDate(d: string) {
  const [y, m, day] = d.split('-');
  const months = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
  const mi = parseInt(m, 10) - 1;
  return `${day ? parseInt(day, 10) + ' ' : ''}${months[mi] ?? m} ${parseInt(y, 10) + 543}`;
}
