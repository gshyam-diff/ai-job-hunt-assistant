import json
import re

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

ANALYZE_PROMPT = """Analyze this resume and return a single JSON object.

Pick ONE best-fit job title based on the most recent role and demonstrated strengths. Do not hedge, do not output alternatives. The same resume must always produce the same title.

Fields:
- best_fit_title: the single best job title to search for (e.g. "Senior Backend Engineer", "Staff ML Engineer"). Be specific about seniority.
- title_reasoning: ONE sentence explaining why this title was chosen
- skills: array of up to 15 technical and soft skills pulled from the resume
- experience_summary: one sentence summarizing their experience
- years_experience: total years of experience as integer (sum of professional roles)
- location: extract from resume if present. Return the most specific location (e.g. "Bengaluru, India", "San Francisco, CA"). Empty string if not present.
- open_to_remote: true if resume explicitly mentions remote work preference or current remote role, else false

Resume:
{resume_text}

Return ONLY valid JSON, no markdown fences or extra text."""


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


def analyze_resume(raw_text: str) -> dict:
    if not ANTHROPIC_API_KEY:
        return {
            "best_fit_title": "Software Engineer",
            "title_reasoning": "API key not set — using default.",
            "skills": ["Python", "JavaScript", "SQL"],
            "experience_summary": "Software developer (API key not set — using defaults)",
            "years_experience": 3,
            "location": "",
            "open_to_remote": False,
            "job_titles": ["Software Engineer"],
        }

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=768,
        temperature=0,
        system="You are a resume analyst. Return only valid JSON. Your output must be deterministic: the same resume must always produce the same output.",
        messages=[{"role": "user", "content": ANALYZE_PROMPT.format(resume_text=raw_text[:4000])}],
    )

    parsed = _extract_json_object(response.content[0].text)
    if not parsed:
        return {
            "best_fit_title": "Software Engineer",
            "title_reasoning": "Could not parse analysis.",
            "skills": [],
            "experience_summary": "",
            "years_experience": 0,
            "location": "",
            "open_to_remote": False,
            "job_titles": ["Software Engineer"],
        }

    best = parsed.get("best_fit_title") or "Software Engineer"
    return {
        "best_fit_title": best,
        "title_reasoning": parsed.get("title_reasoning", ""),
        "skills": parsed.get("skills", []) or [],
        "experience_summary": parsed.get("experience_summary", ""),
        "years_experience": int(parsed.get("years_experience", 0) or 0),
        "location": parsed.get("location", "") or "",
        "open_to_remote": bool(parsed.get("open_to_remote", False)),
        "job_titles": [best],
    }
