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
