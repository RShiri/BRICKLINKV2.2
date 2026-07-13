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
