from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from app.config import UPLOAD_DIR
from app.schemas.upload import UploadResponse, UploadedFileInfo
from app.utils.file_utils import (

    validate_excel_file,
    generate_session_id,
    build_saved_filename,
    save_upload_file,
)

router = APIRouter(prefix="/upload", tags=["Upload"])

@router.post(
    "/",
    response_model=UploadResponse,
    summary="Upload GST and Tally Excel files",
    description=(
        "Accepts exactly two Excel files: one GST portal export "
        "(GSTR1 / GSTR2A / GSTR2B) and one Tally export. "
        "Returns a session_id used in subsequent reconciliation calls."
    ),
)
async def upload_files(
    gst_file: UploadFile = File(..., description="GST portal Excel export (.xlsx / .xls)"),
    tally_file: UploadFile = File(..., description="Tally Excel export (.xlsx / .xls)"),
) -> UploadResponse:
    # --- Validate both files before touching disk ---
    validate_excel_file(gst_file)
    validate_excel_file(tally_file)

    # --- Generate a session ID that ties this pair together ---
    session_id = generate_session_id()

    # --- Build destination paths ---
    gst_saved_name = build_saved_filename(session_id, "gst", gst_file.filename)
    tally_saved_name = build_saved_filename(session_id, "tally", tally_file.filename)

    gst_dest = UPLOAD_DIR / gst_saved_name
    tally_dest = UPLOAD_DIR / tally_saved_name

    # --- Save to disk ---
    gst_bytes = await save_upload_file(gst_file, gst_dest)
    tally_bytes = await save_upload_file(tally_file, tally_dest)

    return UploadResponse(
        message="Both files uploaded successfully. Use the session_id to run reconciliation.",
        session_id=session_id,
        gst_file=UploadedFileInfo(
            original_filename=gst_file.filename,
            saved_filename=gst_saved_name,
            file_size_bytes=gst_bytes,
            file_type="gst",
        ),
        tally_file=UploadedFileInfo(
            original_filename=tally_file.filename,
            saved_filename=tally_saved_name,
            file_size_bytes=tally_bytes,
            file_type="tally",
        ),
    )


@router.get(
    "/list",
    summary="List uploaded files",
    description="Returns all files currently in the uploads directory.",
)
async def list_uploads() -> dict:
    files = [f.name for f in UPLOAD_DIR.iterdir() if f.is_file()]
    return {"upload_directory": str(UPLOAD_DIR), "files": sorted(files), "count": len(files)}


@router.delete(
    "/{session_id}",
    summary="Delete uploaded files for a session",
    description="Removes both GST and Tally files for the given session_id.",
)
async def delete_session_files(session_id: str) -> dict:
    deleted = []
    for f in UPLOAD_DIR.iterdir():
        if f.is_file() and f.name.startswith(session_id):
            f.unlink()
            deleted.append(f.name)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"No files found for session_id '{session_id}'.",
        )

    return {"message": f"Deleted {len(deleted)} file(s).", "deleted_files": deleted}
