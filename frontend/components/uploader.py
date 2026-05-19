from __future__ import annotations

from typing import List, Optional

import streamlit as st


def upload_section(label: str, file_key: str, accept_ext: List[str]) -> Optional[object]:
    st.subheader(label)
    uploaded = st.file_uploader(
        label="Choose file",
        type=[ext.replace(".", "") for ext in accept_ext],
        accept_multiple_files=False,
        key=file_key,
    )
    return uploaded

