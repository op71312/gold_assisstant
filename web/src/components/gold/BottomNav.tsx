'use client';

import { Home, MessageCircleMore, Wallet, Newspaper, Menu } from 'lucide-react';

const ITEMS = [
  { id: 'home', label: 'หน้าแรก', icon: Home },
  { id: 'assistant', label: 'ทีมวิเคราะห์', icon: MessageCircleMore },
  { id: 'portfolio', label: 'พอร์ต', icon: Wallet },
  { id: 'news', label: 'ข่าว & ตลาด', icon: Newspaper },
] as const;

/**
 * Bottom navigation for mobile (< xl). 5-second-reach to the four top jobs.
 * "เมนู" opens the full drawer (the remaining tabs live there).
 */
export function BottomNav({
  active,
  onNavigate,
  onOpenMenu,
}: {
  active: string;
  onNavigate: (id: string) => void;
  onOpenMenu: () => void;
}) {
  return (
    <nav
      aria-label="เมนูหลัก (มือถือ)"
      className="fixed inset-x-0 bottom-0 z-40 border-t border-sidebar-border bg-sidebar pb-[env(safe-area-inset-bottom)] xl:hidden"
    >
      <ul className="grid grid-cols-5">
        {ITEMS.map((it) => {
          const isActive = active === it.id;
          return (
            <li key={it.id}>
              <button
                onClick={() => onNavigate(it.id)}
                aria-current={isActive ? 'page' : undefined}
                className={`flex w-full flex-col items-center gap-0.5 py-2 text-[10.5px] font-semibold transition-colors ${
                  isActive ? 'text-gold-soft' : 'text-sidebar-foreground/65'
                }`}
              >
                <it.icon className="h-[18px] w-[18px]" style={isActive ? { color: '#f2cf7d' } : undefined} />
                {it.label}
              </button>
            </li>
          );
        })}
        <li>
          <button
            onClick={onOpenMenu}
            className="flex w-full flex-col items-center gap-0.5 py-2 text-[10.5px] font-semibold text-sidebar-foreground/65 transition-colors"
          >
            <Menu className="h-[18px] w-[18px]" />
            เมนู
          </button>
        </li>
      </ul>
    </nav>
  );
}
