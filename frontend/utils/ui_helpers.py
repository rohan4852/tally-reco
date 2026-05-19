from __future__ import annotations

import streamlit as st


def inject_streamlit_branding_css() -> None:
    # Hide Streamlit default header/footer as much as possible.
    # Note: class names may differ between Streamlit versions.
    css = """
    <style>
      /* Hide Streamlit menu bar */
      #MainMenu {visibility: hidden;}
      /* Hide footer */
      footer {visibility: hidden;}
      /* Hide hamburger if present */
      header {padding-top: 0px;}
      /* Reduce top padding for clean look */
      .block-container {padding-top: 1rem;}
      /* Make metric cards feel modern */
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

