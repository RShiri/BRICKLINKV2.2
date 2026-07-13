"use client";

import { useTransition } from "react";
import { removeFromCollection } from "./actions";

export function RemoveButton({ itemId }: { itemId: string }) {
  const [pending, startTransition] = useTransition();
  return (
    <button
      type="button"
      disabled={pending}
      aria-label={`Remove ${itemId} from collection`}
      onClick={() => startTransition(() => removeFromCollection(itemId))}
      className="rounded px-1.5 py-0.5 text-[12px] text-ink-muted hover:bg-[#DC2626]/10 hover:text-[#DC2626] disabled:opacity-50"
    >
      ✕
    </button>
  );
}
