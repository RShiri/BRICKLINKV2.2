# BrickSniper Roadmap — Building a Real Alternative to BrickLink & BrickOwl

## The honest starting point

BrickLink (owned by the LEGO Group since 2019) and BrickOwl are **marketplaces**:
their moat is liquidity — a million sellers' inventories and buyers who default
to them. Nobody beats a marketplace by cloning it with zero sellers.

But both have real, exploitable weaknesses:

| Weakness | BrickLink | BrickOwl | Our answer |
|---|---|---|---|
| Analytics | 6-month averages, no filtering, dated UI | Even thinner | Statistical price pipeline (IQR, bulk/incomplete filtering, confidence tiers) — already live |
| Deal discovery | None — you find deals by hand | None | Sniper War Room: rated, ranked, margin-scored deals — already live |
| Portfolio intelligence | Wanted lists only | Similar | Collection ROI, buy targets, part-out analysis |
| UX / speed | 2005-era page loads | Better but plain | Modern SSR app, instant search, dark mode, mobile |
| Openness | Locked API, approval walls | Limited | Public read API + CSV exports from day one |

**The wedge strategy: don't out-marketplace them — out-intelligence them.**
Become the Bloomberg terminal for LEGO first (indispensable *alongside*
BrickLink), then add liquidity features once we own the audience that decides
where money gets spent.

---

## Phase 0 — Production foundation ✅ (done / this week)

- [x] Next.js 16 catalog site: 27k sets, 17k minifigs, themes, search
- [x] Statistical price guide + methodology page
- [x] Sniper deals with profit/margin ratings
- [x] Auth, collections, analyzer job queue, admin
- [x] Design system, dark mode, mobile layout, SEO (robots/sitemap)
- [x] Supabase RLS, weekly catalog auto-refresh, one-shot db-setup workflow
- [x] Full part inventories per set & minifig (~1M rows) + parts tables on detail pages

## Phase 1 — Catalog parity (2–4 weeks)

Goal: nobody needs to open BrickLink *to look something up*.

- Part detail pages: image, colors it exists in, **"appears in N sets"**, element ids
- Color guide page (all ~270 colors, swatches, BrickLink↔Rebrickable id mapping)
- Search upgrade: parts included, fuzzy matching, id-prefix autocomplete in header
- Set instructions links, alternate/B-model listing, sticker sheets
- Superset/subset relations (which sets contain this set's inventory)
- Image fallbacks everywhere + our own image cache/CDN proxy (stop hotlinking)
- **KPI:** any set/fig/part id resolves to a rich page in <1s

## Phase 2 — The intelligence moat (1–2 months)

Goal: the data product neither incumbent can match.

- Scraper fleet hardening: scheduled queues, freshness SLAs per theme,
  polite rate limits, retry/ban-avoidance hygiene
- Price history per condition with event annotations (retirement, re-release)
- **Alerts**: "tell me when 75192 used < ₪2,400" — email + push (mobile app shell exists)
- Part-out calculator: set price vs. sum-of-parts+figs, spread ranking
- Cross-market arbitrage: BrickLink vs BrickOwl vs eBay sold listings
- Portfolio: cost basis, unrealized P/L, value-over-time chart per collection
- Public REST API (read) + CSV/Sheets export — developers become distribution
- **KPI:** 1k weekly active users; >50% of sessions use an intelligence feature

## Phase 3 — Community & retention (2–4 months)

Goal: reasons to come back that aren't a purchase.

- Public profiles, shareable collections & want lists
- Follow themes/items; activity feed of price moves on followed items
- Reviews/notes on sets (investment-angle: "seals poorly", "minifig-driven value")
- Hebrew + English i18n (unique regional edge — ILS pricing already native)
- Ship the mobile app (Expo shell already in `mobile_app/`)
- **KPI:** 30% of registered users return weekly without an alert email

## Phase 4 — Liquidity: the marketplace leap (6+ months, gated on Phase 2–3 traction)

Goal: transactions happen *here*.

Sequenced deliberately — classifieds before checkout, checkout before escrow:

1. **Listings v1 (classifieds):** sellers list items at a price; buyers contact
   via the platform. Zero payment liability, immediate liquidity signal.
2. **Want-list matching:** notify when a listing matches a want list under target price.
3. **Checkout v2:** Stripe Connect (destination charges), platform fee **1.5%**
   (BrickLink charges 3%, BrickOwl 2.5%) — undercut visibly.
4. **Seller migration tooling:** BrickLink store XML / BrickOwl CSV importers —
   make moving inventory a 10-minute job. This is the single highest-leverage
   marketplace feature.
5. Buyer protection, dispute flow, seller ratings; VAT/tax handling (start IL + EU OSS).
- **KPI:** 100 active stores, first ₪100k GMV month

## Phase 5 — AI & data edge (parallel, ongoing)

- Fair-value model per item (features: theme, lifecycle, fig count, retail delta,
  scarcity) → replaces the 80% heuristic buy target with a learned one
- "Sniper Score" v2: probability-of-profit, expected days-to-flip
- **Photo → part id** recognition (killer feature for sorters/pickers; neither
  incumbent has a good one)
- Retirement predictor (sets nearing EOL = investment windows)

---

## Infrastructure track (runs under everything)

- Move imports from GitHub Actions to scheduled Supabase cron / worker fleet as volume grows
- Partition `price_history` by month; materialized views for deal ranking
- Observability: Sentry + uptime checks + scrape-health dashboard (admin page exists)
- Image pipeline: cache Rebrickable/BrickLink images into our own storage/CDN
- Cost ceiling awareness: Supabase free tier → Pro at ~10k MAU; Vercel Hobby → Pro at first real traffic

## Legal & data-provenance guardrails (non-negotiable)

- Rebrickable catalog data is CC-BY-SA — attribution already in footer, keep it
- BrickLink price scraping: public pages only, polite volumes, no ToS-violating
  authenticated scraping; migrate toward cleaner sources (eBay API, own marketplace
  data) as they become available
- Never present ourselves as affiliated with LEGO/BrickLink/Rebrickable (disclaimer live)
- PII: RLS everywhere (done), GDPR-style export/delete before Phase 3 social features

## What we deliberately do NOT do

- No feature-for-feature BrickLink clone — we win on intelligence, UX, and fees
- No paid ads before Phase 2 retention proves itself
- No marketplace escrow before legal/tax review
- No scraping arms race — if a source blocks us, we buy/partner/substitute, not evade

---

*Sequencing rule of thumb: each phase ships only when the previous phase's KPI
is met — traction gates spend.*
