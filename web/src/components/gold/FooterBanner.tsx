'use client';

import Image from 'next/image';

export function FooterBanner() {
  return (
    <section aria-label="แบนเนอร์ปิดท้าย" className="relative overflow-hidden rounded-2xl">
      <div className="relative h-[190px] w-full md:h-[220px]">
        <Image
          src="/gold/cat-footer.png"
          alt="แมววิเชียรมาสนอนบนกองทองคำหน้าเมืองยามค่ำคืน"
          fill
          unoptimized
          className="object-cover"
          sizes="(max-width: 768px) 100vw, 800px"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-navy-deep/75 via-transparent to-transparent" />
        <div className="absolute bottom-4 left-5 right-5 flex flex-wrap items-end justify-between gap-2">
          <div className="text-white drop-shadow">
            <p className="font-display text-sm font-semibold md:text-base">ทุกการตรวจสอบ นำไปสู่ผลลัพธ์ที่ดีเสมอ</p>
            <p className="text-[11px] text-white/75">ด้วยรอยยิ้มของทีมนักวิเคราะห์ทั้ง 5 ตัว ✦</p>
          </div>
          <p className="text-[11px] text-white/60">Gold Assistant · ชุดข้อมูลย้อนหลังถึง ต.ค. 2569</p>
        </div>
      </div>
      {/* Trust strip: visible on every money tab (deep research: trust surfaces) */}
      <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-2xl border border-border bg-white px-4 py-2.5 text-[11px] text-muted-foreground">
        <span className="font-semibold text-foreground/75">Gold Assistant</span>
        <span>พอร์ตและข่าวเป็นข้อมูลตัวอย่าง · ไม่มีราคาสด</span>
        <span>คำวิเคราะห์ของทีมเป็นความเห็น ไม่ใช่คำแนะนำการลงทุน</span>
        <span className="text-loss/80">AI อาจผิดพลาด ตรวจสอบก่อนตัดสินใจเสมอ</span>
      </div>
    </section>
  );
}
