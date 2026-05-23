from pydantic import BaseModel
from typing import List, Optional


class ReconcileEngineMatch(BaseModel):
    """A single matched invoice row between GST and Tally after normalization."""

    gst_gstin: str
    gst_supplier_name: str
    gst_invoice_number: str
    gst_invoice_date: str
    gst_taxable_amount: float

    gst_cgst: float
    gst_sgst: float
    gst_igst: float
    gst_total_amount: float

    tally_supplier_name: str
    tally_invoice_date: str
    tally_taxable_amount: float

    tally_cgst: float
    tally_sgst: float
    tally_igst: float
    tally_total_amount: float

    match_key: str


class ReconcileMismatch(BaseModel):
    """A single mismatch entry with a classified reason + remarks + status."""

    gst_gstin: str = ""
    gst_supplier_name: str = ""
    gst_invoice_number: str = ""
    gst_invoice_date: str = ""
    gst_taxable_amount: float = 0.0

    gst_cgst: float = 0.0
    gst_sgst: float = 0.0
    gst_igst: float = 0.0
    gst_total_amount: float = 0.0

    # Tally side (books)
    tally_gstin: str = ""
    tally_supplier_name: str = ""
    # ---- IMPORTANT: schema consistency field name expected by exporter ----
    tally_invoice_number: str = ""
    tally_invoice_date: str = ""
    tally_taxable_amount: float = 0.0

    # Backward-compatible alias for older schema field name (if present)
    # (If any upstream code still sets `tally_invoice_no`, map it to the canonical field.)
    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()

    tally_cgst: float = 0.0

    tally_sgst: float = 0.0
    tally_igst: float = 0.0
    tally_total_amount: float = 0.0

    match_key: str = ""

    mismatch_type: str
    mismatch_reason: str
    remarks: str = ""
    status: str = "Mismatched"


class ReconcileSummary(BaseModel):
    """High-level counts for reconciliation run."""

    matched_count: int
    mismatched_count: int
    missing_in_gst_count: int
    missing_in_books_count: int
    duplicate_invoice_count: int
    total_gst_records: int
    total_books_records: int
    missing_records_count: int
    true_mismatch_count: int
    accuracy_percent: float


class ReconcileResponse(BaseModel):
    session_id: str
    message: str
    summary: ReconcileSummary

    # For MVP we return counts + small previews; full Excel export comes later.
    matched_preview: List[ReconcileEngineMatch] = []
    mismatches_preview: List[ReconcileMismatch] = []

    matched_sheet_name: str = "Matched"
    unmatched_sheet_name: str = "Unmatched"
    mismatch_sheet_name: str = "Mismatches"
    missing_in_gst_sheet_name: str = "Missing in GST"
    missing_in_books_sheet_name: str = "Missing in Books"

