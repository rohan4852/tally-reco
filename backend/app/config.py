"""Compatibility config module.

The project keeps shared settings in backend/config.py, while app code imports
from app.config. This file re-exports those settings so imports work when
running via Uvicorn (e.g. uvicorn app.main:app).
"""

from config import (  # type: ignore
    ALLOWED_EXTENSIONS,
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    MAX_FILE_SIZE_BYTES,
    OUTPUT_DIR,
    UPLOAD_DIR,
)

__all__ = [
    "ALLOWED_EXTENSIONS",
    "APP_DESCRIPTION",
    "APP_TITLE",
    "APP_VERSION",
    "MAX_FILE_SIZE_BYTES",
    "OUTPUT_DIR",
    "UPLOAD_DIR",
]

