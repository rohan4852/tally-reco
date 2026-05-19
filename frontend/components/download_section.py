from __future__ import annotations

from typing import Optional

import streamlit as st

from frontend.services.api_service import get_download_url


def download_report_section(api_base_url: str, session_id: Optional[str]) -> None:
    if not session_id:
        return

    st.subheader("Download Report")
    download_url = get_download_url(api_base_url=api_base_url, session_id=session_id)

    # Streamlit's built-in download_button requires bytes; easiest is to fetch.
    # requests is already used in api_service, but importing requests here would be fine.
    import requests

    with st.spinner("Preparing Excel download..."):
        resp = requests.get(download_url, timeout=180)
        resp.raise_for_status()

    filename = f"reconciliation_{session_id}.xlsx"

    st.download_button(
        label="Download Excel Report",
        data=resp.content,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

