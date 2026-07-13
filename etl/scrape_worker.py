"""Consume scrape_jobs enqueued by the web app's /tools/analyzer.

Runs on a machine with a browser (the same box that runs the scan scripts;
Vercel cannot run Playwright). Claims jobs with FOR UPDATE SKIP LOCKED so
several workers can run safely.

Usage:
    python -m etl.scrape_worker [--once] [--poll-seconds 10]
"""
import argparse
import sys
import time
import traceback


def claim_job(cur):
    cur.execute(
        """
        select id, item_id, item_type, deep_scan
        from scrape_jobs
        where status = 'queued'
        order by created_at
        for update skip locked
        limit 1
        """
    )
    return cur.fetchone()


def run_job(scraper, item_id: str, item_type: str, deep_scan: bool) -> None:
    scraper.scrape(item_id, item_type=item_type, force=True)
    if item_type == "S" and deep_scan:
        for fig in scraper.get_minifigs_in_set(item_id) or []:
            fig_id = fig.get("id")
            if fig_id:
                scraper.scrape(fig_id, item_type="M", force=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="process one job and exit")
    parser.add_argument("--poll-seconds", type=int, default=10)
    args = parser.parse_args()

    from etl.db import connect
    from scraper_playwright import BrickLinkScraperV2

    while True:
        with connect() as conn:
            cur = conn.cursor()
            job = claim_job(cur)
            if job is None:
                conn.commit()
                if args.once:
                    print("no queued jobs")
                    return
                time.sleep(args.poll_seconds)
                continue

            job_id, item_id, item_type, deep_scan = job
            cur.execute(
                "update scrape_jobs set status = 'running', started_at = now() where id = %s",
                (job_id,),
            )
            conn.commit()
            print(f"job {job_id}: scraping {item_id} ({item_type}, deep={deep_scan})")

            try:
                scraper = BrickLinkScraperV2()
                try:
                    run_job(scraper, item_id, item_type, deep_scan)
                finally:
                    scraper.close()
                cur.execute(
                    "update scrape_jobs set status = 'done', finished_at = now() where id = %s",
                    (job_id,),
                )
            except Exception:
                cur.execute(
                    """update scrape_jobs
                       set status = 'error', error = %s, finished_at = now()
                       where id = %s""",
                    (traceback.format_exc()[-2000:], job_id),
                )
            conn.commit()

        if args.once:
            return


if __name__ == "__main__":
    sys.exit(main())
