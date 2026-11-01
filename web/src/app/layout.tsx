import type { Metadata, Viewport } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "Gold Assistant | พอร์ตทองคำอัจฉริยะ | Smart Gold Portfolio",
  description:
    "เดโมวิเคราะห์พอร์ตทองด้วยข้อมูลย้อนหลังและธุรกรรมตัวอย่าง ไม่มีราคาสดหรือบัญชีลงทุนจริง",
  keywords: ["ทองคำ", "พอร์ตลงทุน", "Gold Portfolio", "Gold Assistant", "XAUSUSD", "ราคาทองไทย"],
  icons: {
    icon: "/gold/logo.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#1C2942",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="th" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link
          href="https://fonts.googleapis.com/css2?family=Prompt:wght@400;500;600;700;800&family=Noto+Sans+Thai:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased bg-background text-foreground font-sans">
        {children}
        <Toaster />
        <Analytics />
      </body>
    </html>
  );
}
