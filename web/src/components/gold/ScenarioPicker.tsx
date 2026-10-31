'use client';

import { useState } from 'react';
import { FlaskConical, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { SCENARIOS } from '@/lib/gold/scenarios';

interface ScenarioPickerProps {
  value: string;
  onChange: (id: string) => void;
}

/**
 * Compact scenario picker: one chip row + collapsible detail.
 * The default "real" scenario must not push the user's portfolio below the fold
 * (UX audit #8: the old 4-card band buried the portfolio).
 */
export function ScenarioPicker({ value, onChange }: ScenarioPickerProps) {
  const [open, setOpen] = useState(false);
  const current = SCENARIOS.find((s) => s.id === value);

  return (
    <section aria-label="โหมดจำลองพอร์ต" className="card-warm rounded-2xl px-4 py-3.5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="flex items-center gap-1.5 text-xs font-bold text-accent-foreground">
          <FlaskConical className="h-3.5 w-3.5 text-gold-deep" /> สถานการณ์ที่ใช้:
        </span>
        <div className="flex flex-1 flex-wrap gap-1.5">
          {SCENARIOS.map((s) => {
            const isActive = s.id === value;
            return (
              <button
                key={s.id}
                onClick={() => onChange(s.id)}
                aria-pressed={isActive}
                className={`inline-flex min-h-[36px] items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11.5px] font-semibold transition-colors ${
                  isActive ? 'border-gold bg-accent text-accent-foreground' : 'border-border bg-white text-foreground/75 hover:border-gold/50'
                }`}
              >
                {isActive && <Check className="h-3 w-3 text-gold-deep" />}
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.tagColor }} aria-hidden />
                {s.name}
              </button>
            );
          })}
        </div>
        <button
          onClick={() => setOpen((v) => !v)}
          className="inline-flex min-h-[36px] items-center gap-1 rounded-full bg-muted/70 px-3 py-1.5 text-[11px] font-semibold text-muted-foreground hover:bg-muted"
          aria-expanded={open}
        >
          รายละเอียด {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </button>
      </div>
      {open && current && (
        <div className="mt-3 flex flex-col gap-1 rounded-2xl bg-muted/60 p-3.5">
          <p className="text-xs leading-relaxed text-foreground/85">{current.desc}</p>
          <p className="text-[11px] italic text-muted-foreground">{current.disclaimer}</p>
        </div>
      )}
    </section>
  );
}
