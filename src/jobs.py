import math

from jobspy import scrape_jobs

from config import JOB_SITES, JOB_RESULTS_WANTED, JOB_HOURS_OLD, JOB_COUNTRY


def search_jobs(query: str, location: str = "") -> list[dict]:
    try:
        df = scrape_jobs(
            site_name=JOB_SITES,
            search_term=query,
            location=location if location else None,
            results_wanted=JOB_RESULTS_WANTED,
            hours_old=JOB_HOURS_OLD,
            country_indeed=JOB_COUNTRY,
        )
    except Exception as e:
        return [{"error": str(e)}]

    if df is None or df.empty:
        return []

    jobs = []
    for _, row in df.iterrows():
        def safe(val):
            if val is None:
                return ""
            if isinstance(val, float) and math.isnan(val):
                return ""
            return str(val)

        description = safe(row.get("description"))
        jobs.append({
            "id": safe(row.get("id")) or str(len(jobs)),
            "title": safe(row.get("title")),
            "company": safe(row.get("company")),
            "location": safe(row.get("location")),
            "job_url": safe(row.get("job_url")),
            "description": description,
            "description_snippet": description[:200] + "..." if len(description) > 200 else description,
            "salary": safe(row.get("min_amount")) + (" - " + safe(row.get("max_amount")) if safe(row.get("max_amount")) else ""),
            "site": safe(row.get("site")),
            "date_posted": safe(row.get("date_posted")),
        })

    return jobs
