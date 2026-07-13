export type GuideSide = {
  min: number;
  avg: number;
  max: number;
  qty: number;
  lots: number;
};

export type GuideCondition = {
  sold: GuideSide;
  stock: GuideSide;
};

/** Price-guide quadrant stored in items.guide (see etl/promote.py). */
export type Guide = {
  new: GuideCondition;
  used: GuideCondition;
};

export type Rating = "EXCELLENT" | "GREAT INVEST" | "GOOD" | "IRRELEVANT" | "N/A";
export type Confidence = "HIGH" | "MEDIUM" | "LOW" | "N/A";
export type Lifecycle = "NEW" | "EOL WATCH" | "RETIRED" | "UNKNOWN";

/** A row from the items table (promoted columns only — never json_data). */
export type Item = {
  item_id: string;
  item_type: "set" | "minifig" | null;
  name: string | null;
  year_released: number | null;
  price_new: number | null;
  price_used: number | null;
  confidence_new: Confidence | null;
  confidence_used: Confidence | null;
  buy_target: number | null;
  lifecycle: Lifecycle | null;
  guide: Guide | null;
  cached_rating: Rating | null;
  cached_profit: number | null;
  cached_margin: number | null;
  updated_at: string | null;
};

export type CatalogSet = {
  set_num: string;
  name: string;
  year: number | null;
  theme_id: number | null;
  num_parts: number | null;
  img_url: string | null;
};

export type CatalogMinifig = {
  fig_num: string;
  name: string;
  num_parts: number | null;
  img_url: string | null;
};

export type CatalogPart = {
  part_num: string;
  name: string;
  part_cat_id: number | null;
};

export type Theme = {
  id: number;
  name: string;
  parent_id: number | null;
};

export type ThemeStats = {
  theme_id: number;
  theme_name: string;
  set_count: number;
  year_from: number | null;
  year_to: number | null;
};

export type PricePoint = {
  price_new: number | null;
  price_used: number | null;
  scraped_at: string;
};

export type SearchResult = {
  result_type: "set" | "minifig" | "part";
  id: string;
  name: string;
  year: number | null;
  img_url: string | null;
  price_new: number | null;
  rating: Rating | null;
};

export type ScrapeJob = {
  id: number;
  item_id: string;
  item_type: "S" | "M";
  deep_scan: boolean;
  status: "queued" | "running" | "done" | "error";
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};
