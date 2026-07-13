/** All prices in the database are stored in ILS (see etl/currency.py). */
export function ils(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `₪${value.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function pct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(1)}%`;
}

export function num(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-US");
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

/** BrickLink CDN image for an item id; minifig ids start with a letter. */
export function blImageUrl(itemId: string): string {
  const kind = /^[a-zA-Z]/.test(itemId) ? "MN" : "SN";
  const id = kind === "SN" && !itemId.includes("-") ? `${itemId}-1` : itemId;
  return `https://img.bricklink.com/ItemImage/${kind}/0/${id}.png`;
}

export function blCatalogUrl(itemId: string): string {
  const isFig = /^[a-zA-Z]/.test(itemId);
  return isFig
    ? `https://www.bricklink.com/v2/catalog/catalogitem.page?M=${itemId}`
    : `https://www.bricklink.com/v2/catalog/catalogitem.page?S=${itemId.includes("-") ? itemId : `${itemId}-1`}`;
}
