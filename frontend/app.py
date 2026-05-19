import streamlit as st

# Ensure this script can import sibling package modules when executed as `streamlit run app.py`
# (which does not always set `d:/tally-reconcilliation` on PYTHONPATH).
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.components.download_section import download_report_section
from frontend.components.summary_cards import summary_cards
from frontend.components.uploader import upload_section
from frontend.components.status_box import status_box

from frontend.utils.ui_helpers import inject_streamlit_branding_css


def _init_session_state() -> None:
    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("reconcile_summary", None)
    st.session_state.setdefault("error_message", None)
    st.session_state.setdefault("is_reconciling", False)


def main() -> None:
    st.set_page_config(
        page_title="GST Reconciliation",
        page_icon="✅",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    inject_streamlit_branding_css()
    _init_session_state()

    st.title("GST Reconciliation Automation")
    st.caption("Upload GST portal export + Tally export, then reconcile and download CA-ready Excel report.")

    status_box(
        session_id=st.session_state.get("session_id"),
        is_reconciling=st.session_state.get("is_reconciling", False),
        error_message=st.session_state.get("error_message"),
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        gst_file = upload_section(label="GST Excel (GSTR1/GSTR2A/GSTR2B export)", file_key="gst_file", accept_ext=[".xlsx", ".xls"])

    with col_right:
        tally_file = upload_section(label="Tally Excel (Books export)", file_key="tally_file", accept_ext=[".xlsx", ".xls"])

    st.divider()

    start_col, _ = st.columns([2, 1])
    with start_col:
        if st.button(
            "Start Reconciliation",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.get("is_reconciling", False) or gst_file is None or tally_file is None,
        ):
            from frontend.services.api_service import reconcile_upload_and_run

            st.session_state["is_reconciling"] = True
            st.session_state["error_message"] = None
            st.session_state["session_id"] = None
            st.session_state["reconcile_summary"] = None

            with st.spinner("Uploading files and running reconciliation..."):
                try:
                    session_id, summary = reconcile_upload_and_run(
                        api_base_url=st.secrets.get("API_BASE_URL", "http://127.0.0.1:8000"),
                        gst_file=st.session_state.get("gst_file"),
                        tally_file=st.session_state.get("tally_file"),
                    )
                    st.session_state["session_id"] = session_id
                    st.session_state["reconcile_summary"] = summary
                    st.success("Reconciliation completed successfully.")
                except Exception as e:
                    st.session_state["error_message"] = str(e)
                    st.error("Reconciliation failed. See error above.")
                finally:
                    st.session_state["is_reconciling"] = False

    if st.session_state.get("reconcile_summary") is not None:
        st.divider()
        summary_cards(st.session_state["reconcile_summary"])
        st.divider()
        download_report_section(
            api_base_url=st.secrets.get("API_BASE_URL", "http://127.0.0.1:8000"),
            session_id=st.session_state.get("session_id"),
        )


if __name__ == "__main__":
    main()

