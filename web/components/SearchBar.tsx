"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { SearchResult } from "@/lib/types";
import { ils } from "@/lib/format";

const SCOPES = [
  { value: "all", label: "All" },
  { value: "sets", label: "Sets" },
  { value: "minifigs", label: "Minifigs" },
  { value: "parts", label: "Parts" },
] as const;

function resultHref(r: SearchResult): string {
  if (r.result_type === "set") return `/catalog/sets/${encodeURIComponent(r.id)}`;
  if (r.result_type === "minifig") return `/catalog/minifigs/${encodeURIComponent(r.id)}`;
  return `/catalog/parts/${encodeURIComponent(r.id)}`;
}

export function SearchBar() {
  const router = useRouter();
  const [scope, setScope] = useState<string>("all");
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const boxRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const runSearch = useCallback((query: string, s: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `/api/search?q=${encodeURIComponent(query)}&scope=${s}`,
        );
        const data: SearchResult[] = res.ok ? await res.json() : [];
        setResults(data);
        setOpen(true);
        setActive(-1);
      } catch {
        setResults([]);
      }
    }, 150);
  }, []);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function submit() {
    setOpen(false);
    if (active >= 0 && results[active]) {
      router.push(resultHref(results[active]));
    } else if (q.trim()) {
      router.push(`/search?q=${encodeURIComponent(q.trim())}&scope=${scope}`);
    }
  }

  return (
    <div ref={boxRef} className="relative w-full max-w-xl">
      <div className="flex overflow-hidden rounded border border-white/20 bg-white">
        <select
          aria-label="Search scope"
          className="border-r border-edge bg-surface-2 px-2 text-[13px] text-ink outline-none"
          value={scope}
          onChange={(e) => {
            setScope(e.target.value);
            runSearch(q, e.target.value);
          }}
        >
          {SCOPES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <input
          type="search"
          placeholder="Search sets, minifigs, parts…"
          aria-label="Search"
          className="w-full px-3 py-1.5 text-[14px] text-gray-900 outline-none"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            runSearch(e.target.value, scope);
          }}
          onFocus={() => results.length && setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setActive((a) => Math.min(a + 1, results.length - 1));
            } else if (e.key === "ArrowUp") {
              e.preventDefault();
              setActive((a) => Math.max(a - 1, -1));
            } else if (e.key === "Enter") {
              e.preventDefault();
              submit();
            } else if (e.key === "Escape") {
              setOpen(false);
            }
          }}
        />
        <button
          type="button"
          onClick={submit}
          className="bg-yellow px-4 text-[13px] font-semibold text-navy-deep hover:bg-yellow-hover"
        >
          Search
        </button>
      </div>

      {open && results.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full overflow-hidden rounded border border-edge bg-surface shadow-lg">
          {results.map((r, i) => (
            <li key={`${r.result_type}-${r.id}`}>
              <button
                type="button"
                className={`flex w-full items-center gap-3 px-3 py-2 text-left text-[13px] hover:bg-surface-2 ${
                  i === active ? "bg-surface-2" : ""
                }`}
                onMouseEnter={() => setActive(i)}
                onClick={() => {
                  setOpen(false);
                  router.push(resultHref(r));
                }}
              >
                <span className="w-14 shrink-0 font-mono text-ink-muted">{r.id}</span>
                <span className="min-w-0 flex-1 truncate text-ink">{r.name}</span>
                <span className="shrink-0 rounded bg-surface-2 px-1.5 py-0.5 text-[11px] uppercase text-ink-muted">
                  {r.result_type}
                </span>
                {r.price_new != null && r.price_new > 0 && (
                  <span className="shrink-0 font-medium text-ink">{ils(r.price_new)}</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
