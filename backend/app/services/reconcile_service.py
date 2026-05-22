from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pandas as pd

from app.matching.classifier import classify_mismatch_for_pair, MISMATCH_TYPES

from app.matching.remarks import generate_remarks

from app.matching.matcher import match_records
from app.schemas.reconcile import (
    ReconcileEngineMatch,
    ReconcileMismatch,
    ReconcileResponse,
    ReconcileSummary,
)
from app.services.parser_service import parse_both_files

def _row_to_match(gst_row: pd.Series, tally_row: pd.Series, match_key: str) -> ReconcileEngineMatch:
    return ReconcileEngineMatch(
        gst_gstin=str(gst_row.get("gstin", "") or ""),
        gst_supplier_name=str(gst_row.get("supplier_name", "") or ""),
        gst_invoice_number=str(gst_row.get("invoice_number", "") or ""),
        gst_invoice_date=str(gst_row.get("invoice_date", "") or ""),
        gst_taxable_amount=float(gst_row.get("taxable_amount", 0.0) or 0.0),
        gst_cgst=float(gst_row.get("cgst", 0.0) or 0.0),
        gst_sgst=float(gst_row.get("sgst", 0.0) or 0.0),
        gst_igst=float(gst_row.get("igst", 0.0) or 0.0),
        gst_total_amount=float(gst_row.get("total_amount", 0.0) or 0.0),
        tally_supplier_name=str(tally_row.get("supplier_name", "") or ""),
        tally_invoice_date=str(tally_row.get("invoice_date", "") or ""),
        tally_taxable_amount=float(tally_row.get("taxable_amount", 0.0) or 0.0),
        tally_cgst=float(tally_row.get("cgst", 0.0) or 0.0),
        tally_sgst=float(tally_row.get("sgst", 0.0) or 0.0),
        tally_igst=float(tally_row.get("igst", 0.0) or 0.0),
        tally_total_amount=float(tally_row.get("total_amount", 0.0) or 0.0),
        match_key=match_key,
    )


def _build_key_for_pair(gst_row: pd.Series) -> str:
    gstin = str(gst_row.get("gstin", "") or "")
    inv = str(gst_row.get("invoice_number", "") or "")
    taxable = float(gst_row.get("taxable_amount", 0.0) or 0.0)
    return f"{gstin}__{inv}__{taxable:.2f}"


def reconcile_session(session_id: str, gst_path: Path, tally_path: Path) -> ReconcileResponse:
    gst_parsed, tally_parsed = parse_both_files(gst_path, tally_path)
    gst_df = gst_parsed.dataframe
    tally_df = tally_parsed.dataframe

    match_result = match_records(gst_df, tally_df)

    matched_preview: List[ReconcileEngineMatch] = []
    mismatches: List[ReconcileMismatch] = []
    true_mismatch_entries = 0
    matched_pair_count = 0

    for gst_idx, tally_idx in match_result.matched:
        gst_row = gst_df.iloc[gst_idx]
        tally_row = tally_df.iloc[tally_idx]
        match_key = _build_key_for_pair(gst_row)

        pair_mismatches = classify_mismatch_for_pair(gst_row, tally_row, match_key)
        for m in pair_mismatches:
            m.remarks = generate_remarks(m.mismatch_type, m.mismatch_reason)

        if pair_mismatches:
            mismatches.extend(pair_mismatches)
            true_mismatch_entries += len(pair_mismatches)
        else:
            matched_preview.append(_row_to_match(gst_row, tally_row, match_key))
            matched_pair_count += 1

    # Emit missing-in-GST and missing-in-books mismatches (Day 4 coverage)
    for tally_idx in match_result.missing_in_gst:
        tally_row = tally_df.iloc[tally_idx]
        gst_row = pd.Series(dtype=object)  # empty side; we keep GST fields blank

        match_key = ""
        mm = ReconcileMismatch(
            gst_gstin="",
            gst_supplier_name="",
            gst_invoice_number="",
            gst_invoice_date="",
            gst_taxable_amount=0.0,
            gst_cgst=0.0,
            gst_sgst=0.0,
            gst_igst=0.0,
            gst_total_amount=0.0,
            tally_gstin=str(tally_row.get("gstin", "") or ""),
            tally_supplier_name=str(tally_row.get("supplier_name", "") or ""),
            tally_invoice_number=str(tally_row.get("invoice_number", "") or ""),
            tally_invoice_date=str(tally_row.get("invoice_date", "") or ""),
            tally_taxable_amount=float(tally_row.get("taxable_amount", 0.0) or 0.0),
            tally_cgst=float(tally_row.get("cgst", 0.0) or 0.0),
            tally_sgst=float(tally_row.get("sgst", 0.0) or 0.0),
            tally_igst=float(tally_row.get("igst", 0.0) or 0.0),
            tally_total_amount=float(tally_row.get("total_amount", 0.0) or 0.0),
            match_key=match_key,
            mismatch_type=MISMATCH_TYPES["Missing in GST"],
            mismatch_reason="Invoice exists in Tally but missing in GST export.",
        )
        mm.remarks = generate_remarks(mm.mismatch_type, mm.mismatch_reason)
        mismatches.append(mm)

    for gst_idx in match_result.missing_in_books:
        gst_row = gst_df.iloc[gst_idx]
        tally_row = pd.Series(dtype=object)  # empty side; we keep Books fields blank

        match_key = _build_key_for_pair(gst_row)
        mm = ReconcileMismatch(
            gst_gstin=str(gst_row.get("gstin", "") or ""),
            gst_supplier_name=str(gst_row.get("supplier_name", "") or ""),
            gst_invoice_number=str(gst_row.get("invoice_number", "") or ""),
            gst_invoice_date=str(gst_row.get("invoice_date", "") or ""),
            gst_taxable_amount=float(gst_row.get("taxable_amount", 0.0) or 0.0),
            gst_cgst=float(gst_row.get("cgst", 0.0) or 0.0),
            gst_sgst=float(gst_row.get("sgst", 0.0) or 0.0),
            gst_igst=float(gst_row.get("igst", 0.0) or 0.0),
            gst_total_amount=float(gst_row.get("total_amount", 0.0) or 0.0),
            tally_gstin="",
            tally_supplier_name="",
            tally_invoice_number="",
            tally_invoice_date="",
            tally_taxable_amount=0.0,
            tally_cgst=0.0,
            tally_sgst=0.0,
            tally_igst=0.0,
            tally_total_amount=0.0,
            match_key=match_key,
            mismatch_type=MISMATCH_TYPES["Missing in Books"],
            mismatch_reason="Invoice exists in GST export but missing in Tally books.",
        )
        mm.remarks = generate_remarks(mm.mismatch_type, mm.mismatch_reason)
        mismatches.append(mm)


    missing_in_gst_count = len(match_result.missing_in_gst)
    missing_in_books_count = len(match_result.missing_in_books)
    total_gst_records = matched_pair_count + missing_in_books_count
    total_books_records = matched_pair_count + missing_in_gst_count
    missing_records_count = missing_in_gst_count + missing_in_books_count
    accuracy_percent = (
        matched_pair_count / max(1, matched_pair_count + true_mismatch_entries + missing_records_count)
    ) * 100.0

    summary = ReconcileSummary(
        matched_count=matched_pair_count,
        mismatched_count=true_mismatch_entries,
        missing_in_gst_count=missing_in_gst_count,
        missing_in_books_count=missing_in_books_count,
        duplicate_invoice_count=int((gst_df.get("is_duplicate", False)).sum())
        if "is_duplicate" in gst_df.columns
        else 0,
        total_gst_records=total_gst_records,
        total_books_records=total_books_records,
        missing_records_count=missing_records_count,
        true_mismatch_count=true_mismatch_entries,
        accuracy_percent=round(accuracy_percent, 2),
    )

    # Ensure missing-in-GST/Books fields never export as None.
    # (Observed issue: tally-side values on Missing in GST sheet were coming through as None.)
    def _coerce_str(v) -> str:
        return "" if v is None else str(v)

    def _coerce_float(v) -> float:
        try:
            if v is None:
                return 0.0
            return float(v)
        except Exception:
            return 0.0

    for mm in mismatches:
        # tally side
        mm.tally_gstin = _coerce_str(mm.tally_gstin)
        mm.tally_supplier_name = _coerce_str(mm.tally_supplier_name)
        mm.tally_invoice_number = _coerce_str(mm.tally_invoice_number)
        mm.tally_invoice_date = _coerce_str(mm.tally_invoice_date)
        mm.tally_taxable_amount = _coerce_float(mm.tally_taxable_amount)
        mm.tally_cgst = _coerce_float(mm.tally_cgst)
        mm.tally_sgst = _coerce_float(mm.tally_sgst)
        mm.tally_igst = _coerce_float(mm.tally_igst)

        # gst side
        mm.gst_gstin = _coerce_str(mm.gst_gstin)
        mm.gst_supplier_name = _coerce_str(mm.gst_supplier_name)
        mm.gst_invoice_number = _coerce_str(mm.gst_invoice_number)
        mm.gst_invoice_date = _coerce_str(mm.gst_invoice_date)
        mm.gst_taxable_amount = _coerce_float(mm.gst_taxable_amount)
        mm.gst_cgst = _coerce_float(mm.gst_cgst)
        mm.gst_sgst = _coerce_float(mm.gst_sgst)
        mm.gst_igst = _coerce_float(mm.gst_igst)


