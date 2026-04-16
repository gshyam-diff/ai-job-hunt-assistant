import os
import sys
from datetime import datetime, timezone

from flask import Flask, request, jsonify, render_template

from config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS
from pdf_processor import extract_text, chunk_text
from embeddings import TFIDFIndex
from retriever import retrieve
from chat import generate_answer, generate_suggestions

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_BYTES

# In-memory state (single user, single session)
state = {
    "resume": None,
    "index": None,
    "conversation": [],
    "suggestions": [],
}


def reset_state():
    state["resume"] = None
    state["index"] = None
    state["conversation"] = []
    state["suggestions"] = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    reset_state()

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Only PDF files are accepted"}), 400

    file_bytes = file.read()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return jsonify({"error": f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB"}), 400

    raw_text = extract_text(file_bytes)

    if not raw_text.strip():
        return jsonify({"error": "Could not extract text from this PDF. It may be a scanned image."}), 400

    chunks = chunk_text(raw_text)

    if not chunks:
        return jsonify({"error": "No usable text found in the PDF"}), 400

    index = TFIDFIndex()
    index.build(chunks)

    state["resume"] = {
        "filename": file.filename,
        "raw_text": raw_text,
        "chunks": chunks,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    state["index"] = index

    suggestions = generate_suggestions(raw_text)
    state["suggestions"] = suggestions

    return jsonify({
        "message": f"Resume '{file.filename}' uploaded successfully",
        "chunks": len(chunks),
        "suggestions": suggestions,
    })


@app.route("/chat", methods=["POST"])
def chat():
    if state["resume"] is None or state["index"] is None:
        return jsonify({"error": "Please upload a resume first"}), 400

    data = request.get_json()
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Please provide a message"}), 400

    query = data["message"].strip()

    state["conversation"].append({
        "role": "user",
        "content": query,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    context_chunks = retrieve(query, state["index"])

    answer = generate_answer(query, context_chunks, state["conversation"][:-1])

    state["conversation"].append({
        "role": "assistant",
        "content": answer,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    return jsonify({
        "answer": answer,
        "sources": [{"content": c["content"][:100] + "...", "score": c["score"]} for c in context_chunks],
        "conversation": state["conversation"],
    })


@app.route("/suggestions", methods=["GET"])
def suggestions():
    return jsonify({"suggestions": state["suggestions"]})


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set. Set it with:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print()

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"Starting Resume RAG Chatbot on http://localhost:{port}")
    app.run(debug=debug, host="0.0.0.0", port=port)
