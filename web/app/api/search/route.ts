import { NextRequest, NextResponse } from "next/server";
import { searchCatalog, type SearchScope } from "@/lib/queries/search";

const SCOPES = new Set(["all", "sets", "parts", "minifigs"]);

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get("q") ?? "";
  const scopeParam = request.nextUrl.searchParams.get("scope") ?? "all";
  const scope = (SCOPES.has(scopeParam) ? scopeParam : "all") as SearchScope;
  const results = await searchCatalog(q, scope, 10);
  return NextResponse.json(results, {
    headers: { "Cache-Control": "public, max-age=60" },
  });
}
