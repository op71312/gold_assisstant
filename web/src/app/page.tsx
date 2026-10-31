'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import { Menu, X, MessageCircle, RefreshCw, PanelRightOpen } from 'lucide-react';
import { Sidebar } from '@/components/gold/Sidebar';
import { BottomNav } from '@/components/gold/BottomNav';
import { StatsRow } from '@/components/gold/StatsRow';
import { PriceChart, type ChartRange } from '@/components/gold/PriceChart';
import { AllocationPanel } from '@/components/gold/AllocationPanel';
import { TransactionsTable } from '@/components/gold/TransactionsTable';
import { NewsList } from '@/components/gold/NewsList';
import { FooterBanner } from '@/components/gold/FooterBanner';
import { ChatPanel } from '@/components/gold/ChatPanel';
import { HomeView } from '@/components/gold/views/HomeView';
import { AnalysisView } from '@/components/gold/views/AnalysisView';
import { NewsView } from '@/components/gold/views/NewsView';
import { MarketView } from '@/components/gold/views/MarketView';
import { ProjectDetailsView } from '@/components/gold/views/ProjectDetailsView';
import { SettingsView } from '@/components/gold/views/SettingsView';
import { AssistantWorkspace } from '@/components/gold/views/AssistantWorkspace';
import { NewsMarketView } from '@/components/gold/views/NewsMarketView';
import { ScenarioPicker } from '@/components/gold/ScenarioPicker';
import { AGENT_META, type AgentStatus } from '@/components/gold/agent-meta';
import type { MarketPayload } from '@/lib/gold/payload';
import { formatThaiDate } from '@/lib/gold/format';

export default function Home() {
  const [scenarioId, setScenarioId] = useState('real');
  const [range, setRange] = useState<ChartRange>('3M');
  const [data, setData] = useState<MarketPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadedKey, setLoadedKey] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);
  const [activeNav, setActiveNav] = useState('home');
  const [fontScale, setFontScale] = useState<'base' | 'lg' | 'xl'>('base');
  const [chatOpen, setChatOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [activeAgentId, setActiveAgentId] = useState<number | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<Record<number, AgentStatus>>({});
  const [autoQuestion, setAutoQuestion] = useState<string | null>(null);
  const [defaultScenario, setDefaultScenario] = useState('real');
  const hydratedRef = useRef(false);

  // Restore expand/collapse preferences after mount (avoid SSR mismatch).
  // Chat overlay is restored on wide screens only: on small screens a full-screen
  // chat covering the content on first paint is a dead end (UX audit #17).
  useEffect(() => {
    const t = setTimeout(() => {
      try {
        if (localStorage.getItem('ga-sidebar-collapsed') === '1') setSidebarCollapsed(true);
        const isWide = window.matchMedia('(min-width: 1280px)').matches;
        if (isWide) {
          const chat = localStorage.getItem('ga-chat-open');
          if (chat !== null) setChatOpen(chat === '1');
          else setChatOpen(true);
        } else {
          setChatOpen(false);
        }
        const ds = localStorage.getItem('ga-default-scenario');
        if (ds) {
          setDefaultScenario(ds);
          setScenarioId(ds);
        }
        const fs = localStorage.getItem('ga-font-scale');
        if (fs === 'lg' || fs === 'xl') setFontScale(fs);
      } catch {
        // ignore
      }
      hydratedRef.current = true;
    }, 0);
    return () => clearTimeout(t);
  }, []);

  // Reset the chat overlay when crossing the xl breakpoint (mobile/desktop switch)
  useEffect(() => {
    const mq = window.matchMedia('(min-width: 1280px)');
    const onChange = (e: MediaQueryListEvent) => {
      if (!e.matches) setChatOpen(false);
    };
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  useEffect(() => {
    if (!hydratedRef.current) return;
    try {
      localStorage.setItem('ga-sidebar-collapsed', sidebarCollapsed ? '1' : '0');
    } catch {
      // ignore
    }
  }, [sidebarCollapsed]);

  useEffect(() => {
    if (!hydratedRef.current) return;
    try {
      localStorage.setItem('ga-chat-open', chatOpen ? '1' : '0');
    } catch {
      // ignore
    }
  }, [chatOpen]);

  const onAgentActivity = useCallback((agentId: number | null, status: AgentStatus) => {
    setActiveAgentId(agentId);
    if (agentId !== null) {
      setAgentStatuses((prev) => ({ ...prev, [agentId]: status }));
    }
  }, []);

  const pendingKey = `${scenarioId}|${range}|${refreshTick}`;
  const loading = pendingKey !== loadedKey;

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/market?scenario=${scenarioId}&range=${range}`)
      .then((r) => {
        if (!r.ok) throw new Error('โหลดข้อมูลไม่สำเร็จ');
        return r.json();
      })
      .then((d: MarketPayload) => {
        if (!cancelled) {
          setData(d);
          setError(null);
          setLoadedKey(pendingKey);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError((e as Error).message || 'เกิดข้อผิดพลาด');
          setLoadedKey(pendingKey);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [pendingKey, scenarioId, range]);

  const handleNavigate = (id: string) => {
    setActiveNav(id);
    setMobileMenu(false);
  };

  const askFromTab = (q: string) => {
    setAutoQuestion(q);
    setActiveNav('assistant');
    setMobileMenu(false);
  };

  const changeDefaultScenario = (id: string) => {
    setDefaultScenario(id);
    setScenarioId(id);
    try {
      localStorage.setItem('ga-default-scenario', id);
    } catch {
      // ignore
    }
  };

  const changeFontScale = (fs: 'base' | 'lg' | 'xl') => {
    setFontScale(fs);
    try {
      localStorage.setItem('ga-font-scale', fs);
    } catch {
      // ignore
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-cream">
      {/* Desktop sidebar (collapsible) */}
      <div className="hidden lg:block">
        <Sidebar
          active={activeNav}
          onNavigate={handleNavigate}
          activeAgentId={activeAgentId}
          agentStatuses={agentStatuses}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
        />
      </div>

      {/* Mobile menu drawer */}
      {mobileMenu && (
        <div className="fixed inset-0 z-50 bg-navy-deep/60 lg:hidden" onClick={() => setMobileMenu(false)}>
          <div className="h-full w-[260px]" onClick={(e) => e.stopPropagation()}>
            <div className="relative h-full bg-sidebar">
              <button
                onClick={() => setMobileMenu(false)}
                className="absolute right-3 top-3 z-10 rounded-full p-1.5 text-white/70 hover:bg-white/10"
                aria-label="ปิดเมนู"
              >
                <X className="h-5 w-5" />
              </button>
              <Sidebar
                active={activeNav}
                onNavigate={handleNavigate}
                activeAgentId={activeAgentId}
                agentStatuses={agentStatuses}
                collapsed={false}
                onToggleCollapse={() => setMobileMenu(false)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Main column */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top bar: no dead controls. Single cat button = start a team diagnosis. */}
        <header className="flex items-center gap-3 border-b border-border bg-cream/90 px-4 py-3 backdrop-blur md:px-6">
          <button
            onClick={() => setMobileMenu(true)}
            className="rounded-xl p-2 text-foreground/70 hover:bg-accent lg:hidden"
            aria-label="เปิดเมนู"
          >
            <Menu className="h-5 w-5" />
          </button>
          <p className="hidden min-w-0 flex-1 truncate text-sm font-semibold text-foreground/80 sm:block">
            ข้อมูลทองย้อนหลังและพอร์ตตัวอย่าง · วิเคราะห์จากชุดข้อมูลที่ติดตั้ง
          </p>
          <div className="ml-auto flex items-center gap-3">
            <button
              onClick={() => askFromTab('ทำไมพอร์ตเราถึงขาดทุน?')}
              className="group relative h-14 w-20 shrink-0 overflow-hidden rounded-2xl transition-transform hover:scale-[1.02] md:h-20 md:w-28"
              aria-label="ให้ทีม Gold Assistant วินิจฉัยพอร์ต"
              title="ให้ทีม Gold Assistant วินิจฉัยพอร์ต"
            >
              <Image src="/gold/cat-hero.png" alt="Gold Assistant" fill className="object-cover object-top" sizes="112px" />
            </button>
            <span className="hidden max-w-[150px] text-[11px] leading-snug text-muted-foreground lg:block">
              กดรูปแมว
              <br />
              ให้ทีมวินิจฉัยพอร์ต
            </span>
          </div>
        </header>

        {/* Content */}
        <main
          data-font-scale={fontScale}
          className="nice-scroll flex-1 overflow-y-auto px-4 pb-24 pt-5 md:px-6 xl:pb-6"
          role="main"
        >
          {data && activeNav !== 'project' && (
            <div className="mx-auto mb-4 flex max-w-[1180px] flex-wrap items-center gap-x-2 gap-y-1 rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-2.5 text-xs leading-relaxed text-amber-950">
              <strong>โหมดข้อมูลตัวอย่าง</strong>
              <span>
                พอร์ตและธุรกรรมเป็นข้อมูลสาธิต; ราคาย้อนหลังล่าสุด {formatThaiDate(data.facts.lastDate)} · ไม่มีราคาสดหรือบัญชีผู้ใช้จริง
              </span>
            </div>
          )}

          {loading && !data && (
            <div className="flex h-[60vh] flex-col items-center justify-center gap-3 text-muted-foreground">
              <RefreshCw className="h-8 w-8 animate-spin text-gold" />
              <p className="text-sm">กำลังโหลดชุดข้อมูลตัวอย่าง...</p>
            </div>
          )}

          {error && !data && (
            <div className="mx-auto mt-10 max-w-md rounded-2xl border border-loss/30 bg-white p-6 text-center">
              <p className="mb-3 text-sm font-semibold text-loss">{error}</p>
              <button
                onClick={() => setRefreshTick((t) => t + 1)}
                className="rounded-xl gold-gradient px-4 py-2 text-sm font-semibold text-navy-deep"
              >
                ลองใหม่
              </button>
            </div>
          )}

          {data && activeNav === 'home' && (
            <div className="mx-auto max-w-[1080px] transition-opacity">
              <HomeView data={data} onGoTab={handleNavigate} onAskSample={askFromTab} />
            </div>
          )}

          {data && activeNav === 'assistant' && (
            <div className="mx-auto max-w-[1180px] transition-opacity">
              <AssistantWorkspace
                data={data}
                onAgentActivity={onAgentActivity}
                autoQuestion={autoQuestion}
                onAutoQuestionConsumed={() => setAutoQuestion(null)}
              />
            </div>
          )}

          {data && activeNav === 'portfolio' && (
            <div className={`mx-auto max-w-[1080px] space-y-5 transition-opacity ${loading ? 'opacity-50' : 'opacity-100'}`}>
              <ScenarioPicker value={scenarioId} onChange={setScenarioId} />
              <StatsRow data={data} />

              <div className="grid grid-cols-1 gap-5 xl:grid-cols-[1.55fr_1fr]">
                <div className="space-y-5">
                  <PriceChart data={data} range={range} onRangeChange={setRange} />
                  <TransactionsTable data={data} />
                </div>
                <div className="space-y-5">
                  <AllocationPanel data={data} />
                  <NewsList data={data} />
                </div>
              </div>

              <FooterBanner />
            </div>
          )}

          {data && activeNav === 'analysis' && (
            <div className={`mx-auto max-w-[1080px] transition-opacity ${loading ? 'opacity-50' : 'opacity-100'}`}>
              <AnalysisView data={data} />
            </div>
          )}

          {data && (activeNav === 'news' || activeNav === 'market') && (
            <div className={`mx-auto max-w-[1080px] transition-opacity ${loading ? 'opacity-50' : 'opacity-100'}`}>
              <NewsMarketView data={data} initialTab={activeNav === 'market' ? 'market' : 'news'} />
            </div>
 )}

          {data && activeNav === 'project' && (
            <div className="mx-auto max-w-[1080px] transition-opacity">
              <ProjectDetailsView data={data} onOpenAssistant={() => handleNavigate('assistant')} />
            </div>
          )}

          {data && activeNav === 'settings' && (
            <div className="mx-auto max-w-[1080px] transition-opacity">
              <SettingsView
                data={data}
                defaultScenario={defaultScenario}
                onDefaultScenarioChange={changeDefaultScenario}
                fontScale={fontScale}
                onFontScaleChange={changeFontScale}
              />
            </div>
          )}

        </main>
      </div>

      {/* Mobile bottom navigation: 4 top jobs + menu drawer */}
      <BottomNav active={activeNav} onNavigate={handleNavigate} onOpenMenu={() => setMobileMenu(true)} />

      {/* Chat: single instance, desktop collapsible column / mobile overlay */}
      {data && (
        <div
          className={
            activeNav === 'assistant'
              ? 'hidden'
              : chatOpen
              ? 'fixed inset-0 z-50 flex bg-navy-deep/60 backdrop-blur-sm xl:static xl:z-auto xl:h-auto xl:w-auto xl:shrink-0 xl:border-l xl:border-sidebar-border xl:bg-transparent xl:backdrop-blur-none'
              : 'hidden xl:flex xl:h-auto xl:shrink-0'
          }
        >
          <div
            className={`h-full transition-[width] duration-300 ease-out ${
              chatOpen ? 'mx-auto w-full max-w-md xl:mx-0 xl:w-[404px] xl:max-w-none' : 'w-14'
            }`}
          >
            {/* Panel stays mounted (display:none when collapsed) so history is preserved */}
            <div className={`h-full w-full xl:w-[404px] ${chatOpen ? '' : 'hidden'}`}>
              <ChatPanel
                data={data}
                onAgentActivity={onAgentActivity}
                onClose={chatOpen ? () => setChatOpen(false) : undefined}
                onCollapse={() => setChatOpen(false)}
              />
            </div>

            {/* Collapsed rail (desktop) */}
            {!chatOpen && (
              <div className="hidden h-full w-14 flex-col items-center gap-3 border-l border-sidebar-border bg-cream/70 py-4 xl:flex">
                <button
                  onClick={() => setChatOpen(true)}
                  className="flex h-11 w-11 items-center justify-center rounded-2xl gold-gradient transition-transform"
                  aria-label="ขยายแผง Gold Assistant"
                  title="ขยายแผง Gold Assistant"
                >
                  <PanelRightOpen className="h-5 w-5 text-navy-deep" />
                </button>
                <span className="select-none text-[11px] font-bold tracking-[0.22em] text-muted-foreground/80 [writing-mode:vertical-rl]">
                  GOLD ASSISTANT
                </span>
                <div className="mt-auto flex flex-col items-center gap-1.5 pb-1">
                  {AGENT_META.map((a) => {
                    const st = agentStatuses[a.id] ?? 'idle';
                    return (
                      <span
                        key={a.id}
                        className={`h-2 w-2 rounded-full ${st !== 'idle' ? 'animate-pulse' : 'opacity-25'}`}
                        style={{ backgroundColor: a.color }}
                        title={`${a.name}${st !== 'idle' ? ' (กำลังทำงาน)' : ''}`}
                      />
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mobile floating chat button (sits above the bottom nav) */}
      {data && activeNav !== 'assistant' && !chatOpen && (
        <button
          onClick={() => {
            setActiveNav('assistant');
            setChatOpen(true);
          }}
          className="fixed bottom-20 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full gold-gradient shadow-xl transition-transform xl:bottom-5"
          aria-label="เปิดแชต Gold Assistant"
        >
          <MessageCircle className="h-6 w-6 text-navy-deep" />
        </button>
      )}
    </div>
  );
}
