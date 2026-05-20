from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Make the backend app package importable as a top-level package when
# streamlit runs this root `main.py`.
BACKEND_APP_PATH = ROOT / "backend" / "app"
if str(BACKEND_APP_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_APP_PATH))

from streamlit_app import main as streamlit_main

if __name__ == "__main__":
    streamlit_main()
