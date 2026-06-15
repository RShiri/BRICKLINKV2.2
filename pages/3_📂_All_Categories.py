import streamlit as st
from database import Database
from pricing_engine import PriceAnalyzer
import pandas as pd
import re

st.set_page_config(page_title="LEGO Categories", page_icon="📂", layout="wide")
st.title("📂 All LEGO Categories")
st.markdown("Browse minifigures by theme — powered by your local BrickLink database.")

# BrickLink minifig ID prefix → theme metadata
CATEGORIES = {
    "Star Wars":          {"prefix": "sw",   "icon": "🚀", "desc": "All Star Wars minifigures (sw####)"},
    "Superheroes (all)":  {"prefix": "sh",   "icon": "🦸", "desc": "Marvel + DC combined (sh####)"},
    "Harry Potter":       {"prefix": "hp",   "icon": "⚡", "desc": "Harry Potter & Fantastic Beasts (hp####)"},
    "Ninjago":            {"prefix": "njo",  "icon": "🐉", "desc": "Ninjago minifigures (njo####)"},
    "CMF":                {"prefix": "col",  "icon": "🎭", "desc": "Collectible Minifigures Series (col####)"},
    "The LEGO Movie":     {"prefix": "tlm",  "icon": "🎬", "desc": "The LEGO Movie 1 & 2 (tlm####)"},
    "Lord of the Rings":  {"prefix": "lor",  "icon": "💍", "desc": "LotR & The Hobbit (lor/hob####)"},
    "The Hobbit":         {"prefix": "hob",  "icon": "🧙", "desc": "The Hobbit minifigures (hob####)"},
    "Jurassic World":     {"prefix": "jw",   "icon": "🦕", "desc": "Jurassic World / Park (jw####)"},
    "Indiana Jones":      {"prefix": "iaj",  "icon": "🎩", "desc": "Indiana Jones minifigures (iaj####)"},
    "Pirates of Caribbean":{"prefix": "poc", "icon": "☠️", "desc": "Pirates of the Caribbean (poc####)"},
    "Legends of Chima":   {"prefix": "loc",  "icon": "🦁", "desc": "Legends of Chima (loc####)"},
    "Nexo Knights":       {"prefix": "nex",  "icon": "🛡️", "desc": "Nexo Knights (nex####)"},
    "Elves":              {"prefix": "elf",  "icon": "🧝", "desc": "Elves theme (elf####)"},
    "Friends":            {"prefix": "frnd", "icon": "👧", "desc": "LEGO Friends (frnd####)"},
    "Toy Story":          {"prefix": "toy",  "icon": "🤠", "desc": "Toy Story minifigures (toy####)"},
    "Speed Champions":    {"prefix": "sc",   "icon": "🏎️", "desc": "Speed Champions drivers (sc####)"},
    "Hidden Side":        {"prefix": "hs",   "icon": "👻", "desc": "Hidden Side (hs####)"},
    "Monkie Kid":         {"prefix": "mk",   "icon": "🐒", "desc": "Monkie Kid (mk####)"},
    "City / Town":        {"prefix": "cty",  "icon": "🏙️", "desc": "City & Town minifigures (cty####)"},
}

# Sidebar: category selector
st.sidebar.header("Select Theme")
selected_name = st.sidebar.radio(
    "Theme",
    list(CATEGORIES.keys()),
    format_func=lambda k: f"{CATEGORIES[k]['icon']} {k}"
)
cat = CATEGORIES[selected_name]

st.markdown(f"## {cat['icon']} {selected_name}")
st.caption(cat["desc"])

db = Database()

@st.cache_data(ttl=300, show_spinner=False)
def load_category(prefix: str):
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
            new_p = analysis.get("new", {}).get("market_price", 0)
            used_p = analysis.get("used", {}).get("market_price", 0)
            new_c = analysis.get("new", {}).get("confidence", "N/A")
            used_c = analysis.get("used", {}).get("confidence", "N/A")
            profit = analysis.get("deep_dive", {}).get("sniper", {}).get("profit_abs", 0)
            rating = analysis.get("deep_dive", {}).get("sniper", {}).get("rating", "N/A")

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

with st.spinner(f"Loading {selected_name} data..."):
    data_rows = load_category(cat["prefix"])

df = pd.DataFrame(data_rows)

if df.empty:
    st.warning(f"No {selected_name} minifigures found in the database yet.")
    st.info("Use the **Set Analyzer** on the main dashboard to scan sets and populate your database.")
    db.close()
    st.stop()

# --- Metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Figures", f"{len(df):,}")
col2.metric("Avg New Price", f"{df['new_price'].mean():.0f} ₪")
col3.metric("Avg Used Price", f"{df['used_price'].mean():.0f} ₪")
col4.metric("Best Profit", f"{df['profit'].max():.0f} ₪")

st.divider()

# --- Filters ---
f1, f2, f3, f4 = st.columns([3, 1, 1, 1])
with f1:
    search = st.text_input("🔍 Search", placeholder="Name or ID")
with f2:
    year_opts = ["All"] + sorted(df["year"].unique().tolist(), reverse=True)
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
    fdf = fdf[fdf["name"].str.lower().str.contains(q, na=False) | fdf["id"].str.lower().str.contains(q, na=False)]
if year_f != "All":
    fdf = fdf[fdf["year"] == year_f]
if rating_f != "All":
    fdf = fdf[fdf["rating"] == rating_f]

sort_map = {
    "New Price": ("new_price", False),
    "Used Price": ("used_price", False),
    "Profit": ("profit", False),
    "Name": ("name", True),
    "Year (Newest)": ("year_int", False),
}
sc, asc = sort_map[sort_f]
fdf = fdf.sort_values(sc, ascending=asc)

st.caption(f"Showing {len(fdf)} of {len(df)} figures")

if view_mode == "Gallery":
    cols_per_row = 5
    for i in range(0, len(fdf), cols_per_row):
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
else:
    st.dataframe(
        fdf[["img", "id", "name", "year", "new_price", "new_conf", "used_price", "used_conf", "profit", "rating"]],
        column_config={
            "img":       st.column_config.ImageColumn("Image", width="small"),
            "id":        st.column_config.TextColumn("ID", width="small"),
            "name":      st.column_config.TextColumn("Name", width="large"),
            "year":      st.column_config.TextColumn("Year", width="small"),
            "new_price": st.column_config.NumberColumn("New ₪", format="%.2f ₪"),
            "new_conf":  st.column_config.TextColumn("Conf", width="small"),
            "used_price":st.column_config.NumberColumn("Used ₪", format="%.2f ₪"),
            "used_conf": st.column_config.TextColumn("Conf", width="small"),
            "profit":    st.column_config.NumberColumn("Profit ₪", format="%.2f ₪"),
            "rating":    st.column_config.TextColumn("Rating", width="small"),
        },
        hide_index=True,
        use_container_width=True,
        height=650,
    )

# CSV Export
csv_out = fdf[["id", "name", "year", "new_price", "used_price", "profit", "rating"]].to_csv(index=False)
st.download_button(
    f"📥 Export {selected_name} to CSV",
    csv_out,
    f"{selected_name.lower().replace(' ', '_')}_export.csv",
    "text/csv"
)

db.close()
