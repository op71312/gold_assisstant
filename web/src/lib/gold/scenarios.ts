import type { Scenario, DayPoint } from './types';

// ---------------------------------------------------------------------------
// Deterministic pseudo-noise (stable across requests)
// ---------------------------------------------------------------------------
function hash01(seed: number): number {
  const x = Math.sin(seed * 12.9898) * 43758.5453;
  return x - Math.floor(x); // 0..1
}

function ramp(i: number, n: number): number {
  return Math.max(0, Math.min(1, i / Math.max(1, n)));
}

// ---------------------------------------------------------------------------
// News: real-market themed items (sources reflect actual 2026 market events)
// ---------------------------------------------------------------------------
const REAL_NEWS = [
  {
    date: '2026-01-29',
    title: 'ทองคำทำสถิติสูงสุดใหม่แตะ $5,516/oz ทองแท่งไทยแตะ ฿81,500 ก่อนเทกะไล่ราคา',
    source: 'ราคาทองราคา.com / Bloomberg',
    sentiment: 'bullish' as const,
    impact: 'high' as const,
    tags: ['ATH', 'FOMO', 'reconciliation'],
    marketMovePct: 0,
  },
  {
    date: '2026-02-05',
    title: 'ทองร่วงหนักสุดวันเดียวในรอบ 10 ปี -10% จาก $5,377 ทดสอบ $4,688 แรงเทขายรับกำไร',
    source: 'ฮั่วเซ่งเฮง / LINE TODAY',
    sentiment: 'bearish' as const,
    impact: 'high' as const,
    tags: ['correction', 'profit-taking'],
    marketMovePct: -9.4,
  },
  {
    date: '2026-02-28',
    title: 'ทองเด้งกลับแรงปิดเดือนที่ $5,280 นักลงทุนหวังวงจรขาขึ้นกลับมา เงินบาทแข็ง 31.07',
    source: 'ราคาทองราคา.com',
    sentiment: 'bullish' as const,
    impact: 'medium' as const,
    tags: ['rebound', 'false-hope'],
    marketMovePct: -14.9,
  },
  {
    date: '2026-03-27',
    title: 'ทองหลุด $4,500 กลางเดือน มี.ค. นักวิเคราะห์ชี้ ETF ตะวันตกไหลออกหนักต่อเนื่อง',
    source: 'RoboForex / WGC',
    sentiment: 'bearish' as const,
    impact: 'high' as const,
    tags: ['ETF-outflow', 'breakdown'],
    marketMovePct: -9.2,
  },
  {
    date: '2026-04-13',
    title: 'สหรัฐประกาศปิดล้อมท่าเรืออิหร่าน ทองย่อตัวลงแทนที่จะขึ้น UBP ยืนยันเป้า $6,000 เพิ่มน้ำหนักทองเป็น 6%',
    source: 'GBI Direct / Union Bancaire Privée',
    sentiment: 'neutral' as const,
    impact: 'high' as const,
    tags: ['geopolitics', 'blockade'],
    marketMovePct: -1.7,
  },
  {
    date: '2026-07-01',
    title: 'ทองแตะต่ำสุด $3,988 สะสมขาลง -27.7% จากจุดสูงสุด ปรับฐานรอบใหญ่รอบที่ 2 ของปี',
    source: 'ฐานเศรษฐกิจ',
    sentiment: 'bearish' as const,
    impact: 'high' as const,
    tags: ['trough', 'technical-selling'],
    marketMovePct: 9.1,
  },
  {
    date: '2026-08-24',
    title: 'ธนาคารกลางซื้อทองจ่อ 800 ตัน/ปี (JPMorgan) ดันทองเด้งแรงขึ้น $4,648 สูงสุดรอบ 5 เดือน',
    source: 'World Gold Council / JPMorgan',
    sentiment: 'bullish' as const,
    impact: 'medium' as const,
    tags: ['central-bank', 'rebound'],
    marketMovePct: -12.1,
  },
  {
    date: '2026-10-20',
    title: 'ทองอึดอัดแคบรอบ $4,100 ตลาดรอนโยบายดอกเบี้ยเฟด ดัชนี DXY แข็งค่าสุดในรอบ 3 เดือน',
    source: 'LiteFinance / ฮั่วเซ่งเฮง',
    sentiment: 'neutral' as const,
    impact: 'medium' as const,
    tags: ['range-bound', 'DXY'],
    marketMovePct: -0.3,
  },
];

const MACRO_NEWS = [
  {
    date: '2026-08-06',
    title: '[จำลอง] เฟดประชุมสภาพันธ์: ยันคงดอกเบี้ยสูงต่อเนื่อง เงินเฟ้อจากน้ำมันยังเหนียวแน่น',
    source: 'Scenario Engine',
    sentiment: 'bearish' as const,
    impact: 'high' as const,
    tags: ['Fed', 'hawkish'],
    marketMovePct: -2.1,
  },
  {
    date: '2026-09-02',
    title: '[จำลอง] เงินเฟ้อสหรัฐพุ่ง 4.9% ตลาดตัดโอกาสลดดอกเบี้ยปีนี้เหลือ 5% กดดันทองหนัก',
    source: 'Scenario Engine',
    sentiment: 'bearish' as const,
    impact: 'high' as const,
    tags: ['inflation', 'rates'],
    marketMovePct: -3.8,
  },
  {
    date: '2026-09-18',
    title: '[จำลอง] ดัชนี DXY ทะลุ 106 แข็งค่าสุดในรอบ 2 ปี ทองหลุด $3,800 เป็นครั้งแรกตั้งแต่ปี 2025',
    source: 'Scenario Engine',
    sentiment: 'bearish' as const,
    impact: 'high' as const,
    tags: ['DXY', 'dollar-strength'],
    marketMovePct: -2.9,
  },
  {
    date: '2026-10-14',
    title: '[จำลอง] พันธบัตร 10 ปีสหรัฐแตะ 4.85% ต้นทุนค่าเสียโอกาสถือทองสูงสุดในรอบ 15 ปี',
    source: 'Scenario Engine',
    sentiment: 'bearish' as const,
    impact: 'medium' as const,
    tags: ['yield', 'opportunity-cost'],
    marketMovePct: -1.4,
  },
  {
    date: '2026-10-21',
    title: '[จำลอง] กองทุน ETF ทองคำไหลออกสะสม 180 ตันในไตรมาส เงินบาทแข็ง 31.7 กดราคาทองบาทซ้ำ',
    source: 'Scenario Engine',
    sentiment: 'bearish' as const,
    impact: 'medium' as const,
    tags: ['ETF-outflow', 'THB'],
    marketMovePct: -0.8,
  },
];

const GEO_NEWS = [
  {
    date: '2026-08-20',
    title: '[จำลอง] เรือบรรทุกน้ำมันถูกโจมตีในอ่าวฮอร์มุซ น้ำมัน WTI พุ่ง +25% ทองวิ่งหาที่หลบภัย',
    source: 'Scenario Engine',
    sentiment: 'bullish' as const,
    impact: 'high' as const,
    tags: ['Hormuz', 'oil', 'war'],
    marketMovePct: 8.6,
  },
  {
    date: '2026-09-12',
    title: '[จำลอง] ทองทำสถิติใหม่ $5,682/oz แซงจุดสูงสุดเดือน ม.ค. กระแส Fear & Greed เข้าโซน Extreme Greed',
    source: 'Scenario Engine',
    sentiment: 'bullish' as const,
    impact: 'high' as const,
    tags: ['new-ATH', 'euphoria'],
    marketMovePct: -6.4,
  },
  {
    date: '2026-09-26',
    title: '[จำลอง] ประกาศหยุดยิง + ปฏิบัติการคุ้มครองเรือสำเร็จ น้ำมันดิ่ง -18% ทองถูกเทขายหนัก',
    source: 'Scenario Engine',
    sentiment: 'bearish' as const,
    impact: 'high' as const,
    tags: ['ceasefire', 'whipsaw'],
    marketMovePct: -16.2,
  },
  {
    date: '2026-10-15',
    title: '[จำลอง] ทองลงไปตั้งหลัก $4,300 นักกลยุทธ์เตือน "ตลาดวูบวาบแบบนี้คือกับดักนักลงทุนรายย่อย"',
    source: 'Scenario Engine',
    sentiment: 'neutral' as const,
    impact: 'medium' as const,
    tags: ['whipsaw', 'retail-trap'],
    marketMovePct: -0.5,
  },
];

// ---------------------------------------------------------------------------
// Macro anchors (deterministic paths for DXY / US10Y / WTI)
// ---------------------------------------------------------------------------
const REAL_MACRO = [
  { date: '2025-11-14', dxy: 99.4, us10y: 4.05, wti: 68.5 },
  { date: '2026-01-29', dxy: 96.8, us10y: 3.88, wti: 72.0 },
  { date: '2026-02-05', dxy: 98.9, us10y: 4.02, wti: 70.5 },
  { date: '2026-03-27', dxy: 100.6, us10y: 4.18, wti: 66.0 },
  { date: '2026-04-13', dxy: 99.8, us10y: 4.12, wti: 63.5 },
  { date: '2026-07-01', dxy: 98.2, us10y: 4.02, wti: 74.0 },
  { date: '2026-08-24', dxy: 97.8, us10y: 4.02, wti: 68.0 },
  { date: '2026-09-15', dxy: 100.2, us10y: 4.35, wti: 64.0 },
  { date: '2026-10-22', dxy: 102.4, us10y: 4.48, wti: 61.0 },
];

const MACRO_HAWK_MACRO = [
  { date: '2025-11-14', dxy: 99.4, us10y: 4.05, wti: 68.5 },
  { date: '2026-07-31', dxy: 97.8, us10y: 4.02, wti: 74.0 },
  { date: '2026-08-06', dxy: 98.9, us10y: 4.15, wti: 78.0 },
  { date: '2026-09-02', dxy: 101.5, us10y: 4.42, wti: 80.0 },
  { date: '2026-09-18', dxy: 106.2, us10y: 4.68, wti: 81.0 },
  { date: '2026-10-14', dxy: 106.8, us10y: 4.85, wti: 82.0 },
  { date: '2026-10-22', dxy: 106.5, us10y: 4.83, wti: 81.0 },
];

const HORMUZ_MACRO = [
  { date: '2025-11-14', dxy: 99.4, us10y: 4.05, wti: 68.5 },
  { date: '2026-07-31', dxy: 97.8, us10y: 4.02, wti: 74.0 },
  { date: '2026-08-20', dxy: 96.9, us10y: 3.96, wti: 92.0 },
  { date: '2026-09-12', dxy: 94.5, us10y: 3.75, wti: 97.0 },
  { date: '2026-09-26', dxy: 98.2, us10y: 4.08, wti: 79.0 },
  { date: '2026-10-15', dxy: 99.8, us10y: 4.18, wti: 68.0 },
  { date: '2026-10-22', dxy: 100.1, us10y: 4.2, wti: 66.5 },
];

// ---------------------------------------------------------------------------
// Scenarios (4 categories, as requested by the user)
// ---------------------------------------------------------------------------
export const SCENARIOS: Scenario[] = [
  {
    id: 'real',
    name: 'คอร์เรกชันหลังจุดสูงสุด',
    category: 'real',
    categoryLabel: 'ข้อมูลย้อนหลัง',
    tagColor: '#D9A441',
    shortDesc: 'ชุดข้อมูลย้อนหลังถึง ต.ค. 69',
    desc: 'แสดงชุดข้อมูลราคาย้อนหลังที่ติดตั้งมากับแอป พร้อมพอร์ตและธุรกรรมตัวอย่างสำหรับทดลองวิเคราะห์ ข้อมูลไม่ใช่ราคาสด และพอร์ตนี้ไม่ใช่บัญชีของผู้ใช้',
    disclaimer: 'ชุดข้อมูลย้อนหลังและธุรกรรมตัวอย่างใช้เพื่อการศึกษาเท่านั้น; ไม่ได้เชื่อมผู้ให้บริการราคาสดหรือบัญชีการลงทุนจริง',
    signal: { label: 'Risk Off', tone: 'risk-off' },
    news: REAL_NEWS,
    macroAnchors: REAL_MACRO,
    transformStart: '9999-12-31', // no transform, real data
    showStrategyCompare: false,
  },
  {
    id: 'macro',
    name: 'เฟดเข้มงวด + ดอลลาร์แข็ง',
    category: 'macro',
    categoryLabel: 'จำลองมหภาค',
    tagColor: '#1F7A4D',
    shortDesc: 'เฟดไม่ลดดอกเบี้ย DXY → 106',
    desc: 'จำลองกรณีเงินเฟ้อน้ำมันยั่งยืนทำให้เฟดต้องคงดอกเบี้ยสูงตลอดปี ดัชนีดอลลาร์ DXY แข็งค่าต่อเนื่องทะลุ 106 พันธบัตร 10 ปีแตะ 4.85% ทองคำจึงถูกกดดันจากต้นทุนค่าเสียโอกาสและแรงซื้อ ETF ที่ไหลออก ราคาจบที่ราว $3,600',
    disclaimer: 'สถานการณ์สมมติเชิงมหภาค (จำลองจากโมเดลอัตราแลกเปลี่ยน-ดอกเบี้ยที่ปรับจากข้อมูลจริงถึง ก.ค. 69) ไม่ใช่คำพยากรณ์',
    signal: { label: 'Risk Off', tone: 'risk-off' },
    news: MACRO_NEWS,
    macroAnchors: MACRO_HAWK_MACRO,
    transformStart: '2026-08-01',
    showStrategyCompare: false,
    transform: (date, i, spot, fx) => {
      const days = i % 84; // index within ~4-month window
      const r = ramp(days, 82);
      const noise = (hash01(days + 7) - 0.5) * 0.012;
      const spotMul = 1 - 0.115 * r + noise * r;
      const fxMul = 1 - 0.058 * r + noise * r * 0.5; // THB strengthens harder
      return { spot: spot * spotMul, fx: fx * fxMul };
    },
  },
  {
    id: 'geo',
    name: 'วิกฤตฮอร์มุซรอบสอง',
    category: 'geo',
    categoryLabel: 'จำลองภูมิรัฐศาสตร์',
    tagColor: '#C23A3F',
    shortDesc: 'น้ำมันพุ่ง ทองทำ ATH ใหม่ แล้ววูบ',
    desc: 'จำลองการโจมตีเรือในอ่าวฮอร์มุซปลาย ส.ค. 69 น้ำมันพุ่ง +25% ทองคำวิ่งทำสถิติใหม่ราว $5,680 กลาง ก.ย. ก่อนพังทลายเมื่อมีประกาศหยุดยิงปลาย ก.ย. จบที่ราว $4,290 สถานการณ์วูบวาบ (whipsaw) แบบที่นักลงทุนรายย่อยแพ้มาที่สุด',
    disclaimer: 'สถานการณ์สมมติเชิงภูมิรัฐศาสตร์ อ้างอิงความผันผวนจากเหตุการณ์จริงช่วงต้นปี 69 เพื่อการศึกษาพฤติกรรมพอร์ต',
    signal: { label: 'Whipsaw · ผันผวนสูงมาก', tone: 'mixed' },
    news: GEO_NEWS,
    macroAnchors: HORMUZ_MACRO,
    transformStart: '2026-08-20',
    showStrategyCompare: false,
    transform: (date, i, spot, fx) => {
      // i = days since 2026-08-20
      const noise = (hash01(i + 31) - 0.5) * 0.018;
      let spotMul: number;
      let fxMul: number;
      if (i <= 23) {
        // Aug 20 -> Sep 12 : rally to new ATH (+38%)
        const r = ramp(i, 23);
        spotMul = 1 + 0.38 * r + noise;
        fxMul = 1 + 0.026 * r; // THB weakens on oil shock
      } else if (i <= 37) {
        // Sep 12 -> Sep 26 : high & volatile
        spotMul = 1.38 - (i - 23) * 0.004 + noise * 2;
        fxMul = 1.026 - (i - 23) * 0.001;
      } else if (i <= 51) {
        // Sep 26 -> Oct 10 : crash on ceasefire
        const r = ramp(i - 37, 14);
        spotMul = 1.328 - 0.278 * r + noise * 2;
        fxMul = 1.012 - 0.018 * r;
      } else {
        // settle ~ +5% above pre-crisis
        spotMul = 1.05 + noise * 0.6;
        fxMul = 0.995 + noise * 0.3;
      }
      return { spot: spot * spotMul, fx: fx * fxMul };
    },
  },
  {
    id: 'behavior',
    name: 'พอร์ตจริง vs DCA vs ถือยาว',
    category: 'behavior',
    categoryLabel: 'จำลองพฤติกรรม',
    tagColor: '#6D5BA6',
    shortDesc: 'ราคาเดิม เทียบ 3 กลยุทธ์การลงทุน',
    desc: 'ใช้ราคาจริงชุดเดียวกับสถานการณ์ "เหตุการณ์จริง" แต่เปรียบเทียบพฤติกรรมการลงทุน 3 แบบบนเงินลงทุนเท่ากัน: (1) พอร์ตจริงที่ซื้อขายตามอารมณ์ (2) DCA ฝากเดือนละ ฿150,000 (3) ถือยาวซื้อครั้งเดียวตั้งแต่วันแรก เพื่อวัด "Behavior Gap" ซึ่งคือต้นทุนที่จ่ายไปกับการตัดสินใจ',
    disclaimer: 'การจำลองกลยุทธ์ใช้ราคาปิดประกาศรายวัน ไม่รวมค่าธรรมเนียมและภาษี สมมติซื้อได้ทุกวันทำการที่ราคาประกาศ',
    signal: { label: 'Risk Off', tone: 'risk-off' },
    news: REAL_NEWS,
    macroAnchors: REAL_MACRO,
    transformStart: '9999-12-31',
    showStrategyCompare: true,
  },
];

export function getScenario(id: string): Scenario {
  return SCENARIOS.find((s) => s.id === id) ?? SCENARIOS[0];
}

/** Apply scenario transform to a full daily series (mutable copy). */
export function applyScenario(base: DayPoint[], scenario: Scenario): DayPoint[] {
  if (!scenario.transform || scenario.transformStart === '9999-12-31') return base;
  const startIdx = base.findIndex((d) => d.date >= scenario.transformStart);
  if (startIdx < 0) return base;
  return base.map((d, i) => {
    if (i < startIdx) return d;
    const t = scenario.transform!(d.date, i - startIdx, d.spot, d.fx);
    return { ...d, spot: round2(t.spot), fx: round4(t.fx), barSell: Math.round((d.barSell * t.spot) / d.spot / 50) * 50 };
  });
}

function round2(x: number) { return Math.round(x * 100) / 100; }
function round4(x: number) { return Math.round(x * 10000) / 10000; }

/** Interpolate DXY / US10Y / WTI to daily values for a date range. */
export function macroAt(anchors: Scenario['macroAnchors'], date: string): { dxy: number; us10y: number; wti: number } {
  if (date <= anchors[0].date) return pick(anchors[0]);
  for (let i = 1; i < anchors.length; i++) {
    if (date <= anchors[i].date) {
      const a = anchors[i - 1];
      const b = anchors[i];
      const t = (Date.parse(date) - Date.parse(a.date)) / (Date.parse(b.date) - Date.parse(a.date) || 1);
      return {
        dxy: a.dxy + (b.dxy - a.dxy) * t,
        us10y: a.us10y + (b.us10y - a.us10y) * t,
        wti: a.wti + (b.wti - a.wti) * t,
      };
    }
  }
  return pick(anchors[anchors.length - 1]);
}

function pick(a: Scenario['macroAnchors'][number]) {
  return { dxy: a.dxy, us10y: a.us10y, wti: a.wti };
}
