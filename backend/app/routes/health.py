from fastapi import APIRouter
from app.config import UPLOAD_DIR, OUTPUT_DIR

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
async def health_check() -> dict:
    """Returns API status and confirms upload/output directories are accessible."""
    return {
        "status": "ok",
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "output_dir_exists": OUTPUT_DIR.exists(),
        "version": "1.0.0",
    }
