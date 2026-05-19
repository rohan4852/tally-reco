from __future__ import annotations

from typing import Optional


def generate_remarks(mismatch_type: str, mismatch_reason: str) -> str:
    """Rule-based remarks text shown in reports.

    Day 4 MVP requirement: provide human-readable remarks aligned with mismatch_type.
    """
    base = (mismatch_reason or "").strip()

    def _dedup_whitespace(s: str) -> str:
        return " ".join((s or "").split())

    def _append_unique(prefix: str) -> str:
        s = _dedup_whitespace(f"{prefix} {base}".strip()) if base else _dedup_whitespace(prefix)
        # If base already appears inside generated text, avoid repeating it.
        if base and s.count(base) > 1:
            s = s.replace(base, "", 1)
            s = _dedup_whitespace(s)
        return s

    if mismatch_type == "GSTIN mismatch":
        return _append_unique("GSTIN does not match after normalization.")

    if mismatch_type == "Invoice mismatch":
        return _append_unique("Invoice number/date pairing does not match.")

    if mismatch_type == "Amount mismatch":
        return _append_unique("Taxable amount differs between GST portal and Tally.")

    if mismatch_type == "Tax mismatch":
        return _append_unique("CGST/SGST/IGST values differ between GST portal and Tally.")

    if mismatch_type == "Missing in GST":
        return _append_unique("Invoice exists in Tally but missing in GST export.")

    if mismatch_type == "Missing in Books":
        return _append_unique("Invoice exists in GST export but missing in Tally books.")

    if mismatch_type == "Duplicate invoice":
        return _append_unique("GST export contains a duplicate invoice (same invoice number appears multiple times).")

    return base if base else "Mismatch detected."
