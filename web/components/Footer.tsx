import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-12 bg-navy-deep text-white/70">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-8 text-[13px] sm:grid-cols-3">
        <div>
          <p className="mb-2 font-semibold text-white">BrickSniper</p>
          <p>
            Data-driven buy/sell decisions for LEGO® collectors and investors.
            Market prices, sniper deals, and collection tracking.
          </p>
        </div>
        <div>
          <p className="mb-2 font-semibold text-white">Explore</p>
          <ul className="space-y-1">
            <li><Link className="hover:text-white" href="/catalog">Catalog</Link></li>
            <li><Link className="hover:text-white" href="/deals">Sniper Deals</Link></li>
            <li><Link className="hover:text-white" href="/price-guide">Price Guide Methodology</Link></li>
            <li><Link className="hover:text-white" href="/search">Search</Link></li>
          </ul>
        </div>
        <div>
          <p className="mb-2 font-semibold text-white">About</p>
          <p>
            Built by Ram Shiri. Catalog data from{" "}
            <a className="underline hover:text-white" href="https://rebrickable.com/downloads/">
              Rebrickable
            </a>
            . Price data sourced from public BrickLink listings. Not affiliated
            with the LEGO Group, BrickLink, or Rebrickable.
          </p>
        </div>
      </div>
    </footer>
  );
}
