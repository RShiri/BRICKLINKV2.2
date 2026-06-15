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
@st.cache_data(ttl=60, show_spinner=False)
def load_superhero_data(search_filter=None, _progress_callback=None):
    """Loads all superhero minifigures (sh prefix) from database.
    
    Args:
        search_filter: Optional search term to filter items before expensive processing
        _progress_callback: Optional callback function for progress updates (not cached)
    """
    raw_items = db.get_items_by_prefix("sh")
    total_items = len(raw_items)
    
    display_data = []
    processed_count = 0
    
    for idx, data in enumerate(raw_items):
        if "error" in data:
            continue
        
        # OPTIMIZATION: Filter BEFORE expensive PriceAnalyzer processing
        meta = data.get("meta", {})
        item_id = meta.get("item_id", "")
        item_name = meta.get("item_name", "Unknown")
        
        if search_filter:
            term = search_filter.lower()
            if term not in item_name.lower() and term not in item_id.lower():
                continue  # Skip items that don't match search
        
        try:
            analyzer = PriceAnalyzer(data)
            analysis = analyzer.analyze()
            
            year = meta.get("year_released")
            year_int = int(year) if year and str(year).replace('.', '').isdigit() else 0
            year_str = str(year_int) if year_int > 0 else "Unknown"
            
            # Categorization logic
            is_exclusive = "exclusive" in item_name.lower() or "sdcc" in item_name.lower() or "nycc" in item_name.lower()
            is_big_fig = "giant" in item_name.lower() or "big fig" in item_name.lower() or "bigfig" in item_name.lower()
            
            display_data.append({
                "id": item_id,
                "name": item_name,
                "year": year_str,
                "year_int": year_int,
                "used_price": analysis.get("used", {}).get("market_price", 0),
                "new_price": analysis.get("new", {}).get("market_price", 0),
                "used_conf": analysis.get("used", {}).get("confidence", "N/A"),
                "new_conf": analysis.get("new", {}).get("confidence", "N/A"),
                "img": f"https://img.bricklink.com/ItemImage/MN/0/{item_id}.png",
                "is_exclusive": is_exclusive,
                "is_big_fig": is_big_fig
            })
            
            processed_count += 1
            
            # Update progress every 10 items
            if _progress_callback and processed_count % 10 == 0:
                _progress_callback(idx + 1, total_items, item_name)
                
        except Exception as e:
            continue
    
    return display_data

# Sidebar Filters (moved before data loading for optimization)
st.sidebar.header("🔍 Filters")
search_term = st.sidebar.text_input("Search by Name or ID", placeholder="e.g. Spider-Man, sh001")

# Load data with progress tracking
progress_bar = st.progress(0)
progress_text = st.empty()

def update_progress(current, total, item_name):
    """Update progress bar and text"""
    progress = current / total
    progress_bar.progress(progress)
    progress_text.text(f"Loading superhero data... {current}/{total} items processed ({item_name[:30]}...)")

progress_text.text("Loading superhero database...")
all_figures = load_superhero_data(
    search_filter=search_term if search_term else None,
    _progress_callback=update_progress
)

# Clear progress indicators
progress_bar.empty()
progress_text.empty()

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
    
    # Search filtering already applied during data load
    filtered_df = category_df.copy()
    
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
    
    # Export columns defined here so they're available in both view modes
    export_cols = ["id", "name", "year", "used_price", "new_price", "used_conf", "new_conf"]

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
        st.dataframe(
            filtered_df[["img"] + export_cols],
            use_container_width=True,
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

    # Export button — uses export_cols which is always defined above
    st.divider()
    csv_data = filtered_df[export_cols].to_csv(index=False)
    st.download_button(
        label=f"📥 Export {category_name} to CSV",
        data=csv_data,
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

db.close()
