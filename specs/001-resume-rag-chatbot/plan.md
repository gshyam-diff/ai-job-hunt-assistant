# Implementation Plan: Resume RAG Chatbot

**Branch**: `001-resume-rag-chatbot` | **Date**: 2026-04-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-resume-rag-chatbot/spec.md`

## Summary

Build a local RAG chatbot that lets users upload a PDF resume and ask natural language questions about it. The system extracts text from the PDF, chunks it, generates embeddings, performs semantic retrieval, and uses Claude to generate grounded answers. Single-page Flask web app with a clean chat UI.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: Flask (web server), PyPDF2 (PDF extraction), anthropic (Claude API), numpy (vector math)
**Storage**: In-memory (no database — session-scoped data only)
**Testing**: Manual testing via browser
**Target Platform**: Local machine (macOS/Linux/Windows)
**Project Type**: Web application (single-page)
**Performance Goals**: First answer within 30 seconds of upload
**Constraints**: Max 10MB PDF, no external services beyond Claude API
**Scale/Scope**: Single user, single resume per session

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Privacy-First | PASS | All processing in-memory, no persistence, no external storage |
| Grounded Answers Only | PASS | RAG retrieval ensures answers sourced from resume chunks |
| Simplicity | PASS | Single Flask app, no database, minimal dependencies |
| Accuracy Over Speed | PASS | Chunk overlap and top-k retrieval prioritize answer quality |
| User Experience | PASS | Single-page chat UI, drag-and-drop upload, loading indicators |

## Project Structure

### Documentation (this feature)

```text
specs/001-resume-rag-chatbot/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── spec.md              # Feature specification
├── checklists/          # Quality checklists
└── tasks.md             # Task breakdown (from /speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── app.py               # Flask application entry point + routes
├── pdf_processor.py     # PDF text extraction and chunking
├── embeddings.py        # Embedding generation using Claude
├── retriever.py         # Semantic search over chunks
├── chat.py              # Chat orchestration (retrieval + generation)
├── config.py            # Configuration and constants
├── templates/
│   └── index.html       # Single-page chat UI (Jinja2 template)
└── static/
    ├── style.css         # Chat UI styles
    └── app.js            # Frontend JavaScript (upload, chat, UX)

requirements.txt          # Pinned Python dependencies
```

**Structure Decision**: Single project layout. No frontend/backend split — Flask serves the HTML directly via Jinja2 templates. All Python modules live in `src/`. This is the simplest architecture that satisfies all requirements.

## Key Technical Decisions

### Embedding Strategy
Use Claude's API with a simple prompt to generate semantic representations of text chunks, then compute cosine similarity with numpy. This avoids adding a separate embedding model dependency.

**Alternative considered**: sentence-transformers — rejected because it adds a large ML dependency (torch) for a simple use case. Claude can generate descriptive summaries that serve as lightweight semantic representations.

**Updated approach**: Use Voyage AI embeddings via the `voyageai` package (lightweight, purpose-built for embeddings) OR implement a simple TF-IDF approach with scikit-learn for zero-API-cost retrieval. Final choice: **TF-IDF with scikit-learn** — no additional API costs, fast, and sufficient for single-document retrieval.

### Chunking Strategy
Split resume text into overlapping chunks of ~500 characters with 100-character overlap. This ensures context isn't lost at chunk boundaries. Chunks respect paragraph boundaries where possible.

### Retrieval
Top-3 most relevant chunks retrieved via cosine similarity on TF-IDF vectors. All 3 chunks included as context in the Claude prompt.

### Answer Generation
Single Claude API call per question with system prompt enforcing grounded answers. The prompt explicitly instructs Claude to only use the provided resume context and to say "not found in resume" when information is absent.

## Complexity Tracking

No constitution violations. Architecture is intentionally minimal.
