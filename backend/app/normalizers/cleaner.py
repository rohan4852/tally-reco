"""
cleaner.py
----------
DataFrame-level cleaning utilities.
Operates on whole DataFrames after initial parsing.

Responsibilities:
- Drop fully empty rows/columns
- Rename columns to canonical internal names
- Fill NaN with safe defaults
- Flag duplicate invoice numbers
- Strip BOM characters from column headers
"""

import pandas as pd
from typing import Dict, List


# ---------------------------------------------------------------------------
# Column name mapping helpers
# ---------------------------------------------------------------------------

# Canonical internal column names → common aliases found in GST / Tally exports
COLUMN_ALIASES: Dict[str, List[str]] = {
    "gstin": [
        "gstin", "gstin of supplier", "supplier gstin", "party gstin",
        "gstin/uin of recipient", "gstin of recipient", "gst no", "gstin no",
    ],
    "invoice_number": [
        "invoice number", "invoice no", "invoice no.", "bill no", "bill number",
        "voucher number", "voucher no", "inv no", "document number", "doc no",
    ],
    "invoice_date": [
        "invoice date", "date", "bill date", "voucher date",
        "document date", "invoice dt", "inv date",
    ],
    "supplier_name": [
        "supplier name", "party name", "trade name", "legal name",
        "supplier", "vendor name", "party", "name of supplier",
    ],
    "taxable_amount": [
        "taxable amount", "taxable value", "taxable amt", "assessable value",
        "taxable", "base amount", "value", "net amount",
    ],
    "cgst": [
        "cgst", "cgst amount", "cgst amt", "central tax",
    ],
    "sgst": [
        "sgst", "sgst amount", "sgst amt", "state tax", "utgst",
    ],
    "igst": [
        "igst", "igst amount", "igst amt", "integrated tax",
    ],
    "total_amount": [
        "total amount", "total", "invoice value", "gross amount",
        "total value", "grand total",
    ],
}


def _build_reverse_alias_map() -> Dict[str, str]:
    """Returns {alias_lower: canonical_name} for fast lookup."""
    reverse: Dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            reverse[alias.lower().strip()] = canonical
    return reverse


REVERSE_ALIAS_MAP = _build_reverse_alias_map()


def strip_bom(text: str) -> str:
    """Remove UTF-8 BOM and zero-width characters from column headers."""
    return text.replace("\ufeff", "").replace("\u200b", "").strip()


def clean_column_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Strips BOM, leading/trailing spaces from column names.
    Does NOT rename to canonical yet — that's done in map_columns_to_canonical.
    """
    df.columns = [strip_bom(str(c)) for c in df.columns]
    return df


def map_columns_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renames columns to canonical internal names using COLUMN_ALIASES.
    Unknown columns are left as-is (prefixed with 'extra_' for clarity).
    """
    new_cols = {}
    seen_canonicals = set()

    for col in df.columns:
        key = col.lower().strip()
        canonical = REVERSE_ALIAS_MAP.get(key)
        if canonical and canonical not in seen_canonicals:
            new_cols[col] = canonical
            seen_canonicals.add(canonical)
        # leave extra columns as-is

    return df.rename(columns=new_cols)


def drop_empty_rows_and_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows and columns that are entirely NaN."""
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    return df.reset_index(drop=True)


def fill_safe_defaults(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fills NaN in numeric columns with 0.0,
    and NaN in string columns with empty string.
    """
    numeric_cols = ["taxable_amount", "cgst", "sgst", "igst", "total_amount"]
    string_cols = ["gstin", "invoice_number", "invoice_date", "supplier_name"]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    return df


def flag_duplicates(df: pd.DataFrame, key_col: str = "invoice_number") -> pd.DataFrame:
    """
    Adds a boolean column `is_duplicate` = True for rows where
    the key_col value appears more than once.
    """
    if key_col not in df.columns:
        df["is_duplicate"] = False
        return df
    df["is_duplicate"] = df.duplicated(subset=[key_col], keep=False)
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Master cleaning pipeline. Call this after parsing an Excel sheet.
    Steps:
      1. Strip BOM from headers
      2. Drop empty rows/cols
      3. Map to canonical column names
      4. Fill safe defaults
      5. Flag duplicates
    """
    df = clean_column_headers(df)
    df = drop_empty_rows_and_cols(df)
    df = map_columns_to_canonical(df)
    df = fill_safe_defaults(df)
    df = flag_duplicates(df)
    return df


def get_missing_canonical_columns(df: pd.DataFrame) -> List[str]:
    """
    Returns list of canonical columns that are absent from the DataFrame.
    Used to warn users about incomplete Excel formats.
    """
    required = ["gstin", "invoice_number", "taxable_amount"]
    return [col for col in required if col not in df.columns]
