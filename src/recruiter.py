import json
import re
from urllib.parse import quote_plus

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

OUTREACH_SYSTEM = """You are writing a short, warm cold-outreach email to a recruiter or hiring manager
for a specific job opening. Use facts from the candidate's resume only.

Return ONLY a JSON object with:
  - "subject": short subject line (max 70 chars)
  - "body": email body, under 150 words, no signature block, no "[Name]" placeholders.
           Start with "Hi there," (we don't know the recruiter's name).
           One paragraph on why this role, one on why the candidate, one call-to-action.

No markdown, no prose outside the JSON."""


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


def _name_from_resume(resume_text: str) -> str:
    """Best-effort: first non-empty line as candidate name."""
    for line in resume_text.splitlines():
        s = line.strip()
        if s and len(s) < 60:
            return s
    return "the candidate"


def linkedin_search_url(company: str, role_hint: str = "recruiter") -> str:
    """Google-powered LinkedIn people search URL (no LinkedIn login required)."""
    q = f'site:linkedin.com/in "{role_hint}" "{company}"'
    return f"https://www.google.com/search?q={quote_plus(q)}"


def draft_outreach(job: dict, resume_text: str) -> dict:
    """Return {subject, body, linkedin_recruiter_url, linkedin_hiring_manager_url, emails_found}."""
    result = {
        "subject": "",
        "body": "",
        "linkedin_recruiter_url": linkedin_search_url(job.get("company", ""), "recruiter"),
        "linkedin_hiring_manager_url": linkedin_search_url(
            job.get("company", ""), f"{job.get('title', '')} hiring"
        ),
        "emails_found": job.get("emails"),
    }

    if not ANTHROPIC_API_KEY:
        result["subject"] = f"Interested in {job.get('title', 'your open role')}"
        result["body"] = (
            "Hi there,\n\n"
            f"I came across the {job.get('title')} role at {job.get('company')} and would love to "
            "learn more. Set ANTHROPIC_API_KEY and regenerate for a tailored draft.\n\n"
            "Thanks!"
        )
        return result

    name = _name_from_resume(resume_text)
    payload = (
        f"Candidate name: {name}\n"
        f"Resume:\n{resume_text[:3000]}\n\n---\n\n"
        f"Role: {job.get('title')} at {job.get('company')}\n"
        f"Location: {job.get('location') or 'N/A'}\n"
        f"Job description:\n{(job.get('description') or '')[:2000]}"
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=800,
        system=OUTREACH_SYSTEM,
        messages=[{"role": "user", "content": payload}],
    )
    parsed = _extract_json_object(resp.content[0].text)
    result["subject"] = parsed.get("subject", f"Interested in {job.get('title')}")
    result["body"] = parsed.get("body", "").strip() or result["body"]
    return result
