export interface Minifig {
  id: string;
  name: string;
  year: string;
  yearInt: number;
  newPrice: number;
  usedPrice: number;
  profit: number;
  margin: number;
  rating: string;
  imageUrl: string;
  updatedAt: string;
}

export interface Theme {
  name: string;
  prefix: string;
  icon: string;
  desc: string;
}

export interface CollectionItem {
  itemId: string;
  collectionName: string;
  addedAt: string;
}

export type RatingLevel = "EXCELLENT" | "GREAT" | "GOOD" | "FAIR" | "POOR" | "N/A";

export type SortOption = "profit" | "newPrice" | "usedPrice" | "name" | "year";
