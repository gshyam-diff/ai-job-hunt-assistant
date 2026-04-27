import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from security import log_secret_status, sanitize_error, is_secret_set

RATER_SYSTEM = """You are a strict ATS analyst. Score each job against the resume the way a hiring manager would: unsentimental, calibrated, no inflation.

For each job, output a JSON object with:
  - "id": copy from input
  - "match": integer 0-100 (honest match percentage)
  - "verdict": ONE short sentence (max 15 words) on the fit

Scoring rules (apply strictly, in order):
1. Identify the role's primary tech stack and seniority from title + description.
2. If primary stack differs from the resume's demonstrated stack (e.g. React role vs Angular resume, backend role vs frontend resume, ML role vs pure web dev), cap match at 40 regardless of other overlap.
3. If seniority is mismatched by more than one level (e.g. Staff role vs junior resume, or mid role vs principal), cap match at 55.
4. If the resume is a clear on-stack, on-seniority fit, score 75-95 based on depth.
5. Never score above 90 unless resume demonstrates exact role experience at the same seniority.
6. Count synonyms as matches (React = ReactJS, AWS = Amazon Web Services).
7. Be terse. Verdict must name the specific gap or strength driving the score.

Calibration bands:
- 85-100: direct hire, obvious fit
- 70-84: strong candidate, minor gaps
- 55-69: stretch, missing something real
- 40-54: significant mismatch on stack or seniority
- 0-39: wrong stack, wrong seniority, or wrong domain

Return ONLY a JSON array of objects, no prose, no markdown fences."""

BATCH_SIZE = 8


def _extract_json_array(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []


def _rate_batch(jobs: list[dict], resume_text: str, client) -> dict[str, dict]:
    job_payload = [
        {
            "id": j["id"],
            "title": j["title"],
            "company": j["company"],
            "location": j.get("location"),
            "description": (j.get("description") or "")[:2500],
        }
        for j in jobs
    ]

    user_msg = (
        f"Resume:\n{resume_text[:3500]}\n\n"
        f"---\n\nJobs to score (array of {len(job_payload)}):\n{json.dumps(job_payload)}"
    )

    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        temperature=0,
        system=RATER_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    stop_reason = getattr(resp, "stop_reason", None)
    if stop_reason == "max_tokens":
        print(f"[JOB_RATER] ⚠️  Response hit max_tokens — batch of {len(jobs)} likely truncated")

    ratings = _extract_json_array(resp.content[0].text)
    print(f"[JOB_RATER] batch size={len(jobs)} parsed={len(ratings)} stop={stop_reason}")

    out = {}
    for r in ratings:
        jid = r.get("id")
        if not jid:
            continue
        out[jid] = {
            "match": int(r.get("match", 0) or 0),
            "verdict": r.get("verdict", ""),
        }
    return out


def rate_jobs(jobs: list[dict], resume_text: str) -> dict[str, dict]:
    """Return dict mapping job_id -> {match, verdict}. Match is 0-100."""
    if not jobs:
        return {}

    print(f"[JOB_RATER] Starting to rate {len(jobs)} jobs")
    print(f"[JOB_RATER] {log_secret_status('API_KEY', ANTHROPIC_API_KEY)}")
    print(f"[JOB_RATER] Model: {ANTHROPIC_MODEL}")

    if not is_secret_set(ANTHROPIC_API_KEY):
        return {
            j["id"]: {"match": 0, "verdict": "API key not set."}
            for j in jobs
        }

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    out: dict[str, dict] = {}

    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i : i + BATCH_SIZE]
        print(f"[JOB_RATER] Rating batch {i // BATCH_SIZE + 1} ({len(batch)} jobs)")
        try:
            out.update(_rate_batch(batch, resume_text, client))
        except Exception as e:
            print(f"[JOB_RATER] ❌ Batch error: {sanitize_error(e)}")

    for j in jobs:
        if j["id"] not in out:
            out[j["id"]] = {"match": 0, "verdict": "Could not score this job."}

    rated = sum(1 for j in jobs if out[j["id"]]["verdict"] != "Could not score this job.")
    print(f"[JOB_RATER] ✓ Rated {rated}/{len(jobs)} jobs successfully")
    return out
