import { NextRequest, NextResponse } from "next/server";
import { supabaseServer } from "@/lib/supabase/server";

/** Enqueue scrape jobs consumed by etl/scrape_worker.py. */
export async function POST(request: NextRequest) {
  const sb = await supabaseServer();
  if (!sb) return NextResponse.json({ error: "not configured" }, { status: 503 });
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const body = await request.json().catch(() => null);
  const ids: string[] = Array.isArray(body?.items) ? body.items : [];
  const deepScan = Boolean(body?.deepScan);
  const clean = [...new Set(ids.map((s) => String(s).trim().toLowerCase()).filter(Boolean))].slice(0, 25);
  if (!clean.length) {
    return NextResponse.json({ error: "no item ids" }, { status: 400 });
  }

  const rows = clean.map((id) => ({
    item_id: id,
    item_type: /^[a-z]/.test(id) ? "M" : "S",
    deep_scan: deepScan,
    requested_by: user.id,
    status: "queued",
  }));
  const { data, error } = await sb.from("scrape_jobs").insert(rows).select("id, item_id");
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ jobs: data });
}

export async function GET(request: NextRequest) {
  const sb = await supabaseServer();
  if (!sb) return NextResponse.json({ error: "not configured" }, { status: 503 });
  const {
    data: { user },
  } = await sb.auth.getUser();
  if (!user) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const idsParam = request.nextUrl.searchParams.get("ids") ?? "";
  const ids = idsParam.split(",").map(Number).filter(Boolean).slice(0, 50);
  if (!ids.length) return NextResponse.json({ jobs: [] });

  const { data } = await sb
    .from("scrape_jobs")
    .select("id, item_id, item_type, deep_scan, status, error, created_at, started_at, finished_at")
    .in("id", ids)
    .order("id");
  return NextResponse.json({ jobs: data ?? [] });
}
