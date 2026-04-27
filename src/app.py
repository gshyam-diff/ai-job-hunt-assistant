import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from flask import Flask, Response, request, jsonify, render_template, stream_with_context

from config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS
from pdf_processor import extract_text
from resume_analyzer import analyze_resume
from job_search import search_jobs, format_salary
from job_rater import rate_jobs
from tailor import tailor_resume, tailor_resume_stream, cover_letter
from recruiter import draft_outreach
from jd_parser import parse_jd
from ats_score import score_ats

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_BYTES

# In-memory state (single user, single session)
state = {
    "resume": None,
    "jobs": {},  # id -> job dict (enriched with rating)
    "resume_versions": {},  # job_id -> {job_title, company, content, created_at}
}


def reset_state():
    state["resume"] = None
    state["jobs"] = {}
    state["resume_versions"] = {}


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

    state["resume"] = {
        "filename": file.filename,
        "raw_text": raw_text,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    analysis = analyze_resume(raw_text)

    return jsonify({
        "message": f"Resume '{file.filename}' uploaded successfully",
        "inferred_role": analysis.get("best_fit_title", "Software Engineer"),
        "inferred_location": analysis.get("location", ""),
        "open_to_remote": analysis.get("open_to_remote", False),
    })


SAMPLE_RESUME_TEXT = """Alex Morgan
San Francisco, CA · alex.morgan@example.com · linkedin.com/in/alexmorgan-eng · open to remote

SUMMARY
Senior Backend Engineer with 6 years of experience building distributed systems in Python and Go. Shipped payments infrastructure at scale (500M+ transactions/year), mentored 4 engineers, and led a cross-team migration from monolith to event-driven microservices on AWS.

EXPERIENCE

Senior Backend Engineer — Stripe-like Payments Startup (2022 - Present)
- Designed and shipped a multi-region ledger service handling 2B+ rows; 99.99% uptime SLA.
- Led migration of 12-service monolith to Kafka-based event streaming; reduced p99 latency by 40%.
- Built internal tooling for fraud detection team using Python, FastAPI, PostgreSQL, Redis.
- Mentored 4 junior engineers through code reviews, 1:1s, and on-call shadowing.

Backend Engineer — Mid-stage SaaS (2019 - 2022)
- Owned billing pipeline: Stripe integration, invoice generation, dunning flow. $50M ARR passed through it.
- Designed GraphQL API gateway used by iOS, Android, and Web clients.
- Reduced AWS bill 35% by rearchitecting RDS schema and introducing Redis caching layer.

Software Engineer — Agency (2018 - 2019)
- Built REST APIs for 6 client projects using Django, Flask, and Node.
- Set up CI/CD pipelines on GitHub Actions and AWS CodeBuild.

SKILLS
Python, Go, PostgreSQL, Redis, Kafka, AWS (EC2, Lambda, RDS, S3, SQS), Docker, Kubernetes, Terraform, FastAPI, Django, gRPC, GraphQL, Celery, Observability (Datadog, Sentry)

EDUCATION
B.S. Computer Science — UC Davis, 2018
"""


@app.route("/demo", methods=["POST"])
def demo():
    reset_state()
    state["resume"] = {
        "filename": "sample-resume.pdf",
        "raw_text": SAMPLE_RESUME_TEXT,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    analysis = analyze_resume(SAMPLE_RESUME_TEXT)
    return jsonify({
        "message": "Sample resume loaded",
        "filename": "sample-resume.pdf",
        "inferred_role": analysis.get("best_fit_title", "Senior Backend Engineer"),
        "inferred_location": analysis.get("location", "San Francisco, CA"),
        "open_to_remote": analysis.get("open_to_remote", True),
    })


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
            "match": r.get("match", 0),
            "verdict": r.get("verdict", ""),
        }
        j["salary_display"] = format_salary(j)
        state["jobs"][j["id"]] = j
        enriched.append(j)

    # Sort by match % desc
    enriched.sort(key=lambda x: x["rating"]["match"], reverse=True)

    return jsonify({"jobs": enriched, "count": len(enriched)})


@app.route("/resume", methods=["GET"])
def get_resume():
    if state["resume"] is None:
        return jsonify({"error": "No resume loaded"}), 404
    return jsonify({
        "filename": state["resume"]["filename"],
        "raw_text": state["resume"]["raw_text"],
    })


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


@app.route("/jobs/<job_id>/tailor-stream")
def jobs_tailor_stream(job_id):
    # EventSource only does GET. We validate eagerly and let the stream fail
    # gracefully with an SSE error event if something breaks mid-stream.
    if state["resume"] is None:
        return Response("data: " + json.dumps({"error": "No resume loaded"}) + "\n\n",
                        mimetype="text/event-stream")
    job = state["jobs"].get(job_id)
    if not job:
        return Response("data: " + json.dumps({"error": "Job not found"}) + "\n\n",
                        mimetype="text/event-stream")

    resume_text = state["resume"]["raw_text"]

    def generate():
        chunks = []
        try:
            for chunk in tailor_resume_stream(resume_text, job):
                chunks.append(chunk)
                yield f"data: {json.dumps({'token': chunk})}\n\n"
            full = "".join(chunks)
            state["resume_versions"][job_id] = {
                "job_title": job.get("title"),
                "company": job.get("company"),
                "content": full,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'error': f'{e.__class__.__name__}: {e}'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx/railway)
        },
    )


@app.route("/jobs/<job_id>/versions", methods=["GET"])
def jobs_versions(job_id):
    version = state["resume_versions"].get(job_id)
    if not version:
        return jsonify({"version": None})
    return jsonify({"version": version})


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


@app.route("/jobs/<job_id>/parse", methods=["POST"])
def jobs_parse(job_id):
    job, err, status = _get_job(job_id)
    if err:
        return err, status

    if "parsed_jd" in job:
        return jsonify(job["parsed_jd"])

    description = job.get("description") or ""
    parsed = parse_jd(description)
    job["parsed_jd"] = parsed
    return jsonify(parsed)


@app.route("/jobs/<job_id>/ats", methods=["POST"])
def jobs_ats(job_id):
    err, status = _require_resume()
    if err:
        return err, status
    job, err, status = _get_job(job_id)
    if err:
        return err, status

    if "ats" in job:
        return jsonify({"parsed_jd": job.get("parsed_jd", {}), "ats": job["ats"]})

    if "parsed_jd" not in job:
        job["parsed_jd"] = parse_jd(job.get("description") or "")

    job["ats"] = score_ats(job["parsed_jd"], state["resume"]["raw_text"])
    return jsonify({"parsed_jd": job["parsed_jd"], "ats": job["ats"]})


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
