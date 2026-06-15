"""
Shared renderer for per-theme LEGO minifigure database pages.
Each page in pages/ imports this and calls render_category_page().
"""
import streamlit as st
from database import Database
from pricing_engine import PriceAnalyzer
import pandas as pd


@st.cache_data(ttl=300, show_spinner=False)
def _load_category_data(prefix: str):
    db = Database()
    try:
        raw_items = db.get_items_by_prefix(prefix)
        rows = []
        for data in raw_items:
            if "error" in data:
                continue
            try:
                meta = data.get("meta", {})
                item_id = meta.get("item_id", "")
                name = meta.get("item_name", "Unknown")
                yr = meta.get("year_released")
                year_int = int(float(yr)) if yr and str(yr).replace(".", "").isdigit() else 0

                analysis = PriceAnalyzer(data).analyze()
                new_p  = analysis.get("new", {}).get("market_price", 0) or 0
                used_p = analysis.get("used", {}).get("market_price", 0) or 0
                new_c  = analysis.get("new", {}).get("confidence", "N/A")
                used_c = analysis.get("used", {}).get("confidence", "N/A")
                sniper = analysis.get("deep_dive", {}).get("sniper") or {}
                profit = sniper.get("profit_abs", 0) or 0
                rating = sniper.get("rating", "N/A") or "N/A"

                rows.append({
                    "img":       f"https://img.bricklink.com/ItemImage/MN/0/{item_id}.png",
                    "id":        item_id,
                    "name":      name,
                    "year":      str(year_int) if year_int > 0 else "Unknown",
                    "year_int":  year_int,
                    "new_price": new_p,
                    "used_price": used_p,
                    "new_conf":  new_c,
                    "used_conf": used_c,
                    "profit":    profit,
                    "rating":    rating,
                })
            except:
                continue
        return rows
    finally:
        db.close()


EXPORT_COLS = ["id", "name", "year", "new_price", "new_conf", "used_price", "used_conf", "profit", "rating"]
TABLE_COLS  = ["img"] + EXPORT_COLS


def render_category_page(name: str, prefix: str, icon: str, desc: str):
    st.set_page_config(page_title=f"{name} | BrickLink Sniper", page_icon=icon, layout="wide")
    st.title(f"{icon} {name} Minifigure Database")
    st.caption(desc)

    with st.spinner(f"Loading {name} figures..."):
        rows = _load_category_data(prefix)

    df = pd.DataFrame(rows)

    if df.empty:
        st.warning(f"No {name} minifigures found in the database yet.")
        st.info("Use the **Set Analyzer** on the main dashboard to scan sets and populate your database.")
        st.stop()

    # ── Metrics ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Figures", f"{len(df):,}")
    c2.metric("Avg New Price", f"{df['new_price'].mean():.0f} ₪")
    c3.metric("Avg Used Price", f"{df['used_price'].mean():.0f} ₪")
    best = df['profit'].max()
    c4.metric("Best Profit", f"{best:.0f} ₪" if best > 0 else "N/A")

    st.divider()

    # ── Filters ──────────────────────────────────────────────────────────────
    f1, f2, f3, f4 = st.columns([3, 1, 1, 1])
    with f1:
        search = st.text_input("🔍 Search", placeholder="Name or ID")
    with f2:
        known_years = sorted([y for y in df["year"].unique() if y != "Unknown"], reverse=True)
        has_unknown = "Unknown" in df["year"].values
        year_opts = ["All"] + known_years + (["Unknown"] if has_unknown else [])
        year_f = st.selectbox("Year", year_opts)
    with f3:
        rating_opts = ["All"] + sorted(df["rating"].dropna().unique().tolist())
        rating_f = st.selectbox("Rating", rating_opts)
    with f4:
        sort_f = st.selectbox("Sort by", ["New Price", "Used Price", "Profit", "Name", "Year (Newest)"])

    view_mode = st.radio("View", ["Table", "Gallery"], horizontal=True)

    # Apply filters
    fdf = df.copy()
    if search:
        q = search.lower()
        fdf = fdf[
            fdf["name"].str.lower().str.contains(q, na=False) |
            fdf["id"].str.lower().str.contains(q, na=False)
        ]
    if year_f != "All":
        fdf = fdf[fdf["year"] == year_f]
    if rating_f != "All":
        fdf = fdf[fdf["rating"] == rating_f]

    sort_map = {
        "New Price":     ("new_price",  False),
        "Used Price":    ("used_price", False),
        "Profit":        ("profit",     False),
        "Name":          ("name",       True),
        "Year (Newest)": ("year_int",   False),
    }
    sort_col, sort_asc = sort_map[sort_f]
    fdf = fdf.sort_values(sort_col, ascending=sort_asc)

    st.caption(f"Showing {len(fdf)} of {len(df)} figures")

    # ── View ─────────────────────────────────────────────────────────────────
    if view_mode == "Gallery":
        cols_per_row = 5
        for i in range(0, min(len(fdf), 200), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(fdf):
                    row = fdf.iloc[i + j]
                    with col:
                        st.image(row["img"], use_container_width=True)
                        st.caption(f"**{row['id']}**")
                        label = row["name"] if len(row["name"]) <= 22 else row["name"][:20] + "…"
                        st.caption(label)
                        st.caption(f"📅 {row['year']}")
                        st.caption(f"New: {row['new_price']:.0f} ₪ | Used: {row['used_price']:.0f} ₪")
        if len(fdf) > 200:
            st.info("Showing first 200 in gallery mode. Narrow your search to see more.")
    else:
        st.dataframe(
            fdf[TABLE_COLS],
            column_config={
                "img":       st.column_config.ImageColumn("Image",    width="small"),
                "id":        st.column_config.TextColumn("ID",        width="small"),
                "name":      st.column_config.TextColumn("Name",      width="large"),
                "year":      st.column_config.TextColumn("Year",      width="small"),
                "new_price": st.column_config.NumberColumn("New ₪",   format="%.2f ₪"),
                "new_conf":  st.column_config.TextColumn("Conf",      width="small"),
                "used_price":st.column_config.NumberColumn("Used ₪",  format="%.2f ₪"),
                "used_conf": st.column_config.TextColumn("Conf",      width="small"),
                "profit":    st.column_config.NumberColumn("Profit ₪",format="%.2f ₪"),
                "rating":    st.column_config.TextColumn("Rating",    width="small"),
            },
            hide_index=True,
            use_container_width=True,
            height=650,
        )

    # ── Export ───────────────────────────────────────────────────────────────
    st.divider()
    csv_data = fdf[EXPORT_COLS].to_csv(index=False)
    st.download_button(
        f"📥 Export {name} to CSV",
        csv_data,
        f"{name.lower().replace(' ', '_')}_minifigs.csv",
        "text/csv"
    )

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
