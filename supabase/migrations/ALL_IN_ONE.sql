-- Rebrickable catalog tables. Columns mirror the CSV dumps at
-- https://rebrickable.com/downloads/ so etl/import_rebrickable.py can
-- COPY straight into staging and upsert here.

create table if not exists themes (
    id        integer primary key,
    name      text not null,
    parent_id integer references themes(id)
);
create index if not exists idx_themes_parent on themes(parent_id);

create table if not exists colors (
    id       integer primary key,
    name     text not null,
    rgb      text,
    is_trans boolean default false
);

create table if not exists part_categories (
    id   integer primary key,
    name text not null
);

create table if not exists catalog_sets (
    set_num   text primary key,
    name      text not null,
    year      integer,
    theme_id  integer references themes(id),
    num_parts integer,
    img_url   text
);
create index if not exists idx_catalog_sets_theme on catalog_sets(theme_id);
create index if not exists idx_catalog_sets_year on catalog_sets(year);

create table if not exists catalog_parts (
    part_num     text primary key,
    name         text not null,
    part_cat_id  integer references part_categories(id),
    part_material text
);
create index if not exists idx_catalog_parts_cat on catalog_parts(part_cat_id);

create table if not exists catalog_minifigs (
    fig_num   text primary key,
    name      text not null,
    num_parts integer,
    img_url   text
);

create table if not exists inventories (
    id      integer primary key,
    version integer not null default 1,
    set_num text not null
    -- no FK: inventories.csv includes minifig inventories whose set_num
    -- is a fig_num, so the reference is polymorphic by design
);
create index if not exists idx_inventories_set on inventories(set_num);

create table if not exists inventory_parts (
    inventory_id integer not null references inventories(id) on delete cascade,
    part_num     text not null,
    color_id     integer not null,
    quantity     integer not null,
    is_spare     boolean not null default false,
    img_url      text,
    primary key (inventory_id, part_num, color_id, is_spare)
);
create index if not exists idx_inventory_parts_part on inventory_parts(part_num);

create table if not exists inventory_minifigs (
    inventory_id integer not null references inventories(id) on delete cascade,
    fig_num      text not null references catalog_minifigs(fig_num),
    quantity     integer not null,
    primary key (inventory_id, fig_num)
);
create index if not exists idx_inventory_minifigs_fig on inventory_minifigs(fig_num);

create table if not exists inventory_sets (
    inventory_id integer not null references inventories(id) on delete cascade,
    set_num      text not null,
    quantity     integer not null,
    primary key (inventory_id, set_num)
);

create table if not exists elements (
    element_id text primary key,
    part_num   text,
    color_id   integer,
    design_id  text
);

-- Daily FX rates so displayed prices can show provenance (base: ILS).
create table if not exists fx_rates (
    currency   text not null,
    rate_to_ils numeric not null,
    fetched_on date not null,
    primary key (currency, fetched_on)
);
-- BrickLink <-> Rebrickable ID mapping and promoted columns on items,
-- so web clients never parse the large items.json_data blob.

create table if not exists external_id_map (
    item_type    text not null check (item_type in ('set', 'minifig', 'part')),
    rb_id        text not null,   -- Rebrickable id: set_num / fig_num / part_num
    provider     text not null default 'bricklink',
    ext_id       text not null,   -- e.g. '76042-1' -> '76042', 'fig-000123' -> 'sh0031'
    match_method text not null,   -- 'set_number' | 'inventory_intersection' | 'name_exact' | 'manual'
    confidence   real not null default 1.0,
    verified     boolean not null default false,
    created_at   timestamptz not null default now(),
    primary key (item_type, provider, ext_id)
);
create index if not exists idx_external_id_map_rb on external_id_map(item_type, rb_id);

-- Promoted columns on the existing price layer (items is keyed by BrickLink id).
alter table items add column if not exists item_type       text;
alter table items add column if not exists name            text;
alter table items add column if not exists year_released   integer;
alter table items add column if not exists price_new       real;
alter table items add column if not exists price_used      real;
alter table items add column if not exists confidence_new  text;
alter table items add column if not exists confidence_used text;
alter table items add column if not exists buy_target      real;
alter table items add column if not exists lifecycle       text;
-- ~1KB price-guide quadrant summary rendered by the web PriceGuideTable:
-- {"new":{"sold":{"min":..,"avg":..,"max":..,"qty":..,"lots":..},"stock":{...}},"used":{...}}
alter table items add column if not exists guide           jsonb;

create index if not exists idx_items_item_type on items(item_type);
create index if not exists idx_items_year on items(year_released);
create index if not exists idx_price_history_item_scraped
    on price_history(item_id, scraped_at desc);
-- Row Level Security. Before this migration the anon key could write to
-- every table. Public data becomes SELECT-only for anon/authenticated;
-- ETL keeps writing as the postgres table owner (RLS does not apply to
-- table owners), so no service-role key is needed anywhere.

-- Public read-only tables
do $$
declare t text;
begin
  foreach t in array array[
    'items', 'inventory_lists', 'collections', 'price_history',
    'themes', 'colors', 'part_categories',
    'catalog_sets', 'catalog_parts', 'catalog_minifigs',
    'inventories', 'inventory_parts', 'inventory_minifigs', 'inventory_sets',
    'elements', 'external_id_map', 'fx_rates'
  ]
  loop
    execute format('alter table %I enable row level security', t);
    execute format('drop policy if exists "public read" on %I', t);
    execute format(
      'create policy "public read" on %I for select to anon, authenticated using (true)', t);
  end loop;
end $$;
-- Views, aggregates and trigram search used by the web app.

create extension if not exists pg_trgm;

-- Deal leaderboard (Sniper War Room) over the promoted/cached columns.
create or replace view v_deals as
select
    i.item_id,
    i.item_type,
    coalesce(i.name, i.item_id)      as name,
    i.year_released,
    i.price_new,
    i.price_used,
    i.buy_target,
    i.lifecycle,
    i.cached_rating,
    i.cached_profit,
    i.cached_margin,
    i.updated_at,
    m.rb_id
from items i
left join external_id_map m
       on m.provider = 'bricklink'
      and m.ext_id = i.item_id
      and m.item_type = coalesce(i.item_type, m.item_type)
where i.cached_rating in ('EXCELLENT', 'GREAT INVEST', 'GOOD');

-- Per-theme aggregates for theme landing pages.
create or replace view v_theme_stats as
select
    s.theme_id,
    t.name                       as theme_name,
    count(*)                     as set_count,
    min(s.year)                  as year_from,
    max(s.year)                  as year_to
from catalog_sets s
join themes t on t.id = s.theme_id
group by s.theme_id, t.name;

-- Trigram indexes for instant search.
create index if not exists idx_items_name_trgm
    on items using gin (name gin_trgm_ops);
create index if not exists idx_items_id_trgm
    on items using gin (item_id gin_trgm_ops);
create index if not exists idx_catalog_sets_name_trgm
    on catalog_sets using gin (name gin_trgm_ops);
create index if not exists idx_catalog_minifigs_name_trgm
    on catalog_minifigs using gin (name gin_trgm_ops);
create index if not exists idx_catalog_parts_name_trgm
    on catalog_parts using gin (name gin_trgm_ops);

-- Scoped autocomplete search. scope: 'all' | 'sets' | 'parts' | 'minifigs'
create or replace function search_catalog(q text, scope text default 'all', lim int default 10)
returns table (
    result_type text,
    id          text,
    name        text,
    year        integer,
    img_url     text,
    price_new   real,
    rating      text
)
language sql stable
as $$
    with results as (
        select 'set'::text as result_type,
               s.set_num   as id,
               s.name,
               s.year,
               s.img_url,
               i.price_new,
               i.cached_rating as rating,
               greatest(similarity(s.name, q), similarity(s.set_num, q)) as sim
        from catalog_sets s
        left join external_id_map m on m.item_type = 'set' and m.rb_id = s.set_num
        left join items i on i.item_id = m.ext_id
        where (scope in ('all', 'sets'))
          and (s.name % q or s.set_num ilike q || '%')

        union all

        select 'minifig',
               coalesce(m.ext_id, f.fig_num),
               f.name,
               null::integer,
               f.img_url,
               i.price_new,
               i.cached_rating,
               greatest(similarity(f.name, q), similarity(f.fig_num, q))
        from catalog_minifigs f
        left join external_id_map m on m.item_type = 'minifig' and m.rb_id = f.fig_num
        left join items i on i.item_id = m.ext_id
        where (scope in ('all', 'minifigs'))
          and (f.name % q or f.fig_num ilike q || '%')

        union all

        -- Scraped items not yet mapped to the Rebrickable catalog still
        -- need to be findable (they carry their own BrickLink name).
        select case when i.item_type = 'S' or i.item_type = 'set' then 'set' else 'minifig' end,
               i.item_id,
               coalesce(i.name, i.item_id),
               i.year_released,
               null::text,
               i.price_new,
               i.cached_rating,
               greatest(similarity(coalesce(i.name, ''), q), similarity(i.item_id, q))
        from items i
        where (scope = 'all')
          and (i.name % q or i.item_id ilike q || '%')
          and not exists (
              select 1 from external_id_map m
              where m.provider = 'bricklink' and m.ext_id = i.item_id)

        union all

        select 'part', p.part_num, p.name, null::integer, null::text,
               null::real, null::text,
               greatest(similarity(p.name, q), similarity(p.part_num, q))
        from catalog_parts p
        where (scope in ('all', 'parts'))
          and (p.name % q or p.part_num ilike q || '%')
    )
    select result_type, id, name, year, img_url, price_new, rating
    from results
    order by sim desc
    limit lim;
$$;

grant execute on function search_catalog(text, text, int) to anon, authenticated;
-- Supabase Auth: profiles with roles, per-user collections, RLS.

create table if not exists profiles (
    id         uuid primary key references auth.users(id) on delete cascade,
    username   text unique,
    role       text not null default 'user' check (role in ('user', 'admin')),
    created_at timestamptz not null default now()
);

-- Auto-create a profile row on signup.
create or replace function handle_new_user()
returns trigger
language plpgsql security definer set search_path = public
as $$
begin
    insert into profiles (id, username)
    values (new.id, split_part(new.email, '@', 1))
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function handle_new_user();

create or replace function is_admin()
returns boolean
language sql stable security definer set search_path = public
as $$
    select exists (
        select 1 from profiles
        where id = auth.uid() and role = 'admin'
    );
$$;

create table if not exists user_collections (
    user_id         uuid not null references auth.users(id) on delete cascade,
    collection_name text not null default 'default',
    item_id         text not null,
    added_at        timestamptz not null default now(),
    primary key (user_id, collection_name, item_id)
);
create index if not exists idx_user_collections_user on user_collections(user_id);

alter table profiles enable row level security;
drop policy if exists "own profile read" on profiles;
create policy "own profile read" on profiles
    for select to authenticated using (id = auth.uid() or is_admin());
drop policy if exists "own profile update" on profiles;
create policy "own profile update" on profiles
    for update to authenticated using (id = auth.uid()) with check (id = auth.uid() and role = role);

alter table user_collections enable row level security;
drop policy if exists "own collection all" on user_collections;
create policy "own collection all" on user_collections
    for all to authenticated
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

-- Portfolio stats for the collection dashboard.
create or replace function collection_stats(p_collection text default null)
returns table (
    total_items    bigint,
    value_new      double precision,
    value_used     double precision,
    profit_potential double precision
)
language sql stable security definer set search_path = public
as $$
    select count(*),
           coalesce(sum(i.price_new), 0),
           coalesce(sum(i.price_used), 0),
           coalesce(sum(i.cached_profit), 0)
    from user_collections c
    join items i on i.item_id = c.item_id
    where c.user_id = auth.uid()
      and (p_collection is null or c.collection_name = p_collection);
$$;
grant execute on function collection_stats(text) to authenticated;

-- One-off legacy migration (run manually after Ram's and Udi's auth users
-- exist; replace the UUIDs):
-- insert into user_collections (user_id, collection_name, item_id, added_at)
-- select '<ram-uuid>'::uuid, 'main', item_id, added_at from collections
--  where collection_name ilike 'ram%'
-- union all
-- select '<udi-uuid>'::uuid, 'main', item_id, added_at from collections
--  where collection_name ilike 'udi%';
-- Scrape job queue: the web app enqueues, etl/scrape_worker.py consumes
-- with FOR UPDATE SKIP LOCKED (Vercel cannot run a browser).

create table if not exists scrape_jobs (
    id           bigint generated always as identity primary key,
    item_id      text not null,
    item_type    text not null default 'S' check (item_type in ('S', 'M')),
    deep_scan    boolean not null default false,
    status       text not null default 'queued'
                 check (status in ('queued', 'running', 'done', 'error')),
    error        text,
    requested_by uuid references auth.users(id),
    created_at   timestamptz not null default now(),
    started_at   timestamptz,
    finished_at  timestamptz
);
create index if not exists idx_scrape_jobs_status on scrape_jobs(status, created_at);

alter table scrape_jobs enable row level security;

drop policy if exists "own jobs read" on scrape_jobs;
create policy "own jobs read" on scrape_jobs
    for select to authenticated
    using (requested_by = auth.uid() or is_admin());

drop policy if exists "authenticated enqueue" on scrape_jobs;
create policy "authenticated enqueue" on scrape_jobs
    for insert to authenticated
    with check (requested_by = auth.uid() and status = 'queued');
