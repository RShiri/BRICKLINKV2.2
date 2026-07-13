"""Compute the promoted items columns from a raw scrape dict.

Shared by database.Database.save_item (Streamlit/scraper write path) and
etl/backfill_item_columns.py so both always agree. The `guide` dict is the
price-guide quadrant rendered by the web app's PriceGuideTable.
"""
from typing import Any, Dict, Optional


def _side_summary(stats: Dict[str, Any]) -> Dict[str, Any]:
    items = stats.get("clean_items", [])
    prices = [x["price"] for x in items]
    return {
        "min": round(min(prices), 2) if prices else 0,
        "avg": round(stats.get("avg", 0) or 0, 2),
        "max": round(max(prices), 2) if prices else 0,
        "qty": sum(x.get("qty", 1) for x in items),
        "lots": len(items),
    }


def infer_item_type(item_id: str) -> str:
    """BrickLink minifig ids start with a letter prefix (sw0001); sets are numeric."""
    return "minifig" if item_id and item_id[0].isalpha() else "set"


def promoted_columns(item_id: str, data: Dict[str, Any],
                     analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Returns a dict of column -> value for the items table."""
    if analysis is None:
        from pricing_engine import PriceAnalyzer
        analysis = PriceAnalyzer(data).analyze()

    meta = data.get("meta", {})
    new = analysis.get("new", {})
    used = analysis.get("used", {})
    lifecycle = analysis.get("deep_dive", {}).get("lifecycle", {})

    guide = {
        cond: {
            "sold": _side_summary(res.get("stats", {}).get("sold", {})),
            "stock": _side_summary(res.get("stats", {}).get("stock", {})),
        }
        for cond, res in (("new", new), ("used", used))
    }

    return {
        "item_type": infer_item_type(item_id),
        "name": meta.get("item_name"),
        "year_released": meta.get("year_released"),
        "price_new": new.get("market_price", 0),
        "price_used": used.get("market_price", 0),
        "confidence_new": new.get("confidence", "N/A"),
        "confidence_used": used.get("confidence", "N/A"),
        "buy_target": new.get("buy_target", 0),
        "lifecycle": lifecycle.get("status", "UNKNOWN"),
        "guide": guide,
    }
