"use client";

import { useState, useTransition } from "react";
import { addToCollection, removeFromCollection } from "@/app/collection/actions";

export function CollectionButton({
  itemId,
  initialInCollection,
}: {
  itemId: string;
  /** null = not signed in (button hidden) */
  initialInCollection: boolean | null;
}) {
  const [inCollection, setInCollection] = useState(initialInCollection);
  const [pending, startTransition] = useTransition();

  if (inCollection === null) return null;

  return (
    <button
      type="button"
      disabled={pending}
      onClick={() =>
        startTransition(async () => {
          if (inCollection) {
            await removeFromCollection(itemId);
            setInCollection(false);
          } else {
            await addToCollection(itemId);
            setInCollection(true);
          }
        })
      }
      className={`rounded px-3 py-1.5 text-[13px] font-semibold disabled:opacity-50 ${
        inCollection
          ? "border border-edge text-ink-muted hover:text-[#DC2626]"
          : "bg-blue text-white hover:opacity-90"
      }`}
    >
      {pending ? "…" : inCollection ? "✓ In collection — remove" : "+ Add to collection"}
    </button>
  );
}
