# 🧱 BrickLink Sniper V1.4

> **Professional LEGO Investment Analysis & Portfolio Management Platform**  
> Built with Python + Streamlit | Powered by real-time BrickLink market data

---

## Overview

BrickLink Sniper is a web application that helps LEGO collectors and investors make data-driven buy/sell decisions. It scrapes live pricing data from BrickLink, applies statistical filtering to compute fair market values, identifies profitable "sniper" deals, and tracks personal collections — all through an interactive Streamlit dashboard.

---

## Features

| Feature | Description |
|---|---|
| **Set Analyzer** | Real-time scraping and analysis for any LEGO set or minifigure by ID |
| **Batch Processing** | Analyze up to dozens of items at once (sequential ≤5, parallel >5) |
| **Minifigure Breakdown** | Automatically fetches the minifig inventory of any set and prices each figure |
| **Part-Out Strategist** | Detects sets where minifig value exceeds 80% of the used set price |
| **Investment Hub** | Ranks portfolio items by profit potential and margin |
| **Sniper War Room** | Live dashboard of the highest-profit items updated in the last 24 hours |
| **Personal Collections** | Track Ram's and Udi's collections with full portfolio metrics |
| **Price History** | Logs every scrape to a `price_history` table for trend analysis |
| **Smart Cache** | 30-minute in-memory cache per item + 5-minute data cache to minimize scraping |
| **Role-Based Access** | User mode (read-only) and Admin mode (edit, delete, collection management) |
| **Mobile Responsive** | CSS media queries for a usable phone experience |

---

## Architecture

```
BrickLink Sniper
├── dashboard.py          # Main Streamlit app — UI, routing, analysis orchestration
├── database.py           # SQLite layer with connection pooling and schema management
├── scraper.py            # Selenium/BeautifulSoup scraper for BrickLink price data
├── pricing_engine.py     # Statistical price analysis, outlier filtering, sniper scoring
├── currency_converter.py # Exchange rate utilities (USD → ILS)
├── pages/
│   ├── 1_🦸_Marvel.py   # Marvel superhero minifigure browser
│   └── 2_🦇_DC.py       # DC superhero minifigure browser
└── scripts/              # One-off utility scripts (catalog scanning, backfilling, etc.)
```

### Data Flow

```
User Input (Set ID)
      │
      ▼
Database Cache Check ──► Cached & Fresh? ──► Return cached data
      │
      ▼ (stale or missing)
BrickLinkScraper (Selenium + BeautifulSoup)
      │   scrapes sold history + current stock
      ▼
PriceAnalyzer
      │   filters incomplete listings (blacklist + regex)
      │   removes statistical outliers (IQR method)
      │   computes market price, sniper opportunity, lifecycle status
      ▼
Database.save_item()
      │   stores JSON data + cached_rating, cached_profit, cached_margin columns
      │   appends a row to price_history
      ▼
Dashboard renders report, minifig gallery, investment metrics
```

---

## Database Schema

### `items`
| Column | Type | Description |
|---|---|---|
| `item_id` | TEXT PK | BrickLink set/minifig ID (e.g., `75001`, `sh0232`) |
| `json_data` | TEXT | Full scraped data as JSON |
| `updated_at` | DATETIME | Last scrape timestamp |
| `cached_rating` | TEXT | Pre-computed investment rating (`EXCELLENT`, `GREAT INVEST`, etc.) |
| `cached_profit` | REAL | Pre-computed absolute profit in ILS |
| `cached_margin` | REAL | Pre-computed margin percentage |

### `inventory_lists`
| Column | Type | Description |
|---|---|---|
| `set_id` | TEXT PK | Parent set ID |
| `json_data` | TEXT | JSON array of minifigures with `id`, `name`, `qty` |
| `updated_at` | DATETIME | Last fetch timestamp |

### `collections`
| Column | Type | Description |
|---|---|---|
| `item_id` | TEXT | Set or minifig ID |
| `collection_name` | TEXT | e.g., `"Ram's Collection"` |
| `added_at` | DATETIME | When added |

### `price_history`
| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `item_id` | TEXT | References `items.item_id` |
| `price_new` | REAL | Market price (new) at scrape time |
| `price_used` | REAL | Market price (used) at scrape time |
| `confidence_new/used` | TEXT | `HIGH` / `MEDIUM` / `LOW` / `NO DATA` |
| `scraped_at` | DATETIME | Scrape timestamp |

---

## Pricing Engine

`PriceAnalyzer` applies a multi-layer filtering pipeline before computing any price:

1. **Completeness filter** — removes listings flagged as incomplete via a keyword blacklist and regex patterns (e.g., "no minifigs", "build only", "missing parts").
2. **Bulk seller filter** — excludes sellers listing 3+ identical items (likely dealers, not representative market).
3. **IQR outlier removal** — drops prices outside `[Q1 - 1.5×IQR, Q3 + 1.5×IQR]`.
4. **Market price** — weighted mean of remaining sold prices.

**Sniper Opportunity scoring:**
```
Profit  = Market Price - (Cheapest Listing × 1.13)   # 1.13 = BrickLink fees
Margin% = (Profit / Cheapest Listing) × 100

Rating:
  EXCELLENT    → Margin ≥ 20%
  GREAT INVEST → Margin ≥ 15%
  GOOD         → Margin ≥ 10%
  IRRELEVANT   → Margin < 10%
```

**Confidence levels** are based on the number of filtered sales:
- `HIGH` — 10+ sales
- `MEDIUM` — 5–9 sales
- `LOW` — 1–4 sales
- `NO DATA` — 0 sales

---

## Setup & Running

### Requirements
```
Python 3.10+
Google Chrome (for Selenium scraping)
ChromeDriver (matching your Chrome version)
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the app
```bash
streamlit run dashboard.py
```

The app will be available at `http://localhost:8501`.

### First-time use
The SQLite database (`bricklink_data.db`) is created automatically on first run. No manual schema setup needed.

---

## Usage Guide

### Set Analyzer
1. Navigate to **Set Analyzer** in the sidebar.
2. Enter one or more IDs in the chat input:
   - `75001` — single LEGO set
   - `sh0232` — single minifigure
   - `75001 75002 sh0232` — batch (space-separated)
   - `75001 force` — force re-scrape, ignore cache
3. Results include: market price (new + used), confidence, investment rating, profit potential, and a minifigure gallery with individual prices.

### Set Analyzer Database
Browse the full database of all scraped sets and minifigures with sorting, filtering, and the **Sniper War Room** hot deals section (deals with `GREAT INVEST` or `EXCELLENT` rating updated in the last 24h).

### Collections (Admin only)
- **Ram's Collection / Udi's Collection**: Personal portfolio views with tabs for Investment Hub, Part-Out Strategist, All Items, and Minifigures.
- Add items via the sidebar input. Sets automatically pull in their minifigures.
- Delete items individually or in bulk via checkbox selection or sidebar text input.

### Access Levels
| Mode | Capabilities |
|---|---|
| **User** | View all data, run analysis, browse database |
| **Admin** | + Delete items, manage collections, import CSV |

---

## Marvel & DC Pages

The `pages/` directory contains superhero-specific minifigure browsers (`1_🦸_Marvel.py`, `2_🦇_DC.py`) that filter the database to show only Marvel/DC minifigures with their current market prices — useful for tracking superhero minifig investments separately.

---

## Key Files Reference

| File | Purpose |
|---|---|
| `dashboard.py` | App entry point, all UI logic |
| `database.py` | `Database` class + SQLite connection pool |
| `scraper.py` | `BrickLinkScraper` — Selenium driver + HTML parsing |
| `pricing_engine.py` | `PriceAnalyzer` — statistical price calculation |
| `currency_converter.py` | USD → ILS conversion |
| `pages/1_🦸_Marvel.py` | Marvel minifig browser |
| `pages/2_🦇_DC.py` | DC minifig browser |
| `bricklink_data.db` | SQLite database (auto-created) |
| `logs/system.log` | App logs |

---

## Author

**Ram Shiri** — Data Engineering Student  
[LinkedIn](https://www.linkedin.com/in/ram-shiri-1a1056304/)

---

*BrickLink Sniper is an independent tool and is not affiliated with or endorsed by BrickLink or the LEGO Group.*
