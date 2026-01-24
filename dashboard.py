import streamlit as st
import pandas as pd
import json
import sqlite3
import os
import time
import logging
from datetime import datetime, timedelta
from database import Database
from pricing_engine import PriceAnalyzer
from scraper import BrickLinkScraper

# --- CONFIGURATION ---
st.set_page_config(page_title="BrickLink Sniper V1.3", layout="wide", page_icon="🧱")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stChatInputContainer {bottom: 20px;}
    .stMetric {background-color: transparent; padding: 10px; border-radius: 5px; border: 1px solid #333;}
    .stDataFrame {border: 1px solid #e0e0e0; border-radius: 5px;}
    
    /* Mobile Optimization */
    @media (max-width: 600px) {
        .stMetric { margin-bottom: 10px; }
        .stButton button { width: 100%; margin-top: 5px; }
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        h1 { font-size: 1.8rem !important; }
        div[data-testid="column"] { width: 100% !important; flex: 1 1 auto !important; min-width: 100% !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_scraper():
    return BrickLinkScraper()

def get_img_url(item_id):
    item_id = str(item_id).strip()
    is_fig = any(c.isalpha() for c in item_id)
    if is_fig:
        return f"https://img.bricklink.com/ItemImage/MN/0/{item_id}.png"
    else:
        img_id = item_id if "-" in item_id else f"{item_id}-1"
        return f"https://img.bricklink.com/ItemImage/SN/0/{img_id}.png"

def render_gallery_html(images, captions):
    """
    Renders a responsive, aligned gallery using HTML/CSS because st.image 
    doesn't support fixed height/aspect-ratio control well.
    """
    html = '<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 10px; justify-content: center; width: 100%;">'
    
    for img, cap in zip(images, captions):
        caption_html = cap.replace('\n', '<br>')
        html += f"""<div style="display: flex; flex-direction: column; align-items: center; width: 110px;"><div style="height: 110px; display: flex; align-items: center; justify-content: center; overflow: hidden; background: #f9f9f9; border-radius: 8px; border: 1px solid #eee;"><img src="{img}" style="max-width: 100%; max-height: 100%; object-fit: contain;"></div><div style="font-size: 12px; text-align: center; margin-top: 5px; color: #555; line-height: 1.2;">{caption_html}</div></div>"""
    
    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)

def delete_from_db(item_id):
    """Deletes an item from the database."""
    db = Database()
    try:
        db.cursor.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        db.cursor.execute("DELETE FROM inventory_lists WHERE set_id = ?", (item_id,))
        db.remove_from_collection(item_id, "Ram's Collection") 
        db.conn.commit()
        st.toast(f"Deleted {item_id}", icon="🗑️")
    except Exception as e:
        st.error(f"Delete failed: {e}")
    finally:
        db.close()

def create_console_report(item_id, result, minifig_details, mf_new, mf_used):
    """Generates an ASCII-style report EXACTLY matching runner.py output."""
    lines = []
    meta = result['meta']
    
    # Header
    lines.append("="*70)
    lines.append(f"BRICKLINK REPORT: {item_id} - {meta.get('item_name', 'Unknown')}")
    lines.append(f"Last Updated: {meta.get('cache_date', 'Fresh Fetch')}")
    lines.append("="*70)
    
    # 1. Prices
    for cond in ['new', 'used']:
        r = result[cond]
        lines.append(f"\n--- {cond.upper()} ---")
        lines.append(f"Market Price   : {r['market_price']:.2f} ILS")
        lines.append(f"Typical Range  : {r['range'][0]:.2f} - {r['range'][1]:.2f} ILS")
        lines.append(f"Confidence     : {r['confidence']}")
        lines.append(f"Data Integrity : {r['stats']['sold']['final_count']} Sales | {r['stats']['stock']['final_count']} Listings")

    # 2. Investment Analysis
    deep = result.get('deep_dive', {})
    lines.append(f"\n{'-'*70}")
    lines.append("🔍 STEP 2: INVESTMENT ANALYSIS")
    lines.append(f"{'-'*70}")
    status = deep.get('lifecycle', {}).get('status', 'N/A')
    lines.append(f"📅 STATUS: {status} (Released: {meta.get('year_released', 'N/A')})")
    
    sniper = deep.get('sniper', {})
    if sniper:
        lines.append(f"\n🎯 SNIPER OPPORTUNITY (New)")
        rating = sniper.get('rating', 'N/A')
        if "NO LISTINGS" not in rating:
            lines.append(f"   Deal Rating      : {rating}")
            lines.append(f"   Cheapest Listing : {sniper.get('price', 0):.2f} ILS")
            lines.append(f"   Potential Profit : {sniper.get('profit_abs', 0):.2f} ILS (Margin: {sniper.get('margin_pct', 0)}%)")
        else:
             lines.append(f"   Deal Rating      : {rating}")

    # 3. Minifigure Breakdown
    if minifig_details:
        lines.append(f"\n{'-'*70}")
        lines.append("👥 STEP 3: MINIFIGURE BREAKDOWN")
        lines.append(f"{'-'*70}")
        lines.append(f"   ✅ Found {len(minifig_details)} minifigures.")
        
        # Match runner.py column widths: ID<10 Name<35 Qty<5 New<12 Used<12
        lines.append(f"   {'ID':<10} {'Name':<35} {'Qty':<5} {'New (ea)':<12} {'Used (ea)':<12}")
        lines.append(f"   {'-'*10} {'-'*35} {'-'*5} {'-'*12} {'-'*12}")
        
        for m in minifig_details:
            # Name truncation logic
            name_short = (m['name'][:33] + '..') if len(m['name']) > 35 else m['name']
            lines.append(f"   {m['id']:<10} {name_short:<35} {m['qty']:<5} {m['new']:<12.2f} {m['used']:<12.2f}")
            
        # Comparison Section
        lines.append(f"\n{'-'*70}")
        lines.append(f"📊 COMPARISON (Set vs Minifigs)")
        lines.append(f"{'-'*70}")
        
        set_price_new = result['new']['market_price']
        set_price_used = result['used']['market_price']
        
        pct_new = (mf_new / set_price_new * 100) if set_price_new > 0 else 0
        pct_used = (mf_used / set_price_used * 100) if set_price_used > 0 else 0
        
        lines.append(f"   {'Metric':<15} {'NEW':<15} {'USED':<15}")
        lines.append(f"   {'-'*45}")
        lines.append(f"   {'Set Price':<15} {set_price_new:<15.2f} {set_price_used:<15.2f}")
        lines.append(f"   {'Figs Sum':<15} {mf_new:<15.2f} {mf_used:<15.2f}")
        lines.append(f"   {'Figs % of Set':<15} {pct_new:<14.1f}% {pct_used:<14.1f}%")
        
        if pct_new > 80:
            lines.append(f"   🔥 NEW: Strong Part-Out Candidate! (Figs > 80% of Set Price)")
        
    lines.append(f"\n{'='*70}")
    return "\n".join(lines)

def render_mobile_card(item):
    """Renders a simplified HTML card for mobile view."""
    color = "#e6ffe6" if item['Profit'] > 0 else "#fff0f0"
    
    html = f"""
    <div style="background: white; border-radius: 10px; padding: 10px; margin-bottom: 10px; border: 1px solid #eee; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
        <div style="display: flex; gap: 10px; align-items: start;">
            <div style="width: 60px; height: 60px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; background: #f9f9f9; border-radius: 5px;">
                <img src="{item['Image']}" style="max-width: 100%; max-height: 100%;">
            </div>
            <div style="flex-grow: 1;">
                <div style="font-weight: 600; font-size: 14px; margin-bottom: 2px;">{item['ID']} - {item['Name']}</div>
                <div style="font-size: 12px; color: #666; display: flex; gap: 8px;">
                    <span>🆕 <span style="color: #333; font-weight: 500;">{item['New Price']:.0f}₪</span></span>
                    <span>🏷️ <span style="color: #333; font-weight: 500;">{item['Used Price']:.0f}₪</span></span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-weight: 700; color: {'green' if item['Profit'] > 0 else 'red'}; font-size: 14px;">
                    {item['Profit']:+.0f}₪
                </div>
                <div style="font-size: 10px; color: #999;">{item['Rating']}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def process_analysis(item_id, deep_scan_enabled, force_scrape=False, progress_callback=None):
    """
    Core analysis logic shared by Batch and Single modes.
    Returns a dict with results or error.
    """
    if progress_callback: progress_callback(f"🔎 Analyzing {item_id}...")
    
    db = Database()
    item_data = db.get_item(item_id)
    needs_scrape = False
    
    # 1. Validation Logic
    if force_scrape:
        needs_scrape = True
    elif not item_data:
        needs_scrape = True
    else:
        try:
            updated_at = item_data.get("updated_at") or item_data.get("meta", {}).get("timestamp")
            if updated_at:
                last_update = datetime.fromisoformat(updated_at)
            else:
                last_update = datetime(2000, 1, 1)

            if datetime.now() - last_update > timedelta(days=30):
                needs_scrape = True

        except: needs_scrape = True

        if deep_scan_enabled:
            try:
                # Check directly if we have any data rows, since 'price_avg' isn't in raw DB data
                has_new = item_data.get('new', {}).get('sold') or item_data.get('new', {}).get('stock')
                has_used = item_data.get('used', {}).get('sold') or item_data.get('used', {}).get('stock')
                
                if not has_new and not has_used:
                    needs_scrape = True
            except:
                needs_scrape = True

    scraper = get_scraper()
    
    # 2. Scrape if needed
    if needs_scrape:
        try:
            if progress_callback: progress_callback(f"⏳ Scraping {item_id}...")
            
            # Determine type
            itype = 'M' if any(c.isalpha() for c in item_id) else 'S'
            
            scrape_result = scraper.scrape(item_id, item_type=itype, force=True)
            if scrape_result and "error" in scrape_result:
                return {"error": scrape_result["error"]}
            
            if scrape_result:
                item_data = db.get_item(item_id) # Reload cleaned
        except Exception as e:
            return {"error": f"Scrape failed: {e}"}

    if not item_data:
        return {"error": f"No data found for {item_id}"}

    # 3. Minifigure Logic
    minifig_new = 0.0
    minifig_used = 0.0
    mf_details = []
    mf_images = []
    mf_captions = []

    if not any(c.isalpha() for c in item_id):
        inv, _ = db.get_inventory(item_id)
        if not inv:
            try: 
                if progress_callback: progress_callback("🔎 Fetching inventory...")
                inv = scraper.get_minifigs_in_set(item_id)
            except: pass

        if inv:
            num_figs = len(inv)
            if progress_callback: progress_callback(f"👥 Analyzing {num_figs} Minifigures...")
            
            for idx, fig in enumerate(inv):
                # Progress Update
                if progress_callback: 
                    progress_callback(f"👥 Analyzing Minifigures... ({idx+1}/{num_figs}): {fig['name'][:20]}...")

                # Get fig data
                fd = db.get_item(fig['id'])
                
                # Check for bad data or stale data
                fig_needs_scrape = False
                if not fd:
                    fig_needs_scrape = True
                else:
                    # 1. Freshness Check (30 days)
                    last_updated = fd.get("meta", {}).get("timestamp") or fd.get("updated_at")
                    if last_updated:
                        try:
                            dt = datetime.fromisoformat(last_updated)
                            if datetime.now() - dt > timedelta(days=30):
                                fig_needs_scrape = True
                        except: fig_needs_scrape = True

                    # 2. Deep Scan (Missing content)
                    if not fig_needs_scrape and deep_scan_enabled:
                        try:
                            has_new = fd.get('new', {}).get('sold') or fd.get('new', {}).get('stock')
                            has_used = fd.get('used', {}).get('sold') or fd.get('used', {}).get('stock')
                            if not has_new and not has_used:
                                fig_needs_scrape = True
                        except: fig_needs_scrape = True
                
                # Scrape if needed
                if fig_needs_scrape:
                    try:
                        msg = f"⬇️ Fetching data for {fig['name'][:15]}... ({idx+1}/{num_figs})"
                        if progress_callback: progress_callback(msg)
                        else: st.toast(msg, icon="⬇️")
                        
                        fresh_data = scraper.scrape(fig['id'], item_type='M')
                        if fresh_data:
                            db.save_item(fig['id'], fresh_data)
                            fd = db.get_item(fig['id']) # Reload immediately
                    except Exception as e:
                        print(f"Failed to fix {fig['id']}: {e}")

                # Calculate
                if fd:
                    try:
                        fa = PriceAnalyzer(fd).analyze()
                        p_new = fa['new']['market_price']
                        p_used = fa['used']['market_price']
                        
                        qty = fig.get('qty', fig.get('quantity', 1))
                        minifig_new += (p_new * qty)
                        minifig_used += (p_used * qty)
                        
                        mf_details.append({
                            "id": fig['id'], 
                            "name": fig['name'],
                            "qty": qty,
                            "new": p_new, 
                            "used": p_used
                        })
                        
                        img_url = get_img_url(fig['id'])
                        mf_images.append(img_url)
                        short = (fig['name'][:15] + '..') if len(fig['name']) > 15 else fig['name']
                        mf_captions.append(f"{short}\n({p_new:.0f}₪)")
                    except: pass
    
    # 4. Final Report
    analysis = PriceAnalyzer(item_data).analyze(minifig_value_new=minifig_new, minifig_value_used=minifig_used)
    report_text = create_console_report(item_id, analysis, mf_details, minifig_new, minifig_used)
    
    # 5. Summary Data
    sniper = analysis.get("deep_dive", {}).get("sniper", {})
    summary = {
        "ID": item_id,
        "Name": analysis.get("meta", {}).get("item_name", "Unknown"),
        "New Price": analysis.get("new", {}).get("market_price", 0),
        "Used Price": analysis.get("used", {}).get("market_price", 0),
        "Profit": sniper.get("profit_abs", 0),
        "Rating": sniper.get("rating", "N/A"),
        "Status": analysis.get("deep_dive", {}).get("lifecycle", {}).get("status", "N/A")
    }

    # Save to Collection
    # REMOVED: db.add_to_collection(item_id, "Ram's Collection") 
    db.close()
    
    return {
        "success": True,
        "item_id": item_id,
        "summary": summary,
        "report": report_text,
        "images": mf_images,
        "captions": mf_captions,
        "main_img": get_img_url(item_id)
    }

# --- DATA LOADING ---
@st.cache_data(show_spinner=False, ttl=10)
def load_data():
    db = Database()
    
    # 1. Fetch Items
    db.cursor.execute("SELECT item_id, json_data, updated_at FROM items")
    all_rows = db.cursor.fetchall()
    
    # 2. Fetch Stale Items
    stale_items = set(db.get_stale_items(days_threshold=30))
    
    # 3. Fetch Collection (DB + CSV)
    collection_ids = set()
    
    # From DB
    db_collection = db.get_collection_items("Ram's Collection")
    for cid in db_collection:
        collection_ids.add(cid.lower())
        
    # From CSV (Legacy Support)
    try:
        if os.path.exists("BrickEconomy-Sets(2).csv"):
            df_csv = pd.read_csv("BrickEconomy-Sets(2).csv")
            for _, row in df_csv.iterrows():
                raw_id = str(row['Number']).strip().lower()
                base_id = raw_id.split('-')[0] if '-' in raw_id else raw_id
                collection_ids.add(base_id)
                collection_ids.add(raw_id)
    except: pass

    # 4. Fetch Inventory Map
    inventory_map = {}
    db.cursor.execute("SELECT set_id, json_data FROM inventory_lists")
    inv_rows = db.cursor.fetchall()
    db.close() # Close DB connection early

    for r in inv_rows:
        s_id = str(r[0])
        figs_data = json.loads(r[1])
        inventory_map[s_id] = [f['id'] for f in figs_data]
        
        # If set is in collection, assume its figs are too (for visibility)
        if s_id in collection_ids or f"{s_id}-1" in collection_ids:
            for f in figs_data:
                collection_ids.add(f['id'].lower())

    sets, figs = [], []
    price_map = {} 
    junk_keywords = ['python', 'streamlit', 'n', 'test', 'runner', 'cmd']

    for row in all_rows:
        item_id = str(row[0]).strip()
        if any(key in item_id.lower() for key in junk_keywords) or len(item_id) < 2: continue

        try:
            raw_data = json.loads(row[1])
            is_stale = item_id in stale_items
            
            analysis = PriceAnalyzer(raw_data).analyze()
            sniper = analysis.get("deep_dive", {}).get("sniper", {})
            
            yr = analysis.get("meta", {}).get("year_released")
            year_val = str(int(float(yr))) if yr and str(yr).replace('.0','').isdigit() else ""
            
            used_price = analysis.get("used", {}).get("market_price", 0)
            price_map[item_id] = used_price

            item = {
                "ID": item_id,
                "Image": get_img_url(item_id),
                "Name": analysis.get("meta", {}).get("item_name", "Unknown"),
                "Year": year_val,
                "New Price": analysis.get("new", {}).get("market_price", 0),
                "New Conf": analysis.get("new", {}).get("confidence", "N/A"),
                "Used Price": used_price,
                "Used Conf": analysis.get("used", {}).get("confidence", "N/A"),
                "Profit": sniper.get("profit_abs", 0),
                "Margin %": sniper.get("margin_pct", 0),
                "Rating": sniper.get("rating", "N/A"),
                "InCollection": item_id.lower() in collection_ids,
                "Stale": "⚠️" if is_stale else "✅"
            }
            if any(c.isalpha() for c in item_id): figs.append(item)
            else: sets.append(item)
        except: continue

    # Post-process sets for polybags & figs
    for s in sets:
        s_id = s["ID"]
        fig_ids = inventory_map.get(s_id)
        if not fig_ids and "-" in s_id: fig_ids = inventory_map.get(s_id.split("-")[0])

        s["Minifig Count"] = len(fig_ids) if fig_ids else 0
        s["Total Figs Value"] = 0.0
        s["Figs %"] = 0.0
        s["Part-Out Alert"] = ""

        if fig_ids:
            fig_sum = sum(price_map.get(fid, 0) for fid in fig_ids)
            s["Total Figs Value"] = fig_sum
            
            # Polybag Override
            name_lower = s["Name"].lower()
            if ("polybag" in name_lower or "foil pack" in name_lower) and fig_sum > 0:
                s["Used Price"] = fig_sum
                s["Used Conf"] = "Polybag (Figs)"
            
            # Figs % for Used Sets
            if s["Used Price"] > 0:
                pct = (fig_sum / s["Used Price"]) * 100
                s["Figs %"] = pct
                if pct > 80: s["Part-Out Alert"] = "🔥"

    return pd.DataFrame(sets), pd.DataFrame(figs)

# --- SIDEBAR NAV ---
mode = st.sidebar.radio("Navigation", ["🔎 Set Analyzer", "📊 Portfolio Manager"], index=0)
st.sidebar.divider()

if mode == "🔎 Set Analyzer":
    deep_scan = st.sidebar.checkbox("Enable Deep Scan (Fix Zero Prices)", value=True, help="Force re-scrape for items with 0.00 price.")
    
    if st.sidebar.button("🔄 Reset Scraper Engine"):
        get_scraper.clear()
        st.toast("Scraper rebooted!", icon="♻️")
        time.sleep(1)
        st.rerun()
else:
    deep_scan = False

if mode == "📊 Portfolio Manager":
    st.title("📊 Portfolio Manager")
    
    col_filter, col_status = st.columns([2, 1])
    with col_filter:
        collection_source = st.radio("Collection Source:", ["Ram's Collection", "Full Database"], horizontal=True)
        # Mobile view is now global
        
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        if col_btn2.button("📥 Import CSV"):
            try:
                if os.path.exists("BrickEconomy-Sets(2).csv"):
                    df_csv = pd.read_csv("BrickEconomy-Sets(2).csv")
                    db = Database()
                    count = 0
                    for _, row in df_csv.iterrows():
                        raw_id = str(row['Number']).strip()
                        # Clean ID
                        clean_id = raw_id.split('-')[0] if '-' in raw_id else raw_id
                        db.add_to_collection(clean_id, "Ram's Collection")
                        count += 1
                    db.close()
                    st.success(f"Successfully imported {count} items to Ram's Collection!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("CSV file not found: BrickEconomy-Sets(2).csv")
            except Exception as e:
                st.error(f"Import failed: {e}")
    
    df_sets, df_figs = load_data()
    
    if collection_source == "Ram's Collection":
        if not df_sets.empty: df_sets = df_sets[df_sets["InCollection"]]
        if not df_figs.empty: df_figs = df_figs[df_figs["InCollection"]]
        
    # Metrics
    # Metrics
    t_new = 0
    t_used = 0
    t_profit = 0
    
    if not df_sets.empty:
        t_new += df_sets["New Price"].sum()
        t_used += df_sets["Used Price"].sum()
        t_profit += df_sets["Profit"].sum()
        
    if not df_figs.empty:
        t_new += df_figs["New Price"].sum()
        t_used += df_figs["Used Price"].sum()
        t_profit += df_figs["Profit"].sum()
        
    m1, m2, m3 = st.columns(3)
    m1.metric("Portfolio Value (New)", f"{t_new:,.0f} ₪")
    m2.metric("Portfolio Value (Used)", f"{t_used:,.0f} ₪")
    m3.metric("Total Profit Potential", f"{t_profit:,.0f} ₪")
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["💎 Investment Hub", "⚔️ Part-Out Strategist", "📦 All Items", "👥 Minifigures"])
    
    with tab1:
        st.caption("High ROI Secured Sets (New)")
        if not df_sets.empty:
            df_new = df_sets[df_sets["New Price"] > 0].sort_values("Profit", ascending=False)
            
            if mobile_view:
                for _, row in df_new.iterrows():
                    render_mobile_card(row)
            else:
                st.dataframe(
                    df_new,
                    width="stretch",
                    column_order=["Stale", "Image", "ID", "Name", "New Price", "New Conf", "Used Price", "Profit", "Margin %", "Rating"],
                    hide_index=True,
                    column_config={
                        "Image": st.column_config.ImageColumn("Img", width="small"),
                        "New Price": st.column_config.NumberColumn("New Price", format="%.2f ₪"),
                        "Used Price": st.column_config.NumberColumn("Used Price", format="%.2f ₪"),
                        "Profit": st.column_config.NumberColumn("Profit", format="%.2f ₪"),
                        "Margin %": st.column_config.ProgressColumn("Margin", format="%.0f%%", min_value=-50, max_value=100)
                    }
                )

    with tab2:
        st.caption("Undervalued Used Sets (High Minifig Value)")
        if not df_sets.empty:
            df_used = df_sets[df_sets["Used Price"] > 0].sort_values("Figs %", ascending=False)
            st.dataframe(
                df_used,
                width="stretch",
                column_order=["Stale", "Image", "ID", "Part-Out Alert", "Used Price", "Used Conf", "Total Figs Value", "Figs %"],
                hide_index=True,
                column_config={
                    "Image": st.column_config.ImageColumn("Img", width="small"),
                    "Part-Out Alert": st.column_config.TextColumn("Alert"),
                    "Figs %": st.column_config.ProgressColumn("Figs %", format="%.0f%%", min_value=0, max_value=150)
                }
            )

    with tab3:
        st.dataframe(df_sets, width="stretch", hide_index=True, column_config={"Image": st.column_config.ImageColumn()})

    with tab4:
        if not df_figs.empty:
            mf_new = df_figs["New Price"].sum()
            mf_used = df_figs["Used Price"].sum()
            mf_profit = df_figs["Profit"].sum()
            
            st.caption("Minifigure Collection Stats")
            c1, c2, c3 = st.columns(3)
            c1.metric("Minifigs Value (New)", f"{mf_new:,.0f} ₪")
            c2.metric("Minifigs Value (Used)", f"{mf_used:,.0f} ₪")
            c3.metric("Minifigs Profit", f"{mf_profit:,.0f} ₪")
            
        st.dataframe(df_figs, width="stretch", hide_index=True, column_config={"Image": st.column_config.ImageColumn()})

    st.sidebar.subheader("Actions")
    del_id = st.sidebar.text_input("Delete Item ID")
    if st.sidebar.button("Delete Item"):
        if del_id:
            delete_from_db(del_id)
            st.cache_data.clear()
            st.rerun()



elif mode == "🔎 Set Analyzer":
    st.title("🔎 Set Analyzer")
    
    with st.expander("ℹ️ How to Use", expanded=False):
        st.markdown("""
        **Welcome to the Set Analyzer!**  
        Type one or more IDs below to get real-time market data from BrickLink.
        
        **Examples:**
        - **Sets**: `75001` (Republic Troopers), `10333` (Barad-dûr)
        - **Minifigures**: `sw0450` (Captain Rex), `sh0232` (Man-Bat)
        - **Batch Search**: `75001 75002 sw0001` (Space separated)
        - **Force Refresh**: `75001 force` (Ignores cache)
        
        *Tip: Check 'Mobile View' in the sidebar for a better phone experience!*
        """)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! Enter Set IDs (e.g., '75001 75002')."}]

    # Render History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # Render Expanders for Batch items
            if "expanders" in msg:
                for item in msg["expanders"]:
                    with st.expander(f"📄 Report: {item['id']} - {item['name']}"):
                        if mobile_view:
                            st.image(item['main_img'], width=200)
                            st.code(item['report'], language="text")
                        else:
                            col_img, col_txt = st.columns([1,5])
                            with col_img: st.image(item['main_img'], width="stretch")
                            with col_txt: st.code(item['report'], language="text")
                            
                        if item['images']:
                            st.write("### Minifigures")
                            render_gallery_html(item['images'], item['captions'])

            # If batch summary DF exists, show it (AT THE END)
            if "batch_df" in msg:
                st.dataframe(msg["batch_df"], width="stretch", hide_index=True)

            # Standard Single Item Render
            if "image_url" in msg and msg["image_url"]:
                st.image(msg["image_url"], width=200)
            
            if msg.get("type") == "code":
                st.code(msg["content"], language="text")
            
            if msg.get("content") and msg.get("type") != "code":
                st.write(msg["content"])
                
            if "gallery_images" in msg:
                st.markdown("### 👥 Minifigures Gallery")
                render_gallery_html(msg["gallery_images"], msg["gallery_captions"])

    # Chat Input
    if user_input := st.chat_input("Enter Set IDs (e.g., 76001, 75002)"):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        if user_input.strip() == "?":
            st.cache_data.clear()
            st.warning("Cache cleared.")
        else:
            # Parse IDs and Flags
            raw_input = user_input.replace(',', ' ').split()
            ids = []
            force_mode = False
            
            for token in raw_input:
                token = token.strip()
                if token.lower() in ['force', '--force', '-f']:
                    force_mode = True
                elif token:
                    ids.append(token)
            
            raw_ids = ids
            
            # BATCH MODE
            if len(raw_ids) > 1:
                with st.chat_message("assistant"):
                    st.write(f"🚀 Batch Processing {len(raw_ids)} items... (Force: {force_mode})")
                    prog_bar = st.progress(0)
                    status_txt = st.empty()
                    
                    summaries = []
                    expanders_data = []
                    
                    for i, item_id in enumerate(raw_ids):
                        status_txt.write(f"Processing {item_id} ({i+1}/{len(raw_ids)})...")
                        
                        try:
                            # Pass force_scrape
                            res = process_analysis(item_id, deep_scan, force_scrape=force_mode, progress_callback=status_txt.write)
                            
                            if res.get("success"):
                                summaries.append(res["summary"])
                                expanders_data.append({
                                    "id": res["item_id"],
                                    "name": res["summary"]["Name"],
                                    "report": res["report"],
                                    "main_img": res["main_img"],
                                    "images": res["images"],
                                    "captions": res["captions"]
                                })
                            else:
                                st.error(f"Error {item_id}: {res.get('error')}")
                        except Exception as e:
                            st.error(f"Crash on {item_id}: {e}")
                        
                        prog_bar.progress((i + 1) / len(raw_ids))
                    
                    prog_bar.empty()
                    status_txt.empty()
                    
                    # Display Batch Result
                    if summaries:
                        df_summary = pd.DataFrame(summaries)
                        
                        # 1. Expanders
                        for item in expanders_data:
                            with st.expander(f"📄 Report: {item['id']} - {item['name']}"):
                                col1, col2 = st.columns([1, 2])
                                with col1: st.image(item['main_img'], width=350)
                                with col2: st.code(item['report'], language="text")
                                if item['images']:
                                    st.write("### Minifigures")
                                    render_gallery_html(item['images'], item['captions'])

                        # 2. Summary Table (At the end)
                        # Add totals row
                        numeric_cols = df_summary.select_dtypes(include=['number']).columns
                        totals = {col: df_summary[col].sum() for col in numeric_cols}
                        totals['Name'] = '📊 TOTAL'
                        totals_df = pd.DataFrame([totals])
                        df_with_totals = pd.concat([df_summary, totals_df], ignore_index=True)
                        
                        st.dataframe(df_with_totals, width="stretch", hide_index=True)

                        # Save to History
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"Batch completed for {len(raw_ids)} items.",
                            "batch_df": df_summary,
                            "expanders": expanders_data
                        })
                        st.toast("Batch Complete!", icon="✅")

            # SINGLE MODE
            elif raw_ids:
                item_id = raw_ids[0]
                with st.chat_message("assistant"):
                    status_placeholder = st.empty()
                    # Pass force_scrape
                    res = process_analysis(item_id, deep_scan, force_scrape=force_mode, progress_callback=status_placeholder.write)
                    status_placeholder.empty()

                    if res.get("success"):
                        if mobile_view:
                            st.image(res["main_img"], width=200)
                            st.code(res["report"], language="text")
                        else:
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.image(res["main_img"], width=350)
                            with col2:
                                st.code(res["report"], language="text")
                        
                        if res["images"]:
                            st.markdown("### 👥 Minifigures Gallery")
                            render_gallery_html(res["images"], res["captions"])

                        # Save to history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": res["report"],
                            "type": "code",
                            "image_url": res["main_img"],
                            "gallery_images": res["images"],
                            "gallery_captions": res["captions"]
                        })
                        st.toast(f"✅ {item_id} analyzed!", icon="💾")
                        
                        # Manual Add to Collection
                        col_db, col_ram = st.columns(2)
                        
                        with col_db:
                            st.button("✅ Saved to Global DB", disabled=True, help="This item is already auto-saved to the main database.")
                            
                        with col_ram:
                            if st.button(f"➕ Add to Ram's Collection"):
                                db = Database()
                                db.add_to_collection(item_id, "Ram's Collection")
                                db.close()
                                st.toast(f"Added {item_id} to Ram's Collection", icon="📂")
                                st.cache_data.clear()
                                time.sleep(1)
                                st.rerun()

                        st.cache_data.clear()
                    else:
                        st.error(res.get("error"))