import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from flask import Flask, request, jsonify, render_template

from config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS
from pdf_processor import extract_text, chunk_text
from embeddings import TFIDFIndex
from retriever import retrieve
from chat import generate_answer, generate_suggestions
from resume_analyzer import analyze_resume
from job_search import search_jobs, format_salary
from job_rater import rate_jobs
from tailor import tailor_resume, cover_letter, skill_gap
from recruiter import draft_outreach

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_BYTES

# In-memory state (single user, single session)
state = {
    "resume": None,
    "index": None,
    "conversation": [],
    "suggestions": [],
    "jobs": {},  # id -> job dict (enriched with rating)
}


def reset_state():
    state["resume"] = None
    state["index"] = None
    state["conversation"] = []
    state["suggestions"] = []
    state["jobs"] = {}


def _require_resume():
    """Return (error_response, status) or (None, None) if resume is loaded."""
    if state["resume"] is None:
        return jsonify({"error": "Please upload a resume first"}), 400
    return None, None


def _get_job(job_id: str):
    """Fetch job from state by id; return (job, error_response, status)."""
    job = state["jobs"].get(job_id)
    if not job:
        return None, jsonify({"error": "Job not found. Re-run the search."}), 404
    return job, None, None


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

    analysis = analyze_resume(raw_text)
    inferred_role = analysis.get("job_titles", ["Software Engineer"])[0]

    return jsonify({
        "message": f"Resume '{file.filename}' uploaded successfully",
        "chunks": len(chunks),
        "suggestions": suggestions,
        "inferred_role": inferred_role,
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


@app.route("/jobs", methods=["POST"])
def jobs_search():
    err, status = _require_resume()
    if err:
        return err, status

    data = request.get_json() or {}
    query = (data.get("query") or "").strip()
    location = (data.get("location") or "").strip()
    is_remote = bool(data.get("is_remote"))
    sites = data.get("sites") or None

    if not query:
        return jsonify({"error": "Please provide a search query (e.g. 'senior python engineer')."}), 400

    try:
        jobs = search_jobs(query=query, location=location, is_remote=is_remote, sites=sites)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"Job search failed: {e.__class__.__name__}: {e}"}), 500

    if not jobs:
        return jsonify({"jobs": [], "message": "No jobs found. Try a broader query or different location."})

    resume_text = state["resume"]["raw_text"]
    ratings = rate_jobs(jobs, resume_text)

    # Merge rating into each job and store in state
    enriched = []
    for j in jobs:
        r = ratings.get(j["id"], {})
        j["rating"] = {
            "score": r.get("score", 5),
            "rationale": r.get("rationale", ""),
            "strengths": r.get("strengths", []),
            "gaps": r.get("gaps", []),
        }
        j["salary_display"] = format_salary(j)
        state["jobs"][j["id"]] = j
        enriched.append(j)

    # Sort by rating desc
    enriched.sort(key=lambda x: x["rating"]["score"], reverse=True)

    return jsonify({"jobs": enriched, "count": len(enriched)})


@app.route("/jobs/<job_id>/tailor", methods=["POST"])
def jobs_tailor(job_id):
    err, status = _require_resume()
    if err:
        return err, status
    job, err, status = _get_job(job_id)
    if err:
        return err, status
    content = tailor_resume(state["resume"]["raw_text"], job)
    return jsonify({"content": content, "format": "markdown"})


@app.route("/jobs/<job_id>/cover-letter", methods=["POST"])
def jobs_cover_letter(job_id):
    err, status = _require_resume()
    if err:
        return err, status
    job, err, status = _get_job(job_id)
    if err:
        return err, status
    content = cover_letter(state["resume"]["raw_text"], job)
    return jsonify({"content": content, "format": "text"})


@app.route("/jobs/<job_id>/gap", methods=["POST"])
def jobs_gap(job_id):
    err, status = _require_resume()
    if err:
        return err, status
    job, err, status = _get_job(job_id)
    if err:
        return err, status
    content = skill_gap(state["resume"]["raw_text"], job)
    return jsonify({"content": content, "format": "markdown"})


@app.route("/jobs/<job_id>/outreach", methods=["POST"])
def jobs_outreach(job_id):
    err, status = _require_resume()
    if err:
        return err, status
    job, err, status = _get_job(job_id)
    if err:
        return err, status
    outreach = draft_outreach(job, state["resume"]["raw_text"])
    return jsonify(outreach)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set. Set it with:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print()

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"Starting Resume RAG Chatbot on http://localhost:{port}")
    app.run(debug=debug, host="0.0.0.0", port=port)
