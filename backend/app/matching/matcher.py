from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd


PRIMARY_KEY_COLS = ["gstin", "invoice_number", "taxable_amount"]
SECONDARY_TAX_COLS = ["cgst", "sgst", "igst"]


def build_match_key(row: pd.Series) -> str:
    """Build deterministic match key based on normalized canonical columns."""

    gstin = str(row.get("gstin", "") or "")
    inv = str(row.get("invoice_number", "") or "")
    taxable = row.get("taxable_amount", 0.0)

    # taxable_amount is already normalized to numeric rounded floats by Day 2
    return f"{gstin}__{inv}__{taxable:.2f}"


@dataclass(frozen=True)
class MatchResult:
    matched: List[Tuple[int, int]]  # list of (gst_row_idx, tally_row_idx)
    missing_in_gst: List[int]  # tally row indices
    missing_in_books: List[int]  # gst row indices


def match_records(gst_df: pd.DataFrame, tally_df: pd.DataFrame) -> MatchResult:
    """
    Matches GST portal rows with Tally rows.

    Primary matching:
      GSTIN + Invoice Number + Taxable Amount

    Secondary fields are used later for mismatch classification.
    """

    if gst_df.empty and tally_df.empty:
        return MatchResult(matched=[], missing_in_gst=[], missing_in_books=[])

    gst_work = gst_df.copy()
    tally_work = tally_df.copy()

    gst_work = gst_work.reset_index(drop=True)
    tally_work = tally_work.reset_index(drop=True)

    for col in ["gstin", "invoice_number", "taxable_amount"]:
        if col not in gst_work.columns:
            gst_work[col] = "" if col != "taxable_amount" else 0.0
        if col not in tally_work.columns:
            tally_work[col] = "" if col != "taxable_amount" else 0.0

    gst_keys = gst_work.apply(build_match_key, axis=1)
    tally_keys = tally_work.apply(build_match_key, axis=1)

    gst_key_to_rows: Dict[str, List[int]] = {}
    for i, k in enumerate(gst_keys.tolist()):
        gst_key_to_rows.setdefault(k, []).append(i)

    tally_key_to_rows: Dict[str, List[int]] = {}
    for i, k in enumerate(tally_keys.tolist()):
        tally_key_to_rows.setdefault(k, []).append(i)

    matched_pairs: List[Tuple[int, int]] = []

    # Deterministic pairing: first GST row with first Tally row per key.
    all_keys = set(gst_key_to_rows.keys()) & set(tally_key_to_rows.keys())
    for k in all_keys:
        gst_rows = gst_key_to_rows.get(k, [])
        tally_rows = tally_key_to_rows.get(k, [])
        for j in range(min(len(gst_rows), len(tally_rows))):
            matched_pairs.append((gst_rows[j], tally_rows[j]))

    matched_gst_rows = {g for g, _ in matched_pairs}
    matched_tally_rows = {t for _, t in matched_pairs}

    missing_in_books = [i for i in range(len(gst_work)) if i not in matched_gst_rows]
    missing_in_gst = [i for i in range(len(tally_work)) if i not in matched_tally_rows]

    return MatchResult(
        matched=matched_pairs,
        missing_in_gst=missing_in_gst,
        missing_in_books=missing_in_books,
    )

