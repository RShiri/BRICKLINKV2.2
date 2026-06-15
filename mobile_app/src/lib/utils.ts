export function ratingColor(rating: string): string {
  switch (rating?.toUpperCase()) {
    case "EXCELLENT": return "#00e676";
    case "GREAT":     return "#69f0ae";
    case "GOOD":      return "#ffeb3b";
    case "FAIR":      return "#ffa726";
    case "POOR":      return "#ef5350";
    default:          return "#8888aa";
  }
}

export function formatPrice(price: number): string {
  if (!price || price <= 0) return "—";
  return `₪${price.toFixed(0)}`;
}

export function formatProfit(profit: number): string {
  if (!profit || profit <= 0) return "";
  return `+₪${profit.toFixed(0)}`;
}
