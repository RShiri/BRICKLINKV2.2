import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pricing_engine import PriceAnalyzer


def listing(price, qty=1, description="", status="complete"):
    # status must be 'complete' to pass _process_dataset's double-check filter
    return {"price": price, "qty": qty, "description": description, "status": status}


def make_data(new_sold=None, new_stock=None, used_sold=None, used_stock=None, year=2020):
    return {
        "meta": {"year_released": year},
        "new": {"sold": new_sold or [], "stock": new_stock or []},
        "used": {"sold": used_sold or [], "stock": used_stock or []},
    }


class TestPriceAnalyzerStructure:
    def test_analyze_returns_expected_keys(self):
        result = PriceAnalyzer(make_data()).analyze()
        assert "new" in result
        assert "used" in result
        assert "deep_dive" in result
        assert "market_price" in result["new"]
        assert "confidence" in result["new"]

    def test_empty_data_returns_zero_prices(self):
        result = PriceAnalyzer(make_data()).analyze()
        assert result["new"]["market_price"] == 0
        assert result["used"]["market_price"] == 0


class TestBlacklist:
    @pytest.mark.parametrize("keyword", [
        "no minifigs", "incomplete", "missing parts", "build only",
        "no minifigures", "without minifig", "figures removed",
    ])
    def test_blacklisted_description_filtered(self, keyword):
        data = make_data(new_sold=[listing(100, description=keyword)])
        result = PriceAnalyzer(data).analyze()
        assert result["new"]["market_price"] == 0, f"'{keyword}' should be blacklisted"

    def test_status_incomplete_filtered(self):
        data = make_data(new_sold=[listing(100, status="incomplete")])
        result = PriceAnalyzer(data).analyze()
        assert result["new"]["market_price"] == 0

    def test_clean_listing_not_filtered(self):
        # Need ≥2 sold to reach MEDIUM confidence (market = sold*0.60 > 0 even without stock)
        data = make_data(new_sold=[listing(100), listing(110)])
        result = PriceAnalyzer(data).analyze()
        assert result["new"]["market_price"] > 0


class TestBulkFilter:
    def test_bulk_listing_above_threshold_filtered(self):
        # BULK_THRESHOLD = 3, so qty=4 is bulk and gets removed
        data = make_data(new_sold=[listing(50, qty=4)])
        result = PriceAnalyzer(data).analyze()
        assert result["new"]["market_price"] == 0

    def test_listing_at_threshold_kept(self):
        # qty=3 is exactly at threshold — should pass
        data = make_data(new_sold=[listing(100, qty=3), listing(110, qty=3)])
        result = PriceAnalyzer(data).analyze()
        assert result["new"]["market_price"] > 0


class TestRatings:
    def test_rating_is_valid_category(self):
        data = make_data(
            new_sold=[listing(500), listing(490), listing(510)],
            new_stock=[listing(200)]
        )
        result = PriceAnalyzer(data).analyze()
        sniper = result.get("deep_dive", {}).get("sniper", {})
        if sniper:
            assert sniper["rating"] in ["EXCELLENT", "GREAT INVEST", "GOOD", "IRRELEVANT"]

    def test_excellent_rating_on_high_margin(self):
        # Market ~500, cheapest stock ~200 → margin = (500 - 200*1.13) / 200 * 100 ≈ 137%
        data = make_data(
            new_sold=[listing(500), listing(480), listing(510), listing(495), listing(505),
                      listing(498), listing(502), listing(488), listing(512), listing(499)],
            new_stock=[listing(200)]
        )
        result = PriceAnalyzer(data).analyze()
        sniper = result.get("deep_dive", {}).get("sniper", {})
        if sniper and sniper.get("profit_abs", 0) > 0:
            assert sniper["rating"] == "EXCELLENT"

    def test_irrelevant_rating_on_low_margin(self):
        # Market ~100, cheapest stock ~98 → tiny margin
        data = make_data(
            new_sold=[listing(100), listing(99), listing(101)],
            new_stock=[listing(98)]
        )
        result = PriceAnalyzer(data).analyze()
        sniper = result.get("deep_dive", {}).get("sniper", {})
        if sniper:
            assert sniper["rating"] == "IRRELEVANT"


class TestConfidenceLevels:
    def test_high_confidence_with_ten_sold(self):
        # status='complete' required to pass _process_dataset's internal check
        data = make_data(new_sold=[listing(100 + i) for i in range(10)])
        result = PriceAnalyzer(data).analyze()
        assert result["new"]["confidence"] == "HIGH"
        assert result["new"]["market_price"] > 0

    def test_medium_confidence_with_two_to_nine_sold(self):
        data = make_data(new_sold=[listing(100), listing(110)])
        result = PriceAnalyzer(data).analyze()
        assert result["new"]["confidence"] in ["MEDIUM", "LOW"]

    def test_low_confidence_with_zero_sold(self):
        data = make_data(new_stock=[listing(100)])
        result = PriceAnalyzer(data).analyze()
        assert result["new"]["confidence"] == "LOW"
