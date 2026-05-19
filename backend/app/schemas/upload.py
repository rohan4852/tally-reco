from pydantic import BaseModel
from typing import Optional


class UploadedFileInfo(BaseModel):
    """Details of a single successfully uploaded file."""
    original_filename: str
    saved_filename: str
    file_size_bytes: int
    file_type: str


class UploadResponse(BaseModel):
    """Response returned after a successful dual-file upload."""
    message: str
    gst_file: UploadedFileInfo
    tally_file: UploadedFileInfo
    session_id: str


class ErrorResponse(BaseModel):
    """Standard error response shape."""
    error: str
    detail: Optional[str] = None