// Thai formatting helpers (client-safe)

const THAI_MONTHS_ABBR = [
  'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
  'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.',
];

export function formatThaiDate(date: string): string {
  // date = YYYY-MM-DD or YYYY-MM
  const [y, m, d] = date.split('-');
  const mi = parseInt(m, 10) - 1;
  const month = THAI_MONTHS_ABBR[mi] ?? m;
  const by = (parseInt(y, 10) + 543).toString();
  if (d) return `${parseInt(d, 10)} ${month} ${by}`;
  return `${month} ${by}`;
}

export function formatBaht(x: number, showSign = false): string {
  const sign = showSign && x > 0 ? '+' : x < 0 ? '-' : '';
  return `${sign}฿${Math.abs(Math.round(x)).toLocaleString('en-US')}`;
}

export function formatPct(x: number, showSign = true): string {
  const sign = showSign && x > 0 ? '+' : '';
  return `${sign}${x.toFixed(2)}%`;
}

export function formatBahtShort(x: number): string {
  const abs = Math.abs(x);
  if (abs >= 1_000_000) return `${(x / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `${(x / 1_000).toFixed(0)}K`;
  return x.toFixed(0);
}
