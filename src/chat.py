import anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about a person's resume.
You MUST only use the provided resume context to answer questions. Do NOT make up or infer
information that is not explicitly stated in the resume context.

If the resume context does not contain enough information to answer the question, clearly state:
"I couldn't find that information in the provided resume."

Be concise and direct in your answers. Use bullet points for lists."""


def generate_answer(
    query: str,
    context_chunks: list[dict],
    conversation_history: list[dict],
) -> str:
    if not ANTHROPIC_API_KEY:
        return "Error: ANTHROPIC_API_KEY environment variable is not set. Please set it and restart the app."

    context_text = "\n\n---\n\n".join(c["content"] for c in context_chunks)

    messages = []
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({
        "role": "user",
        "content": f"Resume context:\n\n{context_text}\n\n---\n\nQuestion: {query}",
    })

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    return response.content[0].text


def generate_suggestions(resume_text: str) -> list[str]:
    if not ANTHROPIC_API_KEY:
        return [
            "What are the key skills listed?",
            "Summarize the work experience",
            "What is the education background?",
            "What companies has this person worked at?",
        ]

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=256,
        system="Generate exactly 4 short questions a recruiter might ask about this resume. Return ONLY the questions, one per line, no numbering or bullets.",
        messages=[{"role": "user", "content": f"Resume:\n\n{resume_text[:2000]}"}],
    )

    lines = [l.strip() for l in response.content[0].text.strip().split("\n") if l.strip()]
    return lines[:4]
