import Link from "next/link";

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 shrink-0" aria-label="BrickSniper home">
      <span className="grid grid-cols-2 gap-[2px]" aria-hidden>
        {[0, 1, 2, 3].map((i) => (
          <span key={i} className="h-2 w-2 rounded-[2px] bg-yellow" />
        ))}
      </span>
      <span className="text-lg font-bold tracking-tight text-white">
        Brick<span className="text-yellow">Sniper</span>
      </span>
    </Link>
  );
}
