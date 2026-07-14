"""Tests for shared BrickLink row parsing (incomplete-set detection).

These are hermetic — they only need BeautifulSoup, not a live browser or DB —
so they exercise the exact logic both scrapers use to decide whether a
price-guide listing is incomplete and must be excluded from pricing.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bs4 import BeautifulSoup

from bricklink_parsing import row_is_incomplete, row_description


def _row(html):
    return BeautifulSoup(html, 'html.parser').find('tr')


class TestRowIsIncomplete:
    def test_class_on_row_itself(self):
        # Regression: the old check used tr.find(class_=...), which searches
        # only DESCENDANTS, so an incomplete class on the <tr> was missed.
        tr = _row('<tr class="js-item-status-incomplete">'
                  '<td>1</td><td>US $5.00</td></tr>')
        assert row_is_incomplete(tr) is True

    def test_class_on_descendant(self):
        tr = _row('<tr><td>1</td>'
                  '<td>US $5.00 <span class="pciItemStatusIncomplete"></span></td></tr>')
        assert row_is_incomplete(tr) is True

    def test_paren_i_superscript_marker(self):
        tr = _row('<tr><td>1</td><td>US $5.00 <sup>(i)</sup></td></tr>')
        assert row_is_incomplete(tr) is True

    def test_incomplete_word_in_text(self):
        tr = _row('<tr><td>1</td><td>US $5.00 (Incomplete)</td></tr>')
        assert row_is_incomplete(tr) is True

    def test_complete_row_not_flagged(self):
        tr = _row('<tr><td>1</td><td>US $5.00</td></tr>')
        assert row_is_incomplete(tr) is False

    def test_store_name_is_not_a_false_positive(self):
        # A normal current-stock row (store + qty + price) must not be flagged.
        tr = _row('<tr><td>BrickWorld Store</td><td>2</td><td>US $12.34</td></tr>')
        assert row_is_incomplete(tr) is False


class TestRowDescription:
    def test_captures_visible_text(self):
        # Live scrapes previously stored NO description, leaving the pricing
        # engine's keyword filter inert. The row text must now be captured.
        tr = _row('<tr><td>MyStore</td><td>1</td><td>US $9.99</td></tr>')
        desc = row_description(tr)
        assert 'MyStore' in desc
        assert '9.99' in desc
