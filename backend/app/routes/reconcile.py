from fastapi import APIRouter, HTTPException
from pathlib import Path

from app.config import OUTPUT_DIR, UPLOAD_DIR
from app.reports.excel_report import generate_excel_report
from app.schemas.reconcile import ReconcileResponse
from app.services.reconcile_service import reconcile_session


router = APIRouter(prefix="/reconcile", tags=["Reconcile"])



def _find_session_file(session_id: str, file_type: str) -> Path:
    matches = [
        f
        for f in UPLOAD_DIR.iterdir()
        if f.is_file() and f.name.startswith(f"{session_id}_{file_type}_")
    ]
    if not matches:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No {file_type.upper()} file found for session '{session_id}'. "
                "Upload first via POST /upload/."
            ),
        )
    return matches[0]


@router.post(
    "/{session_id}",
    response_model=ReconcileResponse,
    summary="Run reconciliation (Day 3 matching)",
    description=(
        "Runs the Day 3 matching engine between GST portal export and Tally export for a session_id. "
        "Primary matching uses (GSTIN + Invoice Number + Taxable Amount). "
        "Secondary checks classify mismatches mainly for tax differences and duplicates."
    ),
)
async def reconcile_files(session_id: str) -> ReconcileResponse:
    gst_path = _find_session_file(session_id, "gst")
    tally_path = _find_session_file(session_id, "tally")

    try:
        result = reconcile_session(
            session_id=session_id,
            gst_path=gst_path,
            tally_path=tally_path,
        )

        # Never allow FastAPI to validate `None` against response_model.
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to reconcile: reconcile_session returned None",
            )

        # Ensure preview lists are never None (defensive).
        if result.matched_preview is None:
            result.matched_preview = []
        if result.mismatches_preview is None:
            result.mismatches_preview = []

        return result

    except HTTPException:
        raise
    except Exception as e:
        # Surface traceback details via logs while keeping response user-safe.
        raise HTTPException(status_code=500, detail=f"Failed to reconcile: {str(e)}")



@router.get(
    "/reports/{session_id}",
    summary="Generate and download reconciliation Excel report",
    description="Generates the Day 5 Excel reconciliation report and returns it as a downloadable .xlsx.",
)
async def download_reconciliation_report(session_id: str) -> "openpyxl.workbook.workbook.Workbook":
    # Import inside function to avoid import-time overhead
    from fastapi.responses import FileResponse

    gst_path = _find_session_file(session_id, "gst")
    tally_path = _find_session_file(session_id, "tally")

    try:
        reconcile_response = reconcile_session(
            session_id=session_id,
            gst_path=gst_path,
            tally_path=tally_path,
        )

        if reconcile_response is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate report: reconciliation returned None",
            )

        filename = f"reconciliation_{session_id}.xlsx"
        out_path = generate_excel_report(
            reconcile_response=reconcile_response,
            output_dir=OUTPUT_DIR,
            filename=filename,
        )

        # Validate output file exists
        if out_path is None or not Path(out_path).exists():
            raise HTTPException(
                status_code=500,
                detail="Failed to generate reconciliation report: output file was not created.",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate reconciliation report.",
        ) from e

    return FileResponse(
        path=str(out_path),
        filename=out_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )



