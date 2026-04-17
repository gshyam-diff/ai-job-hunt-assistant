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

    if not ANTHROPIC_API_KEY:
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

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=RATER_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    ratings = _extract_json_array(resp.content[0].text)
    out = {}
    for r in ratings:
        jid = r.get("id")
        if not jid:
            continue
        out[jid] = {
            "score": int(r.get("score", 5)),
            "rationale": r.get("rationale", ""),
            "strengths": r.get("strengths", []) or [],
            "gaps": r.get("gaps", []) or [],
        }

    # Ensure every job has a rating (fill missing with neutral)
    for j in jobs:
        out.setdefault(
            j["id"],
            {"score": 5, "rationale": "Could not rate this job.", "strengths": [], "gaps": []},
        )
    return out
