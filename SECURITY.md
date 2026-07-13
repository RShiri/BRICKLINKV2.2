# Security Notes

## ⚠️ ACTION REQUIRED: rotate Supabase credentials

A previous commit contained the Supabase database password in plaintext
(`tests/test_db_standalone.py`, now deleted). The file is gone from the
current tree, but **the password still exists in git history** and must be
treated as compromised. In addition, the database currently has **no
Row Level Security**, which means the public `anon` key used by the mobile
app has effectively been a *write* key.

Do the following in the Supabase dashboard (Settings → Database / API):

1. **Reset the database password** and update it in:
   - `.streamlit/secrets.toml` (Streamlit Cloud → App settings → Secrets)
   - the `DATABASE_URL` GitHub Actions secret (used by the ETL workflow)
   - any local `.env` files
2. **Regenerate the `anon` and `service_role` API keys** and update:
   - `mobile_app` env (`EXPO_PUBLIC_SUPABASE_URL` / `EXPO_PUBLIC_SUPABASE_ANON_KEY`)
   - `web/.env.local` (`NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
3. **Apply the RLS migration** (`supabase/migrations/0003_rls.sql`) so the
   anon key becomes read-only for public data.
4. Optionally purge the secret from git history with
   [`git filter-repo`](https://github.com/newren/git-filter-repo)
   (`--replace-text`) or BFG and force-push. Rotation (steps 1–2) is the
   real mitigation; history rewrite is defense in depth.

## Secret handling rules

- Never commit passwords, API keys, or project-specific connection strings.
- Python (Streamlit) reads secrets from `st.secrets` / `.streamlit/secrets.toml` (gitignored).
- Python (ETL) reads `DATABASE_URL` from the environment (see `etl/.env.example`).
- Next.js reads `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  from `web/.env.local` (gitignored; template in `web/.env.example`).
  The `service_role` key must never appear anywhere under `web/`.
