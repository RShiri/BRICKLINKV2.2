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
