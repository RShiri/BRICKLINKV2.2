"""Shared BrickLink price-guide row parsing helpers.

Both scrapers — Selenium (`scraper.py`) and Playwright (`scraper_playwright.py`)
— parse the same ``pcipgInnerTable`` rows, so the logic for deciding whether a
listing is *incomplete* (and must therefore be excluded from pricing) lives
here in one place instead of being duplicated, and drifting, across the two.

Why this exists / what it fixes
-------------------------------
The previous inline check was::

    if tr.find(class_="js-item-status-incomplete") or "(i)" in tr.get_text().lower():

which had two gaps:

1. ``tr.find(class_=...)`` only searches *descendants*, so when BrickLink puts
   the status class on the ``<tr>`` element itself the row was NOT flagged.
2. Live scrapes never stored the row's text, so the pricing engine's keyword
   completeness filter ("no minifigs", "build only", …) had nothing to scan
   and was effectively inert on real data.

``row_is_incomplete`` closes gap 1 (and generalises the class match), and
``row_description`` closes gap 2 by giving each listing real text to filter on.
"""
import re

from bs4 import Tag

# A class token BrickLink attaches to an incomplete listing. Matched as a
# case-insensitive substring so every variant — ``js-item-status-incomplete``,
# ``pciItemStatusIncomplete``, ``incompleteFlag`` … — is caught.
_INCOMPLETE_CLASS_HINT = "incomplete"

# Textual incompleteness markers within a row: the superscript "(i)" indicator
# BrickLink renders next to incomplete sets, or the literal word "incomplete".
_INCOMPLETE_TEXT_RE = re.compile(r"\(i\)|\bincomplete\b", re.IGNORECASE)


def row_is_incomplete(tr: Tag) -> bool:
    """Return True if a price-guide row is flagged as an incomplete set.

    Checks, most-reliable first:

    1. an ``incomplete`` class token on the row itself **or** any descendant
       (the old code only searched descendants);
    2. the "(i)" superscript marker, or the word "incomplete", in the row's
       visible text.

    Detection is deliberately conservative — it fires only on explicit
    incompleteness signals — so genuine complete sales are never dropped.
    """
    for el in (tr, *tr.find_all(True)):
        for cls in el.get("class") or []:
            if _INCOMPLETE_CLASS_HINT in cls.lower():
                return True
    return bool(_INCOMPLETE_TEXT_RE.search(row_description(tr)))


def row_description(tr: Tag) -> str:
    """Return the visible text of a listing row.

    Persisted on each scraped listing so the pricing engine's keyword
    completeness filter has real text to scan. On live scrapes the listing
    dict previously carried no description at all, which left that filter inert.
    """
    return tr.get_text(" ", strip=True)
