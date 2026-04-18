import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env with override to ensure we get fresh value
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K = 3
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf"}
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Safe logging of API key status (without exposing the actual key)
from security import log_secret_status
if ANTHROPIC_API_KEY:
    print(log_secret_status("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY))
else:
    print("⚠️  ANTHROPIC_API_KEY is not set — rating will be unavailable")

# Job search defaults
JOB_SITES = ["indeed", "linkedin", "google"]
JOB_RESULTS_WANTED = 15
JOB_HOURS_OLD = 72
JOB_COUNTRY = "USA"
