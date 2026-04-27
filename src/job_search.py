import hashlib
import math
from typing import Optional

from jobspy import scrape_jobs

from config import JOB_SITES, JOB_RESULTS_WANTED, JOB_HOURS_OLD, JOB_COUNTRY

# JobSpy's country_indeed picks which Indeed regional site to hit. If we leave
# it at "USA", queries for Bengaluru/London/Toronto return nothing because we
# are scraping the wrong Indeed. Infer from the location string.
COUNTRY_KEYWORDS = {
    "India": [
        "india", "bengaluru", "bangalore", "mumbai", "delhi", "new delhi",
        "hyderabad", "pune", "chennai", "noida", "gurgaon", "gurugram",
        "kolkata", "ahmedabad", "kochi", "trivandrum", "thiruvananthapuram",
        "jaipur", "chandigarh", "indore",
    ],
    "UK": [
        "united kingdom", " uk", "london", "manchester", "birmingham",
        "edinburgh", "glasgow", "bristol", "leeds", "cambridge", "oxford",
    ],
    "Canada": [
        "canada", "toronto", "vancouver", "montreal", "ottawa", "calgary",
        "edmonton", "winnipeg", "waterloo",
    ],
    "Australia": ["australia", "sydney", "melbourne", "brisbane", "perth", "adelaide"],
    "Germany": ["germany", "berlin", "munich", "münchen", "frankfurt", "hamburg", "stuttgart", "cologne", "köln"],
    "Singapore": ["singapore"],
    "Ireland": ["ireland", "dublin"],
    "Netherlands": ["netherlands", "amsterdam", "rotterdam", "utrecht"],
    "France": ["france", "paris", "lyon", "toulouse"],
    "Spain": ["spain", "madrid", "barcelona"],
    "UAE": ["uae", "united arab emirates", "dubai", "abu dhabi"],
}


def infer_country(location: str) -> str:
    if not location:
        return JOB_COUNTRY
    loc = f" {location.lower()} "
    for country, keywords in COUNTRY_KEYWORDS.items():
        if any(kw in loc for kw in keywords):
            return country
    return JOB_COUNTRY


def _clean(value) -> Optional[str]:
    """Convert pandas NaN / None / empty to None; stringify otherwise."""
    if value is None:
        return None
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
    except (TypeError, ValueError):
        pass
    s = str(value).strip()
    return s if s and s.lower() != "nan" else None


def _make_id(row: dict) -> str:
    """Deterministic id from job url (fallback: title+company)."""
    key = row.get("job_url") or f"{row.get('title', '')}-{row.get('company', '')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def search_jobs(
    query: str,
    location: str = "",
    results_wanted: int = JOB_RESULTS_WANTED,
    hours_old: int = JOB_HOURS_OLD,
    is_remote: bool = False,
    sites: list[str] = None,
) -> list[dict]:
    """Fetch job listings from Indeed/LinkedIn/Google and return normalized dicts."""
    if sites is None:
        sites = JOB_SITES

    country = infer_country(location)
    google_search = (
        f"{query} jobs in {location}" if location else f"{query} jobs"
    )

    df = scrape_jobs(
        site_name=sites,
        search_term=query,
        google_search_term=google_search,
        location=location or None,
        results_wanted=results_wanted,
        hours_old=hours_old,
        country_indeed=country,
        is_remote=is_remote,
        description_format="markdown",
        verbose=0,
    )

    if df is None or df.empty:
        return []

    jobs = []
    for _, row in df.iterrows():
        rec = row.to_dict()
        description = _clean(rec.get("description"))
        job = {
            "id": _make_id(rec),
            "site": _clean(rec.get("site")),
            "title": _clean(rec.get("title")) or "Untitled role",
            "company": _clean(rec.get("company")) or "Unknown company",
            "location": _clean(rec.get("location")),
            "is_remote": bool(rec.get("is_remote")) if rec.get("is_remote") is not None else False,
            "date_posted": _clean(rec.get("date_posted")),
            "job_type": _clean(rec.get("job_type")),
            "min_amount": rec.get("min_amount") if _clean(rec.get("min_amount")) else None,
            "max_amount": rec.get("max_amount") if _clean(rec.get("max_amount")) else None,
            "currency": _clean(rec.get("currency")),
            "job_url": _clean(rec.get("job_url_direct")) or _clean(rec.get("job_url")),
            "description": description,
            "description_short": (description[:600] + "…") if description and len(description) > 600 else description,
            "company_url": _clean(rec.get("company_url")),
            "company_logo": _clean(rec.get("company_logo")),
            "emails": _clean(rec.get("emails")),
        }
        jobs.append(job)

    return jobs


def format_salary(job: dict) -> Optional[str]:
    """Human-readable salary string or None."""
    lo, hi, cur = job.get("min_amount"), job.get("max_amount"), job.get("currency") or "USD"
    if not lo and not hi:
        return None
    try:
        lo_i = int(float(lo)) if lo else None
        hi_i = int(float(hi)) if hi else None
    except (TypeError, ValueError):
        return None
    if lo_i and hi_i:
        return f"{cur} {lo_i:,} – {hi_i:,}"
    if lo_i:
        return f"{cur} {lo_i:,}+"
    return f"up to {cur} {hi_i:,}"
