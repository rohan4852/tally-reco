from fastapi import APIRouter, HTTPException, Query
from pathlib import Path

from app.config import UPLOAD_DIR
from app.schemas.parser import ParseResponse, FileParseInfo, DataPreviewResponse
from app.services.parser_service import parse_both_files, parse_excel_file


router = APIRouter(prefix="/parse", tags=["Parse"])


def _find_session_file(session_id: str, file_type: str) -> Path:
    """
    Locates the uploaded file for a session by scanning uploads/ for
    a filename that starts with {session_id}_{file_type}_.
    Raises 404 if not found.
    """
    matches = [
        f for f in UPLOAD_DIR.iterdir()
        if f.is_file() and f.name.startswith(f"{session_id}_{file_type}_")
    ]
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=f"No {file_type.upper()} file found for session '{session_id}'. Upload first via POST /upload/.",
        )
    return matches[0]


@router.post(
    "/{session_id}",
    response_model=ParseResponse,
    summary="Parse uploaded Excel files",
    description=(
        "Reads both GST and Tally Excel files for the given session, "
        "detects headers, maps columns to canonical names, and applies "
        "full normalization (GSTIN, invoice no, dates, amounts). "
        "Returns a summary with row counts, detected columns, and any warnings."
    ),
)
async def parse_files(session_id: str) -> ParseResponse:
    gst_path = _find_session_file(session_id, "gst")
    tally_path = _find_session_file(session_id, "tally")

    try:
        gst_result, tally_result = parse_both_files(gst_path, tally_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse Excel files: {str(e)}",
        )

    return ParseResponse(
        session_id=session_id,
        message="Both files parsed and normalized successfully.",
        gst_file=FileParseInfo(**gst_result.to_summary_dict()),
        tally_file=FileParseInfo(**tally_result.to_summary_dict()),
    )


@router.get(
    "/{session_id}/preview",
    response_model=DataPreviewResponse,
    summary="Preview parsed rows",
    description="Returns the first N rows of the parsed + normalized DataFrame for a file type (gst or tally).",
)
async def preview_parsed_file(
    session_id: str,
    file_type: str = Query("gst", pattern="^(gst|tally)$", description="'gst' or 'tally'"),
    rows: int = Query(10, ge=1, le=100, description="Number of rows to preview (1–100)"),
) -> DataPreviewResponse:
    file_path = _find_session_file(session_id, file_type)

    try:
        result = parse_excel_file(file_path, file_type)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Parse error: {str(e)}")

    df = result.dataframe
    preview = df.head(rows).fillna("").astype(str).to_dict(orient="records")

    return DataPreviewResponse(
        session_id=session_id,
        file_type=file_type,
        sheet_name=result.sheet_name,
        row_count=result.row_count,
        columns=result.columns_found,
        preview_rows=preview,
    )
