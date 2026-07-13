"""Backfill the promoted items columns (migration 0002) for existing rows.

Extends scripts/backfill_cached_columns.py: recomputes PriceAnalyzer output
from items.json_data and writes name/year/prices/confidence/buy_target/
lifecycle/guide (and the legacy cached_* columns) in one pass.

Usage:
    python -m etl.backfill_item_columns [--all]   # default: only rows where guide is null
"""
import argparse
import json
import sys

from psycopg2.extras import Json

from etl.db import connect
from etl.promote import promoted_columns
from pricing_engine import PriceAnalyzer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true",
                        help="recompute every row, not just rows missing guide")
    args = parser.parse_args()

    where = "" if args.all else "where guide is null"
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(f"select item_id, json_data from items {where}")
        rows = cur.fetchall()
        total, done, errors = len(rows), 0, 0
        print(f"backfilling {total} items")

        for item_id, json_data in rows:
            try:
                data = json.loads(json_data)
                analysis = PriceAnalyzer(data).analyze()
                cols = promoted_columns(item_id, data, analysis)
                sniper = analysis.get("deep_dive", {}).get("sniper") or {}
                cur.execute(
                    """
                    update items set
                        item_type = %s, name = %s, year_released = %s,
                        price_new = %s, price_used = %s,
                        confidence_new = %s, confidence_used = %s,
                        buy_target = %s, lifecycle = %s, guide = %s,
                        cached_rating = %s, cached_profit = %s, cached_margin = %s
                    where item_id = %s
                    """,
                    (
                        cols["item_type"], cols["name"], cols["year_released"],
                        cols["price_new"], cols["price_used"],
                        cols["confidence_new"], cols["confidence_used"],
                        cols["buy_target"], cols["lifecycle"], Json(cols["guide"]),
                        sniper.get("rating", "N/A"),
                        sniper.get("profit_abs", 0),
                        sniper.get("margin_pct", 0),
                        item_id,
                    ),
                )
                done += 1
            except Exception as exc:  # noqa: BLE001 - keep going, report at end
                print(f"  error on {item_id}: {exc}")
                errors += 1
            if (done + errors) % 100 == 0:
                conn.commit()
                print(f"  {done + errors}/{total}")
        conn.commit()
        print(f"done: {done} updated, {errors} errors")


if __name__ == "__main__":
    sys.exit(main())
