import Link from "next/link";
import { Logo } from "@/components/Logo";
import { SearchBar } from "@/components/SearchBar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { NavTabs } from "@/components/NavTabs";
import { supabaseServer } from "@/lib/supabase/server";

export async function Header() {
  const sb = await supabaseServer();
  let email: string | null = null;
  if (sb) {
    const {
      data: { user },
    } = await sb.auth.getUser();
    email = user?.email ?? null;
  }

  return (
    <header className="sticky top-0 z-40">
      <div className="bg-navy">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2.5">
          <Logo />
          <div className="order-3 w-full sm:order-2 sm:w-auto sm:flex-1">
            <SearchBar />
          </div>
          <div className="order-2 ml-auto flex items-center gap-2 sm:order-3">
            <ThemeToggle />
            {email ? (
              <Link
                href="/collection"
                className="rounded px-2 py-1 text-[13px] text-white/90 hover:bg-white/10"
              >
                {email.split("@")[0]}
              </Link>
            ) : (
              <Link
                href="/login"
                className="rounded bg-yellow px-3 py-1 text-[13px] font-semibold text-navy-deep hover:bg-yellow-hover"
              >
                Sign in
              </Link>
            )}
          </div>
        </div>
      </div>
      <NavTabs />
    </header>
  );
}
