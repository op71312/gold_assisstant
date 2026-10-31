interface LogoProps {
  size?: number;
  className?: string;
}

/** Gold Assistant brand mark: gold coin with rising bars + sparkle */
export function Logo({ size = 44, className = '' }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label="Gold Assistant"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="ga-coin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f7df9a" />
          <stop offset="0.5" stopColor="#d9a441" />
          <stop offset="1" stopColor="#b8860b" />
        </linearGradient>
      </defs>
      <circle cx="32" cy="32" r="30" fill="url(#ga-coin)" />
      <circle cx="32" cy="32" r="30" fill="none" stroke="#8a6410" strokeOpacity="0.35" strokeWidth="2" />
      <circle cx="32" cy="32" r="24" fill="none" stroke="#ffffff" strokeOpacity="0.45" strokeWidth="1.5" />
      <rect x="18" y="34" width="6" height="12" rx="2" fill="#16203a" opacity="0.8" />
      <rect x="27" y="28" width="6" height="18" rx="2" fill="#16203a" opacity="0.9" />
      <rect x="36" y="22" width="6" height="24" rx="2" fill="#16203a" />
      <path d="M46 14l1.9 4.6 4.6 1.9-4.6 1.9-1.9 4.6-1.9-4.6-4.6-1.9 4.6-1.9z" fill="#fff8e1" />
    </svg>
  );
}
