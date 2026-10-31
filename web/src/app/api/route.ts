import { NextResponse } from "next/server";
import { loadManifest } from "@/lib/project-data";

export async function GET() {
  const manifest = await loadManifest();
  return NextResponse.json({
    status: "ok",
    app: "Gold Assistant",
    mode: "versioned-project-data",
    assistantMode: "gaib-1-notebook-proxy",
    gaibRuntimeConfigured: Boolean(process.env.GAIB_RUNTIME_URL?.trim() && process.env.GAIB_SERVICE_TOKEN?.trim()),
    dataThrough: manifest.market.end_date,
  });
}