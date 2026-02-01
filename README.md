# 🧱 BrickLink Sniper Dashboard

A comprehensive Streamlit dashboard for analyzing BrickLink market data, tracking collections, and discovering profitable LEGO deals. Features role-based access control, superhero minifigure databases, and advanced pricing analytics.

## ✨ Features

### 🔐 User/Admin Access System
- **Landing Page**: Choose between User (public) or Admin (password-protected) mode
- **Role-Based Navigation**: Different features available based on access level
- **Admin Password**: 7399 (for full access to collections)

### 📊 Dashboard Modes

#### **User Mode** (Public Access)
- **Set Analyzer**: Analyze LEGO sets with market pricing and profit calculations
- **Set Analyzer Database**: Browse all analyzed sets with filtering and sorting
- **Marvel Database**: Browse Marvel superhero minifigures (2005+) with pricing
- **DC Database**: Browse DC superhero minifigures (2005+) with pricing

#### **Admin Mode** (Password Required)
All User Mode features plus:
- **🔐 Ram's Collection**: Personal investment portfolio with analytics
- **🔐 Udi's Collection**: Secondary collection tracking

### 🦸 Superhero Databases
- **Separate Marvel & DC Pages**: Dedicated pages for each universe
- **Categorization**: Standard, Exclusives, and Big Figures tabs
- **Big Figures Detection**: Automatically identifies big figures (7+ parts, Giant Arms/Hands)
- **Filtering**: Year-based filtering and multiple sort options
- **View Modes**: Table (default) or Gallery view
- **Export**: CSV export for each category
- **Debug Tools**: Built-in debug section to verify big figure detection

### 💰 Pricing Engine
- **Market Analysis**: Scrapes "New" and "Used" prices from BrickLink
- **Confidence Levels**: HIGH/MEDIUM/LOW based on sales volume
- **Outlier Filtering**: Intelligent removal of incomplete sets and scams
- **Part Out Value (POV)**: Estimates profitable breakdown values
- **Minifigure Breakdown**: Automatic valuation of all minifigures in sets

### 📈 Analytics Features
- **Profit Tracking**: Visual profit margins and "Sniper" ratings
- **Trend Analysis**: Price change tracking (▲/▼ with percentages)
- **Interactive Tables**: Sortable, filterable data tables
- **Image Display**: Set and minifigure images directly in UI
- **Drill-Down Details**: Inspect individual components

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/RShiri/BRICKLINKV2.2.git
   cd BRICKLINKV2.2
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the dashboard**:
   ```bash
   streamlit run dashboard.py
   ```

4. **Access the app**:
   - Opens at `http://localhost:8501`
   - Choose User or Admin mode on landing page
   - Admin password: `7399`

## 📂 Project Structure

```
V2.2/
├── dashboard.py              # Main Streamlit dashboard
├── database.py               # SQLite database handler
├── scraper.py                # BrickLink web scraper
├── pricing_engine.py         # Market analysis algorithms
├── pages/
│   ├── 1_🦸_Marvel.py       # Marvel minifigure database
│   └── 2_🦇_DC.py           # DC minifigure database
├── scan_superheroes.py       # Superhero minifig scanner
├── scan_catalog.py           # Catalog-based scanner
├── scan_all_minifigs.py      # Universal minifig scanner
├── bricklink_data.db         # SQLite database
└── backup/                   # Archived files
```

## 🛠️ Scanners

### Scan Superheroes
```bash
python scan_superheroes.py
```
Scans all superhero minifigures (sh001-sh999) from BrickLink.

### Scan Catalog
```bash
python scan_catalog.py
```
Scans specific sets from a predefined catalog.

### Scan All Minifigs
```bash
python scan_all_minifigs.py
```
Universal scanner for any minifigure range.

## 🧠 Pricing Algorithm

### Data Cleaning
- **Blacklist Filter**: Removes "incomplete", "no minifigs", "box only" listings
- **Dynamic Price Floor**: 
  - 60% of median for most items
  - 1 ILS floor for 2025 releases (early market data)

### Market Price Calculation

| Sales Volume | Formula | Confidence |
|:-------------|:--------|:-----------|
| **10+ sales** | `(70% × Sold Avg) + (30% × Stock)` | HIGH |
| **1-9 sales** | `100% × Sold Avg` | MEDIUM |
| **0 sales** | `100% × Stock Price` | LOW |

**Stock Price** = Competitive Anchor (average of cheapest 35% of listings)

## 🦸 Big Figures Detection

Big figures are identified by:
- **Keywords**: "Big Fig", "BigFig", or "Giant" in name
- **Part Count**: Minimum 7 parts
- **Giant Parts**: Most have Giant Arms/Hands (part 43093)
- **Verified IDs**: Manually verified big figure IDs

**Marvel Big Figures**: Thanos variants, Cull Obsidian, Hulk giants  
**DC Big Figures**: Bane, Killer Croc variants

## 📊 Database Schema

### Collections Table
- `id`, `item_id`, `item_type`, `collection_name`
- `purchase_price`, `purchase_date`, `notes`

### Items Cache
- Stores scraped BrickLink data
- Includes metadata, pricing, and analysis results

## 🔒 Security Notes

- Admin password is hardcoded (7399) - change in production
- Session state manages authentication
- No sensitive data stored in database

## 🤝 Contributing

Pull requests welcome! For major changes, open an issue first.

## 📄 License

[MIT](https://choosealicense.com/licenses/mit/)

## 🎯 Roadmap

- [ ] User-configurable admin password
- [ ] Export collections to CSV
- [ ] Price history charts
- [ ] Email alerts for "Sniper" deals
- [ ] Multi-user support with individual collections
