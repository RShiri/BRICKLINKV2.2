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
