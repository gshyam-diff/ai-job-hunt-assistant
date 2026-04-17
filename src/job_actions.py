import urllib.parse

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL


def _call_claude(system: str, user: str, max_tokens: int = 1024) -> str:
    if not ANTHROPIC_API_KEY:
        return "Error: ANTHROPIC_API_KEY not set. Please set it and restart."

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text


def tailor_resume(resume_text: str, profile: dict, job: dict) -> str:
    return _call_claude(
        system="You are an expert resume writer. Rewrite bullet points and a professional summary tailored for the target role. Keep it truthful — only emphasize and reframe existing experience, never fabricate.",
        user=f"""RESUME:
{resume_text[:3000]}

TARGET JOB:
Title: {job['title']}
Company: {job['company']}
Description: {job['description'][:1500]}

Write:
1. A tailored professional summary (2-3 sentences)
2. 5-8 tailored bullet points from their experience that best match this role
3. Keywords to include from the job description""",
        max_tokens=1500,
    )


def draft_email(resume_text: str, profile: dict, job: dict) -> str:
    skills = ", ".join(profile.get("skills", [])[:8])
    return _call_claude(
        system="Write a concise, professional cold outreach email to a recruiter. Warm but not overly casual. Under 150 words. Include a clear ask.",
        user=f"""CANDIDATE PROFILE:
{profile.get('experience_summary', '')}
Key skills: {skills}

TARGET ROLE:
{job['title']} at {job['company']}

Write an email with Subject line and Body. The candidate wants to express interest and ask about the hiring process.""",
        max_tokens=512,
    )


def interview_prep(resume_text: str, profile: dict, job: dict) -> str:
    return _call_claude(
        system="You are a senior technical interviewer. Generate realistic interview questions for this role.",
        user=f"""JOB:
Title: {job['title']}
Company: {job['company']}
Description: {job['description'][:1500]}

Generate:
1. 3 behavioral questions (with STAR format guidance for each)
2. 3 technical/role-specific questions
3. 2 questions the candidate should ask the interviewer

For each question, include a brief tip on how to answer well.""",
        max_tokens=1500,
    )


def skills_gap(resume_text: str, profile: dict, job: dict) -> str:
    skills = ", ".join(profile.get("skills", []))
    return _call_claude(
        system="Compare a candidate's skills against job requirements. Be specific and actionable.",
        user=f"""CANDIDATE SKILLS: {skills}
CANDIDATE EXPERIENCE: {profile.get('experience_summary', '')}

JOB REQUIREMENTS:
Title: {job['title']}
Description: {job['description'][:1500]}

Analyze:
1. MATCHING SKILLS: Skills the candidate has that match the job
2. GAPS: Skills/requirements in the job the candidate appears to lack
3. RECOMMENDATIONS: For each gap, suggest a specific way to address it (course, project, certification)""",
        max_tokens=1200,
    )


def cover_letter(resume_text: str, profile: dict, job: dict) -> str:
    return _call_claude(
        system="Write a professional cover letter. 3 paragraphs, under 300 words. Be specific to both the candidate and the role. No cliches like 'I am writing to express my interest.'",
        user=f"""RESUME:
{resume_text[:3000]}

TARGET ROLE:
{job['title']} at {job['company']}
Description: {job['description'][:1500]}

Write a compelling cover letter.""",
        max_tokens=1024,
    )


def recruiter_search_url(company: str, role: str) -> str:
    query = f"{company} {role} recruiter LinkedIn"
    return f"https://www.google.com/search?q={urllib.parse.quote(query)}"
