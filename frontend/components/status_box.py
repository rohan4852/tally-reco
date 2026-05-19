from __future__ import annotations

from typing import Optional

import streamlit as st


def status_box(session_id: Optional[str], is_reconciling: bool, error_message: Optional[str]) -> None:
    st.markdown(
        """
        <div style="padding:12px 16px;border:1px solid #e5e7eb;border-radius:12px;background:#f9fafb;">
          <div style="font-size:13px;color:#111827;font-weight:700;">Run Status</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Session", session_id or "—")
    with col2:
        st.metric("Processing", "Running" if is_reconciling else "Idle")
    with col3:
        st.metric("Errors", error_message is not None)

    if error_message:
        st.error(error_message)

