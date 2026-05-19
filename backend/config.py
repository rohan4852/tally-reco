import os
from pathlib import Path

# Base directory of the backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Upload and output directories
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

# Ensure directories exist at startup
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {".xlsx", ".xls"}

# Max file size: 20 MB
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024

# App metadata
APP_TITLE = "GST Reconciliation API"
APP_DESCRIPTION = (
    "Automates reconciliation between GST portal exports "
    "(GSTR1 / GSTR2A / GSTR2B) and Tally Excel exports."
)
APP_VERSION = "1.0.0"
