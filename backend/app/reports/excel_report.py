from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import openpyxl
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from app.schemas.reconcile import (
    ReconcileEngineMatch,
    ReconcileMismatch,
    ReconcileResponse,
    ReconcileSummary,
)


COMMON_CORE_COLUMNS = [
    "GSTIN",
    "Supplier Name",
    "Invoice Number",
    "Invoice Date",
    "Taxable Amount",
    "CGST",
    "SGST",
    "IGST",
]


def _apply_header_style(ws, header_row_idx: int = 1) -> None:
    for cell in ws[header_row_idx]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _set_reasonable_widths(ws, max_width: int = 45) -> None:
    for col in range(1, ws.max_column + 1):
        values = [
            str(ws.cell(row=r, column=col).value or "") for r in range(1, ws.max_row + 1)
        ]
        max_len = max((len(v) for v in values), default=0)
        ws.column_dimensions[get_column_letter(col)].width = min(max_width, max_len + 2)



def _format_invoice_for_export(invoice_number: str) -> str:
    # Preserve the formatter expectations from CA workflow: keep hyphenated form when present.
    # If we only have digits/letters, do not alter it; normalization happened internally already.
    s = (invoice_number or "").strip()
    # If it looks like INV-009 missing hyphen (e.g., INV009), reinsert after 3 chars.
    if len(s) > 3 and s[:3].upper() in {"INV", "BILL", "INV"} and "-" not in s:
        return s[:3] + "-" + s[3:]
    return s


def _map_match_to_matched_row(m: ReconcileEngineMatch) -> List:
    return [
        m.gst_gstin,
        m.gst_supplier_name,
        _format_invoice_for_export(m.gst_invoice_number),
        m.gst_invoice_date,
        m.gst_taxable_amount,
        m.gst_cgst,
        m.gst_sgst,
        m.gst_igst,
        "Matched",
    ]



def _map_mismatch_to_mismatch_row(mm: ReconcileMismatch) -> List:
    gst_tax_amount = float(mm.gst_cgst) + float(mm.gst_sgst) + float(mm.gst_igst)
    books_tax_amount = float(mm.tally_cgst) + float(mm.tally_sgst) + float(mm.tally_igst)

    return [
        mm.gst_gstin,
        mm.gst_supplier_name,
        _format_invoice_for_export(mm.gst_invoice_number),
        mm.gst_invoice_date,
        mm.gst_taxable_amount,
        mm.tally_taxable_amount,
        gst_tax_amount,
        books_tax_amount,
        mm.mismatch_reason,
        mm.remarks,
    ]


MISSING_RECORD_TYPES = {"Missing in GST", "Missing in Books"}


def _map_missing_invoice_to_row(mm: ReconcileMismatch, missing_in: str) -> List:
    # missing_in: "GST" or "Books"
    if missing_in == "GST":
        # Missing in GST: use Tally side values
        return [
            mm.tally_gstin,
            mm.tally_supplier_name,
            _format_invoice_for_export(getattr(mm, "tally_invoice_number", "") or ""),
            mm.tally_invoice_date,
            mm.tally_taxable_amount,
            mm.remarks,
        ]

    # Missing in Books: use GST side values
    return [
        mm.gst_gstin,
        mm.gst_supplier_name,
        _format_invoice_for_export(mm.gst_invoice_number),
        mm.gst_invoice_date,
        mm.gst_taxable_amount,
        mm.remarks,
    ]





def generate_excel_report(
    reconcile_response: ReconcileResponse,
    output_dir: Path,
    filename: Optional[str] = None,
) -> Path:

    """Generate Excel report for a reconciliation response.

    Day 5 requirement: required sheets + standardized header titles + summary.

    Notes:
    - Current MVP reconcile_response only includes preview lists.
      This exporter will export those previews consistently.
    - When Day 3/4 pipelines are expanded to return full datasets,
      this exporter will automatically include them.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    if filename is None:
        filename = f"reconciliation_{reconcile_response.session_id}.xlsx"

    out_path = output_dir / filename

    wb = openpyxl.Workbook()
    # Remove default sheet
    default_ws = wb.active
    wb.remove(default_ws)

    # -----------------
    # Matched
    # -----------------
    ws_matched = wb.create_sheet(reconcile_response.matched_sheet_name)
    matched_headers = [
        "GSTIN",
        "Supplier Name",
        "Invoice Number",
        "Invoice Date",
        "Taxable Amount",
        "CGST",
        "SGST",
        "IGST",
        "Match Status",
    ]
    ws_matched.append(matched_headers)
    for m in reconcile_response.matched_preview:
        ws_matched.append(_map_match_to_matched_row(m))
    _apply_header_style(ws_matched)
    _set_reasonable_widths(ws_matched)

    # -----------------
    # Mismatches
    # -----------------
    ws_mismatch = wb.create_sheet(reconcile_response.mismatch_sheet_name)
    mismatch_headers = [
        "GSTIN",
        "Supplier Name",
        "Invoice Number",
        "Invoice Date",
        "GST Taxable Amount",
        "Books Taxable Amount",
        "GST Tax Amount",
        "Books Tax Amount",
        "Mismatch Reason",
        "Remarks",
    ]
    ws_mismatch.append(mismatch_headers)
    for mm in reconcile_response.mismatches_preview:
        if mm.mismatch_type not in MISSING_RECORD_TYPES:
            ws_mismatch.append(_map_mismatch_to_mismatch_row(mm))
    _apply_header_style(ws_mismatch)
    _set_reasonable_widths(ws_mismatch)

    # -----------------
    # Missing in GST / Books
    # -----------------
    # For MVP Day 5: current ReconcileResponse does not include missing-row payload.
    # However mismatch entries already carry both GST and Tally fields.
    # We populate Missing in GST/Books based on mismatch_type.
    ws_missing_gst = wb.create_sheet(reconcile_response.missing_in_gst_sheet_name)
    missing_gst_headers = [
        "GSTIN",
        "Supplier Name",
        "Invoice Number",
        "Invoice Date",
        "Taxable Amount",
        "Remarks",
    ]
    ws_missing_gst.append(missing_gst_headers)


    ws_missing_books = wb.create_sheet(reconcile_response.missing_in_books_sheet_name)
    missing_books_headers = [
        "GSTIN",
        "Supplier Name",
        "Invoice Number",
        "Invoice Date",
        "Taxable Amount",
        "Remarks",
    ]
    ws_missing_books.append(missing_books_headers)

    for mm in reconcile_response.mismatches_preview:
        if mm.mismatch_type == "Missing in GST":
            ws_missing_gst.append(_map_missing_invoice_to_row(mm, "GST"))
        elif mm.mismatch_type == "Missing in Books":
            ws_missing_books.append(_map_missing_invoice_to_row(mm, "Books"))








    _apply_header_style(ws_missing_gst)
    _set_reasonable_widths(ws_missing_gst)
    _apply_header_style(ws_missing_books)
    _set_reasonable_widths(ws_missing_books)

    # -----------------
    # Summary
    # -----------------


    # -----------------
    # Summary
    # -----------------
    ws_summary = wb.create_sheet("Summary")


    s: ReconcileSummary = reconcile_response.summary
    true_mismatch_count = s.mismatched_count
    missing_records_count = s.missing_in_gst_count + s.missing_in_books_count

    ws_summary.append(["Metric", "Value"])
    ws_summary.append(["Total GST Records", s.matched_count + s.missing_in_books_count])
    ws_summary.append(["Total Books Records", s.matched_count + s.missing_in_gst_count])
    ws_summary.append(["Matched Count", s.matched_count])
    ws_summary.append(["True Mismatch Count", true_mismatch_count])
    ws_summary.append(["Missing Records Count", missing_records_count])
    ws_summary.append(["Missing in GST Count", s.missing_in_gst_count])
    ws_summary.append(["Missing in Books Count", s.missing_in_books_count])

    accuracy = 0.0
    denom = max(1, s.matched_count + true_mismatch_count + missing_records_count)
    accuracy = (s.matched_count / denom) * 100.0
    ws_summary.append(["Reconciliation Accuracy %", round(accuracy, 2)])

    _apply_header_style(ws_summary)
    _set_reasonable_widths(ws_summary)

    wb.save(out_path)
    return out_path