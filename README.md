# Resume RAG Chatbot

Upload a PDF resume and ask natural language questions about it. Answers are grounded in the actual resume content using Retrieval-Augmented Generation (RAG).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
export ANTHROPIC_API_KEY='your-key-here'

# 3. Run the app
cd src
python app.py
```

Open http://localhost:5001 in your browser.

## How It Works

1. **Upload** a PDF resume (drag & drop or click to browse, max 10MB)
2. **Ask questions** like "What are the key skills?", "Summarize work experience", etc.
3. **Get answers** grounded in the actual resume content

## Architecture

- **Backend**: Flask (Python)
- **PDF Processing**: PyPDF2 for text extraction
- **Retrieval**: TF-IDF vectorization with scikit-learn for semantic search
- **Generation**: Claude API for answer generation
- **Frontend**: Vanilla HTML/CSS/JS with a chat-style UI

## Project Structure

```
src/
├── app.py               # Flask app + routes
├── pdf_processor.py     # PDF text extraction & chunking
├── embeddings.py        # TF-IDF vectorizer index
├── retriever.py         # Semantic search over chunks
├── chat.py              # Claude API integration
├── config.py            # Configuration constants
├── templates/
│   └── index.html       # Chat UI
└── static/
    ├── style.css         # Styles
    └── app.js            # Frontend logic
```

## Built With

This project was built using [GitHub Spec Kit](https://github.com/github/spec-kit) for spec-driven development. See the `specs/` directory for the full specification, plan, and task breakdown.
