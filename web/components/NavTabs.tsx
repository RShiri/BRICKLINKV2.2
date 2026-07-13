"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/", label: "Home", exact: true },
  { href: "/catalog", label: "Catalog" },
  { href: "/price-guide", label: "Price Guide" },
  { href: "/deals", label: "Deals" },
  { href: "/collection", label: "My Collection" },
  { href: "/tools/analyzer", label: "Tools" },
];

export function NavTabs() {
  const pathname = usePathname();
  return (
    <nav className="bg-navy-deep">
      <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4">
        {TABS.map((tab) => {
          const activeTab = tab.exact
            ? pathname === tab.href
            : pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`whitespace-nowrap border-b-2 px-3 py-2 text-[13px] font-medium transition-colors ${
                activeTab
                  ? "border-yellow text-white"
                  : "border-transparent text-white/70 hover:text-white"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
