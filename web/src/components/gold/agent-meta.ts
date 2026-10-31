import { Newspaper, Globe2, Sigma, ShieldAlert, Crown, type LucideIcon } from 'lucide-react';

export interface AgentMeta {
  id: number;
  name: string;
  role: string;
  color: string;
  icon: LucideIcon;
  /** รูปแมวประจำตัว (แต่ละตัวเป็นแมวคนละแบบ) */
  avatar: string;
  /** ชื่อเครื่องมือหลักที่แสดงบนการ์ดในกราฟ */
  tool: string;
  /** บรรทัดสรุปสั้น (ไม่เกิน 15 คำ) แสดงบนหน้าแรก: ตัวนี้ช่วยอะไรได้ */
  takeaway: string;
}

export const AGENT_META: AgentMeta[] = [
  { id: 1, name: 'News Analyst', role: 'ค้นหลักฐานข่าวจาก RAG และแยกข้อเท็จจริงจากการตีความ', color: '#3e5f8a', icon: Newspaper, avatar: '/gold/agents/cat-1.png', tool: 'GAIB-1 RAG evidence review', takeaway: 'สรุปเฉพาะข้อเท็จจริงที่มีแหล่งอ้างอิง' },
  { id: 2, name: 'Macro Analyst', role: 'อ่าน market snapshot และอธิบายกลไกมหภาคอย่างระมัดระวัง', color: '#3e7c5b', icon: Globe2, avatar: '/gold/agents/cat-2.png', tool: 'GAIB-1 market snapshot analysis', takeaway: 'เชื่อมตัวเลขตลาดกับปัจจัยมหภาคโดยไม่อ้างเหตุและผลเกินข้อมูล' },
  { id: 3, name: 'Quant + Regime Analyst', role: 'สรุปสถิติจาก feature dataset และผล Gaussian HMM', color: '#6d5ba6', icon: Sigma, avatar: '/gold/agents/cat-3.png', tool: 'GAIB-1 quant + Gaussian HMM', takeaway: 'รายงาน regime และตัวเลขย้อนหลังพร้อมข้อจำกัด' },
  { id: 4, name: 'Risk & Data Auditor', role: 'ตรวจสอบความเสี่ยง คุณภาพข้อมูล และการกระทบยอด', color: '#b4690e', icon: ShieldAlert, avatar: '/gold/agents/cat-4.png', tool: 'GAIB-1 risk and accounting audit', takeaway: 'แจ้งความเสี่ยงและจุดที่ข้อมูลยังยืนยันไม่ได้' },
  { id: 5, name: 'Lead Researcher', role: 'ตรวจ citation และสังเคราะห์คำตอบจากผล agent 1 ถึง 4', color: '#0f766e', icon: Crown, avatar: '/gold/agents/cat-5.png', tool: 'GAIB-1 citation audit + synthesis', takeaway: 'งดข้อกล่าวอ้างที่ไม่มีหลักฐานรองรับ' },
];

export type AgentStatus = 'idle' | 'thinking' | 'tool' | 'reading' | 'done' | 'error';

export const STATUS_LABEL: Record<AgentStatus, string> = {
  idle: 'พร้อมทำงาน',
  thinking: 'กำลังคิด...',
  tool: 'กำลังเรียกเครื่องมือ...',
  reading: 'กำลังอ่านผลลัพธ์...',
  done: 'เสร็จสิ้น',
  error: 'ผลลัพธ์ไม่ผ่านการตรวจสอบ',
};

/** ป้ายกำกับเส้นหลักฐานที่แต่ละตัวส่งเข้าหา Lead Researcher */
export const EVIDENCE_LABEL: Record<number, string> = {
  1: 'หลักฐานข่าว',
  2: 'สัญญาณแมโคร',
  3: 'สถิติ & ตัวเลข',
  4: 'ข้อจำกัด & ความเสี่ยง',
};
