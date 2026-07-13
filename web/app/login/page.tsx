"use client";

import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { supabaseBrowser } from "@/lib/supabase/client";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setInfo(null);
    setBusy(true);
    const sb = supabaseBrowser();
    try {
      if (mode === "signup") {
        const { error } = await sb.auth.signUp({ email, password });
        if (error) throw error;
        setInfo("Account created. If email confirmation is enabled, check your inbox — then sign in.");
        setMode("login");
      } else {
        const { error } = await sb.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.push(params.get("next") ?? "/collection");
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-12">
      <h1 className="mb-1 text-xl font-bold">
        {mode === "login" ? "Sign in" : "Create account"}
      </h1>
      <p className="mb-6 text-[13px] text-ink-muted">
        Track your collection and run live price analyses.
      </p>

      <form onSubmit={onSubmit} className="space-y-3">
        <label className="block">
          <span className="mb-1 block text-[12px] font-medium uppercase text-ink-muted">Email</span>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded border border-edge bg-surface px-3 py-2 text-[14px]"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-[12px] font-medium uppercase text-ink-muted">Password</span>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded border border-edge bg-surface px-3 py-2 text-[14px]"
          />
        </label>

        {error && <p className="rounded bg-[#DC2626]/10 px-3 py-2 text-[13px] text-[#DC2626]">{error}</p>}
        {info && <p className="rounded bg-[#16A34A]/10 px-3 py-2 text-[13px] text-[#16A34A]">{info}</p>}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded bg-yellow px-4 py-2 text-[14px] font-semibold text-navy-deep hover:bg-yellow-hover disabled:opacity-50"
        >
          {busy ? "…" : mode === "login" ? "Sign in" : "Sign up"}
        </button>
      </form>

      <button
        type="button"
        onClick={() => setMode(mode === "login" ? "signup" : "login")}
        className="mt-4 text-[13px] text-link hover:underline"
      >
        {mode === "login" ? "No account? Sign up" : "Have an account? Sign in"}
      </button>

      <p className="mt-6 text-[12px] text-ink-muted">
        <Link href="/" className="text-link hover:underline">← Back to catalog</Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
