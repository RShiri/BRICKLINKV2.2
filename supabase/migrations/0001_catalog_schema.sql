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
