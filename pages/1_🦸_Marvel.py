import streamlit as st
from database import Database
from pricing_engine import PriceAnalyzer
import pandas as pd

st.set_page_config(page_title="Marvel Database 🦸", page_icon="🦸‍♂️", layout="wide")

# Title
st.title("🦸‍♂️ Marvel Minifigure Database")
st.markdown("**Marvel Universe Collection (2005+)**")

# Initialize
db = Database()

# Marvel character keywords for filtering
MARVEL_KEYWORDS = [
    "spider", "iron man", "captain america", "thor", "hulk", "black widow", "hawkeye",
    "avengers", "guardians", "star-lord", "groot", "rocket", "gamora", "drax",
    "ant-man", "wasp", "doctor strange", "scarlet witch", "vision", "falcon",
    "winter soldier", "black panther", "deadpool", "wolverine", "x-men", "cyclops",
    "storm", "magneto", "professor x", "venom", "carnage", "thanos", "loki",
    "ultron", "nebula", "war machine", "nick fury", "maria hill", "agent",
    "daredevil", "punisher", "jessica jones", "luke cage", "iron fist",
    "fantastic four", "thing", "human torch", "mr. fantastic", "invisible woman",
    "silver surfer", "galactus", "doctor doom", "green goblin", "doc ock",
    "sandman", "mysterio", "vulture", "shocker", "rhino", "scorpion",
    "miles morales", "gwen stacy", "spider-gwen", "silk", "prowler",
    "shang-chi", "ms. marvel", "kamala khan", "she-hulk", "moon knight",
    "blade", "ghost rider", "elektra", "kingpin", "bullseye"
]

# Load all superhero minifigures
@st.cache_data(ttl=10)  # Reduced TTL for debugging
def load_marvel_data():
    """Loads all Marvel superhero minifigures from database."""
    raw_items = db.get_items_by_prefix("sh")
    
    display_data = []
    for data in raw_items:
        if "error" in data:
            continue
        
        try:
            analyzer = PriceAnalyzer(data)
            analysis = analyzer.analyze()
            
            meta = data.get("meta", {})
            year = meta.get("year_released")
            year_int = int(year) if year and str(year).replace('.', '').isdigit() else 0
            year_str = str(year_int) if year_int > 0 else "Unknown"
            
            name = meta.get("item_name", "Unknown")
            name_lower = name.lower()
            
            # Filter: Only Marvel characters
            is_marvel = any(keyword in name_lower for keyword in MARVEL_KEYWORDS)
            if not is_marvel:
                continue
            
            # Categorization logic - improved Big Figures detection
            is_exclusive = "exclusive" in name_lower or "sdcc" in name_lower or "nycc" in name_lower
            
            # Big Figures: Detect by explicit keywords OR specific IDs known to be big figs
            # Exclude "giant-man" as that's a character name, not a big figure indicator
            # Note: All big figures have at least 7 parts and most have Giant Arms/Hands (part 43093)
            has_giant_keyword = "giant" in name_lower and "giant-man" not in name_lower
            item_id = meta.get("item_id", "")
            
            # Marvel big figure IDs (verified from database - all use sh0XXX format)
            # Thanos: sh0230, sh0504, sh0507 (Cull Obsidian), sh0576, sh0733, sh0896
            marvel_big_fig_ids = [
                "sh0230", "sh0504", "sh0507", "sh0576", "sh0733", "sh0896",  # Thanos and Cull Obsidian
                "sh353", "sh496", "sh568", "sh614", "sh651"  # Other Thanos variants (if they exist)
            ]
            
            is_big_fig = (
                "big fig" in name_lower or 
                "bigfig" in name_lower or
                has_giant_keyword or
                item_id in marvel_big_fig_ids
            )
            
            display_data.append({
                "id": meta.get("item_id"),
                "name": name,
                "year": year_str,
                "year_int": year_int,
                "used_price": analysis.get("used", {}).get("market_price", 0),
                "new_price": analysis.get("new", {}).get("market_price", 0),
                "used_conf": analysis.get("used", {}).get("confidence", "N/A"),
                "new_conf": analysis.get("new", {}).get("confidence", "N/A"),
                "img": f"https://img.bricklink.com/ItemImage/MN/0/{meta.get('item_id')}.png",
                "is_exclusive": is_exclusive,
                "is_big_fig": is_big_fig
            })
        except Exception as e:
            continue
    
    return display_data

with st.spinner("Loading Marvel Database..."):
    all_figures = load_marvel_data()

# Convert to DataFrame
df = pd.DataFrame(all_figures)

if df.empty:
    st.warning("⚠️ No Marvel minifigures found in database. Run `scan_superheroes.py` to populate the database.")
    st.stop()

# Filter by year (2005+)
df_2005_plus = df[df["year_int"] >= 2005].copy()

# Categorize
df_standard = df_2005_plus[(~df_2005_plus["is_exclusive"]) & (~df_2005_plus["is_big_fig"])].copy()
df_exclusives = df_2005_plus[df_2005_plus["is_exclusive"]].copy()
df_big_figs = df_2005_plus[df_2005_plus["is_big_fig"]].copy()

# Overall Metrics
st.markdown("### 📊 Marvel Statistics (2005+)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Figures", f"{len(df_2005_plus):,}")
col2.metric("Standard", f"{len(df_standard):,}")
col3.metric("Exclusives", f"{len(df_exclusives):,}")
col4.metric("Big Figures", f"{len(df_big_figs):,}")

# Debug section
with st.expander("🔍 Debug: Big Figures Detection"):
    st.caption("Big figure IDs found in database:")
    if not df_big_figs.empty:
        big_fig_ids = df_big_figs["id"].tolist()
        st.code(", ".join(big_fig_ids))
        st.caption(f"Total: {len(big_fig_ids)} big figures")
    else:
        st.warning("No big figures detected!")
        st.caption("Expected IDs: sh280, sh0280, sh321, sh0321, sh353, sh496, sh507, sh0507, sh568, sh576, sh0576, sh614, sh651, sh733, sh0733, sh896, sh0896")
    
    if st.button("🔄 Clear Cache"):
        st.cache_data.clear()
        st.rerun()

st.divider()

# Tabs for categories
tab1, tab2, tab3 = st.tabs(["🦸 Standard", "⭐ Exclusives", "🦾 Big Figures"])

def render_category_table(category_df, category_name):
    """Renders a filterable table for a specific category."""
    if category_df.empty:
        st.info(f"No {category_name} figures found.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        year_options = sorted(category_df["year"].unique(), reverse=True)
        selected_years = st.multiselect(f"Filter by Year", year_options, key=f"year_{category_name}")
    
    with col2:
        sort_by = st.selectbox(f"Sort by", ["New Price", "Used Price", "Name", "Year (Newest)", "Year (Oldest)"], key=f"sort_{category_name}")
    
    with col3:
        view_mode = st.radio(f"View", ["Table", "Gallery"], horizontal=True, key=f"view_{category_name}")
    
    # Apply filters
    filtered_df = category_df.copy()
    if selected_years:
        filtered_df = filtered_df[filtered_df["year"].isin(selected_years)]
    
    # Apply sorting
    if sort_by == "Name":
        filtered_df = filtered_df.sort_values("name")
    elif sort_by == "Year (Newest)":
        filtered_df = filtered_df.sort_values("year_int", ascending=False)
    elif sort_by == "Year (Oldest)":
        filtered_df = filtered_df.sort_values("year_int", ascending=True)
    elif sort_by == "New Price":
        filtered_df = filtered_df.sort_values("new_price", ascending=False)
    elif sort_by == "Used Price":
        filtered_df = filtered_df.sort_values("used_price", ascending=False)
    
    st.caption(f"Showing {len(filtered_df)} of {len(category_df)} figures")
    
    if view_mode == "Gallery":
        # Gallery view
        cols_per_row = 5
        for i in range(0, len(filtered_df), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(filtered_df):
                    row = filtered_df.iloc[i + j]
                    with col:
                        st.image(row["img"], use_container_width=True)
                        st.caption(f"**{row['id']}**")
                        st.caption(f"{row['name'][:30]}...")
                        st.caption(f"📅 {row['year']}")
                        st.caption(f"💰 New: {row['new_price']:.0f} ₪")
                        st.caption(f"💵 Used: {row['used_price']:.0f} ₪")
    else:
        # Table view
        st.dataframe(
            filtered_df[["img", "id", "name", "year", "new_price", "new_conf", "used_price", "used_conf"]],
            column_config={
                "img": st.column_config.ImageColumn("Image", width="small"),
                "id": st.column_config.TextColumn("ID", width="small"),
                "name": st.column_config.TextColumn("Name", width="large"),
                "year": st.column_config.TextColumn("Year", width="small"),
                "new_price": st.column_config.NumberColumn("New Price", format="%.2f ₪"),
                "new_conf": st.column_config.TextColumn("New Conf", width="small"),
                "used_price": st.column_config.NumberColumn("Used Price", format="%.2f ₪"),
                "used_conf": st.column_config.TextColumn("Used Conf", width="small")
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )
    
    # Export button
    st.divider()
    if st.button(f"📥 Export {category_name} to CSV", key=f"export_{category_name}"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label=f"Download {category_name} CSV",
            data=csv,
            file_name=f"marvel_{category_name.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            key=f"download_{category_name}"
        )

with tab1:
    render_category_table(df_standard, "Standard")

with tab2:
    render_category_table(df_exclusives, "Exclusives")

with tab3:
    render_category_table(df_big_figs, "Big Figures")

db.close()
