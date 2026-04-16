<!-- Sync Impact Report
  Version change: 0.0.0 → 1.0.0
  Modified principles: N/A (initial creation)
  Added sections: Core Principles (5), Privacy & Data Handling, Development Workflow, Governance
  Removed sections: None
  Templates requiring updates: ✅ plan-template.md (aligned), ✅ spec-template.md (aligned), ✅ tasks-template.md (aligned)
  Follow-up TODOs: None
-->

# Resume RAG Chatbot Constitution

## Core Principles

### I. Privacy-First

All resume data MUST be processed locally. No resume content is sent to external services beyond the LLM API call required for answer generation. Uploaded files MUST NOT be persisted beyond the active session unless the user explicitly opts in. Temporary files MUST be cleaned up on session end.

### II. Grounded Answers Only

Every chatbot response MUST be grounded in the actual content of the uploaded resume. The system MUST NOT hallucinate or fabricate information not present in the document. When the resume lacks information to answer a query, the system MUST clearly state that the information is not available in the provided resume.

### III. Simplicity

Prefer minimal dependencies and straightforward architecture. A single-page web application with a Python backend is the target. Avoid over-engineering: no microservices, no external databases, no complex deployment pipelines. The entire application MUST be runnable with a single command.

### IV. Accuracy Over Speed

Retrieval quality takes priority over response latency. Chunk sizing, embedding quality, and retrieval strategy MUST be optimized for correctness of answers. Performance optimization is secondary to answer accuracy.

### V. User Experience

The interface MUST be intuitive: upload a resume, ask questions, get answers. No configuration required from the user beyond providing an API key. Error messages MUST be clear and actionable. The system MUST provide visual feedback during processing (upload progress, thinking indicators).

## Privacy & Data Handling

- Resume files MUST be processed in-memory or in temporary storage only
- No analytics or tracking of resume content
- API keys MUST be stored client-side only and never logged
- The application MUST work without any user account or authentication

## Development Workflow

- All code changes MUST be tested manually before marking complete
- The application MUST start with a single command (`python app.py` or equivalent)
- Dependencies MUST be pinned in a requirements file
- Code MUST follow standard Python formatting (PEP 8)

## Governance

This constitution governs all development decisions for the Resume RAG Chatbot project. Any deviation from these principles MUST be explicitly justified. The constitution may be amended with documented rationale and version bump.

**Version**: 1.0.0 | **Ratified**: 2026-04-16 | **Last Amended**: 2026-04-16
