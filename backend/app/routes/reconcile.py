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
        return reconcile_session(session_id=session_id, gst_path=gst_path, tally_path=tally_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to reconcile: {str(e)}")


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
        filename = f"reconciliation_{session_id}.xlsx"
        out_path = generate_excel_report(
            reconcile_response=reconcile_response,
            output_dir=OUTPUT_DIR,
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to generate report: {str(e)}")

    return FileResponse(
        path=str(out_path),
        filename=out_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


