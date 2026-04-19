# AI Job Hunt Assistant

An agentic AI application that takes you from resume upload to interview-ready. Built with Claude (Anthropic API) and Python.

**Live demo:** https://resume-rag-chatbot-production-7270.up.railway.app

---

## What it does

Upload your resume and the system:

1. **Analyzes your profile** — extracts skills, experience, infers your best-fit role
2. **Searches matching jobs** — across Indeed, Google, LinkedIn, Glassdoor, ZipRecruiter
3. **Auto-rates each job** — Claude scores how well each role fits your background (1-10) with rationale, strengths, and gaps
4. **Tailors your resume** — generates ATS-optimized resume bullets per role
5. **Drafts outreach emails** — recruiter outreach, ready to send
6. **Generates cover letters** — personalized to the specific role
7. **Skills gap analysis** — what to learn next for each role
8. **Finds recruiters** — generates LinkedIn search URLs to find recruiters at the company

---

## Architecture

```
Resume Upload
     │
     ▼
[Resume Analyzer Agent]  ← Claude extracts skills + suggests roles
     │
     ▼
[Job Search Agent]       ← JobSpy scrapes 5 platforms
     │
     ▼
[Job Rating Agent]       ← Claude rates each job vs your resume
     │
     ▼
[Action Agents]
  - Tailor Agent         ← Resume bullets per role
  - Outreach Agent       ← Recruiter emails
  - Cover Letter Agent   ← Personalized cover letters
  - Skills Gap Agent     ← Learning recommendations
```

All Claude calls are wrapped through `src/security.py` to ensure no API keys are ever logged.

---

## Tech Stack

- **Backend:** Flask (Python)
- **LLM:** Anthropic Claude (claude-haiku-4-5)
- **Job Data:** python-jobspy (scrapes Indeed, Google, LinkedIn, Glassdoor, ZipRecruiter)
- **Resume Parsing:** PyPDF2
- **RAG:** TF-IDF + cosine similarity (scikit-learn)
- **Frontend:** Vanilla HTML/CSS/JS with streaming UI
- **Deployment:** Railway

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 3. Run the app
cd src
python app.py
```

Open http://localhost:5001

---

## Project Structure

```
src/
├── app.py                # Flask routes + state management
├── resume_analyzer.py    # Resume → structured profile (Claude)
├── job_search.py         # JobSpy wrapper, multi-platform search
├── job_rater.py          # Batch job rating (Claude)
├── tailor.py             # Resume tailoring + cover letter + skill gap
├── recruiter.py          # Recruiter outreach drafts
├── job_actions.py        # Per-job action handlers
├── chat.py               # RAG chat over resume
├── retriever.py          # TF-IDF retrieval
├── embeddings.py         # TF-IDF index builder
├── pdf_processor.py      # PDF text extraction
├── security.py           # Safe credential handling
├── config.py             # Configuration
├── templates/
│   └── index.html        # Single-page UI
└── static/
    ├── style.css         # Dark theme, glassmorphism
    └── app.js            # Frontend logic + jobs Map
```

---

## Roadmap

This is Phase 1. The full vision:

- [x] Resume analysis + auto-role inference
- [x] Multi-platform job search with site selection
- [x] Auto-rating with rationale
- [x] Resume tailoring + cover letter + skill gap + outreach
- [ ] **Phase 2:** Live ATS scoring + streaming resume diff
- [ ] **Phase 3:** Company research agent (web search + news)
- [ ] **Phase 4:** Interview prep + OA Blueprint (Reddit/LeetCode forum mining)
- [ ] **Phase 5:** Gmail tracking agent (parse recruiter emails)
- [ ] **Phase 6:** Semi-automated apply (browser agent + human approval)

---

## Why I'm Building This

I'm a 4-year SDE transitioning into agentic AI engineering. Each feature in the roadmap is chosen to teach a specific agentic AI pattern: tool use, RAG, multi-step reasoning, computer use, evaluation. The job-hunt domain is the vehicle. The real product is the engineering discipline of building reliable non-deterministic systems.
