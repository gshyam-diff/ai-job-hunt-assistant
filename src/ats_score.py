import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from security import is_secret_set, sanitize_error

SCORER_SYSTEM = """You are an ATS (Applicant Tracking System) analyst. Given a parsed job description and a resume, evaluate fit with realistic standards.
Return ONLY a JSON object, no prose, no markdown fences."""

SCORER_PROMPT = """Score this candidate against the parsed job description.

Parsed JD:
{parsed_jd}

Resume:
{resume_text}

Rules for matching skills:
- Treat synonyms as matches (e.g. "React" matches "ReactJS", "React.js")
- Treat subsets as partial matches but still count as match (e.g. "AWS" matches "AWS Lambda")
- Do not invent skills the resume does not mention

Return a JSON object with:
- overall_match: integer 0-100 representing ATS-style fit score
- must_have_matched: array of must-have skills the resume demonstrates
- must_have_missing: array of must-have skills the resume does not show
- nice_to_have_matched: array of nice-to-have skills the resume demonstrates
- nice_to_have_missing: array of nice-to-have skills the resume does not show
- keyword_gaps: array of 3-6 specific keywords or phrases from the JD that would strengthen the resume if added honestly
- verdict: ONE sentence honest verdict (e.g. "Strong fit; missing one core skill")

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


def _empty_score(reason: str) -> dict:
    return {
        "overall_match": 0,
        "must_have_matched": [],
        "must_have_missing": [],
        "nice_to_have_matched": [],
        "nice_to_have_missing": [],
        "keyword_gaps": [],
        "verdict": reason,
    }


def score_ats(parsed_jd: dict, resume_text: str) -> dict:
    if not parsed_jd or not parsed_jd.get("role"):
        return _empty_score("JD could not be parsed.")

    if not is_secret_set(ANTHROPIC_API_KEY):
        return _empty_score("API key not set — ATS scoring unavailable.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    compact_jd = {
        "role": parsed_jd.get("role"),
        "seniority": parsed_jd.get("seniority"),
        "years_required": parsed_jd.get("years_required"),
        "must_have_skills": parsed_jd.get("must_have_skills", []),
        "nice_to_have_skills": parsed_jd.get("nice_to_have_skills", []),
        "responsibilities": parsed_jd.get("responsibilities", []),
    }

    try:
        resp = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1536,
            system=SCORER_SYSTEM,
            messages=[{
                "role": "user",
                "content": SCORER_PROMPT.format(
                    parsed_jd=json.dumps(compact_jd, indent=2),
                    resume_text=resume_text[:4000],
                ),
            }],
        )
        scored = _extract_json_object(resp.content[0].text)
        if not scored:
            return _empty_score("Could not compute ATS score.")

        return {
            "overall_match": int(scored.get("overall_match", 0) or 0),
            "must_have_matched": scored.get("must_have_matched", []) or [],
            "must_have_missing": scored.get("must_have_missing", []) or [],
            "nice_to_have_matched": scored.get("nice_to_have_matched", []) or [],
            "nice_to_have_missing": scored.get("nice_to_have_missing", []) or [],
            "keyword_gaps": scored.get("keyword_gaps", []) or [],
            "verdict": scored.get("verdict", ""),
        }

    except Exception as e:
        print(f"[ATS_SCORE] ❌ Error: {sanitize_error(e)}")
        return _empty_score("ATS scoring temporarily unavailable.")
