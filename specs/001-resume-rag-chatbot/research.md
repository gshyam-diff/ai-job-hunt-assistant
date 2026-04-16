# Research: Resume RAG Chatbot

## Decision: Embedding Approach

**Decision**: Use TF-IDF vectorization with scikit-learn for semantic search
**Rationale**: For single-document retrieval (one resume), TF-IDF provides sufficient accuracy without additional API costs or heavy ML dependencies. Resume text is domain-specific and keyword-rich, making TF-IDF effective.
**Alternatives considered**:
- Voyage AI embeddings: Higher quality but adds API dependency and cost
- sentence-transformers: Best quality but requires PyTorch (~2GB dependency)
- Claude-generated summaries: Creative but slow and expensive per chunk

## Decision: Web Framework

**Decision**: Flask with Jinja2 templates
**Rationale**: Minimal, well-known, single-file capable. No need for async (one user at a time). Serves both API and HTML from the same process.
**Alternatives considered**:
- FastAPI: Overkill for single-page app, adds uvicorn dependency
- Streamlit: Faster to prototype but limited UI customization
- Gradio: Similar to Streamlit, less control over chat UX

## Decision: PDF Processing

**Decision**: PyPDF2 for text extraction
**Rationale**: Pure Python, no system dependencies, handles most text-based PDFs well. Lightweight.
**Alternatives considered**:
- pdfplumber: More accurate for tables but heavier
- pymupdf (fitz): Fast but requires C library compilation
- pdfminer: More features but complex API

## Decision: Frontend Approach

**Decision**: Vanilla HTML/CSS/JavaScript served via Flask templates
**Rationale**: No build step, no Node.js required. A chat UI only needs a message list, input box, and file upload — all achievable with vanilla JS and modern CSS.
**Alternatives considered**:
- React/Vue: Overkill for a single-page chat interface
- HTMX: Good option but adds learning curve for a simple app

## Decision: State Management

**Decision**: In-memory Python objects (global state for single-user use)
**Rationale**: Constitution mandates no persistence. Single-user local app means no concurrency concerns. Resume data, chunks, and embeddings stored in module-level variables.
**Alternatives considered**:
- Flask session: Size limited, not suitable for embedding vectors
- SQLite: Adds persistence complexity against constitution principles
- Redis: External dependency, overkill
