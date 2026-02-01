import streamlit as st
from database import Database
from pricing_engine import PriceAnalyzer
import pandas as pd

st.set_page_config(page_title="Superhero Database 🦸", page_icon="🦸", layout="wide")

# Title
st.title("🦸 Superhero Minifigure Database")
st.markdown("**Marvel & DC Universe Collection (2005+)**")

# Initialize
db = Database()

# Load all superhero minifigures
@st.cache_data(ttl=60)
def load_superhero_data():
    """Loads all superhero minifigures (sh prefix) from database."""
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
            
            # Categorization logic
            is_exclusive = "exclusive" in name.lower() or "sdcc" in name.lower() or "nycc" in name.lower()
            is_big_fig = "giant" in name.lower() or "big fig" in name.lower() or "bigfig" in name.lower()
            
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

with st.spinner("Loading Superhero Database..."):
    all_figures = load_superhero_data()

# Convert to DataFrame
df = pd.DataFrame(all_figures)

if df.empty:
    st.warning("⚠️ No superhero minifigures found in database. Run `scan_superheroes.py` to populate the database.")
    st.stop()

# Filter by year (2005+)
df_2005_plus = df[df["year_int"] >= 2005].copy()

# Categorize
df_standard = df_2005_plus[(~df_2005_plus["is_exclusive"]) & (~df_2005_plus["is_big_fig"])].copy()
df_exclusives = df_2005_plus[df_2005_plus["is_exclusive"]].copy()
df_big_figs = df_2005_plus[df_2005_plus["is_big_fig"]].copy()

# Overall Metrics
st.markdown("### 📊 Marvel & DC Statistics (2005+)")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Figures", f"{len(df_2005_plus):,}")
col2.metric("Standard", f"{len(df_standard):,}")
col3.metric("Exclusives", f"{len(df_exclusives):,}")
col4.metric("Big Figures", f"{len(df_big_figs):,}")

st.divider()

# Sidebar Filters
st.sidebar.header("🔍 Filters")
search_term = st.sidebar.text_input("Search by Name or ID", placeholder="e.g. Spider-Man, sh001")

# Tabs for different categories
tab_standard, tab_exclusive, tab_bigfig, tab_all = st.tabs([
    f"📋 Standard ({len(df_standard)})", 
    f"⭐ Exclusives ({len(df_exclusives)})", 
    f"🦾 Big Figures ({len(df_big_figs)})",
    f"🌐 All ({len(df_2005_plus)})"
])

def render_category_table(category_df, category_name):
    """Renders a table for a specific category with filters and sorting."""
    
    if category_df.empty:
        st.info(f"No {category_name} found.")
        return
    
    # Apply search filter
    filtered_df = category_df.copy()
    if search_term:
        term = search_term.lower()
        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(term, na=False) |
            filtered_df["id"].str.lower().str.contains(term, na=False)
        ]
    
    # Category-specific metrics
    total_value_new = filtered_df["new_price"].sum()
    total_value_used = filtered_df["used_price"].sum()
    avg_price_used = filtered_df["used_price"].mean()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Value (New)", f"{total_value_new:,.0f} ₪")
    col2.metric("Total Value (Used)", f"{total_value_used:,.0f} ₪")
    col3.metric("Avg Price (Used)", f"{avg_price_used:.0f} ₪")
    
    st.caption(f"Showing {len(filtered_df)} of {len(category_df)} {category_name}")
    
    # Sort options
    sort_by = st.selectbox(
        "Sort By",
        ["Price (High to Low)", "Price (Low to High)", "Name (A-Z)", "ID", "Year (Newest First)"],
        key=f"sort_{category_name}"
    )
    
    # Apply sorting
    if sort_by == "Price (High to Low)":
        filtered_df = filtered_df.sort_values("used_price", ascending=False)
    elif sort_by == "Price (Low to High)":
        filtered_df = filtered_df.sort_values("used_price", ascending=True)
    elif sort_by == "Name (A-Z)":
        filtered_df = filtered_df.sort_values("name")
    elif sort_by == "ID":
        filtered_df = filtered_df.sort_values("id")
    elif sort_by == "Year (Newest First)":
        filtered_df = filtered_df.sort_values("year_int", ascending=False)
    
    # View mode
    view_mode = st.radio("View Mode", ["Gallery", "Table"], horizontal=True, key=f"view_{category_name}")
    
    if view_mode == "Gallery":
        # Gallery view
        items_per_row = 5
        rows = [filtered_df.iloc[i:i+items_per_row] for i in range(0, min(len(filtered_df), 100), items_per_row)]
        
        for row_data in rows:
            cols = st.columns(items_per_row)
            for idx, (_, item) in enumerate(row_data.iterrows()):
                with cols[idx]:
                    st.image(item["img"], use_container_width=True)
                    st.caption(f"**{item['id']}**")
                    st.caption(f"{item['name'][:30]}...")
                    st.caption(f"💰 {item['used_price']:.0f} ₪")
                    st.caption(f"📅 {item['year']}")
        
        if len(filtered_df) > 100:
            st.info("⚠️ Showing first 100 results in gallery view. Use table view or search to see more.")
    
    else:
        # Table view
        display_cols = ["img", "id", "name", "year", "used_price", "new_price", "used_conf", "new_conf"]
        st.dataframe(
            filtered_df[display_cols],
            width="stretch",
            hide_index=True,
            column_config={
                "img": st.column_config.ImageColumn("Image", width="small"),
                "id": st.column_config.TextColumn("ID"),
                "name": st.column_config.TextColumn("Name"),
                "year": st.column_config.TextColumn("Year"),
                "used_price": st.column_config.NumberColumn("Used Price", format="%.2f ₪"),
                "new_price": st.column_config.NumberColumn("New Price", format="%.2f ₪"),
                "used_conf": st.column_config.TextColumn("Used Conf"),
                "new_conf": st.column_config.TextColumn("New Conf")
            }
        )
    
    # Export button
    st.divider()
    if st.button(f"📥 Export {category_name} to CSV", key=f"export_{category_name}"):
        csv = filtered_df[display_cols[1:]].to_csv(index=False)  # Exclude img column
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"superhero_{category_name.lower().replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            key=f"download_{category_name}"
        )

# Render each tab
with tab_standard:
    st.markdown("### 📋 Standard Minifigures")
    st.caption("Regular superhero minifigures (excluding exclusives and big figures)")
    render_category_table(df_standard, "Standard Figures")

with tab_exclusive:
    st.markdown("### ⭐ Exclusive Minifigures")
    st.caption("Convention exclusives, promotional items, and limited editions")
    render_category_table(df_exclusives, "Exclusives")

with tab_bigfig:
    st.markdown("### 🦾 Big Figures")
    st.caption("Giant/oversized minifigures (Hulk, Thanos, etc.)")
    render_category_table(df_big_figs, "Big Figures")

with tab_all:
    st.markdown("### 🌐 All Superhero Minifigures (2005+)")
    st.caption("Complete database of all Marvel & DC minifigures from 2005 onwards")
    render_category_table(df_2005_plus, "All Figures")

# Footer
st.divider()
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
