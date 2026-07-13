# Deploying BrickSniper Web

The new site is a Next.js app (`web/`) on Vercel over the existing Supabase
database, with Python ETL (`etl/`) providing catalog + price data. The
Streamlit app keeps working unchanged throughout — everything here is
additive until you decide to switch over.

## 0. Security first (one-time)

Follow [SECURITY.md](../SECURITY.md): rotate the Supabase DB password and
API keys — the old ones were committed to git history and must be treated
as compromised.

## 1. Apply database migrations (one-time)

In the Supabase dashboard → SQL Editor, run each file in order:

1. `supabase/migrations/0001_catalog_schema.sql` — Rebrickable catalog tables
2. `supabase/migrations/0002_id_map_and_promoted_columns.sql` — ID mapping + promoted `items` columns
3. `supabase/migrations/0003_rls.sql` — **Row Level Security** (public data becomes read-only for the anon key)
4. `supabase/migrations/0004_views_and_search.sql` — deal views + trigram search
5. `supabase/migrations/0005_auth_profiles_collections.sql` — profiles, user collections
6. `supabase/migrations/0006_scrape_jobs.sql` — analyzer job queue

## 2. Load the catalog (one-time, then weekly)

On any machine (or via the GitHub Action):

```bash
cp etl/.env.example etl/.env   # fill DATABASE_URL (Supabase connection string)
pip install psycopg2-binary requests
python -m etl.import_rebrickable          # ~10 min; add --skip-inventory-parts to go faster
python -m etl.map_bricklink_ids           # builds BrickLink <-> Rebrickable mapping
python -m etl.backfill_item_columns       # fills promoted columns incl. price-guide quadrants
```

The GitHub Actions workflow `.github/workflows/rebrickable-import.yml` re-runs
the import weekly — add a `DATABASE_URL` repository secret to enable it.

## 3. Deploy the web app

1. In [Vercel](https://vercel.com), import the GitHub repo.
2. Set **Root Directory = `web`** (Framework: Next.js — autodetected).
3. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL` — Supabase project URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` — anon key (safe in browser once RLS is applied)
   - `REVALIDATE_SECRET` — any random string (optional; enables `/api/revalidate`)
4. Deploy. Every push to the connected branch redeploys automatically.

Local development:

```bash
cd web
cp .env.example .env.local   # fill in the Supabase values
npm install
npm run dev                  # http://localhost:3000
```

## 4. Auth + admin (one-time)

1. Supabase dashboard → Authentication → Providers: enable Email.
2. Sign up in the web app (`/login`).
3. Grant yourself admin:
   ```sql
   update profiles set role = 'admin' where id = '<your-user-uuid>';
   ```
4. Migrate the legacy collections (optional) — see the commented SQL at the
   bottom of `0005_auth_profiles_collections.sql`.

## 5. Run the scrape worker (for /tools/analyzer)

The analyzer page enqueues jobs into `scrape_jobs`; a worker with a real
browser executes them (Vercel cannot). On the machine that already runs the
scan scripts:

```bash
pip install playwright && playwright install chromium
python -m etl.scrape_worker            # long-running; or --once for a single job
```

Scrapes automatically fill the promoted columns and price history that the
web app renders.

## Verification checklist

- `python -m pytest tests/test_pricing.py` — pricing engine still green
- After migrations: anon key can `select` from `items` but any `insert` fails (RLS)
- Home page shows live stats; `/deals` lists rated items; search autocompletes
- A set page (e.g. `/catalog/sets/76042`) shows the price-guide quadrant,
  history chart, and minifig breakdown once data is loaded
- Sign-up → add item to collection → appears under `/collection`
- Enqueue an analyzer job → worker picks it up → item page updates
