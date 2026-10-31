'use client';

import Image from 'next/image';
import {
  Home,
  Wallet,
  LineChart,
  Newspaper,
  Settings,
  MessageCircleMore,
  Database,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react';
import { Logo } from './Logo';
import { AGENT_META, type AgentStatus, STATUS_LABEL } from './agent-meta';

const NAV = [
  { id: 'home', label: 'หน้าแรก', icon: Home },
  { id: 'assistant', label: 'Gold Assistant', icon: MessageCircleMore },
  { id: 'portfolio', label: 'พอร์ตการลงทุน', icon: Wallet },
  { id: 'analysis', label: 'วิเคราะห์', icon: LineChart },
  { id: 'news', label: 'ข่าว & ตลาด', icon: Newspaper },
  { id: 'project', label: 'ข้อมูลโครงการ', icon: Database },
  { id: 'settings', label: 'ตั้งค่า', icon: Settings },
];

interface SidebarProps {
  active: string;
  onNavigate: (id: string) => void;
  activeAgentId: number | null;
  agentStatuses: Record<number, AgentStatus>;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function Sidebar({
  active,
  onNavigate,
  activeAgentId,
  agentStatuses,
  collapsed,
  onToggleCollapse,
}: SidebarProps) {
  return (
    <aside
      className={`flex h-full shrink-0 flex-col bg-sidebar text-sidebar-foreground transition-[width] duration-300 ease-out ${
        collapsed ? 'w-[76px]' : 'w-[248px]'
      }`}
    >
      {/* Logo */}
      <div className={`flex items-center gap-3 pt-6 pb-4 ${collapsed ? 'flex-col px-2' : 'px-5'}`}>
        <div className="relative shrink-0">
          <span className="block overflow-hidden rounded-full ring-2 ring-gold/70">
            <Logo size={collapsed ? 42 : 48} />
          </span>
          {collapsed && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full gold-gradient text-[11px] font-bold text-navy-deep shadow">
              5
            </span>
          )}
        </div>
        {!collapsed && (
          <div className="min-w-0 flex-1">
            <div className="font-display text-xl font-bold leading-tight text-white">
              Gold Assistant <span className="text-gold">✦</span>
            </div>
            <div className="text-[11px] leading-tight text-sidebar-foreground/60">
              Smarter Portfolio
              <br />
              Brighter Tomorrow
            </div>
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          className={`hidden shrink-0 items-center justify-center rounded-xl text-sidebar-foreground/60 transition-colors hover:bg-sidebar-accent hover:text-gold-soft lg:flex ${
            collapsed ? 'mt-3 h-8 w-8' : 'h-8 w-8 self-start'
          }`}
          aria-label={collapsed ? 'ขยายแถบเมนู' : 'ย่อแถบเมนู'}
          title={collapsed ? 'ขยายแถบเมนู' : 'ย่อแถบเมนู'}
        >
          {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        </button>
      </div>

      {/* Nav */}
      <nav className={`mt-2 flex flex-col gap-1 ${collapsed ? 'px-3' : 'px-3'}`} aria-label="เมนูหลัก">
        {NAV.map((n) => {
          const isActive = active === n.id;
          return (
            <button
              key={n.id}
              onClick={() => onNavigate(n.id)}
              className={`group relative flex items-center rounded-xl text-left text-sm font-medium transition-colors ${
                collapsed ? 'justify-center px-0 py-2.5' : 'gap-3 px-3.5 py-2.5'
              } ${
                isActive
                  ? n.id === 'assistant'
                    ? 'border border-gold/40 bg-gradient-to-r from-gold/20 to-transparent text-gold-soft'
                    : 'bg-sidebar-accent text-gold-soft'
                  : 'text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground'
              }`}
              aria-current={isActive ? 'page' : undefined}
              title={collapsed ? n.label : undefined}
            >
              <n.icon
                className={`${collapsed ? 'h-5 w-5' : 'h-[18px] w-[18px]'}`}
                style={isActive ? { color: '#f2cf7d' } : undefined}
              />
              {!collapsed && n.label}
              {collapsed && (
                <span className="pointer-events-none absolute left-[calc(100%+12px)] top-1/2 z-50 -translate-y-1/2 whitespace-nowrap rounded-lg bg-navy-deep px-2.5 py-1.5 text-[11px] font-medium text-white opacity-0 transition-opacity group-hover:opacity-100">
                  {n.label}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Mascot card */}
      {!collapsed && (
        <div className="mx-4 mt-5 overflow-hidden rounded-2xl border border-sidebar-border bg-sidebar-accent/50">
          <div className="relative h-28 w-full">
            <Image
              src="/gold/cat-hero.png"
              alt="แมววิเชียรมาสกอดทองคำ"
              fill
              className="object-cover object-top"
              sizes="216px"
            />
          </div>
          <div className="px-3.5 py-2.5 text-center text-xs leading-relaxed text-gold-soft/90">
            ทองอาจแกว่ง แต่หลักฐานต้องแน่น
            <br />
            <span className="text-sidebar-foreground/60">วิเคราะห์ก่อนตัดสินใจเสมอ</span>
          </div>
        </div>
      )}

      {/* Analyst team */}
      <div
        className={`mx-4 mt-4 mb-4 flex-1 rounded-2xl border border-sidebar-border bg-navy-deep/60 ${
          collapsed ? 'p-2.5' : 'p-3.5'
        }`}
      >
        {!collapsed && (
          <>
            <div className="mb-2.5 flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-lg gold-gradient text-[11px] font-bold text-navy-deep">
                5
              </span>
              <div className="text-[13px] font-semibold text-gold-soft">ทีมนักวิเคราะห์ 5 ตัว</div>
            </div>
            <div className="text-[11px] text-sidebar-foreground/55 mb-3">กำลังทำงานเพื่อคุณ</div>
          </>
        )}
        <ul className={`flex flex-col gap-1.5 ${collapsed ? 'items-center' : ''}`}>
          {AGENT_META.map((a) => {
            const st = agentStatuses[a.id] ?? 'idle';
            const isActive = activeAgentId === a.id;
            return (
              <li
                key={a.id}
                className={`flex items-center rounded-xl transition-all ${
                  collapsed ? 'justify-center p-1' : 'gap-2.5 px-2.5 py-2'
                } ${isActive ? 'agent-active bg-sidebar-accent' : 'hover:bg-sidebar-accent/50'}`}
                title={collapsed ? `${a.name} · ${st !== 'idle' ? STATUS_LABEL[st] : a.role}` : undefined}
              >
                <span className="relative shrink-0">
                  <span
                    className="flex h-7 w-7 items-center justify-center rounded-full text-white"
                    style={{ backgroundColor: a.color }}
                  >
                    <a.icon className="h-3.5 w-3.5" />
                  </span>
                  <span className="absolute -right-1 -top-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-navy-deep text-[11px] font-bold text-gold-soft ring-1 ring-gold/50">
                    {a.id}
                  </span>
                </span>
                {!collapsed && (
                  <span className="min-w-0">
                    <span className="block truncate text-xs font-semibold text-sidebar-foreground/90">{a.name}</span>
                    <span className="block truncate text-[11px] text-sidebar-foreground/50">
                      {st !== 'idle' ? STATUS_LABEL[st] : a.role}
                    </span>
                  </span>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    </aside>
  );
}
