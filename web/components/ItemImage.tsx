"use client";

import { useState } from "react";

/**
 * Catalog item image with a graceful fallback: the BrickLink CDN has no
 * image for many ids, and a raw <img> would show the browser's broken-image
 * icon. Renders a neutral brick glyph instead when src is missing or fails.
 */
export function ItemImage({
  src,
  alt,
  className,
  loading,
}: {
  src: string | null | undefined;
  alt: string;
  className?: string;
  loading?: "lazy" | "eager";
}) {
  const [failed, setFailed] = useState(false);

  if (!src || failed) {
    return (
      <svg
        viewBox="0 0 48 48"
        role="img"
        aria-label={alt || "No image available"}
        className="h-1/2 w-1/2 text-edge"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinejoin="round"
      >
        <rect x="6" y="20" width="36" height="18" rx="2" />
        <rect x="11" y="13" width="9" height="7" rx="1.5" />
        <rect x="28" y="13" width="9" height="7" rx="1.5" />
      </svg>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      loading={loading}
      className={className}
      onError={() => setFailed(true)}
    />
  );
}
