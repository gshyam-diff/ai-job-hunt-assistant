# Feature Specification: Resume RAG Chatbot

**Feature Branch**: `001-resume-rag-chatbot`
**Created**: 2026-04-16
**Status**: Draft
**Input**: User description: "Build a RAG chatbot for resume — upload a PDF resume and ask questions about it"

## User Scenarios & Testing

### User Story 1 - Upload Resume and Ask Questions (Priority: P1)

A job seeker uploads their resume as a PDF file through a simple web interface. Once uploaded, the system processes the resume and enables a chat interface. The user types natural language questions like "What are my skills?", "Summarize my work experience", or "What companies have I worked at?" and receives accurate answers extracted directly from their resume.

**Why this priority**: This is the core value proposition — without upload and Q&A, there is no product. This single story delivers a complete, usable MVP.

**Independent Test**: Can be fully tested by uploading any PDF resume, asking 3-5 questions about its content, and verifying answers match the actual resume text.

**Acceptance Scenarios**:

1. **Given** a user on the home page, **When** they upload a valid PDF resume, **Then** the system displays a success message and enables the chat input
2. **Given** a resume has been uploaded, **When** the user asks "What are my skills?", **Then** the system returns a list of skills mentioned in the resume
3. **Given** a resume has been uploaded, **When** the user asks "Summarize my experience", **Then** the system returns a concise summary based only on resume content
4. **Given** a resume has been uploaded, **When** the user asks about information not in the resume, **Then** the system clearly states the information is not available

---

### User Story 2 - Conversation History (Priority: P2)

The user can see their full conversation history in the chat interface. Previous questions and answers remain visible as the user continues asking new questions, providing context and allowing them to review earlier responses.

**Why this priority**: Enhances usability significantly but the core Q&A works without it. Chat history makes it feel like a real conversation.

**Independent Test**: Upload a resume, ask 5+ questions sequentially, and verify all previous Q&A pairs remain visible and scrollable.

**Acceptance Scenarios**:

1. **Given** a user has asked 3 questions, **When** they scroll up in the chat, **Then** all previous questions and answers are visible
2. **Given** an active chat session, **When** the user asks a new question, **Then** the new Q&A appears below the existing conversation

---

### User Story 3 - Suggested Questions (Priority: P3)

After uploading a resume, the system suggests 3-4 starter questions based on the resume content (e.g., "What are the key skills?", "Summarize work experience", "What is the education background?"). This helps users who are unsure what to ask.

**Why this priority**: Nice-to-have that improves first-time user experience but is not required for core functionality.

**Independent Test**: Upload a resume and verify that suggested question chips appear and clicking one sends it as a question.

**Acceptance Scenarios**:

1. **Given** a resume has just been uploaded, **When** processing completes, **Then** 3-4 suggested question chips are displayed
2. **Given** suggested questions are displayed, **When** the user clicks one, **Then** that question is sent to the chat and answered

---

### Edge Cases

- What happens when the user uploads a non-PDF file? System MUST show a clear error message and only accept PDF files.
- What happens when the uploaded PDF has no extractable text (scanned image)? System MUST inform the user that the PDF could not be read.
- What happens when the PDF is very large (>10MB)? System MUST reject files over 10MB with a clear size limit message.
- How does the system handle questions in a different language than the resume? System answers in the language the question was asked in, based on available resume content.

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept PDF file uploads up to 10MB
- **FR-002**: System MUST extract text content from uploaded PDF files
- **FR-003**: System MUST split extracted text into chunks suitable for retrieval
- **FR-004**: System MUST generate embeddings for each text chunk
- **FR-005**: System MUST perform semantic search over chunks when a question is asked
- **FR-006**: System MUST send retrieved context + question to an LLM for answer generation
- **FR-007**: System MUST display answers in a chat-style interface
- **FR-008**: System MUST clearly indicate when information is not found in the resume
- **FR-009**: System MUST provide visual feedback during file upload and answer generation
- **FR-010**: System MUST validate file type (PDF only) and size (max 10MB) before processing

### Key Entities

- **Resume**: The uploaded PDF document — has extracted text, chunks, and embeddings
- **Chunk**: A segment of resume text — has content, embedding vector, and position metadata
- **Message**: A chat message — has role (user/assistant), content, and timestamp
- **Conversation**: An ordered collection of messages for the current session

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can upload a resume and receive their first answer within 30 seconds
- **SC-002**: 90% of factual questions about resume content receive accurate, grounded answers
- **SC-003**: Users can start using the chatbot with zero configuration beyond an API key
- **SC-004**: The application starts with a single terminal command
- **SC-005**: The system correctly rejects non-PDF files and oversized files 100% of the time

## Assumptions

- Users have a modern web browser (Chrome, Firefox, Safari, Edge)
- Users have a valid Anthropic API key for Claude
- Resume PDFs contain extractable text (not scanned images)
- The application runs locally on the user's machine
- Python 3.10+ is available on the user's system
- Internet connectivity is available for LLM API calls
