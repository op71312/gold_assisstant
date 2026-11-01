import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false,
  outputFileTracingIncludes: {
    "/api": ["./data/manifest.json"],
    "/api/data": ["./data/manifest.json"],
    "/api/data/market": ["./data/market-history.json.gz"],
    "/api/data/portfolios": ["./data/portfolio-catalog.json.gz"],
    "/api/data/portfolios/[portfolioId]": ["./data/manifest.json", "./data/portfolio-years/*.json.gz"],
  },
};

export default nextConfig;
