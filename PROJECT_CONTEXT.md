# AI Job Hunt Assistant — Project Context

**Owner:** Ghanashyam (gshyam-diff)
**Goal:** Transform from SDE-II (.NET / Azure / Angular) into a capable Full-Stack Agentic AI Engineer, by building this app end-to-end.
**Target companies:** Microsoft (primary), Google, AI startups, Samsung, Apple.
**Last updated:** 2026-04-23

---

## The App

An end-to-end Agentic AI system that takes a user from resume upload to interview-ready. Each feature is chosen to teach a specific agentic AI pattern. The job-hunt domain is the vehicle — the real product is the engineering discipline of building reliable non-deterministic systems.

**GitHub:** https://github.com/gshyam-diff/ai-job-hunt-assistant
**Live demo:** https://resume-rag-chatbot-production-7270.up.railway.app
**Deployed on:** Railway (project: resume-rag-chatbot)

---

## Current State (Phase 1 + half of Phase 2 done)

What's shipped and working:

- Resume upload + PDF extraction (PyPDF2)
- Deterministic resume analyzer (temperature=0, extracts single best-fit title, location, remote flag, skills, years)
- Auto-role inference on upload — collapses hero to sticky pill, auto-searches jobs
- Demo mode — "Try with a sample resume" injects canned Alex Morgan resume, no upload needed
- Multi-platform job search (Indeed, Google, LinkedIn, Glassdoor, ZipRecruiter) via python-jobspy
- Site selection checkboxes in UI
- ATS-lite batch rater: 0-100 match with verdict, strict calibration (stack mismatch caps 40, seniority mismatch caps 55, explicit bands), BATCH_SIZE=8, temperature=0
- Per-job actions: tailor resume, cover letter, ATS Deep Dive, recruiter outreach
- JD Parser: structured extraction of role, seniority, must-haves, nice-to-haves, responsibilities, red flags, remote policy
- ATS Score: parsed-JD vs resume match % with keyword gaps, must-have matched/missing chips, verdict
- PDF download of generated content
- Landing page redesign: hero + drop zone collapses to sticky pill after upload, glassmorphism, centered search button
- Security hardening: `src/security.py` with mask_secret / log_secret_status / sanitize_error

Removed this session: chat over resume (TF-IDF RAG, suggestions, chat.py/retriever.py/embeddings.py, scikit-learn dep) — nobody used it.

---

## Tech Stack

- **Backend:** Flask (Python)
- **LLM:** Anthropic Claude (claude-haiku-4-5-20251001)
- **Job Data:** python-jobspy
- **RAG:** TF-IDF + cosine similarity (scikit-learn)
- **Frontend:** Vanilla HTML/CSS/JS
- **Deployment:** Railway
- **PDF:** PyPDF2 (extraction) + jsPDF (client-side generation)

---

## Full Roadmap (6 Phases, ~3 months)

### Phase 1 — Core Intelligence (DONE)
- Resume parsing, job search, auto-rating, per-job actions

### Phase 2 — ATS + Live Tailoring (Weeks 1-2)
- [x] JD Parser — extract role, skills, must-haves, nice-to-haves, red flags
- [x] ATS Score — analyze JD vs resume, show keyword gaps
- [ ] Live Resume Tailoring — streaming edits, diff view (green additions, red removals)
- [ ] Resume Versions — save tailored copy per job
- **Learns:** Streaming responses, structured output, diff rendering

### Phase 3 — Research Agent (Weeks 3-4)
- Company Intel Agent — funding, size, culture, news (web search tools)
- Salary Intelligence — estimation from public data
- Role Fit Score — specific role at specific company
- "Should I apply?" summary with honest AI verdict
- **Learns:** Tool use, multi-step agent, web search orchestration

### Phase 4 — Interview Prep + OA Blueprint (Weeks 5-7)
- Forum scraper pipeline (Reddit, LeetCode Discuss, public Glassdoor)
- Company-specific interview RAG
- OA Blueprint generator — topic frequency, time strategy, past patterns
- Behavioral prep — STAR answers tailored to company values
- Mock interview chat — conversational, gives feedback
- **Learns:** RAG pipeline, vector DB design, data collection at scale

### Phase 5 — Track Agent (Weeks 8-9)
- Gmail OAuth integration
- Email parser — detect recruiter emails, rejections, interview invites, OA links
- Application dashboard — visual status (Applied → OA → Interview → Offer)
- Follow-up nudges
- Weekly summary email
- **Learns:** OAuth flows, email parsing, state machines, async agents

### Phase 6 — Semi-Auto Apply (Weeks 10-12)
- Easy Apply detection (Indeed, LinkedIn)
- Form intelligence — browser agent reads fields, maps resume data
- Human approval UI — show filled form before submitting
- Submission tracker
- Multi-portal support (Greenhouse, Lever, Workday)
- **Learns:** Computer Use APIs, browser automation, agent reliability

---

## Architecture Decisions Made

### 1. LLM Routing (Planned, Not Yet Implemented)
- Use LiteLLM as abstraction layer
- Route simple tasks → cheap model, complex tasks → good model, premium users → best model
- Together AI / Groq for cost baseline once scaling

### 2. Subscription Tier Design (Future)
- Free: Llama 3.2 8B
- Pro $19/mo: Llama 3.3 70B
- Team $49/mo: Claude Sonnet

### 3. Current Model Choice
- Claude Haiku 4.5 for all tasks (demo phase)
- Chosen because available in user's Anthropic tier
- Will migrate to routing layer post-PMF

### 4. State Management
- Currently: in-memory dict (single user, single session)
- Next: Postgres for persistence when adding users
- Redis for cache/queue when adding async workflows

### 5. No LinkedIn / Apollo / paid APIs in MVP
- Cost control: everything is free-tier or scraping
- JobSpy used for job data (no API keys needed)

### 6. Security Guardrails (ACTIVE)
- `src/security.py` is the single source for credential handling
- Never print full API keys
- `.env` is gitignored, `.env.example` is the template
- See `GUARDRAILS.md` for full policy
- See `SECURITY_INCIDENT_REPORT.md` for the 2026-04-18 incident

---

## Cost Estimate for Prototype

| Item | Monthly |
|------|---------|
| Railway (hosting + DB + Redis) | $15-45 |
| Vector DB (Qdrant free → paid) | $0-25 |
| LLM (Anthropic during dev) | $20-40 |
| LLM (Together AI switch) | $10-20 |
| Claude Code Pro | $20 |
| Domain | $1 |

**Total dev phase:** $65-150/month. Over 3 months: $200-450.

**Break-even:** ~10 paid users at $19/mo.

---

## Build-in-Public Strategy

- Post on LinkedIn from Day 1 (not Week 13)
- Focus posts on technology/learnings, not the product ("Building agentic AI" angle)
- Audience = early users = future beta testers
- Covers the company-optics concern: positions it as "AI engineering capability building"
- Cadence: one post every 2 days is fine; algo rewards consistency more than frequency
- First post (2026-04-22) pulled 4 followers + ~1000 impressions in 18 hrs — decent signal for cold start

**Flag:** Check employment contract for IP assignment clauses before posting heavily.

## Strategic Framing (discussed 2026-04-23)

- This app is not funding-worthy on its own: market is crowded (Naukri, Teal, Jobscan), moat is thin, 1-month build timeline proves low technical barrier
- Right framing: portfolio piece for Microsoft/Google AI roles + potential side income at ~50 paying users
- Viable niche if monetized: Indian engineers targeting FAANG/US roles — Naukri-style localization, visa-aware filtering, INR pricing
- Decision: ship to PMF, grow as side project, don't raise. The real ROI is the job offer it unlocks.

---

## Hackathon Attempt (2026-04-19, not selected)

Applied to Cerebral Valley "Built with Opus 4.7" hackathon. $500 API credits for 500 participants. Not selected. The pitch we crafted focused on the OA Blueprint feature — multi-step agentic flow, forum scraping, personalized blueprint, mock chat. Good pitch, competitive field. Moving on.

---

## Next Feature to Build

**Phase 2 remaining — Streaming Resume Tailor with Diff Renderer, then Resume Versions.**

JD Parser + ATS Score shipped today. Next is the streaming tailor: SSE endpoint that streams Claude edits token-by-token, frontend renders line-level diff (green adds, red removes) using jsdiff. After that, Resume Versions: save each tailored resume keyed by job_id, view history in a side panel (in-memory for now, Postgres when auth lands).

---

## Known Issues / Tech Debt

- No tests yet (will add pytest alongside streaming tailor)
- No error boundaries in frontend
- In-memory state means server restart loses everything (including cached parsed_jd + ats per job)
- LinkedIn descriptions blocked by their scraping protection — removed from default sites but users can enable
- Single-user mode only; auth/users needed before public launch
- Rater + ATS are two separate Claude calls per job list — room to unify once streaming lands
- README still mentions chat-over-resume in places; needs cleanup pass

---

## Repo Structure

```
resume-rag-chatbot/
├── src/
│   ├── app.py                  # Flask routes + state
│   ├── resume_analyzer.py      # Role/skill inference
│   ├── job_search.py           # JobSpy wrapper
│   ├── job_rater.py            # Batch rating
│   ├── tailor.py               # Resume tailor / cover / gap
│   ├── recruiter.py            # Outreach + LinkedIn URL
│   ├── job_actions.py          # Per-job handlers
│   ├── jd_parser.py            # Structured JD extraction
│   ├── ats_score.py            # Parsed JD vs resume match
│   ├── pdf_processor.py        # PDF extract
│   ├── security.py             # Safe credentials
│   ├── config.py               # Config constants
│   ├── templates/index.html
│   └── static/{style.css, app.js}
├── PROJECT_CONTEXT.md          # This file
├── GUARDRAILS.md               # Security policy
├── SECURITY_INCIDENT_REPORT.md # 2026-04-18 incident
├── README.md                   # Public-facing
├── requirements.txt
├── Procfile
└── .env.example
```

---

## Personal Context (owner)

- 4 years at current company (.NET / Azure / Angular / Neo4j / SQL / MongoDB / Azure DevOps)
- Company is doing AI adoption; owner is one of the people leading it
- Target roles: Microsoft AI, Google AI, AI startups, Samsung, Apple
- Wants to be seen as "AI asset for current company" while transitioning
- Risk: colleagues will see LinkedIn posts; frame the narrative around capability building, not job switching
- Personal GitHub: https://github.com/gshyam-diff
- LinkedIn: https://linkedin.com/in/gsrkp15
