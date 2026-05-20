from pathlib import Path
import sys
import os
from threading import Thread

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BACKEND_APP_PATH = ROOT / "backend" / "app"
if str(BACKEND_APP_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_APP_PATH))

_LOCAL_API_THREAD_STARTED = False


def _start_local_api_if_needed() -> None:
    global _LOCAL_API_THREAD_STARTED
    if _LOCAL_API_THREAD_STARTED:
        return

    api_base_url = os.environ.get("API_BASE_URL")
    if api_base_url:
        return

    try:
        import uvicorn
        from backend.app.main import app as fastapi_app
    except Exception:
        # If the backend cannot be imported or uvicorn is unavailable, do not block
        return

    def _run_api() -> None:
        uvicorn.run(fastapi_app, host="127.0.0.1", port=8000, log_level="warning")

    thread = Thread(target=_run_api, daemon=True)
    thread.start()
    _LOCAL_API_THREAD_STARTED = True


def main() -> None:
    _start_local_api_if_needed()
    from frontend.app import main as app_main

    app_main()


if __name__ == "__main__":
    main()
