import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

TAILOR_SYSTEM = """You are an expert resume writer. Given a candidate's resume and a target job description,
produce a tailored version focused on the role.

Output markdown with these sections:
## Tailored Summary
(2-3 lines pitching the candidate for this specific role)

## Rewritten Bullets
(5-8 impact bullets rewritten from the resume, using keywords from the job description,
quantified wherever the original had metrics, each starting with a strong verb)

## Keywords to Add
(comma-separated list of 6-10 ATS keywords from the JD that the candidate should weave into their resume)

Only use facts from the candidate's resume. Do NOT invent experience."""

COVER_LETTER_SYSTEM = """You are an expert career writer. Write a concise, warm cover letter (max 280 words)
for the candidate applying to the given role. Use facts only from the resume. Avoid clichés.
Return plain text only — no markdown, no salutation placeholders like [Name]."""

GAP_SYSTEM = """You are a career coach. Given a candidate's resume and a job description, identify skill gaps.

Return markdown with:
## Strong Matches
(3-5 bullets of skills/experience the candidate already has that match the JD)

## Gaps to Close
(3-5 bullets of skills/experience the JD asks for that are missing or weak in the resume, each with a concrete learning suggestion like a course, project, or certification)

## Quick Wins
(2-3 bullets of things the candidate could do THIS WEEK to strengthen their application)"""


def _call_claude(system: str, user: str, max_tokens: int = 1500) -> str:
    if not ANTHROPIC_API_KEY:
        return "Error: ANTHROPIC_API_KEY is not set. Please set it and restart the app."
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text


def tailor_resume(resume_text: str, job: dict) -> str:
    payload = (
        f"Resume:\n{resume_text[:4000]}\n\n---\n\n"
        f"Job: {job.get('title')} at {job.get('company')}\n"
        f"Description:\n{(job.get('description') or '')[:3000]}"
    )
    return _call_claude(TAILOR_SYSTEM, payload, max_tokens=2000)


def cover_letter(resume_text: str, job: dict) -> str:
    payload = (
        f"Resume:\n{resume_text[:3500]}\n\n---\n\n"
        f"Applying to: {job.get('title')} at {job.get('company')}\n"
        f"Job Description:\n{(job.get('description') or '')[:2500]}"
    )
    return _call_claude(COVER_LETTER_SYSTEM, payload, max_tokens=800)


def skill_gap(resume_text: str, job: dict) -> str:
    payload = (
        f"Resume:\n{resume_text[:3500]}\n\n---\n\n"
        f"Target role: {job.get('title')} at {job.get('company')}\n"
        f"Description:\n{(job.get('description') or '')[:3000]}"
    )
    return _call_claude(GAP_SYSTEM, payload, max_tokens=1200)
