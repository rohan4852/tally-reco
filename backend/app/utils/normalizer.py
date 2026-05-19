"""
normalizer.py
-------------
Pure transformation functions that standardize field values
so that matching (Day 3) works on clean, comparable data.

All functions are stateless and operate on scalar values or Series.
"""

import re
import numpy as np
import pandas as pd
from dateutil import parser as date_parser


# ---------------------------------------------------------------------------
# GSTIN
# ---------------------------------------------------------------------------

def normalize_gstin(value) -> str:
    """
    Uppercase, strip spaces, remove non-alphanumeric chars.
    GSTIN format: 15 alphanumeric characters.
    Returns empty string if null/invalid.
    """
    if pd.isna(value) or str(value).strip() == "":
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()
    return cleaned


# ---------------------------------------------------------------------------
# Invoice number
# ---------------------------------------------------------------------------

def normalize_invoice_number(value) -> str:
    """
    Uppercase, strip spaces, collapse internal whitespace,
    remove common separator characters (/, -, _) for consistent comparison.
    """
    if pd.isna(value) or str(value).strip() == "":
        return ""
    cleaned = str(value).strip().upper()
    # Remove common separators that vary between Tally and GST portal
    cleaned = re.sub(r"[\s\-_/\\]", "", cleaned)
    return cleaned


# ---------------------------------------------------------------------------
# Amounts
# ---------------------------------------------------------------------------

def normalize_amount(value, decimals: int = 2) -> float:
    """
    Converts value to float rounded to `decimals` places.
    Returns 0.0 if null, empty, or non-numeric.
    """
    if pd.isna(value) or str(value).strip() == "":
        return 0.0
    try:
        return round(float(str(value).replace(",", "").strip()), decimals)
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

def normalize_date(value) -> str:
    """
    Parses a wide variety of date formats and returns ISO 8601 string (YYYY-MM-DD).
    Returns empty string if unparseable.

    Handles:
      - dd/mm/yyyy  (Indian standard)
      - dd-mm-yyyy
      - yyyy-mm-dd
      - dd MMM yyyy  (01 Apr 2024)
      - Excel serial dates (integers)
    """
    if pd.isna(value) or str(value).strip() == "":
        return ""

    # Excel serial date (number stored as float/int)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            # Excel epoch: 1900-01-01, but openpyxl already converts to datetime
            ts = pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(value))
            return ts.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Already a datetime / Timestamp
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d")

    import datetime
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d")

    raw = str(value).strip()
    try:
        # dayfirst=True handles Indian dd/mm/yyyy format
        parsed = date_parser.parse(raw, dayfirst=True)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return raw  # return as-is if totally unparseable


# ---------------------------------------------------------------------------
# Supplier / party name
# ---------------------------------------------------------------------------

def normalize_supplier_name(value) -> str:
    """
    Strip, uppercase, collapse multiple spaces.
    """
    if pd.isna(value) or str(value).strip() == "":
        return ""
    cleaned = str(value).strip().upper()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


# ---------------------------------------------------------------------------
# Generic text field
# ---------------------------------------------------------------------------

def normalize_text(value) -> str:
    """Trim whitespace and uppercase any generic text field."""
    if pd.isna(value) or str(value).strip() == "":
        return ""
    return str(value).strip().upper()
