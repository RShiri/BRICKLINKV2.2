import statistics
import re
import logging
from datetime import datetime
from typing import Dict, List, Any

class PriceAnalyzer:
    """
    Analyzes scrapped BrickLink data to calculate market prices and assess investment potential.
    Implements multi-layer filtering to exclude incomplete sets and statistical outliers.
    """
    BULK_THRESHOLD = 3
    
    # Updated Blacklist with more variations and case-insensitive terms
    BLACKLIST = [
        'incomplete', 'missing', 'no minifig', 'no minifigs', 'no figure', 
        'no figs', 'no box', 'no instructions', 'no manual', 'only build', 
        'build only', 'just build', 'instruction only', 'without minifig',
        'without minifigures', 'figures removed', 'minifigures removed',
        'no figures', 'no mf', 'no character', 'no-minifig', 'no-minifigures',
        '(i)', 'missing parts', 'partially complete', 'only castle', 'no characters'
    ]

    def __init__(self, data: Dict[str, Any]):
        """
        Initializes the analyzer with raw data.
        
        Args:
            data (Dict): The raw data dictionary from the scraper.
        """
        self.data = data
        self.meta = data.get("meta", {})

    def _is_strictly_complete(self, item: Dict) -> bool:
        """
        Layer 1: Checks if an item listing is truly complete based on description analysis.
        
        Args:
            item (Dict): The specific listing dictionary.
            
        Returns:
            bool: True if item passes all completeness checks, False otherwise.
        """
        price = item.get('price', 0)
        
        # 1. Scraper Flag Check
        if item.get('status') == 'incomplete':
            return False
            
        # 2. Text Content Check
        text_to_scan = (str(item) + " " + item.get('description', '')).lower()
        
        # A. Simple Blocklist
        for word in self.BLACKLIST:
            if word in text_to_scan:
                return False
        
        # B. Regex Red Flags (Layer 1)
        # Matches "No/Without" followed within 2 words by "Minifigs/Figures/Manual/Box"
        # Matches "Only" followed by "Build/Castle"
        red_flags_regex = [
            r"\b(no|without)\b.{0,15}\b(minifig|figure|cat|manual|box)\b",
            r"\b(build|castle|vehicle)\b.{0,15}\b(only)\b"
        ]
        
        for pattern in red_flags_regex:
            if re.search(pattern, text_to_scan):
                return False

        # C. Helper check for "Only" patterns
        if 'only' in text_to_scan:
            if any(x in text_to_scan for x in ['build', 'instruction', 'parts']):
                return False
                
        return True

    def analyze(self, minifig_value_new: float = 0.0, minifig_value_used: float = 0.0) -> Dict[str, Any]:
        """
        Main analysis method that returns processed pricing data.
        
        Args:
            minifig_value_new (float): Total market value of the set's minifigs (New).
            minifig_value_used (float): Total market value of the set's minifigs (Used).
            
        Returns:
            Dict: Comprehensive report including market prices, confidence levels, and investment stats.
        """
        results = {}
        # Pass the relevant minifig value for each condition
        results["new"] = self._analyze_condition("new", minifig_value_new)
        results["used"] = self._analyze_condition("used", minifig_value_used)
        
        results["deep_dive"] = self._analyze_investment_potential(results["new"])
        results["part_out"] = self._analyze_part_out_potential(results["new"]["market_price"])
        results["meta"] = self.meta
        return results

    def _analyze_condition(self, condition: str, minifig_val: float = 0.0) -> Dict[str, Any]:
        """
        Calculates market metrics for a specific condition (New/Used).
        
        Args:
            condition (str): "new" or "used".
            minifig_val (float): The total value of minifigures (used for price floor).
            
        Returns:
            Dict: Pricing metrics for the condition.
        """
        sold_raw = self.data.get(condition, {}).get("sold", [])
        stock_raw = self.data.get(condition, {}).get("stock", [])

        # Layer 1: Clean Data
        sold_data = [x for x in sold_raw if self._is_strictly_complete(x)]
        stock_data = [x for x in stock_raw if self._is_strictly_complete(x)]
        
        original_count = len(sold_data) + len(stock_data)

        # Layer 2: Minifig Floor
        if condition == "used" and minifig_val > 0:
            min_allowed = minifig_val * 0.80
            sold_data = [x for x in sold_data if x['price'] >= min_allowed]
            stock_data = [x for x in stock_data if x['price'] >= min_allowed]

        # Calculate Price Floor (Median Based - 20% rule)
        all_prices = [x['price'] for x in sold_data] + [x['price'] for x in stock_data]
        price_floor = 0
        if all_prices:
            global_median = statistics.median(all_prices)
            # 2025 sets are volatile, lower floor
            if self.meta.get("year_released") == 2025:
                price_floor = 1
            else:
                # Dynamic 20% floor (filters out "Box Only" listings)
                price_floor = global_median * 0.20 
        
        sold_data = [x for x in sold_data if x['price'] >= price_floor]
        stock_data = [x for x in stock_data if x['price'] >= price_floor]

        # Process
        sold_res = self._process_dataset(sold_data)
        stock_res = self._process_dataset(stock_data)

        sold_price = sold_res["avg"]
        stock_anchor = self._get_competitive_stock_price(stock_res["clean_items"])
        sold_count = sold_res["final_count"]

        # Layer 4: Confidence Logic (FIXED)
        if sold_count >= 10:
            market_price = (sold_price * 0.70) + (stock_anchor * 0.30)
            confidence = "HIGH"
        elif sold_count >= 2:
            # Fix: Blend Medium confidence too
            market_price = (sold_price * 0.60) + (stock_anchor * 0.40)
            confidence = "MEDIUM"
        else:
            # Fix: Low confidence relies on Stock Anchor to avoid outliers
            market_price = stock_anchor
            confidence = "LOW"
        
        # Confidence downgrade if >30% of data was filtered
        final_count = len(sold_res["clean_items"]) + len(stock_res["clean_items"])
        if original_count > 0:
            filtered_pct = (original_count - final_count) / original_count
            if filtered_pct > 0.30 and confidence == "HIGH":
                confidence = "MEDIUM"
                logging.info(f"⚠️ Confidence downgraded: {filtered_pct*100:.1f}% of data filtered")

        if market_price == 0 and sold_price > 0:
            market_price = sold_price

        return {
            "market_price": round(market_price, 2),
            "range": (round(market_price * 0.9, 2), round(market_price * 1.1, 2)),
            "buy_target": round(market_price * 0.80, 2),
            "confidence": confidence,
            "stats": {"sold": sold_res, "stock": stock_res, "stock_anchor": stock_anchor}
        }

    def _analyze_investment_potential(self, new_data: Dict) -> Dict[str, Any]:
        """
        Evaluates potential for profit by comparing market price ("Sniper") against cheapest listings.
        """
        year = self.meta.get("year_released")
        curr = datetime.now().year
        status, desc = "UNKNOWN", "Year not found"
        
        if year:
            age = curr - year
            if age <= 1: status, desc = "NEW", "Flooded market"
            elif 2 <= age <= 4: status, desc = "EOL WATCH", "Production ending soon"
            else: status, desc = "RETIRED", "Production stopped"

        # Safe extraction from clean data
        stock = new_data["stats"]["stock"]["clean_items"]
        mkt = new_data["market_price"]
        best = None
        
        if stock:
            # Find cheapest real listing
            cheapest_item = sorted(stock, key=lambda x: x['price'])[0]
            cheapest_price = cheapest_item['price']
            
            profit, margin = 0, 0
            if mkt > 0 and cheapest_price > 0:
                profit = mkt - (cheapest_price * 1.13)
                margin = (profit / cheapest_price) * 100
            
            rating = "IRRELEVANT"
            if margin >= 20: rating = "EXCELLENT"
            elif margin >= 10: rating = "GOOD"
            
            if status in ["EOL WATCH", "RETIRED"] and rating == "GOOD": 
                rating = "GREAT INVEST"
            
            best = {
                "price": cheapest_price, 
                "margin_pct": round(margin, 1), 
                "profit_abs": round(profit, 2), 
                "rating": rating
            }
        
        return {"lifecycle": {"status": status, "year": year, "desc": desc}, "sniper": best}

    def _get_competitive_stock_price(self, items):
        """Calculates the median price of the lowest 50% of listings."""
        if not items: return 0.0
        sorted_s = sorted(items, key=lambda x: x['price'])
        # New Logic: Median of the lowest 50%
        cutoff = max(1, int(len(sorted_s) * 0.50))
        subset = sorted_s[:cutoff]
        if not subset: return 0.0
        return statistics.median([x['price'] for x in subset])

    def _weighted_avg(self, items):
        """Helper to calculate weighted average (currently unused in favor of median)."""
        if not items: return 0.0
        val = sum(x["price"] * x["qty"] for x in items)
        qty = sum(x["qty"] for x in items)
        return val / qty if qty > 0 else 0.0

    def _analyze_part_out_potential(self, mkt: float) -> Dict[str, Any]:
        """Calculates Price Per Part (PPP) and other ratios."""
        specs = self.meta.get("specs", {})
        parts, w, minifigs = specs.get("parts", 0), specs.get("weight_g", 0), specs.get("minifigs", 0)
        ppp = mkt / parts if parts > 0 else 0
        ppg = mkt / w if w > 0 else 0
        rating, reason = "LOW", "Expensive per piece"
        if parts > 0:
            if ppp < 0.25: rating, reason = "HIGH", "Excellent PPP (<0.25)"
            elif ppp < 0.35: rating, reason = "MEDIUM", "Decent PPP"
        return {"ppp": round(ppp, 3), "ppg": round(ppg, 3), "parts_count": parts, 
                "weight_g": w, "minifigs_count": minifigs, "rating": rating, "reason": reason}

    def _process_dataset(self, items: List[Dict]) -> Dict[str, Any]:
        """
        Filters outliers using IQR and returns statistical summaries.
        """
        # Double check completeness
        complete_items = [
            x for x in items 
            if x.get('status') == 'complete' and self._is_strictly_complete(x)
        ]
        
        if not complete_items:
            return {"avg": 0.0, "final_count": 0, "clean_items": []}

        # Filter Bulk
        no_bulk = [x for x in complete_items if x["qty"] <= self.BULK_THRESHOLD]
        
        final = no_bulk
        if len(no_bulk) >= 5:
            try:
                vals = []
                for x in no_bulk: vals.extend([x["price"]] * x["qty"])
                if len(vals) >= 4:
                    q1, q3 = statistics.quantiles(vals, n=4)[0], statistics.quantiles(vals, n=4)[2]
                    iqr = q3 - q1
                    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                    # Stats Outlier Filter
                    final = [x for x in no_bulk if low <= x["price"] <= high]
            except: 
                pass
                
        # Layer 3: Return Median instead of Weighted Avg
        avg_val = 0.0
        if final:
            avg_val = statistics.median([x['price'] for x in final])

        return {
            "avg": avg_val, 
            "final_count": len(final), 
            "clean_items": final
        }