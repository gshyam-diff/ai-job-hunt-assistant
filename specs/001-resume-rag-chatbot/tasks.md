# Tasks: Resume RAG Chatbot

**Input**: Design documents from `specs/001-resume-rag-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: src/, src/templates/, src/static/, and requirements.txt
- [X] T002 Initialize requirements.txt with pinned dependencies: flask, PyPDF2, anthropic, scikit-learn, numpy
- [X] T003 [P] Create src/config.py with constants (chunk size, overlap, top-k, max file size)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

- [X] T004 Create src/pdf_processor.py with extract_text(file) and chunk_text(text) functions
- [X] T005 [P] Create src/embeddings.py with TF-IDF vectorizer: build_index(chunks) and query_similarity(query, chunks) functions
- [X] T006 Create src/retriever.py with retrieve(query, chunks, top_k) function that combines T004 and T005
- [X] T007 Create src/chat.py with generate_answer(query, context, conversation_history) using Claude API
- [X] T008 [P] Create src/app.py with Flask app skeleton, file upload route, and chat route

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Upload Resume and Ask Questions (Priority: P1) MVP

**Goal**: User uploads PDF, asks questions, gets grounded answers from resume content

**Independent Test**: Upload any PDF resume, ask 3-5 questions, verify answers match resume content

### Implementation for User Story 1

- [X] T009 [US1] Implement POST /upload route in src/app.py: validate PDF, extract text, chunk, build TF-IDF index, store in memory
- [X] T010 [US1] Implement POST /chat route in src/app.py: receive question, retrieve relevant chunks, call Claude, return answer
- [X] T011 [US1] Create src/templates/index.html with file upload area (drag-and-drop + click), chat message list, and input box
- [X] T012 [P] [US1] Create src/static/style.css with chat UI styles: message bubbles, upload area, loading states, responsive layout
- [X] T013 [US1] Create src/static/app.js with upload handler (FormData POST, progress feedback) and chat handler (send message, display response, loading indicator)
- [X] T014 [US1] Add error handling: file type validation, size check, empty PDF detection, API errors — display user-friendly messages in chat

**Checkpoint**: MVP complete — upload + Q&A working end-to-end

---

## Phase 4: User Story 2 - Conversation History (Priority: P2)

**Goal**: Full chat history visible and scrollable in the interface

**Independent Test**: Ask 5+ questions sequentially, verify all Q&A pairs remain visible

### Implementation for User Story 2

- [X] T015 [US2] Update src/app.py to maintain conversation history list in memory, return full history on each /chat response
- [X] T016 [US2] Update src/static/app.js to render full conversation history and auto-scroll to latest message

**Checkpoint**: Chat history working — previous Q&A pairs persist visually

---

## Phase 5: User Story 3 - Suggested Questions (Priority: P3)

**Goal**: After upload, show 3-4 clickable starter question suggestions

**Independent Test**: Upload resume, verify suggested question chips appear and are clickable

### Implementation for User Story 3

- [X] T017 [US3] Add GET /suggestions route in src/app.py that returns 3-4 starter questions based on resume content (use Claude to generate them)
- [X] T018 [US3] Update src/templates/index.html and src/static/app.js to display suggestion chips after upload, send selected suggestion as chat message
- [X] T019 [P] [US3] Update src/static/style.css with suggestion chip styles (rounded pills, hover effect, click feedback)

**Checkpoint**: All three user stories functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements affecting the whole application

- [X] T020 [P] Add loading spinner/animation in src/static/style.css and src/static/app.js during upload and answer generation
- [X] T021 [P] Add a README.md at project root with setup instructions (install deps, set API key, run app)
- [X] T022 Verify end-to-end flow: upload PDF, ask questions, check history, test suggestions, test error cases

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — core MVP
- **User Story 2 (Phase 4)**: Depends on User Story 1 (needs working chat)
- **User Story 3 (Phase 5)**: Depends on User Story 1 (needs working upload)
- **Polish (Phase 6)**: Depends on all user stories

### Parallel Opportunities

- T003 (config) can run in parallel with T001/T002
- T004 and T005 can run in parallel (different files)
- T005 and T008 can run in parallel (different files)
- T012 (CSS) can run in parallel with T011 (HTML) and T013 (JS)
- T019 (CSS) can run in parallel with T017/T018
- T020 and T021 can run in parallel

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test upload + Q&A end-to-end
5. Proceed to Phase 4 and 5

### Total: 22 tasks
- Setup: 3 tasks
- Foundational: 5 tasks
- User Story 1: 6 tasks
- User Story 2: 2 tasks
- User Story 3: 3 tasks
- Polish: 3 tasks
