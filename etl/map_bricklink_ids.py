"""Build the BrickLink <-> Rebrickable external_id_map.

Pass 1 (sets, deterministic): BrickLink and Rebrickable share set numbering;
Rebrickable appends a variant suffix ("75192-1"). Confidence 1.0.

Pass 2 (minifigs, set-inventory intersection): for every scraped set we have
the BrickLink fig list in inventory_lists.json_data ([{id, name, qty}]) and
Rebrickable has the same set's inventory_minifigs. Within a single set the
candidate pool is a handful of figs, so normalized-name token overlap
(Jaccard) picks unique winners with high precision.

Pass 3 (minifigs, global exact name match): only where the normalized name
is unique on both sides; ties are skipped for the manual /admin/mapping UI.

Usage:
    python -m etl.map_bricklink_ids [--min-jaccard 0.5]
"""
import argparse
import json
import re
import sys
from collections import defaultdict

from etl.db import connect

STOPWORDS = {"the", "a", "an", "of", "with", "and", "in", "-"}


def normalize(name: str) -> frozenset:
    tokens = re.sub(r"[^a-z0-9 ]", " ", name.lower()).split()
    return frozenset(t for t in tokens if t not in STOPWORDS)


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def upsert(cur, item_type, rb_id, ext_id, method, confidence):
    cur.execute(
        """
        insert into external_id_map
            (item_type, rb_id, provider, ext_id, match_method, confidence)
        values (%s, %s, 'bricklink', %s, %s, %s)
        on conflict (item_type, provider, ext_id) do update
            set rb_id = excluded.rb_id,
                match_method = excluded.match_method,
                confidence = excluded.confidence
            where external_id_map.verified = false
              and excluded.confidence >= external_id_map.confidence
        """,
        (item_type, rb_id, ext_id, method, confidence),
    )


def map_sets(cur) -> int:
    """BL set id 75192 or 75192-1 -> RB set_num 75192-1."""
    cur.execute("select item_id from items where item_id ~ '^[0-9]+(-[0-9]+)?$'")
    bl_sets = [r[0] for r in cur.fetchall()]
    mapped = 0
    for bl_id in bl_sets:
        rb_id = bl_id if "-" in bl_id else f"{bl_id}-1"
        cur.execute("select 1 from catalog_sets where set_num = %s", (rb_id,))
        if cur.fetchone():
            upsert(cur, "set", rb_id, bl_id, "set_number", 1.0)
            mapped += 1
    return mapped


def map_minifigs_by_inventory(cur, min_jaccard: float) -> int:
    cur.execute("select set_id, json_data from inventory_lists")
    rows = cur.fetchall()
    mapped = 0
    for set_id, json_data in rows:
        try:
            bl_figs = json.loads(json_data)
        except (TypeError, ValueError):
            continue
        if not bl_figs:
            continue

        rb_set = set_id if "-" in set_id else f"{set_id}-1"
        cur.execute(
            """
            select f.fig_num, f.name
            from inventory_minifigs im
            join inventories inv on inv.id = im.inventory_id
            join catalog_minifigs f on f.fig_num = im.fig_num
            where inv.set_num = %s
            """,
            (rb_set,),
        )
        rb_figs = cur.fetchall()
        if not rb_figs:
            continue

        rb_tokens = {fig_num: normalize(name) for fig_num, name in rb_figs}
        for bl in bl_figs:
            bl_id, bl_name = bl.get("id"), bl.get("name", "")
            if not bl_id:
                continue
            bl_tok = normalize(bl_name)
            scored = sorted(
                ((jaccard(bl_tok, toks), fig) for fig, toks in rb_tokens.items()),
                reverse=True,
            )
            if not scored or scored[0][0] < min_jaccard:
                continue
            # require a unique winner
            if len(scored) > 1 and scored[0][0] == scored[1][0]:
                continue
            upsert(cur, "minifig", scored[0][1], bl_id,
                   "inventory_intersection", round(scored[0][0], 3))
            mapped += 1
    return mapped


def map_minifigs_by_name(cur) -> int:
    """Global exact normalized-name match, unique on both sides."""
    cur.execute(
        """
        select i.item_id, i.name from items i
        where i.item_id ~ '^[a-z]{2,4}[0-9]{3,4}[a-z]?$'
          and i.name is not null
          and not exists (
              select 1 from external_id_map m
              where m.provider = 'bricklink' and m.ext_id = i.item_id)
        """
    )
    bl_rows = cur.fetchall()
    if not bl_rows:
        return 0

    cur.execute("select fig_num, name from catalog_minifigs")
    rb_by_name = defaultdict(list)
    for fig_num, name in cur.fetchall():
        rb_by_name[normalize(name)].append(fig_num)

    bl_by_name = defaultdict(list)
    for item_id, name in bl_rows:
        bl_by_name[normalize(name)].append(item_id)

    mapped = 0
    for tokens, bl_ids in bl_by_name.items():
        rb_ids = rb_by_name.get(tokens, [])
        if len(bl_ids) == 1 and len(rb_ids) == 1:
            upsert(cur, "minifig", rb_ids[0], bl_ids[0], "name_exact", 0.9)
            mapped += 1
    return mapped


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-jaccard", type=float, default=0.5)
    args = parser.parse_args()

    with connect() as conn:
        cur = conn.cursor()
        sets = map_sets(cur)
        print(f"pass 1 sets mapped: {sets}")
        inv = map_minifigs_by_inventory(cur, args.min_jaccard)
        print(f"pass 2 minifigs mapped via inventory intersection: {inv}")
        names = map_minifigs_by_name(cur)
        print(f"pass 3 minifigs mapped via exact name: {names}")

        cur.execute(
            """
            select count(*) from items i
            where not exists (
                select 1 from external_id_map m
                where m.provider = 'bricklink' and m.ext_id = i.item_id)
            """
        )
        print(f"unmapped items remaining: {cur.fetchone()[0]}")


if __name__ == "__main__":
    sys.exit(main())
