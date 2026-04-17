import json

import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

ANALYZE_PROMPT = """Analyze this resume and return a JSON object with these fields:
- skills: array of technical and soft skills mentioned (max 15)
- experience_summary: one sentence summarizing their experience
- job_titles: array of 3 job titles they should search for
- years_experience: estimated total years of experience (integer)

Resume:
{resume_text}

Return ONLY valid JSON, no markdown fences or extra text."""


def analyze_resume(raw_text: str) -> dict:
    if not ANTHROPIC_API_KEY:
        return {
            "skills": ["Python", "JavaScript", "SQL"],
            "experience_summary": "Software developer (API key not set — using defaults)",
            "job_titles": ["Software Engineer", "Developer", "Programmer"],
            "years_experience": 3,
        }

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=512,
        system="You are a resume analyst. Return only valid JSON.",
        messages=[{"role": "user", "content": ANALYZE_PROMPT.format(resume_text=raw_text[:4000])}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)
