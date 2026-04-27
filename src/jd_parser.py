import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from security import is_secret_set, sanitize_error

PARSER_SYSTEM = """You are a recruiter's assistant who extracts structured data from job descriptions.
Return ONLY a JSON object, no prose, no markdown fences."""

PARSER_PROMPT = """Parse this job description and return a JSON object with these fields:
- role: the normalized job title (e.g. "Senior Backend Engineer")
- seniority: one of "intern", "junior", "mid", "senior", "staff", "principal", "unspecified"
- years_required: minimum years of experience required as integer, 0 if not specified
- must_have_skills: array of required skills, technologies, or qualifications (max 10)
- nice_to_have_skills: array of preferred but not required skills (max 8)
- responsibilities: array of 3-5 short bullets describing what the role actually does
- red_flags: array of concerning signals. Examples: "no visa sponsorship", "salary not disclosed", "unlimited PTO may signal overwork culture", "requires 10+ years for a mid-level title", "vague compensation", "unrealistic skill stack". Empty array if none.
- remote_policy: one of "remote", "hybrid", "onsite", "unspecified"
- summary: ONE sentence describing the role in plain English

Job description:
{jd_text}

Return ONLY valid JSON."""


def _extract_json_object(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def _empty_parse(reason: str) -> dict:
    return {
        "role": "",
        "seniority": "unspecified",
        "years_required": 0,
        "must_have_skills": [],
        "nice_to_have_skills": [],
        "responsibilities": [],
        "red_flags": [],
        "remote_policy": "unspecified",
        "summary": reason,
    }


def parse_jd(jd_text: str) -> dict:
    """Extract structured data from a job description."""
    if not jd_text or not jd_text.strip():
        return _empty_parse("Job description is empty.")

    if not is_secret_set(ANTHROPIC_API_KEY):
        return _empty_parse("API key not set — JD parsing unavailable.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    try:
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1536,
            system=PARSER_SYSTEM,
            messages=[{"role": "user", "content": PARSER_PROMPT.format(jd_text=jd_text[:6000])}],
        )
        parsed = _extract_json_object(resp.content[0].text)
        if not parsed:
            print("[JD_PARSER] ⚠️  Could not extract JSON from response")
            return _empty_parse("Could not parse job description.")

        return {
            "role": parsed.get("role", ""),
            "seniority": parsed.get("seniority", "unspecified"),
            "years_required": int(parsed.get("years_required", 0) or 0),
            "must_have_skills": parsed.get("must_have_skills", []) or [],
            "nice_to_have_skills": parsed.get("nice_to_have_skills", []) or [],
            "responsibilities": parsed.get("responsibilities", []) or [],
            "red_flags": parsed.get("red_flags", []) or [],
            "remote_policy": parsed.get("remote_policy", "unspecified"),
            "summary": parsed.get("summary", ""),
        }

    except Exception as e:
        print(f"[JD_PARSER] ❌ Error: {sanitize_error(e)}")
        return _empty_parse("JD parser temporarily unavailable.")
