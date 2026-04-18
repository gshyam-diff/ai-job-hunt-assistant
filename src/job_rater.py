import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

RATER_SYSTEM = """You are a career coach scoring how well a candidate's resume matches a job description.
For each job, output a JSON object with:
  - "id": the job id (copy from input)
  - "score": integer 1-10 (10 = excellent fit, 1 = poor fit)
  - "rationale": ONE sentence explaining the score
  - "strengths": 1-3 short bullets of matching qualifications
  - "gaps": 1-3 short bullets of missing or weak areas

Return ONLY a JSON array of objects, no prose, no markdown fences."""


def _extract_json_array(text: str):
    """Pull the first JSON array out of a possibly-wrapped response."""
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


def rate_jobs(jobs: list[dict], resume_text: str) -> dict[str, dict]:
    """Return dict mapping job_id -> {score, rationale, strengths, gaps}."""
    if not jobs:
        return {}

    print(f"[JOB_RATER] Starting to rate {len(jobs)} jobs")
    print(f"[JOB_RATER] API Key available: {bool(ANTHROPIC_API_KEY)}")
    print(f"[JOB_RATER] Model: {ANTHROPIC_MODEL}")

    if not ANTHROPIC_API_KEY:
        print("[JOB_RATER] ⚠️  API key is empty! Returning fallback ratings.")
        # Fallback ratings when no API key — neutral 5s
        return {
            j["id"]: {
                "score": 5,
                "rationale": "API key not set — rating unavailable.",
                "strengths": [],
                "gaps": [],
            }
            for j in jobs
        }

    job_payload = [
        {
            "id": j["id"],
            "title": j["title"],
            "company": j["company"],
            "location": j.get("location"),
            "description": (j.get("description") or "")[:1500],
        }
        for j in jobs
    ]

    user_msg = (
        f"Resume:\n{resume_text[:3500]}\n\n"
        f"---\n\nJobs to rate (array of {len(job_payload)}):\n{json.dumps(job_payload)}"
    )

    try:
        print(f"[JOB_RATER] Creating Anthropic client...")
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        print(f"[JOB_RATER] Calling API with model {ANTHROPIC_MODEL}...")
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            system=RATER_SYSTEM,
            messages=[{"role": "user", "content": user_msg}],
        )

        print(f"[JOB_RATER] API responded successfully")
        ratings = _extract_json_array(resp.content[0].text)
        print(f"[JOB_RATER] Extracted {len(ratings)} job ratings from response")
        
    except Exception as e:
        print(f"[JOB_RATER] ❌ Error rating jobs: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: return neutral ratings on error
        return {
            j["id"]: {
                "score": 5,
                "rationale": f"Rating service error: {type(e).__name__}",
                "strengths": ["Check job description for details"],
                "gaps": ["Unable to analyze"],
            }
            for j in jobs
        }

    out = {}
    for r in ratings:
        jid = r.get("id")
        if not jid:
            continue
        out[jid] = {
            "score": r.get("score", 5),
            "rationale": r.get("rationale", ""),
            "strengths": r.get("strengths", []),
            "gaps": r.get("gaps", []),
        }

    # For any job not rated, give fallback
    for j in jobs:
        if j["id"] not in out:
            out[j["id"]] = {
                "score": 5,
                "rationale": "Rating could not be generated.",
                "strengths": ["Review job description"],
                "gaps": ["Unable to assess"],
            }

    print(f"[JOB_RATER] ✓ Successfully rated {len(out)} jobs")
    return out
