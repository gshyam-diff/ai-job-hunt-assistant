# Data Model: Resume RAG Chatbot

## Entities

### Resume
Represents the uploaded PDF document after text extraction.

| Field | Type | Description |
|-------|------|-------------|
| filename | string | Original filename of the uploaded PDF |
| raw_text | string | Full extracted text content from the PDF |
| chunks | list[Chunk] | Text segments created from raw_text |
| uploaded_at | datetime | Timestamp of upload |

### Chunk
A segment of the resume text optimized for retrieval.

| Field | Type | Description |
|-------|------|-------------|
| content | string | The text content of this chunk |
| index | int | Position of this chunk in the original document |
| start_char | int | Character offset in original text |
| end_char | int | End character offset in original text |

### Message
A single message in the chat conversation.

| Field | Type | Description |
|-------|------|-------------|
| role | string | Either "user" or "assistant" |
| content | string | The message text |
| timestamp | datetime | When the message was created |

### Conversation
The full chat session state.

| Field | Type | Description |
|-------|------|-------------|
| messages | list[Message] | Ordered list of all messages |
| resume | Resume | The currently loaded resume |

## Relationships

- A **Conversation** has exactly one **Resume** and many **Messages**
- A **Resume** has many **Chunks** (typically 5-20 for a standard resume)
- **Messages** are ordered by timestamp within a **Conversation**

## State Lifecycle

1. Initial state: No resume, empty conversation
2. After upload: Resume populated with chunks, TF-IDF matrix computed
3. During chat: Messages accumulate, retrieval uses existing TF-IDF matrix
4. On new upload: Previous state cleared, fresh start
