import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.environ.get("DOCEDITOR_STORAGE", os.path.join(BASE_DIR, "storage"))

ORIGINALS_DIR = os.path.join(STORAGE_DIR, "originals")
VERSIONS_DIR = os.path.join(STORAGE_DIR, "versions")   # legacy, kept for migration
CURRENT_DIR = os.path.join(STORAGE_DIR, "current")
ANNOTATIONS_DIR = os.path.join(STORAGE_DIR, "annotations")
METADATA_DIR = os.path.join(STORAGE_DIR, "metadata")
AUDIT_LOG_PATH = os.path.join(STORAGE_DIR, "audit_log.jsonl")  # legacy, kept for reference

# Database URL: SQLite (default), PostgreSQL, MySQL via DATABASE_URL env var
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(STORAGE_DIR, "doceditor.db"),
)

ALLOWED_EXTENSIONS = {
    "pdf": ["pdf"],
    "image": ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"],
}
ALL_ALLOWED = {ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts}

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

# URL prefix when mounted as sub-app (e.g. "/doceditor")
URL_PREFIX = os.environ.get("DOCEDITOR_PREFIX", "")

# Ensure storage dirs exist
for d in [ORIGINALS_DIR, CURRENT_DIR, ANNOTATIONS_DIR, METADATA_DIR]:
    os.makedirs(d, exist_ok=True)
