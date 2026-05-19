from __future__ import annotations

from typing import Any, Dict

import streamlit as st


def _metric_card(title: str, value: Any, help_text: str | None = None) -> None:
    st.markdown(
        f"""
        <div style="padding:14px 18px;border:1px solid #e5e7eb;border-radius:12px;background:#ffffff;">
          <div style="font-size:12px;color:#6b7280;font-weight:600;">{title}</div>
          <div style="font-size:22px;color:#111827;font-weight:800;margin-top:4px;">{value}</div>
          {f'<div style="font-size:12px;color:#6b7280;margin-top:6px;">{help_text}</div>' if help_text else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def summary_cards(summary: Dict[str, Any]) -> None:
    required_keys = [
        "total_gst_records",
        "total_books_records",
        "matched_count",
        "mismatched_count",
        "missing_in_gst_count",
        "missing_in_books_count",
        "accuracy_percent",
    ]

    # If backend summary uses different casing, fallback gracefully.
    def get_any(*keys: str):
        for k in keys:
            if k in summary:
                return summary[k]
        return None

    total_gst = get_any("total_gst_records", "totalGSTRecords", "total_gst")
    total_books = get_any("total_books_records", "totalBooksRecords", "total_books")
    matched = get_any("matched_count", "matchedCount")
    true_mismatch = get_any("true_mismatch_count", "trueMismatchCount", "true_mismatch")
    mismatched = get_any("mismatched_count", "mismatchedCount", "mismatch_count")
    missing_records = get_any("missing_records_count", "missingRecordsCount", "missing_records")
    missing_gst = get_any("missing_in_gst_count", "missingInGstCount", "missing_in_gst")
    missing_books = get_any("missing_in_books_count", "missingInBooksCount", "missing_in_books")
    accuracy = get_any("accuracy_percent", "accuracyPercent", "accuracy")

    st.subheader("Reconciliation Summary")

    c1, c2, c3 = st.columns(3)
    with c1:
        _metric_card("Total GST Records", total_gst)
    with c2:
        _metric_card("Total Books Records", total_books)
    with c3:
        _metric_card("Reconciliation Accuracy %", accuracy)

    c4, c5, c6 = st.columns(3)
    with c4:
        _metric_card("Matched Count", matched)
    with c5:
        _metric_card("True Mismatch Count", true_mismatch)
    with c6:
        _metric_card("Missing Records Count", missing_records)

    c7, c8, _ = st.columns([1, 1, 1])
    with c7:
        _metric_card("Missing in GST", missing_gst)
    with c8:
        _metric_card("Missing in Books", missing_books)

