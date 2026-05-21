"""Streamlit entrypoint for Streamlit Cloud.

Some Streamlit Cloud setups only allow selecting the Main file path
from within the `backend/` folder. This file delegates to the real
Streamlit entry at repo root: `streamlit_app.py`.

It also ensures sys.path is set so imports work reliably.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent  # <repo>/backend
REPO_ROOT = HERE.parent

# Ensure repo root is importable so `import streamlit_app` works
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app import main as streamlit_main  # noqa: E402


if __name__ == "__main__":
    streamlit_main()

