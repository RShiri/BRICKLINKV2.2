"""Import the Rebrickable catalog CSV dumps into Supabase.

Downloads the daily gzipped CSVs from https://rebrickable.com/downloads/,
COPYs each into a staging table, then upserts into the real tables in
FK-safe order. Idempotent: safe to re-run any time.

Usage:
    python -m etl.import_rebrickable                 # everything
    python -m etl.import_rebrickable --only themes,colors
    python -m etl.import_rebrickable --skip-inventory-parts
"""
import argparse
import gzip
import io
import sys

import requests

from etl.db import connect

CDN = "https://cdn.rebrickable.com/media/downloads/{name}.csv.gz"

# (csv name, target table, columns) in FK-safe order.
TABLES = [
    ("themes", "themes", ["id", "name", "parent_id"]),
    ("colors", "colors", ["id", "name", "rgb", "is_trans"]),
    ("part_categories", "part_categories", ["id", "name"]),
    ("sets", "catalog_sets", ["set_num", "name", "year", "theme_id", "num_parts", "img_url"]),
    ("parts", "catalog_parts", ["part_num", "name", "part_cat_id", "part_material"]),
    ("minifigs", "catalog_minifigs", ["fig_num", "name", "num_parts", "img_url"]),
    ("inventories", "inventories", ["id", "version", "set_num"]),
    ("inventory_parts", "inventory_parts",
     ["inventory_id", "part_num", "color_id", "quantity", "is_spare", "img_url"]),
    ("inventory_minifigs", "inventory_minifigs", ["inventory_id", "fig_num", "quantity"]),
    ("inventory_sets", "inventory_sets", ["inventory_id", "set_num", "quantity"]),
    ("elements", "elements", ["element_id", "part_num", "color_id", "design_id"]),
]

# colors.csv gained extra columns (num_parts, num_sets, ...) over time; we
# only keep the leading ones we model, so staging must accept the full row.
CSV_EXTRA_OK = {"colors"}


def download(name: str) -> io.StringIO:
    url = CDN.format(name=name)
    print(f"  downloading {url}")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    text = gzip.decompress(response.content).decode("utf-8")
    return io.StringIO(text)


def import_table(conn, csv_name: str, table: str, columns: list[str]) -> int:
    buf = download(csv_name)
    header = buf.readline().strip().split(",")
    missing = [c for c in columns if c not in header]
    if missing:
        raise SystemExit(f"{csv_name}.csv is missing expected columns: {missing}")

    col_list = ", ".join(columns)
    staging = f"staging_{table}"
    with conn.cursor() as cur:
        # Stage the full CSV, typed as text, then cast on upsert.
        cur.execute(f"drop table if exists {staging}")
        cur.execute(
            f"create temp table {staging} ({', '.join(f'{c} text' for c in header)})"
        )
        cur.copy_expert(
            f"copy {staging} ({', '.join(header)}) from stdin with (format csv, null '')",
            buf,
        )
        cur.execute(f"select count(*) from {staging}")
        staged = cur.fetchone()[0]

        pk = {
            "themes": "id", "colors": "id", "part_categories": "id",
            "catalog_sets": "set_num", "catalog_parts": "part_num",
            "catalog_minifigs": "fig_num", "inventories": "id",
            "inventory_parts": "inventory_id, part_num, color_id, is_spare",
            "inventory_minifigs": "inventory_id, fig_num",
            "inventory_sets": "inventory_id, set_num",
            "elements": "element_id",
        }[table]
        updatable = [c for c in columns if c not in pk.replace(" ", "").split(",")]
        set_clause = ", ".join(f"{c} = excluded.{c}" for c in updatable)
        conflict_action = f"do update set {set_clause}" if updatable else "do nothing"

        cast = {
            "id": "::integer", "parent_id": "::integer", "theme_id": "::integer",
            "year": "::integer", "num_parts": "::integer", "part_cat_id": "::integer",
            "version": "::integer", "inventory_id": "::integer",
            "color_id": "::integer", "quantity": "::integer",
            "is_trans": "::boolean", "is_spare": "::boolean",
        }
        select_list = ", ".join(
            f"nullif({c}, ''){cast.get(c, '')}" for c in columns
        )
        cur.execute(
            f"""
            insert into {table} ({col_list})
            select {select_list} from {staging}
            on conflict ({pk}) {conflict_action}
            """
        )
        cur.execute(f"drop table if exists {staging}")
    return staged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="comma-separated csv names to import")
    parser.add_argument("--skip-inventory-parts", action="store_true",
                        help="skip the ~1M-row inventory_parts table")
    args = parser.parse_args()

    only = set(args.only.split(",")) if args.only else None
    with connect() as conn:
        for csv_name, table, columns in TABLES:
            if only and csv_name not in only:
                continue
            if args.skip_inventory_parts and csv_name == "inventory_parts":
                print(f"skipping {csv_name}")
                continue
            print(f"importing {csv_name} -> {table}")
            rows = import_table(conn, csv_name, table, columns)
            conn.commit()
            print(f"  staged {rows} rows")
    print("done")


if __name__ == "__main__":
    sys.exit(main())
