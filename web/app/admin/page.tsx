import type { Metadata } from "next";
import Link from "next/link";
import { supabaseServer } from "@/lib/supabase/server";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { StatTile } from "@/components/StatTile";
import { shortDate } from "@/lib/format";

export const metadata: Metadata = { title: "Admin" };

export default async function AdminPage() {
  const sb = await supabaseServer();
  if (!sb) {
    return <p className="p-8 text-center text-ink-muted">Not configured.</p>;
  }
  const {
    data: { user },
  } = await sb.auth.getUser();
  const { data: profile } = user
    ? await sb.from("profiles").select("role").eq("id", user.id).maybeSingle()
    : { data: null };

  if (profile?.role !== "admin") {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <h1 className="mb-2 text-xl font-bold">🔐 Admin only</h1>
        <p className="text-[13px] text-ink-muted">
          Your account does not have the admin role. Grant it in Supabase:
          <code className="mt-2 block rounded bg-surface-2 p-2 text-left text-[12px]">
            update profiles set role = &apos;admin&apos; where id = &apos;&lt;user-uuid&gt;&apos;;
          </code>
        </p>
      </div>
    );
  }

  const staleCutoff = new Date();
  staleCutoff.setDate(staleCutoff.getDate() - 30);

  const [{ count: itemCount }, { count: mappedCount }, { count: staleCount }, { data: jobs }, { data: lowConfidence }] =
    await Promise.all([
      sb.from("items").select("item_id", { count: "exact", head: true }),
      sb
        .from("external_id_map")
        .select("ext_id", { count: "exact", head: true })
        .eq("provider", "bricklink"),
      sb
        .from("items")
        .select("item_id", { count: "exact", head: true })
        .lt("updated_at", staleCutoff.toISOString()),
      sb
        .from("scrape_jobs")
        .select("id, item_id, status, error, created_at, finished_at")
        .order("id", { ascending: false })
        .limit(25),
      sb
        .from("external_id_map")
        .select("item_type, rb_id, ext_id, match_method, confidence")
        .eq("verified", false)
        .lt("confidence", 0.7)
        .order("confidence")
        .limit(25),
    ]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <Breadcrumbs crumbs={[{ label: "Admin" }]} />
      <h1 className="mb-4 text-xl font-bold">🛠 Admin</h1>

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-3">
        <StatTile
          label="Stale items (>30d)"
          value={String(staleCount ?? "—")}
          hint="requeue via etl/scrape_worker or scan scripts"
        />
        <StatTile
          label="ID mappings"
          value={`${mappedCount ?? 0} / ${itemCount ?? 0}`}
          hint="grow coverage with python -m etl.map_bricklink_ids"
        />
        <StatTile label="Recent jobs" value={String(jobs?.length ?? 0)} />
      </div>

      <section className="mb-8">
        <h2 className="mb-2 text-base font-bold">Recent scrape jobs</h2>
        <div className="overflow-x-auto rounded border border-edge bg-surface">
          <table className="table-dense w-full">
            <thead>
              <tr>
                <th>#</th>
                <th>Item</th>
                <th>Status</th>
                <th>Created</th>
                <th>Finished</th>
                <th>Error</th>
              </tr>
            </thead>
            <tbody>
              {(jobs ?? []).map((job) => (
                <tr key={job.id}>
                  <td>{job.id}</td>
                  <td className="font-mono text-[12px]">
                    <Link
                      href={
                        /^[a-z]/i.test(job.item_id)
                          ? `/catalog/minifigs/${encodeURIComponent(job.item_id)}`
                          : `/catalog/sets/${encodeURIComponent(job.item_id)}`
                      }
                      className="text-link hover:underline"
                    >
                      {job.item_id}
                    </Link>
                  </td>
                  <td>{job.status}</td>
                  <td className="text-[12px] text-ink-muted">{shortDate(job.created_at)}</td>
                  <td className="text-[12px] text-ink-muted">{shortDate(job.finished_at)}</td>
                  <td className="max-w-[30ch] truncate text-[12px] text-[#DC2626]">
                    {job.error ?? ""}
                  </td>
                </tr>
              ))}
              {(jobs ?? []).length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-ink-muted">No jobs yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-base font-bold">Low-confidence ID mappings</h2>
        <p className="mb-2 text-[12px] text-ink-muted">
          Review these BrickLink ↔ Rebrickable matches; fix wrong ones directly in the
          external_id_map table (set verified = true to lock a mapping).
        </p>
        <div className="overflow-x-auto rounded border border-edge bg-surface">
          <table className="table-dense w-full">
            <thead>
              <tr>
                <th>Type</th>
                <th>BrickLink</th>
                <th>Rebrickable</th>
                <th>Method</th>
                <th className="text-right">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {(lowConfidence ?? []).map((m) => (
                <tr key={`${m.item_type}-${m.ext_id}`}>
                  <td>{m.item_type}</td>
                  <td className="font-mono text-[12px]">{m.ext_id}</td>
                  <td className="font-mono text-[12px]">{m.rb_id}</td>
                  <td>{m.match_method}</td>
                  <td className="text-right">{Number(m.confidence).toFixed(2)}</td>
                </tr>
              ))}
              {(lowConfidence ?? []).length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-ink-muted">
                    No low-confidence mappings 🎉
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
