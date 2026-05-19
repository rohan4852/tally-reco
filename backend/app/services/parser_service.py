"""
parser_service.py
-----------------
Reads a GST or Tally Excel file from disk, detects the correct sheet,
cleans the DataFrame, and applies all normalizations.

Returns a ParseResult with:
  - cleaned DataFrame
  - detected sheet name
  - list of warnings (missing columns, etc.)
  - row/column counts
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

from app.normalizers.cleaner import (
    clean_dataframe,
    get_missing_canonical_columns,
)

from app.utils.normalizer import (
    normalize_gstin,
    normalize_invoice_number,
    normalize_amount,
    normalize_date,
    normalize_supplier_name,
)

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    file_type: str                        # "gst" or "tally"
    file_path: str
    sheet_name: str
    row_count: int
    column_count: int
    columns_found: list
    missing_required_columns: list
    warnings: list = field(default_factory=list)
    dataframe: Optional[pd.DataFrame] = None

    def to_summary_dict(self) -> dict:
        return {
            "file_type": self.file_type,
            "file_path": self.file_path,
            "sheet_name": self.sheet_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns_found": self.columns_found,
            "missing_required_columns": self.missing_required_columns,
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Sheet detection
# ---------------------------------------------------------------------------

def _detect_best_sheet(excel_file: pd.ExcelFile) -> str:
    """
    Picks the most relevant sheet from the workbook.
    Priority:
      1. Sheet whose name contains keywords: b2b, purchase, gstr, tally, sales, invoice
      2. First sheet that has data (>1 row)
      3. First sheet overall
    """
    keywords = ["b2b", "purchase", "gstr", "tally", "sales", "invoice", "inward", "outward"]
    sheet_names = excel_file.sheet_names

    for name in sheet_names:
        lower = name.lower()
        if any(kw in lower for kw in keywords):
            return name

    # Fallback: first sheet with more than 1 row
    for name in sheet_names:
        try:
            preview = excel_file.parse(name, nrows=2)
            if len(preview) > 0:
                return name
        except Exception:
            continue

    return sheet_names[0]


# ---------------------------------------------------------------------------
# Header row detection
# ---------------------------------------------------------------------------

def _detect_header_row(df_raw: pd.DataFrame) -> int:
    """
    Scans the first 10 rows to find which row contains the actual column headers.
    Heuristic: the header row is the first row containing keywords like
    'gstin', 'invoice', 'amount', 'date', 'tax'.
    Returns the 0-based row index.
    """
    header_keywords = {"gstin", "invoice", "amount", "date", "tax", "cgst", "sgst", "igst", "name", "value"}

    for i, row in df_raw.head(10).iterrows():
        row_values = {str(v).lower().strip() for v in row.values if pd.notna(v)}
        if row_values & header_keywords:  # intersection
            return i

    return 0  # default to first row


# ---------------------------------------------------------------------------
# Core parser
# ---------------------------------------------------------------------------

def parse_excel_file(file_path: Path, file_type: str) -> ParseResult:
    """
    Full parsing pipeline for a single Excel file.

    Steps:
      1. Open workbook, detect best sheet
      2. Read raw (no header assumed yet)
      3. Detect header row
      4. Re-read with correct header
      5. Clean + map columns
      6. Apply field-level normalizations
      7. Return ParseResult

    Args:
        file_path: absolute Path to the .xlsx/.xls file
        file_type: "gst" or "tally"

    Returns:
        ParseResult with cleaned DataFrame
    """
    warnings = []

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # --- Step 1: Open and detect sheet ---
    try:
        excel_file = pd.ExcelFile(file_path, engine="openpyxl")
    except Exception:
        excel_file = pd.ExcelFile(file_path, engine="xlrd")

    sheet_name = _detect_best_sheet(excel_file)

    # --- Step 2: Read raw (all as strings to detect header row safely) ---
    df_raw = excel_file.parse(sheet_name, header=None, dtype=str)

    # --- Step 3: Detect header row candidates ---
    header_row_idx = _detect_header_row(df_raw)
    if header_row_idx > 0:
        warnings.append(f"Header detected at row {header_row_idx + 1} (skipped {header_row_idx} preamble row(s)).")

    # Build candidate header rows: any of first 10 rows that contain header keywords.
    header_keywords = {"gstin", "invoice", "amount", "date", "tax", "cgst", "sgst", "igst", "name", "value", "number"}
    candidates = []
    for i, row in df_raw.head(10).iterrows():
        row_values = {str(v).lower().strip() for v in row.values if pd.notna(v)}
        if row_values & header_keywords:
            candidates.append(i)

    # Always consider the initially detected header_row_idx as a candidate
    if header_row_idx not in candidates:
        candidates.insert(0, header_row_idx)

    # --- Step 4: Try candidates and pick best with a small heuristic ---
    import re

    def _looks_like_iso_date(x: str) -> bool:
        s = (x or "").strip()
        return len(s) >= 8 and bool(re.search(r"\d{4}-\d{2}-\d{2}", s))

    def _looks_like_invoice(x: str) -> bool:
        s = (x or "").strip()
        if not s:
            return False
        if re.search(r"\b(inv|bill)\b", s, re.I):
            return True
        # if it contains letters and digits and is not date-like, consider invoice-like
        if re.search(r"[A-Za-z]", s) and re.search(r"\d", s) and not _looks_like_iso_date(s):
            return True
        return False

    best_score = None
    best_df = None
    best_missing = None
    best_header = None

    for candidate in candidates:
        try:
            df_candidate = excel_file.parse(sheet_name, header=candidate)
        except Exception:
            continue
        df_candidate = clean_dataframe(df_candidate)
        df_candidate = _apply_normalizations(df_candidate)

        missing_candidate = get_missing_canonical_columns(df_candidate)

        # score: prefer fewer missing columns, invoice_number looks invoice-like, invoice_date looks date-like
        score = 0
        if not missing_candidate:
            score += 100

        inv_no_col = df_candidate.get("invoice_number", pd.Series([], dtype=object))
        inv_date_col = df_candidate.get("invoice_date", pd.Series([], dtype=object))

        inv_no_samples = [str(v) for v in inv_no_col.head(10).tolist()]
        inv_date_samples = [str(v) for v in inv_date_col.head(10).tolist()]

        inv_no_like = sum(1 for v in inv_no_samples if _looks_like_invoice(v))
        inv_date_like = sum(1 for v in inv_date_samples if _looks_like_iso_date(v))

        score += inv_no_like * 2
        score += inv_date_like * 3

        # prefer shorter header index (earlier) slightly
        score -= candidate * 0.1

        if best_score is None or score > best_score:
            best_score = score
            best_df = df_candidate
            best_missing = missing_candidate
            best_header = candidate

    if best_df is None:
        # fallback: read with detected header
        df = excel_file.parse(sheet_name, header=header_row_idx)
    else:
        if best_header != header_row_idx:
            warnings.append(f"Selected header row {best_header + 1} after scoring candidates (was {header_row_idx + 1}).")
        df = best_df
        missing = best_missing

    # --- Step 5/6 already done above for the selected best_df ---
    if missing:
        warnings.append(
            f"Required columns not found after mapping: {missing}. "
            "Check that your Excel headers match expected names."
        )


    return ParseResult(
        file_type=file_type,
        file_path=str(file_path),
        sheet_name=sheet_name,
        row_count=len(df),
        column_count=len(df.columns),
        columns_found=list(df.columns),
        missing_required_columns=missing,
        warnings=warnings,
        dataframe=df,
    )


# ---------------------------------------------------------------------------
# Field-level normalization
# ---------------------------------------------------------------------------

def _apply_normalizations(df: pd.DataFrame) -> pd.DataFrame:
    """Apply normalizer functions to each canonical column if present."""

    if "gstin" in df.columns:
        df["gstin"] = df["gstin"].apply(normalize_gstin)

    if "invoice_number" in df.columns:
        df["invoice_number"] = df["invoice_number"].apply(normalize_invoice_number)

    if "invoice_date" in df.columns:
        df["invoice_date"] = df["invoice_date"].apply(normalize_date)

    if "supplier_name" in df.columns:
        df["supplier_name"] = df["supplier_name"].apply(normalize_supplier_name)

    for amt_col in ["taxable_amount", "cgst", "sgst", "igst", "total_amount"]:
        if amt_col in df.columns:
            df[amt_col] = df[amt_col].apply(normalize_amount)

    return df


# ---------------------------------------------------------------------------
# Convenience: parse both files in one call
# ---------------------------------------------------------------------------

def parse_both_files(gst_path: Path, tally_path: Path) -> tuple[ParseResult, ParseResult]:
    """
    Parses both the GST and Tally Excel files.
    Returns (gst_result, tally_result).
    Raises on file-not-found or unreadable Excel.
    """
    gst_result = parse_excel_file(gst_path, file_type="gst")
    tally_result = parse_excel_file(tally_path, file_type="tally")
    return gst_result, tally_result
