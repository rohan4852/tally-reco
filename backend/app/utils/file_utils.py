import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES


def validate_excel_file(file: UploadFile) -> None:
    """
    Validates that the uploaded file is an Excel file and within size limits.
    Raises HTTPException with a clear message if validation fails.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid file type '{suffix}' for '{file.filename}'. "
                f"Only {', '.join(ALLOWED_EXTENSIONS)} files are accepted."
            ),
        )


def generate_session_id() -> str:
    """Returns a unique session ID for grouping a reconciliation run's files."""
    return uuid.uuid4().hex


def build_saved_filename(session_id: str, file_type: str, original_filename: str) -> str:
    """
    Constructs a deterministic filename for storage.
    Format: <session_id>_<file_type>_<original_filename>
    Example: abc123_gst_GSTR2B_April.xlsx
    """
    suffix = Path(original_filename).suffix.lower()
    stem = Path(original_filename).stem
    safe_stem = stem.replace(" ", "_")
    return f"{session_id}_{file_type}_{safe_stem}{suffix}"


async def save_upload_file(file: UploadFile, destination: Path) -> int:
    """
    Streams the uploaded file to disk in 1 MB chunks.
    Returns total bytes written.
    Raises HTTPException if file exceeds MAX_FILE_SIZE_BYTES.
    """
    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB

    with open(destination, "wb") as out_file:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > MAX_FILE_SIZE_BYTES:
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"File '{file.filename}' exceeds the maximum allowed size "
                        f"of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
                    ),
                )
            out_file.write(chunk)

    return total_bytes
