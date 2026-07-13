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
