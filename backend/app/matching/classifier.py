from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from app.schemas.reconcile import ReconcileMismatch


MISMATCH_TYPES = {
    "GSTIN mismatch": "GSTIN mismatch",
    "Invoice mismatch": "Invoice mismatch",
    "Amount mismatch": "Amount mismatch",
    "Tax mismatch": "Tax mismatch",
    "Missing in GST": "Missing in GST",
    "Missing in Books": "Missing in Books",
    "Duplicate invoice": "Duplicate invoice",
}


def _to_float(value) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def classify_mismatch_for_pair(
    gst_row: pd.Series,
    tally_row: pd.Series,
    match_key: str,
) -> List[ReconcileMismatch]:
    """Return list of mismatch entries for one matched pair.

    Day 4 rules (MVP, deterministic):
    - Duplicate invoice: GST row has is_duplicate=True.
    - Tax mismatch: any of CGST/SGST/IGST differs.
    - Amount mismatch: taxable_amount differs.
    - Invoice mismatch: invoice number/date differs.
    - GSTIN mismatch: gstin differs.

    Note: Primary matching is already based on gstin+invoice_number+taxable_amount,
    so GSTIN/Invoice/Amount mismatches may be rare but still supported when data differs.
    """


    mismatches: List[ReconcileMismatch] = []

    gst_gstin = str(gst_row.get("gstin", "") or "")
    tally_gstin = str(tally_row.get("gstin", "") or "")
    gst_inv_no = str(gst_row.get("invoice_number", "") or "")
    tally_inv_no = str(tally_row.get("invoice_number", "") or "")
    gst_inv_date = str(gst_row.get("invoice_date", "") or "")
    tally_inv_date = str(tally_row.get("invoice_date", "") or "")

    gst_taxable = _to_float(gst_row.get("taxable_amount", 0.0))
    tally_taxable = _to_float(tally_row.get("taxable_amount", 0.0))

    gst_is_dup = bool(gst_row.get("is_duplicate", False))
    if gst_is_dup:
        mismatches.append(
            ReconcileMismatch(
                gst_gstin=gst_gstin,
                gst_supplier_name=str(gst_row.get("supplier_name", "") or ""),
                gst_invoice_number=gst_inv_no,
                gst_invoice_date=gst_inv_date,
                gst_taxable_amount=gst_taxable,
                gst_cgst=_to_float(gst_row.get("cgst", 0.0)),
                gst_sgst=_to_float(gst_row.get("sgst", 0.0)),
                gst_igst=_to_float(gst_row.get("igst", 0.0)),
                gst_total_amount=_to_float(gst_row.get("total_amount", 0.0)),
                tally_gstin=tally_gstin,
                tally_supplier_name=str(tally_row.get("supplier_name", "") or ""),
                tally_invoice_number=tally_inv_no,
                tally_invoice_date=tally_inv_date,
                tally_taxable_amount=tally_taxable,
                tally_cgst=_to_float(tally_row.get("cgst", 0.0)),
                tally_sgst=_to_float(tally_row.get("sgst", 0.0)),
                tally_igst=_to_float(tally_row.get("igst", 0.0)),
                tally_total_amount=_to_float(tally_row.get("total_amount", 0.0)),
                match_key=match_key,
                mismatch_type=MISMATCH_TYPES["Duplicate invoice"],
                mismatch_reason="Invoice number is duplicated in GST export.",
            )
        )

    # GSTIN mismatch
    if gst_gstin != tally_gstin:
        mismatches.append(
            ReconcileMismatch(
                gst_gstin=gst_gstin,
                gst_supplier_name=str(gst_row.get("supplier_name", "") or ""),
                gst_invoice_number=gst_inv_no,
                gst_invoice_date=gst_inv_date,
                gst_taxable_amount=gst_taxable,
                gst_cgst=_to_float(gst_row.get("cgst", 0.0)),
                gst_sgst=_to_float(gst_row.get("sgst", 0.0)),
                gst_igst=_to_float(gst_row.get("igst", 0.0)),
                gst_total_amount=_to_float(gst_row.get("total_amount", 0.0)),
                tally_gstin=tally_gstin,
                tally_supplier_name=str(tally_row.get("supplier_name", "") or ""),
                tally_invoice_number=tally_inv_no,
                tally_invoice_date=tally_inv_date,
                tally_taxable_amount=tally_taxable,
                tally_cgst=_to_float(tally_row.get("cgst", 0.0)),
                tally_sgst=_to_float(tally_row.get("sgst", 0.0)),
                tally_igst=_to_float(tally_row.get("igst", 0.0)),
                tally_total_amount=_to_float(tally_row.get("total_amount", 0.0)),
                match_key=match_key,
                mismatch_type=MISMATCH_TYPES["GSTIN mismatch"],
                mismatch_reason="GSTIN value differs between GST portal and Tally after normalization.",
            )
        )

    # Invoice mismatch (invoice number or date differs)
    if gst_inv_no != tally_inv_no or gst_inv_date != tally_inv_date:
        mismatches.append(
            ReconcileMismatch(
                gst_gstin=gst_gstin,
                gst_supplier_name=str(gst_row.get("supplier_name", "") or ""),
                gst_invoice_number=gst_inv_no,
                gst_invoice_date=gst_inv_date,
                gst_taxable_amount=gst_taxable,
                gst_cgst=_to_float(gst_row.get("cgst", 0.0)),
                gst_sgst=_to_float(gst_row.get("sgst", 0.0)),
                gst_igst=_to_float(gst_row.get("igst", 0.0)),
                gst_total_amount=_to_float(gst_row.get("total_amount", 0.0)),
                tally_gstin=tally_gstin,
                tally_supplier_name=str(tally_row.get("supplier_name", "") or ""),
                tally_invoice_number=tally_inv_no,
                tally_invoice_date=tally_inv_date,
                tally_taxable_amount=tally_taxable,
                tally_cgst=_to_float(tally_row.get("cgst", 0.0)),
                tally_sgst=_to_float(tally_row.get("sgst", 0.0)),
                tally_igst=_to_float(tally_row.get("igst", 0.0)),
                tally_total_amount=_to_float(tally_row.get("total_amount", 0.0)),
                match_key=match_key,
                mismatch_type=MISMATCH_TYPES["Invoice mismatch"],
                mismatch_reason="Invoice number/date differs between GST portal and Tally after normalization.",
            )
        )

    # Amount mismatch
    if gst_taxable != tally_taxable:
        mismatches.append(
            ReconcileMismatch(
                gst_gstin=gst_gstin,
                gst_supplier_name=str(gst_row.get("supplier_name", "") or ""),
                gst_invoice_number=gst_inv_no,
                gst_invoice_date=gst_inv_date,
                gst_taxable_amount=gst_taxable,
                gst_cgst=_to_float(gst_row.get("cgst", 0.0)),
                gst_sgst=_to_float(gst_row.get("sgst", 0.0)),
                gst_igst=_to_float(gst_row.get("igst", 0.0)),
                gst_total_amount=_to_float(gst_row.get("total_amount", 0.0)),
                tally_gstin=tally_gstin,
                tally_supplier_name=str(tally_row.get("supplier_name", "") or ""),
                tally_invoice_number=tally_inv_no,
                tally_invoice_date=tally_inv_date,
                tally_taxable_amount=tally_taxable,
                tally_cgst=_to_float(tally_row.get("cgst", 0.0)),
                tally_sgst=_to_float(tally_row.get("sgst", 0.0)),
                tally_igst=_to_float(tally_row.get("igst", 0.0)),
                tally_total_amount=_to_float(tally_row.get("total_amount", 0.0)),
                match_key=match_key,
                mismatch_type=MISMATCH_TYPES["Amount mismatch"],
                mismatch_reason="Taxable amount differs between GST portal and Tally.",
            )
        )

    # Tax comparison (secondary rule)
    gst_cgst = _to_float(gst_row.get("cgst", 0.0))
    gst_sgst = _to_float(gst_row.get("sgst", 0.0))
    gst_igst = _to_float(gst_row.get("igst", 0.0))

    tally_cgst = _to_float(tally_row.get("cgst", 0.0))
    tally_sgst = _to_float(tally_row.get("sgst", 0.0))
    tally_igst = _to_float(tally_row.get("igst", 0.0))


    # If any of the taxes differ, classify as Tax mismatch.
    if not (gst_cgst == tally_cgst and gst_sgst == tally_sgst and gst_igst == tally_igst):
        mismatches.append(
            ReconcileMismatch(
                gst_gstin=str(gst_row.get("gstin", "") or ""),
                gst_supplier_name=str(gst_row.get("supplier_name", "") or ""),
                gst_invoice_number=str(gst_row.get("invoice_number", "") or ""),
                gst_invoice_date=str(gst_row.get("invoice_date", "") or ""),
                gst_taxable_amount=_to_float(gst_row.get("taxable_amount", 0.0)),
                gst_cgst=gst_cgst,
                gst_sgst=gst_sgst,
                gst_igst=gst_igst,
                gst_total_amount=_to_float(gst_row.get("total_amount", 0.0)),
                tally_gstin=str(tally_row.get("gstin", "") or ""),
                tally_supplier_name=str(tally_row.get("supplier_name", "") or ""),
                tally_invoice_number=str(tally_row.get("invoice_number", "") or ""),
                tally_invoice_date=str(tally_row.get("invoice_date", "") or ""),
                tally_taxable_amount=_to_float(tally_row.get("taxable_amount", 0.0)),
                tally_cgst=tally_cgst,
                tally_sgst=tally_sgst,
                tally_igst=tally_igst,
                tally_total_amount=_to_float(tally_row.get("total_amount", 0.0)),
                match_key=match_key,
                mismatch_type=MISMATCH_TYPES["Tax mismatch"],
                mismatch_reason="GST taxes (CGST/SGST/IGST) do not match Tally for the matched invoice.",
            )
        )

    return mismatches