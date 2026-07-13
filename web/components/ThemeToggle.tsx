"use client";

import { useTheme } from "next-themes";
import { useSyncExternalStore } from "react";

const subscribeNoop = () => () => {};

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  // true on the client after hydration, false during SSR — avoids a
  // mismatched icon without setState-in-effect.
  const mounted = useSyncExternalStore(
    subscribeNoop,
    () => true,
    () => false,
  );

  return (
    <button
      type="button"
      aria-label="Toggle dark mode"
      className="rounded p-1.5 text-white/80 hover:bg-white/10 hover:text-white"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
    >
      {mounted && resolvedTheme === "dark" ? "☀️" : "🌙"}
    </button>
  );
}
